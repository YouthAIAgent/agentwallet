"""Agent request/response schemas."""

import uuid

from pydantic import BaseModel


class AgentCreateRequest(BaseModel):
    name: str
    description: str | None = None
    capabilities: list[str] = []
    is_public: bool = False
    metadata: dict = {}


class AgentUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    capabilities: list[str] | None = None
    is_public: bool | None = None
    metadata: dict | None = None


class AgentResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    description: str | None
    status: str
    capabilities: list
    default_wallet_id: uuid.UUID | None
    reputation_score: float
    is_public: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class AgentListResponse(BaseModel):
    data: list[AgentResponse]
    total: int
