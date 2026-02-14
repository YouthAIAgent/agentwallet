"""Agent Swarm schemas."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Swarm ──


class SwarmCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    orchestrator_agent_id: uuid.UUID
    swarm_type: str = Field("general", pattern="^(general|trading|research|content|security|data|custom)$")
    max_members: int = Field(10, ge=2, le=50)
    is_public: bool = False
    config: Dict[str, Any] = Field(default_factory=dict)


class SwarmResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    description: str
    orchestrator_agent_id: uuid.UUID
    swarm_type: str
    max_members: int
    is_active: bool
    is_public: bool
    total_tasks: int
    completed_tasks: int
    avg_completion_time_hours: float
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    member_count: int = 0


class SwarmListResponse(BaseModel):
    swarms: List[SwarmResponse]
    total: int


# ── Members ──


class SwarmMemberAdd(BaseModel):
    agent_id: uuid.UUID
    role: str = Field("worker", pattern="^(orchestrator|worker|specialist|evaluator)$")
    specialization: Optional[str] = Field(None, max_length=255)
    is_contestable: bool = True


class SwarmMemberResponse(BaseModel):
    id: uuid.UUID
    swarm_id: uuid.UUID
    agent_id: uuid.UUID
    role: str
    specialization: Optional[str]
    is_contestable: bool
    is_active: bool
    tasks_completed: int
    avg_rating: float
    joined_at: datetime


class SwarmMemberListResponse(BaseModel):
    members: List[SwarmMemberResponse]
    total: int


# ── Tasks ──


class SwarmTaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    task_type: str = Field("general")
    client_agent_id: Optional[uuid.UUID] = None


class SwarmTaskResponse(BaseModel):
    id: uuid.UUID
    swarm_id: uuid.UUID
    org_id: uuid.UUID
    title: str
    description: str
    task_type: str
    subtasks: List[Dict[str, Any]]
    status: str
    aggregated_result: Optional[Dict[str, Any]]
    total_subtasks: int
    completed_subtasks: int
    client_agent_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]


class SwarmTaskListResponse(BaseModel):
    tasks: List[SwarmTaskResponse]
    total: int


class SubtaskAssign(BaseModel):
    """Assign a subtask to a swarm member."""
    subtask_id: str
    agent_id: uuid.UUID
    description: str


class SubtaskComplete(BaseModel):
    """Mark a subtask as completed."""
    subtask_id: str
    result: Dict[str, Any]
