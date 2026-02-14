"""Webhook dispatcher worker -- deliver webhook events with retries."""

import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select

from ..core.database import get_session_factory
from ..core.logging import get_logger
from ..models.webhook import WebhookDelivery
from .base import BaseWorker

logger = get_logger(__name__)


class WebhookDispatcherWorker(BaseWorker):
    name = "webhook_dispatcher"
    interval_seconds = 1.0

    async def tick(self) -> None:
        factory = get_session_factory()
        async with factory() as db:
            now = datetime.now(timezone.utc)
            result = await db.execute(
                select(WebhookDelivery)
                .where(
                    WebhookDelivery.delivered_at.is_(None),
                    WebhookDelivery.attempts < 5,
                    (WebhookDelivery.next_retry_at.is_(None) | (WebhookDelivery.next_retry_at <= now)),
                )
                .limit(20)
            )
            deliveries = result.scalars().all()

            if not deliveries:
                return

            async with httpx.AsyncClient(timeout=10) as client:
                for delivery in deliveries:
                    await self._deliver(client, delivery)

            await db.commit()

    async def _deliver(self, client: httpx.AsyncClient, delivery: WebhookDelivery) -> None:
        delivery.attempts += 1
        payload_json = json.dumps(delivery.payload)

        # Compute HMAC signature
        webhook = delivery.webhook
        signature = hmac.new(
            webhook.secret.encode(),
            payload_json.encode(),
            hashlib.sha256,
        ).hexdigest()

        try:
            resp = await client.post(
                webhook.url,
                content=payload_json,
                headers={
                    "Content-Type": "application/json",
                    "X-AgentWallet-Signature": f"sha256={signature}",
                    "X-AgentWallet-Event": delivery.event_type,
                },
            )
            delivery.status_code = resp.status_code
            delivery.response_body = resp.text[:1000]

            if 200 <= resp.status_code < 300:
                delivery.delivered_at = datetime.now(timezone.utc)
                logger.info(
                    "webhook_delivered",
                    delivery_id=str(delivery.id),
                    status=resp.status_code,
                )
            else:
                self._schedule_retry(delivery)
        except Exception as e:
            logger.warning(
                "webhook_delivery_failed",
                delivery_id=str(delivery.id),
                error=str(e),
                attempt=delivery.attempts,
            )
            self._schedule_retry(delivery)

    def _schedule_retry(self, delivery: WebhookDelivery) -> None:
        backoff = min(2**delivery.attempts, 300)  # max 5 minutes
        delivery.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=backoff)
