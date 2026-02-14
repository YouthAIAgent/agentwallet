"""ACP (Agent Commerce Protocol) schemas."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── ACP Jobs ──


class AcpJobCreate(BaseModel):
    buyer_agent_id: uuid.UUID
    seller_agent_id: uuid.UUID
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    service_id: Optional[uuid.UUID] = None
    evaluator_agent_id: Optional[uuid.UUID] = None
    requirements: Dict[str, Any] = Field(default_factory=dict)
    deliverables: Dict[str, Any] = Field(default_factory=dict)
    price_usdc: float = Field(..., gt=0)
    fund_transfer: bool = False
    principal_amount_usdc: Optional[float] = None


class AcpJobResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    buyer_agent_id: uuid.UUID
    seller_agent_id: uuid.UUID
    evaluator_agent_id: Optional[uuid.UUID]
    service_id: Optional[uuid.UUID]
    phase: str
    title: str
    description: str
    requirements: Dict[str, Any]
    deliverables: Dict[str, Any]
    agreed_terms: Optional[Dict[str, Any]]
    agreed_price_lamports: int
    fund_transfer: bool
    escrow_id: Optional[uuid.UUID]
    result_data: Optional[Dict[str, Any]]
    evaluation_notes: Optional[str]
    evaluation_approved: Optional[bool]
    rating: Optional[int]
    swarm_task_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime
    negotiated_at: Optional[datetime]
    transacted_at: Optional[datetime]
    evaluated_at: Optional[datetime]
    completed_at: Optional[datetime]


class AcpNegotiate(BaseModel):
    """Submit negotiation terms to advance from request → negotiation."""
    agreed_terms: Dict[str, Any] = Field(..., description="Agreed scope, price, timeline")
    agreed_price_usdc: Optional[float] = Field(None, gt=0)


class AcpDeliver(BaseModel):
    """Submit deliverables to advance from transaction → evaluation."""
    result_data: Dict[str, Any] = Field(..., description="Job output/deliverables")
    notes: Optional[str] = None


class AcpEvaluate(BaseModel):
    """Evaluator approves or rejects deliverables."""
    approved: bool
    evaluation_notes: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)


# ── ACP Memos ──


class AcpMemoCreate(BaseModel):
    memo_type: str = Field(..., pattern="^(job_request|agreement|transaction|deliverable|evaluation|general)$")
    content: Dict[str, Any]
    signature: Optional[str] = None


class AcpMemoResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    sender_agent_id: uuid.UUID
    memo_type: str
    content: Dict[str, Any]
    signature: Optional[str]
    tx_signature: Optional[str]
    advances_phase: bool
    created_at: datetime


# ── Resource Offerings ──


class ResourceOfferingCreate(BaseModel):
    agent_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    endpoint_path: str = Field(..., min_length=1, max_length=500)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    response_schema: Dict[str, Any] = Field(default_factory=dict)


class ResourceOfferingResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    org_id: uuid.UUID
    name: str
    description: str
    endpoint_path: str
    parameters: Dict[str, Any]
    response_schema: Dict[str, Any]
    is_active: bool
    total_calls: int
    avg_response_ms: float
    created_at: datetime
    updated_at: datetime


# ── Lists ──


class AcpJobListResponse(BaseModel):
    jobs: List[AcpJobResponse]
    total: int
    limit: int
    offset: int


class AcpMemoListResponse(BaseModel):
    memos: List[AcpMemoResponse]
    total: int


class ResourceOfferingListResponse(BaseModel):
    offerings: List[ResourceOfferingResponse]
    total: int
