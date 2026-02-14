"""Marketplace API schemas."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ServiceCreate(BaseModel):
    agent_id: uuid.UUID = Field(..., description="Agent offering the service")
    name: str = Field(..., min_length=1, max_length=255, description="Service name")
    description: str = Field(..., min_length=1, description="Service description")
    price_usdc: float = Field(..., gt=0, description="Price in USDC")
    capabilities: List[str] = Field(default_factory=list, description="Service capabilities")
    estimated_duration_hours: Optional[int] = Field(None, ge=1, description="Estimated completion time")
    max_concurrent_jobs: int = Field(1, ge=1, le=10, description="Maximum concurrent jobs")
    requirements: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Input requirements")
    delivery_format: Optional[str] = Field(None, max_length=100, description="Delivery format")


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    price_usdc: Optional[float] = Field(None, gt=0)
    capabilities: Optional[List[str]] = None
    estimated_duration_hours: Optional[int] = Field(None, ge=1)
    max_concurrent_jobs: Optional[int] = Field(None, ge=1, le=10)
    requirements: Optional[Dict[str, Any]] = None
    delivery_format: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class ServiceResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    name: str
    description: str
    price_usdc: float
    token_symbol: str
    capabilities: List[str]
    is_active: bool
    estimated_duration_hours: Optional[int]
    max_concurrent_jobs: int
    requirements: Dict[str, Any]
    delivery_format: Optional[str]
    total_jobs: int
    completed_jobs: int
    avg_rating: Optional[float]
    success_rate: float
    created_at: datetime
    updated_at: datetime

    # Agent info
    agent_name: Optional[str] = None
    agent_reputation_score: Optional[float] = None

    @field_validator("price_usdc", mode="before")
    @classmethod
    def convert_price_from_lamports(cls, v):
        if isinstance(v, int):  # If it's still in lamports
            return v / 1_000_000
        return v


class ServiceSearchRequest(BaseModel):
    query: Optional[str] = Field(None, description="Search query for name/description")
    capability: Optional[str] = Field(None, description="Required capability")
    max_price: Optional[float] = Field(None, gt=0, description="Maximum price in USDC")
    min_rating: Optional[float] = Field(None, ge=1, le=5, description="Minimum average rating")
    agent_id: Optional[uuid.UUID] = Field(None, description="Filter by specific agent")
    limit: int = Field(20, ge=1, le=100, description="Results limit")
    offset: int = Field(0, ge=0, description="Results offset")


class JobCreate(BaseModel):
    buyer_agent_id: uuid.UUID
    service_id: uuid.UUID
    seller_agent_id: uuid.UUID
    wallet_id: uuid.UUID
    input_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Job requirements")
    buyer_notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    deadline_hours: Optional[int] = Field(None, ge=1, description="Deadline in hours from now")


class JobResponse(BaseModel):
    id: uuid.UUID
    service_id: uuid.UUID
    buyer_agent_id: uuid.UUID
    seller_agent_id: uuid.UUID
    escrow_id: Optional[uuid.UUID]
    status: str
    input_data: Dict[str, Any]
    result_data: Optional[Dict[str, Any]]
    buyer_notes: Optional[str]
    seller_notes: Optional[str]
    rating: Optional[int]
    review: Optional[str]
    seller_response: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    deadline: Optional[datetime]

    # Related data
    service_name: Optional[str] = None
    service_price_usdc: Optional[float] = None
    buyer_agent_name: Optional[str] = None
    seller_agent_name: Optional[str] = None


class JobAccept(BaseModel):
    seller_agent_id: uuid.UUID = Field(..., description="Seller agent accepting the job")
    seller_notes: Optional[str] = Field(None, max_length=1000, description="Acceptance message")


class JobComplete(BaseModel):
    result_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Job results")
    completion_notes: Optional[str] = Field(None, max_length=1000, description="Completion notes")


class JobCancel(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500, description="Cancellation reason")


class JobRate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    review: Optional[str] = Field(None, max_length=1000, description="Written review")

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v):
        if not (1 <= v <= 5):
            raise ValueError("Rating must be between 1 and 5")
        return v


class JobMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000, description="Message content")
    message_type: str = Field("chat", description="Message type")
    attachments: Optional[Dict[str, Any]] = Field(default_factory=dict, description="File attachments")

    @field_validator("message_type")
    @classmethod
    def validate_message_type(cls, v):
        allowed_types = ["chat", "update", "delivery", "dispute"]
        if v not in allowed_types:
            raise ValueError(f"Message type must be one of: {allowed_types}")
        return v


class JobMessageResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    sender_agent_id: uuid.UUID
    message_type: str
    content: str
    attachments: Dict[str, Any]
    is_system_message: bool
    read_at: Optional[datetime]
    created_at: datetime

    # Sender info
    sender_agent_name: Optional[str] = None


class AgentReputationResponse(BaseModel):
    agent_id: uuid.UUID
    score: float
    total_jobs: int
    completed_jobs: int
    cancelled_jobs: int
    disputed_jobs: int
    avg_rating: Optional[float]
    rating_count: int
    five_star_count: int
    four_star_count: int
    three_star_count: int
    two_star_count: int
    one_star_count: int
    total_volume_usdc: float
    total_earnings_usdc: float
    total_spent_usdc: float
    avg_completion_time_hours: Optional[float]
    on_time_delivery_rate: float
    response_time_hours: Optional[float]
    reliability_score: float
    quality_score: float
    communication_score: float
    first_job_at: Optional[datetime]
    last_job_at: Optional[datetime]
    updated_at: datetime

    @field_validator("total_volume_usdc", "total_earnings_usdc", "total_spent_usdc", mode="before")
    @classmethod
    def convert_lamports_to_usdc(cls, v):
        if isinstance(v, int):  # If it's still in lamports
            return v / 1_000_000
        return v


class LeaderboardEntry(BaseModel):
    agent_id: uuid.UUID
    agent_name: str
    reputation_score: float
    total_jobs: int
    avg_rating: Optional[float]
    total_volume_usdc: float
    capabilities: List[str]
    active_services: int


class LeaderboardResponse(BaseModel):
    entries: List[LeaderboardEntry]
    total_agents: int
    category: Optional[str] = None
    min_jobs_filter: int


class ServiceAnalyticsResponse(BaseModel):
    service_id: uuid.UUID
    total_jobs: int
    completed_jobs: int
    cancelled_jobs: int
    active_jobs: int
    success_rate: float
    average_rating: Optional[float]
    total_revenue_usdc: float
    price_usdc: float


class MarketplaceStatsResponse(BaseModel):
    total_services: int
    active_services: int
    total_jobs: int
    completed_jobs: int
    total_volume_usdc: float
    average_job_value_usdc: float
    top_categories: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]


class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None
    code: Optional[str] = None
