"""Webhook router -- configure webhook endpoints."""

import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...models.webhook import Webhook
from ..middleware.auth import AuthContext, get_auth_context
from ..middleware.rate_limit import check_rate_limit
from ..schemas.webhooks import (
    WebhookCreateRequest,
    WebhookListResponse,
    WebhookResponse,
    WebhookUpdateRequest,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _webhook_to_response(w: Webhook) -> WebhookResponse:
    return WebhookResponse(
        id=w.id,
        org_id=w.org_id,
        url=w.url,
        events=w.events,
        is_active=w.is_active,
        created_at=w.created_at.isoformat(),
    )


@router.post("", response_model=WebhookResponse, status_code=201)
async def create_webhook(
    req: WebhookCreateRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    webhook = Webhook(
        org_id=auth.org_id,
        url=req.url,
        events=req.events,
        secret=secrets.token_urlsafe(32),
    )
    db.add(webhook)
    await db.flush()
    return _webhook_to_response(webhook)


@router.get("", response_model=WebhookListResponse)
async def list_webhooks(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    count = await db.scalar(select(func.count()).select_from(Webhook).where(Webhook.org_id == auth.org_id))
    result = await db.execute(select(Webhook).where(Webhook.org_id == auth.org_id))
    webhooks = result.scalars().all()
    return WebhookListResponse(
        data=[_webhook_to_response(w) for w in webhooks],
        total=count or 0,
    )


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: uuid.UUID,
    req: WebhookUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    webhook = await db.get(Webhook, webhook_id)
    if not webhook or webhook.org_id != auth.org_id:
        raise HTTPException(status_code=404, detail="Webhook not found")

    for key, value in req.model_dump(exclude_none=True).items():
        setattr(webhook, key, value)
    await db.flush()
    return _webhook_to_response(webhook)


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    webhook = await db.get(Webhook, webhook_id)
    if not webhook or webhook.org_id != auth.org_id:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await db.delete(webhook)
    return {"status": "deleted"}
