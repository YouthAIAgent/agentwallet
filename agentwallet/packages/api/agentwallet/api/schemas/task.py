"""Task marketplace API schemas."""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Short task title")
    description: str = Field(..., min_length=1, description="What the agent should do")
    price_usdc: float = Field(
        ..., gt=0, description="Price in USDC (settles as SOL lamports internally)"
    )
    category: str = Field(
        "general", max_length=100, description="research | writing | coding | data | social | general"
    )
    capability: Optional[str] = Field(None, max_length=100, description="Requested agent capability")
    requirements: Optional[Dict[str, Any]] = Field(default_factory=dict)
    input_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    funder_wallet_id: Optional[uuid.UUID] = None
    auto_assign: bool = Field(True, description="Auto-assign best matching agent")
    auto_run: bool = Field(True, description="Start execution immediately (worker picks it up)")


class TaskResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    title: str
    description: str
    category: str
    capability: Optional[str]
    requirements: Dict[str, Any]
    price_usdc: float
    token_symbol: str
    platform_fee_usdc: float
    escrow_id: Optional[uuid.UUID]
    agent_id: Optional[uuid.UUID]
    agent_name: Optional[str]
    agent_address: Optional[str]
    status: str
    result_data: Optional[Dict[str, Any]]
    delivery_notes: Optional[str]
    provider: Optional[str]
    model: Optional[str]
    posted_at: datetime
    funded_at: Optional[datetime]
    assigned_at: Optional[datetime]
    delivered_at: Optional[datetime]
    released_at: Optional[datetime]
    created_at: datetime


class TaskDeliver(BaseModel):
    result_data: Dict[str, Any] = Field(..., description="Delivery payload")
    delivery_notes: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    auto_release: bool = Field(True, description="Release escrow to agent on delivery")


class TaskAssign(BaseModel):
    agent_id: uuid.UUID = Field(..., description="Agent to execute the task")


class TaskRefund(BaseModel):
    reason: str = Field("not started", max_length=500)


class TaskStats(BaseModel):
    total_tasks: int
    delivered_tasks: int
    released_tasks: int
    platform_fees_usdc: float
