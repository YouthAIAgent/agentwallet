"""Task Service -- human-facing task marketplace lifecycle.

A human posts a task, the platform creates an escrow and funds it, an
agent is assigned, the agent executes (TaskWorker), and the escrow
releases to the agent's wallet on delivery. Refund available before work
starts or when the agent cannot complete.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..core.config import get_settings
from ..core.exceptions import NotFoundError, ValidationError
from ..models.agent import Agent
from ..models.task import Task
from ..models.wallet import Wallet
from ..services.escrow_service import EscrowService
from ..services.fee_collector import FeeCollector

# Allowed status transitions
TASK_TRANSITIONS = {
    "posted": ["funded", "cancelled"],
    "funded": ["assigned", "in_progress", "refunded", "cancelled"],
    "assigned": ["in_progress", "refunded", "cancelled"],
    "in_progress": ["delivered", "refunded", "disputed"],
    "delivered": ["released", "disputed"],
    "released": [],
    "refunded": [],
    "disputed": ["released", "refunded"],
    "cancelled": [],
}


class TaskService:
    """Lifecycle management for human->agent tasks backed by on-chain escrow."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.escrow_service = EscrowService(session)
        self.fee_collector = FeeCollector()

    # ── Helpers ──────────────────────────────────────────

    async def _get_task(self, task_id: uuid.UUID, org_id: uuid.UUID) -> Task:
        result = await self.session.execute(
            select(Task)
            .options(joinedload(Task.agent))
            .where(and_(Task.id == task_id, Task.org_id == org_id))
        )
        task = result.scalar_one_or_none()
        if not task:
            raise NotFoundError("Task", str(task_id))
        return task

    def _validate_transition(self, current: str, next_state: str) -> None:
        allowed = TASK_TRANSITIONS.get(current, [])
        if next_state not in allowed:
            raise ValidationError(f"Task cannot transition from '{current}' to '{next_state}'")

    # ── Post + fund ──────────────────────────────────────

    async def post_task(
        self,
        org_id: uuid.UUID,
        org_tier: str,
        title: str,
        description: str,
        price_lamports: int,
        category: str = "general",
        capability: Optional[str] = None,
        requirements: Optional[Dict[str, Any]] = None,
        input_data: Optional[Dict[str, Any]] = None,
        funder_wallet_id: Optional[uuid.UUID] = None,
        token_symbol: str = "SOL",
    ) -> Task:
        """Post a task and fund it in escrow atomically.

        If funder_wallet_id is not given, the org's default wallet is used.
        The price (minus platform fee) is locked into an escrow that
        releases to the assigned agent on delivery.
        """
        if price_lamports <= 0:
            raise ValidationError("Task price must be greater than zero")

        # Resolve the funder wallet (org default if not specified)
        if funder_wallet_id:
            wallet = await self.session.get(Wallet, funder_wallet_id)
            if not wallet or wallet.org_id != org_id:
                raise NotFoundError("Wallet", str(funder_wallet_id))
        else:
            wallet_result = await self.session.execute(
                select(Wallet)
                .where(and_(Wallet.org_id == org_id, Wallet.is_active))
                .order_by(Wallet.created_at)
                .limit(1)
            )
            wallet = wallet_result.scalar_one_or_none()
            if not wallet:
                raise ValidationError("No funder wallet available — create a wallet first")

        fee = self.fee_collector.calculate_fee(price_lamports, org_tier)
        agent_payout = price_lamports - fee

        task = Task(
            org_id=org_id,
            title=title,
            description=description,
            category=category,
            capability=capability,
            requirements=requirements or {},
            input_data=input_data or {},
            price_lamports=price_lamports,
            token_symbol=token_symbol,
            platform_fee_lamports=fee,
            funder_wallet_id=wallet.id,
            status="posted",
        )
        self.session.add(task)
        await self.session.flush()

        # Create + fund escrow (funds move to platform custody on-chain)
        escrow = await self.escrow_service.create_escrow(
            org_id=org_id,
            funder_wallet_id=wallet.id,
            recipient_address=settings_platform_address(),
            amount_lamports=price_lamports,
            token_mint=None,
            conditions={
                "task_type": "human_task",
                "task_id": str(task.id),
                "title": title,
                "platform_fee_lamports": fee,
                "agent_payout_lamports": agent_payout,
                "completion_criteria": "Agent delivers results matching the task description",
            },
            expires_in_hours=48,
        )

        task.escrow_id = escrow.id
        task.status = "funded" if escrow.status == "funded" else "posted"
        if escrow.status == "funded":
            task.funded_at = datetime.now(timezone.utc)
        await self.session.flush()
        return task

    # ── Agent assignment ─────────────────────────────────

    async def assign_agent(self, task_id: uuid.UUID, org_id: uuid.UUID, agent_id: uuid.UUID) -> Task:
        """Assign an agent to execute the task.

        Allows assigning public specialists from other organizations so any
        org can hire from the marketplace roster.
        """
        task = await self._get_task(task_id, org_id)
        if task.status not in ("funded", "posted"):
            raise ValidationError(f"Cannot assign agent to task in '{task.status}' state")

        agent = await self.session.get(Agent, agent_id)
        if not agent or (agent.org_id != org_id and not agent.is_public):
            raise NotFoundError("Agent", str(agent_id))

        # Resolve the agent's payout address (its default wallet)
        from ..models.wallet import Wallet

        wallet_result = await self.session.execute(
            select(Wallet.address).where(and_(Wallet.agent_id == agent_id, Wallet.is_active)).limit(1)
        )
        agent_address = wallet_result.scalar_one_or_none()
        if not agent_address:
            raise ValidationError("Agent has no active wallet to receive payment")

        task.agent_id = agent_id
        task.agent_address = agent_address
        task.status = "assigned"
        task.assigned_at = datetime.now(timezone.utc)
        await self.session.flush()
        return task

    async def auto_assign(
        self, task_id: uuid.UUID, org_id: uuid.UUID, capability: Optional[str] = None
    ) -> Optional[Task]:
        """Pick the best available agent and assign it.

        Preference order:
          1. An active agent in the task's own org whose capabilities match
             the requested capability (best local fit).
          2. A public specialist (is_public=True, any org) whose capabilities
             match the requested capability (best specialist fit).
          3. Any active agent in the task's own org.
          4. Any public specialist.

        Capability matching happens in Python so it works identically across
        SQLite (tests) and Postgres (prod) JSON columns.
        """
        await self._get_task(task_id, org_id)  # validate ownership + existence

        def _match(a: Agent) -> bool:
            if capability:
                caps = a.capabilities or []
                return capability in caps
            return True

        # 1: task org's own agents with a capability match
        org_result = await self.session.execute(
            select(Agent)
            .where(and_(Agent.org_id == org_id, Agent.status == "active"))
            .order_by(Agent.reputation_score.desc())
        )
        org_agents = list(org_result.scalars().all())
        for a in org_agents:
            if _match(a):
                return await self.assign_agent(task_id, org_id, a.id)

        # 2: public specialists from the marketplace roster with a capability match
        public_result = await self.session.execute(
            select(Agent)
            .where(and_(Agent.is_public.is_(True), Agent.status == "active"))
            .order_by(Agent.reputation_score.desc())
        )
        public_agents = list(public_result.scalars().all())
        for a in public_agents:
            if _match(a):
                return await self.assign_agent(task_id, org_id, a.id)

        # 3: any active org agent
        if org_agents:
            return await self.assign_agent(task_id, org_id, org_agents[0].id)

        # 4: any public specialist
        if public_agents:
            return await self.assign_agent(task_id, org_id, public_agents[0].id)

        return None

    # ── Execution ────────────────────────────────────────

    async def mark_in_progress(self, task_id: uuid.UUID, org_id: uuid.UUID) -> Task:
        task = await self._get_task(task_id, org_id)
        self._validate_transition(task.status, "in_progress")
        task.status = "in_progress"
        await self.session.flush()
        return task

    async def deliver(
        self,
        task_id: uuid.UUID,
        org_id: uuid.UUID,
        result_data: Dict[str, Any],
        delivery_notes: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        auto_release: bool = True,
    ) -> Task:
        """Record agent delivery and release the escrow to the agent."""
        task = await self._get_task(task_id, org_id)
        if task.status not in ("in_progress", "assigned"):
            raise ValidationError(f"Cannot deliver task in '{task.status}' state")

        task.result_data = result_data
        task.delivery_notes = delivery_notes
        task.provider = provider
        task.model = model
        task.status = "delivered"
        task.delivered_at = datetime.now(timezone.utc)
        await self.session.flush()

        if auto_release and task.escrow_id:
            await self.escrow_service.release_escrow(task.escrow_id, org_id)
            task.status = "released"
            task.released_at = datetime.now(timezone.utc)
            await self.session.flush()
        return task

    # ── Refund / dispute / cancel ────────────────────────

    async def refund(self, task_id: uuid.UUID, org_id: uuid.UUID, reason: str = "not started") -> Task:
        task = await self._get_task(task_id, org_id)
        self._validate_transition(task.status, "refunded")
        if task.escrow_id:
            await self.escrow_service.refund_escrow(task.escrow_id, org_id)
        task.status = "refunded"
        task.delivery_notes = reason
        await self.session.flush()
        return task

    async def cancel(self, task_id: uuid.UUID, org_id: uuid.UUID, reason: str = "cancelled by user") -> Task:
        task = await self._get_task(task_id, org_id)
        self._validate_transition(task.status, "cancelled")
        if task.escrow_id and task.status in ("posted", "funded"):
            try:
                await self.escrow_service.refund_escrow(task.escrow_id, org_id)
            except Exception:
                pass
        task.status = "cancelled"
        task.delivery_notes = reason
        await self.session.flush()
        return task

    # ── Query ────────────────────────────────────────────

    async def list_tasks(
        self,
        org_id: uuid.UUID,
        status: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Task]:
        stmt = (
            select(Task)
            .options(joinedload(Task.agent))
            .where(Task.org_id == org_id)
            .order_by(desc(Task.created_at))
        )
        if status:
            stmt = stmt.where(Task.status == status)
        if category:
            stmt = stmt.where(Task.category == category)
        result = await self.session.execute(stmt.limit(limit).offset(offset))
        return list(result.scalars().all())

    async def get_task(self, task_id: uuid.UUID, org_id: uuid.UUID) -> Task:
        return await self._get_task(task_id, org_id)

    async def stats(self, org_id: uuid.UUID) -> Dict[str, Any]:
        result = await self.session.execute(
            select(
                func.count(Task.id).label("total"),
                func.count(Task.id).filter(Task.status == "delivered").label("delivered"),
                func.count(Task.id).filter(Task.status == "released").label("released"),
                func.coalesce(func.sum(Task.platform_fee_lamports), 0).label("fees"),
            ).where(Task.org_id == org_id)
        )
        row = result.first()
        return {
            "total_tasks": row.total or 0,
            "delivered_tasks": row.delivered or 0,
            "released_tasks": row.released or 0,
            "platform_fees_lamports": row.fees or 0,
        }


def settings_platform_address() -> str:
    """Return the platform custody address (recipient of escrow funds)."""
    return get_settings().platform_wallet_address
