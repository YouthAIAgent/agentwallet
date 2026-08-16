"""Task marketplace router -- human posts task, agent executes, escrow settles."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.exceptions import ConflictError, NotFoundError, ValidationError
from ...services.task_service import TaskService
from ..middleware.auth import AuthContext, get_auth_context
from ..middleware.rate_limit import check_rate_limit
from ..schemas.task import (
    TaskAssign,
    TaskCreate,
    TaskDeliver,
    TaskRefund,
    TaskResponse,
    TaskStats,
)

router = APIRouter(prefix="/marketplace/tasks", tags=["marketplace-tasks"])


def _task_to_response(t) -> TaskResponse:
    agent = getattr(t, "agent", None)
    return TaskResponse(
        id=t.id,
        org_id=t.org_id,
        title=t.title,
        description=t.description,
        category=t.category,
        capability=t.capability,
        requirements=t.requirements or {},
        price_usdc=t.price_lamports / 1_000_000,
        token_symbol=t.token_symbol,
        platform_fee_usdc=t.platform_fee_lamports / 1_000_000,
        escrow_id=t.escrow_id,
        agent_id=t.agent_id,
        agent_name=agent.name if agent else None,
        agent_address=t.agent_address,
        status=t.status,
        result_data=t.result_data,
        delivery_notes=t.delivery_notes,
        provider=t.provider,
        model=t.model,
        posted_at=t.posted_at,
        funded_at=t.funded_at,
        assigned_at=t.assigned_at,
        delivered_at=t.delivered_at,
        released_at=t.released_at,
        created_at=t.created_at,
    )


@router.post("", response_model=TaskResponse, status_code=201)
async def post_task(
    req: TaskCreate,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Post a task — escrow is created and funded immediately."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = TaskService(db)
    try:
        task = await svc.post_task(
            org_id=auth.org_id,
            org_tier=auth.org_tier,
            title=req.title,
            description=req.description,
            price_lamports=int(req.price_usdc * 1_000_000),
            category=req.category,
            capability=req.capability,
            requirements=req.requirements,
            input_data=req.input_data,
            funder_wallet_id=req.funder_wallet_id,
        )
        # Auto-assign best matching agent (if requested)
        if req.auto_assign:
            try:
                assigned = await svc.auto_assign(task.id, auth.org_id, req.capability)
                if assigned:
                    task = assigned
            except (ValidationError, NotFoundError):
                pass
        await db.flush()
        await db.refresh(task)
        # Re-attach agent for the response
        from sqlalchemy import select
        from sqlalchemy.orm import joinedload

        from ...models.task import Task

        result = await db.execute(select(Task).options(joinedload(Task.agent)).where(Task.id == task.id))
        task = result.scalar_one()
        return _task_to_response(task)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    request: Request,
    status: str | None = None,
    category: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = TaskService(db)
    tasks = await svc.list_tasks(
        org_id=auth.org_id,
        status=status,
        category=category,
        limit=limit,
        offset=offset,
    )
    return [_task_to_response(t) for t in tasks]


@router.get("/stats", response_model=TaskStats)
async def task_stats(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = TaskService(db)
    data = await svc.stats(auth.org_id)
    return TaskStats(
        total_tasks=data["total_tasks"],
        delivered_tasks=data["delivered_tasks"],
        released_tasks=data["released_tasks"],
        platform_fees_usdc=data["platform_fees_lamports"] / 1_000_000,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = TaskService(db)
    try:
        task = await svc.get_task(task_id, auth.org_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _task_to_response(task)


@router.post("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: uuid.UUID,
    req: TaskAssign,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = TaskService(db)
    try:
        task = await svc.assign_agent(task_id, auth.org_id, req.agent_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _task_to_response(task)


@router.post("/{task_id}/run", response_model=TaskResponse)
async def run_task(
    task_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Mark the task in_progress so the worker picks it up for execution."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = TaskService(db)
    try:
        task = await svc.mark_in_progress(task_id, auth.org_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _task_to_response(task)


@router.post("/{task_id}/deliver", response_model=TaskResponse)
async def deliver_task(
    task_id: uuid.UUID,
    req: TaskDeliver,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Agent delivers results — escrow releases to the agent automatically."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = TaskService(db)
    try:
        task = await svc.deliver(
            task_id=task_id,
            org_id=auth.org_id,
            result_data=req.result_data,
            delivery_notes=req.delivery_notes,
            provider=req.provider,
            model=req.model,
            auto_release=req.auto_release,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _task_to_response(task)


@router.post("/{task_id}/refund", response_model=TaskResponse)
async def refund_task(
    task_id: uuid.UUID,
    req: TaskRefund,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = TaskService(db)
    try:
        task = await svc.refund(task_id, auth.org_id, req.reason)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _task_to_response(task)


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = TaskService(db)
    try:
        task = await svc.cancel(task_id, auth.org_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _task_to_response(task)
