"""Agent Registry -- register, query, manage AI agents."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import ConflictError, NotFoundError, TierLimitError
from ..core.logging import get_logger
from ..models.agent import Agent

logger = get_logger(__name__)

TIER_AGENT_LIMITS = {"free": 3, "pro": 25, "enterprise": 999999}


class AgentRegistry:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_agent(
        self,
        org_id: uuid.UUID,
        org_tier: str,
        name: str,
        description: str | None = None,
        capabilities: list[str] | None = None,
        is_public: bool = False,
        metadata: dict | None = None,
    ) -> Agent:
        """Register a new agent. Auto-creates a default wallet."""
        # Check tier limit
        count = await self.db.scalar(
            select(func.count()).where(Agent.org_id == org_id)
        )
        limit = TIER_AGENT_LIMITS.get(org_tier, 3)
        if count >= limit:
            raise TierLimitError("agents", limit, org_tier)

        # Check name uniqueness within org
        existing = await self.db.scalar(
            select(Agent).where(Agent.org_id == org_id, Agent.name == name)
        )
        if existing:
            raise ConflictError(f"Agent '{name}' already exists in this organization")

        agent = Agent(
            org_id=org_id,
            name=name,
            description=description,
            capabilities=capabilities or [],
            is_public=is_public,
            metadata_=metadata or {},
        )
        self.db.add(agent)
        await self.db.flush()

        logger.info("agent_created", agent_id=str(agent.id), name=name)
        return agent

    async def get_agent(self, agent_id: uuid.UUID, org_id: uuid.UUID) -> Agent:
        agent = await self.db.get(Agent, agent_id)
        if not agent or agent.org_id != org_id:
            raise NotFoundError("Agent", str(agent_id))
        return agent

    async def list_agents(
        self,
        org_id: uuid.UUID,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Agent], int]:
        query = select(Agent).where(Agent.org_id == org_id)
        count_query = select(func.count()).select_from(Agent).where(Agent.org_id == org_id)

        if status:
            query = query.where(Agent.status == status)
            count_query = count_query.where(Agent.status == status)

        total = await self.db.scalar(count_query)
        result = await self.db.execute(query.offset(offset).limit(limit))
        return list(result.scalars().all()), total or 0

    async def update_agent(
        self,
        agent_id: uuid.UUID,
        org_id: uuid.UUID,
        **updates,
    ) -> Agent:
        agent = await self.get_agent(agent_id, org_id)
        for key, value in updates.items():
            if value is not None and hasattr(agent, key):
                setattr(agent, key, value)
        await self.db.flush()
        await self.db.refresh(agent)
        logger.info("agent_updated", agent_id=str(agent_id), updates=list(updates.keys()))
        return agent

    async def compute_reputation(self, agent_id: uuid.UUID, org_id: uuid.UUID) -> float:
        """Compute agent reputation score based on transaction history."""
        from ..models.transaction import Transaction

        agent = await self.get_agent(agent_id, org_id)

        total = await self.db.scalar(
            select(func.count()).where(Transaction.agent_id == agent_id)
        )
        confirmed = await self.db.scalar(
            select(func.count()).where(
                Transaction.agent_id == agent_id,
                Transaction.status == "confirmed",
            )
        )

        if not total:
            return 0.0

        success_rate = (confirmed or 0) / total
        volume_factor = min(total / 100, 1.0)  # scales up to 100 txns
        score = round(success_rate * 0.7 + volume_factor * 0.3, 2)

        agent.reputation_score = score
        await self.db.flush()
        return score

    async def list_public_agents(
        self, limit: int = 50, offset: int = 0
    ) -> tuple[list[Agent], int]:
        """Public directory of discoverable agents."""
        query = select(Agent).where(Agent.is_public.is_(True), Agent.status == "active")
        count_query = select(func.count()).select_from(Agent).where(
            Agent.is_public.is_(True), Agent.status == "active"
        )
        total = await self.db.scalar(count_query)
        result = await self.db.execute(
            query.order_by(Agent.reputation_score.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total or 0
