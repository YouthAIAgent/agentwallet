"""Policy router -- create, update, delete spending policies."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...models.policy import Policy
from ..middleware.auth import AuthContext, get_auth_context
from ..middleware.rate_limit import check_rate_limit
from ..schemas.policies import (
    PolicyCreateRequest,
    PolicyListResponse,
    PolicyResponse,
    PolicyUpdateRequest,
)

router = APIRouter(prefix="/policies", tags=["policies"])


def _policy_to_response(p: Policy) -> PolicyResponse:
    return PolicyResponse(
        id=p.id,
        org_id=p.org_id,
        name=p.name,
        rules=p.rules,
        scope_type=p.scope_type,
        scope_id=p.scope_id,
        priority=p.priority,
        enabled=p.enabled,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
    )


@router.post("", response_model=PolicyResponse, status_code=201)
async def create_policy(
    req: PolicyCreateRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    policy = Policy(
        org_id=auth.org_id,
        name=req.name,
        rules=req.rules,
        scope_type=req.scope_type,
        scope_id=req.scope_id,
        priority=req.priority,
        enabled=req.enabled,
    )
    db.add(policy)
    await db.flush()
    return _policy_to_response(policy)


@router.get("", response_model=PolicyListResponse)
async def list_policies(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    from sqlalchemy import func

    count = await db.scalar(select(func.count()).select_from(Policy).where(Policy.org_id == auth.org_id))
    result = await db.execute(
        select(Policy).where(Policy.org_id == auth.org_id).order_by(Policy.priority).offset(offset).limit(limit)
    )
    policies = result.scalars().all()
    return PolicyListResponse(
        data=[_policy_to_response(p) for p in policies],
        total=count or 0,
    )


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    policy = await db.get(Policy, policy_id)
    if not policy or policy.org_id != auth.org_id:
        raise HTTPException(status_code=404, detail="Policy not found")
    return _policy_to_response(policy)


@router.patch("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: uuid.UUID,
    req: PolicyUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    policy = await db.get(Policy, policy_id)
    if not policy or policy.org_id != auth.org_id:
        raise HTTPException(status_code=404, detail="Policy not found")

    for key, value in req.model_dump(exclude_none=True).items():
        setattr(policy, key, value)
    await db.flush()
    await db.refresh(policy)
    return _policy_to_response(policy)


@router.delete("/{policy_id}")
async def delete_policy(
    policy_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    policy = await db.get(Policy, policy_id)
    if not policy or policy.org_id != auth.org_id:
        raise HTTPException(status_code=404, detail="Policy not found")
    await db.delete(policy)
    return {"status": "deleted"}
