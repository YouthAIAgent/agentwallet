"""ERC-8004 request/response schemas."""

import uuid

from pydantic import BaseModel, Field

# -- Requests --


class RegisterIdentityRequest(BaseModel):
    metadata_uri: str | None = None


class SubmitFeedbackRequest(BaseModel):
    to_agent_id: uuid.UUID
    rating: int = Field(ge=1, le=5)
    comment: str = ""
    task_reference: str | None = None


class BridgeEscrowFeedbackRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = ""


# -- Responses --


class IdentityResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    token_id: int | None
    evm_address: str
    chain_id: int
    metadata_uri: str | None
    status: str
    tx_hash: str | None
    created_at: str

    model_config = {"from_attributes": True}


class FeedbackResponse(BaseModel):
    id: uuid.UUID
    from_agent_id: uuid.UUID
    to_agent_id: uuid.UUID
    rating: int
    comment: str | None
    task_reference: str | None
    tx_hash: str | None
    status: str
    created_at: str

    model_config = {"from_attributes": True}


class ReputationResponse(BaseModel):
    agent_id: str
    erc8004_token_id: int | None
    evm_address: str | None
    reputation_score: float
    feedback_count: int
    on_chain_score: int | None


class FeedbackListResponse(BaseModel):
    data: list[FeedbackResponse]
    total: int


class EVMWalletResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    address: str
    chain_id: int
    label: str | None
    created_at: str

    model_config = {"from_attributes": True}
