"""Policy request/response schemas."""

import uuid

from pydantic import BaseModel


class PolicyCreateRequest(BaseModel):
    name: str
    rules: dict
    scope_type: str = "org"  # org, agent, wallet
    scope_id: uuid.UUID | None = None
    priority: int = 100
    enabled: bool = True


class PolicyUpdateRequest(BaseModel):
    name: str | None = None
    rules: dict | None = None
    priority: int | None = None
    enabled: bool | None = None


class PolicyResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    rules: dict
    scope_type: str
    scope_id: uuid.UUID | None
    priority: int
    enabled: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class PolicyListResponse(BaseModel):
    data: list[PolicyResponse]
    total: int
