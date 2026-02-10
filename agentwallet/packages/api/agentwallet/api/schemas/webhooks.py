"""Webhook request/response schemas."""

import uuid

from pydantic import BaseModel


class WebhookCreateRequest(BaseModel):
    url: str
    events: list[str]


class WebhookUpdateRequest(BaseModel):
    url: str | None = None
    events: list[str] | None = None
    is_active: bool | None = None


class WebhookResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    url: str
    events: list[str]
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}


class WebhookListResponse(BaseModel):
    data: list[WebhookResponse]
    total: int
