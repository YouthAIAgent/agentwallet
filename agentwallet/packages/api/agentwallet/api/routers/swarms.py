"""Agent Swarm router — cluster coordination for multi-agent tasks."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...services.swarm_service import SwarmService
from ..middleware.auth import AuthContext, get_auth_context
from ..schemas.swarms import (
    SubtaskAssign,
    SubtaskComplete,
    SwarmCreate,
    SwarmListResponse,
    SwarmMemberAdd,
    SwarmMemberListResponse,
    SwarmMemberResponse,
    SwarmResponse,
    SwarmTaskCreate,
    SwarmTaskListResponse,
    SwarmTaskResponse,
)

router = APIRouter(prefix="/swarms", tags=["Agent Swarms"])


def _swarm_to_response(swarm, member_count: int = 0) -> SwarmResponse:
    return SwarmResponse(
        id=swarm.id,
        org_id=swarm.org_id,
        name=swarm.name,
        description=swarm.description,
        orchestrator_agent_id=swarm.orchestrator_agent_id,
        swarm_type=swarm.swarm_type,
        max_members=swarm.max_members,
        is_active=swarm.is_active,
        is_public=swarm.is_public,
        total_tasks=swarm.total_tasks,
        completed_tasks=swarm.completed_tasks,
        avg_completion_time_hours=swarm.avg_completion_time_hours,
        config=swarm.config or {},
        created_at=swarm.created_at,
        updated_at=swarm.updated_at,
        member_count=member_count,
    )


# ── Swarm CRUD ──


@router.post("", response_model=SwarmResponse)
async def create_swarm(
    body: SwarmCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Create an agent swarm with an orchestrator. Orchestrator is auto-added as member."""
    svc = SwarmService(db)
    swarm = await svc.create_swarm(
        org_id=auth.org_id,
        name=body.name,
        description=body.description,
        orchestrator_agent_id=body.orchestrator_agent_id,
        swarm_type=body.swarm_type,
        max_members=body.max_members,
        is_public=body.is_public,
        config=body.config,
    )
    return _swarm_to_response(swarm, member_count=1)


@router.get("", response_model=SwarmListResponse)
async def list_swarms(
    is_public: bool | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """List swarms for the org."""
    svc = SwarmService(db)
    swarms, total = await svc.list_swarms(auth.org_id, is_public, limit, offset)
    return SwarmListResponse(
        swarms=[_swarm_to_response(s) for s in swarms],
        total=total,
    )


@router.get("/{swarm_id}", response_model=SwarmResponse)
async def get_swarm(
    swarm_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Get swarm details."""
    svc = SwarmService(db)
    swarm = await svc.get_swarm(swarm_id, auth.org_id)
    members = await svc.list_members(swarm_id, auth.org_id)
    return _swarm_to_response(swarm, member_count=len(members))


# ── Members ──


@router.post("/{swarm_id}/members", response_model=SwarmMemberResponse)
async def add_member(
    swarm_id: uuid.UUID,
    body: SwarmMemberAdd,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Add an agent to a swarm as worker, specialist, or evaluator."""
    svc = SwarmService(db)
    member = await svc.add_member(
        swarm_id, auth.org_id, body.agent_id, body.role, body.specialization, body.is_contestable,
    )
    return SwarmMemberResponse(
        id=member.id, swarm_id=member.swarm_id, agent_id=member.agent_id,
        role=member.role, specialization=member.specialization, is_contestable=member.is_contestable,
        is_active=member.is_active, tasks_completed=member.tasks_completed,
        avg_rating=member.avg_rating, joined_at=member.joined_at,
    )


@router.get("/{swarm_id}/members", response_model=SwarmMemberListResponse)
async def list_members(
    swarm_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """List all active members of a swarm."""
    svc = SwarmService(db)
    members = await svc.list_members(swarm_id, auth.org_id)
    return SwarmMemberListResponse(
        members=[SwarmMemberResponse(
            id=m.id, swarm_id=m.swarm_id, agent_id=m.agent_id,
            role=m.role, specialization=m.specialization, is_contestable=m.is_contestable,
            is_active=m.is_active, tasks_completed=m.tasks_completed,
            avg_rating=m.avg_rating, joined_at=m.joined_at,
        ) for m in members],
        total=len(members),
    )


@router.delete("/{swarm_id}/members/{agent_id}")
async def remove_member(
    swarm_id: uuid.UUID,
    agent_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Remove an agent from a swarm (cannot remove orchestrator)."""
    svc = SwarmService(db)
    await svc.remove_member(swarm_id, auth.org_id, agent_id)
    return {"status": "removed"}


# ── Tasks ──


@router.post("/{swarm_id}/tasks", response_model=SwarmTaskResponse)
async def create_task(
    swarm_id: uuid.UUID,
    body: SwarmTaskCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Submit a complex task to a swarm for decomposition and execution."""
    svc = SwarmService(db)
    task = await svc.create_task(
        swarm_id, auth.org_id, body.title, body.description, body.task_type, body.client_agent_id,
    )
    return SwarmTaskResponse(
        id=task.id, swarm_id=task.swarm_id, org_id=task.org_id,
        title=task.title, description=task.description, task_type=task.task_type,
        subtasks=task.subtasks or [], status=task.status, aggregated_result=task.aggregated_result,
        total_subtasks=task.total_subtasks, completed_subtasks=task.completed_subtasks,
        client_agent_id=task.client_agent_id, created_at=task.created_at,
        updated_at=task.updated_at, completed_at=task.completed_at,
    )


@router.get("/{swarm_id}/tasks", response_model=SwarmTaskListResponse)
async def list_tasks(
    swarm_id: uuid.UUID,
    status: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """List tasks for a swarm."""
    svc = SwarmService(db)
    tasks, total = await svc.list_tasks(swarm_id, auth.org_id, status, limit, offset)
    return SwarmTaskListResponse(
        tasks=[SwarmTaskResponse(
            id=t.id, swarm_id=t.swarm_id, org_id=t.org_id,
            title=t.title, description=t.description, task_type=t.task_type,
            subtasks=t.subtasks or [], status=t.status, aggregated_result=t.aggregated_result,
            total_subtasks=t.total_subtasks, completed_subtasks=t.completed_subtasks,
            client_agent_id=t.client_agent_id, created_at=t.created_at,
            updated_at=t.updated_at, completed_at=t.completed_at,
        ) for t in tasks],
        total=total,
    )


@router.get("/{swarm_id}/tasks/{task_id}", response_model=SwarmTaskResponse)
async def get_task(
    swarm_id: uuid.UUID,
    task_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Get task details with all subtasks."""
    svc = SwarmService(db)
    task = await svc.get_task(task_id, auth.org_id)
    return SwarmTaskResponse(
        id=task.id, swarm_id=task.swarm_id, org_id=task.org_id,
        title=task.title, description=task.description, task_type=task.task_type,
        subtasks=task.subtasks or [], status=task.status, aggregated_result=task.aggregated_result,
        total_subtasks=task.total_subtasks, completed_subtasks=task.completed_subtasks,
        client_agent_id=task.client_agent_id, created_at=task.created_at,
        updated_at=task.updated_at, completed_at=task.completed_at,
    )


@router.post("/{swarm_id}/tasks/{task_id}/assign", response_model=SwarmTaskResponse)
async def assign_subtask(
    swarm_id: uuid.UUID,
    task_id: uuid.UUID,
    body: SubtaskAssign,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Assign a subtask to a swarm member agent."""
    svc = SwarmService(db)
    task = await svc.assign_subtask(task_id, auth.org_id, body.subtask_id, body.agent_id, body.description)
    return SwarmTaskResponse(
        id=task.id, swarm_id=task.swarm_id, org_id=task.org_id,
        title=task.title, description=task.description, task_type=task.task_type,
        subtasks=task.subtasks or [], status=task.status, aggregated_result=task.aggregated_result,
        total_subtasks=task.total_subtasks, completed_subtasks=task.completed_subtasks,
        client_agent_id=task.client_agent_id, created_at=task.created_at,
        updated_at=task.updated_at, completed_at=task.completed_at,
    )


@router.post("/{swarm_id}/tasks/{task_id}/complete", response_model=SwarmTaskResponse)
async def complete_subtask(
    swarm_id: uuid.UUID,
    task_id: uuid.UUID,
    body: SubtaskComplete,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Mark a subtask as completed with results. Auto-aggregates when all done."""
    svc = SwarmService(db)
    task = await svc.complete_subtask(task_id, auth.org_id, body.subtask_id, body.result)
    return SwarmTaskResponse(
        id=task.id, swarm_id=task.swarm_id, org_id=task.org_id,
        title=task.title, description=task.description, task_type=task.task_type,
        subtasks=task.subtasks or [], status=task.status, aggregated_result=task.aggregated_result,
        total_subtasks=task.total_subtasks, completed_subtasks=task.completed_subtasks,
        client_agent_id=task.client_agent_id, created_at=task.created_at,
        updated_at=task.updated_at, completed_at=task.completed_at,
    )
