"""Agent router -- register, list, update AI agents."""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...services.agent_registry import AgentRegistry
from ...services.wallet_manager import WalletManager
from ..middleware.auth import AuthContext, get_auth_context
from ..middleware.rate_limit import check_rate_limit
from ..schemas.agents import (
    AgentCreateRequest,
    AgentListResponse,
    AgentResponse,
    AgentUpdateRequest,
)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(
    req: AgentCreateRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Register a new AI agent. Auto-creates a default wallet."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)

    registry = AgentRegistry(db)
    agent = await registry.create_agent(
        org_id=auth.org_id,
        org_tier=auth.org_tier,
        name=req.name,
        description=req.description,
        capabilities=req.capabilities,
        is_public=req.is_public,
        metadata=req.metadata,
    )

    # Auto-create default wallet
    wallet_mgr = WalletManager(db)
    wallet = await wallet_mgr.create_wallet(
        org_id=auth.org_id,
        org_tier=auth.org_tier,
        agent_id=agent.id,
        wallet_type="agent",
        label=f"{req.name}-wallet",
    )
    agent.default_wallet_id = wallet.id
    await db.flush()
    await db.refresh(agent)

    return AgentResponse(
        id=agent.id,
        org_id=agent.org_id,
        name=agent.name,
        description=agent.description,
        status=agent.status,
        capabilities=agent.capabilities,
        default_wallet_id=agent.default_wallet_id,
        reputation_score=agent.reputation_score,
        is_public=agent.is_public,
        created_at=agent.created_at.isoformat(),
        updated_at=agent.updated_at.isoformat(),
    )


@router.get("", response_model=AgentListResponse)
async def list_agents(
    request: Request,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    registry = AgentRegistry(db)
    agents, total = await registry.list_agents(org_id=auth.org_id, status=status, limit=limit, offset=offset)
    return AgentListResponse(
        data=[
            AgentResponse(
                id=a.id,
                org_id=a.org_id,
                name=a.name,
                description=a.description,
                status=a.status,
                capabilities=a.capabilities,
                default_wallet_id=a.default_wallet_id,
                reputation_score=a.reputation_score,
                is_public=a.is_public,
                created_at=a.created_at.isoformat(),
                updated_at=a.updated_at.isoformat(),
            )
            for a in agents
        ],
        total=total,
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    registry = AgentRegistry(db)
    agent = await registry.get_agent(agent_id, auth.org_id)
    return AgentResponse(
        id=agent.id,
        org_id=agent.org_id,
        name=agent.name,
        description=agent.description,
        status=agent.status,
        capabilities=agent.capabilities,
        default_wallet_id=agent.default_wallet_id,
        reputation_score=agent.reputation_score,
        is_public=agent.is_public,
        created_at=agent.created_at.isoformat(),
        updated_at=agent.updated_at.isoformat(),
    )


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: uuid.UUID,
    req: AgentUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    registry = AgentRegistry(db)
    agent = await registry.update_agent(
        agent_id=agent_id,
        org_id=auth.org_id,
        **req.model_dump(exclude_none=True),
    )
    return AgentResponse(
        id=agent.id,
        org_id=agent.org_id,
        name=agent.name,
        description=agent.description,
        status=agent.status,
        capabilities=agent.capabilities,
        default_wallet_id=agent.default_wallet_id,
        reputation_score=agent.reputation_score,
        is_public=agent.is_public,
        created_at=agent.created_at.isoformat(),
        updated_at=agent.updated_at.isoformat(),
    )
