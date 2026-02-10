"""Billing Service -- Stripe subscription and usage-based billing."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.logging import get_logger
from ..models.usage_meter import UsageMeter

logger = get_logger(__name__)

TIER_PRICES = {
    "free": 0,
    "pro": 4900,        # $49/mo in cents
    "enterprise": 29900, # $299+/mo in cents
}


class BillingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_current_usage(self, org_id: uuid.UUID) -> dict:
        """Get current billing period usage."""
        now = datetime.now(timezone.utc)
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        meter = await self.db.scalar(
            select(UsageMeter).where(
                UsageMeter.org_id == org_id,
                UsageMeter.period_start == period_start,
            )
        )

        if meter:
            return {
                "period_start": meter.period_start.isoformat(),
                "period_end": meter.period_end.isoformat(),
                "tx_count": meter.tx_count,
                "tx_volume_lamports": meter.tx_volume_lamports,
                "api_calls": meter.api_calls,
                "escrow_count": meter.escrow_count,
            }

        return {
            "period_start": period_start.isoformat(),
            "period_end": now.isoformat(),
            "tx_count": 0,
            "tx_volume_lamports": 0,
            "api_calls": 0,
            "escrow_count": 0,
        }

    async def increment_usage(
        self,
        org_id: uuid.UUID,
        tx_count: int = 0,
        tx_volume: int = 0,
        api_calls: int = 0,
        escrow_count: int = 0,
    ) -> None:
        """Increment usage counters for the current period."""
        now = datetime.now(timezone.utc)
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # next month
        if now.month == 12:
            period_end = period_start.replace(year=now.year + 1, month=1)
        else:
            period_end = period_start.replace(month=now.month + 1)

        meter = await self.db.scalar(
            select(UsageMeter).where(
                UsageMeter.org_id == org_id,
                UsageMeter.period_start == period_start,
            )
        )

        if meter:
            meter.tx_count += tx_count
            meter.tx_volume_lamports += tx_volume
            meter.api_calls += api_calls
            meter.escrow_count += escrow_count
        else:
            meter = UsageMeter(
                org_id=org_id,
                period_start=period_start,
                period_end=period_end,
                tx_count=tx_count,
                tx_volume_lamports=tx_volume,
                api_calls=api_calls,
                escrow_count=escrow_count,
            )
            self.db.add(meter)

        await self.db.flush()

    async def create_stripe_customer(self, org_id: uuid.UUID, email: str) -> str | None:
        """Create a Stripe customer for the org."""
        settings = get_settings()
        if not settings.stripe_secret_key:
            return None

        import stripe
        stripe.api_key = settings.stripe_secret_key

        customer = stripe.Customer.create(
            email=email,
            metadata={"org_id": str(org_id)},
        )
        return customer.id

    async def create_subscription(
        self, stripe_customer_id: str, tier: str
    ) -> dict | None:
        """Create a Stripe subscription."""
        settings = get_settings()
        if not settings.stripe_secret_key:
            return None

        import stripe
        stripe.api_key = settings.stripe_secret_key

        # Would use actual Stripe price IDs
        price_lookup = {
            "pro": "price_pro_monthly",
            "enterprise": "price_enterprise_monthly",
        }

        price_id = price_lookup.get(tier)
        if not price_id:
            return None

        subscription = stripe.Subscription.create(
            customer=stripe_customer_id,
            items=[{"price": price_id}],
        )
        return {"subscription_id": subscription.id, "status": subscription.status}
