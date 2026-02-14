"""Agent Swarm service — cluster coordination for multi-agent tasks."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.exceptions import NotFoundError, ValidationError, ConflictError
from ..models.swarm import AgentSwarm, SwarmMember, SwarmTask


class SwarmService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Swarm CRUD ──

    async def create_swarm(
        self,
        org_id: uuid.UUID,
        name: str,
        description: str,
        orchestrator_agent_id: uuid.UUID,
        swarm_type: str = "general",
        max_members: int = 10,
        is_public: bool = False,
        config: dict | None = None,
    ) -> AgentSwarm:
        swarm = AgentSwarm(
            org_id=org_id,
            name=name,
            description=description,
            orchestrator_agent_id=orchestrator_agent_id,
            swarm_type=swarm_type,
            max_members=max_members,
            is_public=is_public,
            config=config or {"fee_split": {"orchestrator": 0.2, "workers": 0.8}, "auto_assign": True},
        )
        self.db.add(swarm)
        await self.db.flush()
        await self.db.refresh(swarm)

        # Auto-add orchestrator as member
        member = SwarmMember(
            swarm_id=swarm.id,
            agent_id=orchestrator_agent_id,
            role="orchestrator",
            is_contestable=False,
        )
        self.db.add(member)
        await self.db.flush()

        return swarm

    async def get_swarm(self, swarm_id: uuid.UUID, org_id: uuid.UUID) -> AgentSwarm:
        result = await self.db.execute(
            select(AgentSwarm).where(AgentSwarm.id == swarm_id, AgentSwarm.org_id == org_id)
        )
        swarm = result.scalar_one_or_none()
        if not swarm:
            raise NotFoundError("swarm", str(swarm_id))
        return swarm

    async def list_swarms(
        self, org_id: uuid.UUID, is_public: bool | None = None, limit: int = 20, offset: int = 0
    ) -> tuple[list[AgentSwarm], int]:
        query = select(AgentSwarm).where(AgentSwarm.org_id == org_id, AgentSwarm.is_active == True)
        count_query = select(func.count()).select_from(AgentSwarm).where(
            AgentSwarm.org_id == org_id, AgentSwarm.is_active == True
        )
        if is_public is not None:
            query = query.where(AgentSwarm.is_public == is_public)
            count_query = count_query.where(AgentSwarm.is_public == is_public)

        total = (await self.db.execute(count_query)).scalar() or 0
        result = await self.db.execute(query.order_by(AgentSwarm.created_at.desc()).limit(limit).offset(offset))
        return list(result.scalars().all()), total

    # ── Members ──

    async def add_member(
        self,
        swarm_id: uuid.UUID,
        org_id: uuid.UUID,
        agent_id: uuid.UUID,
        role: str = "worker",
        specialization: str | None = None,
        is_contestable: bool = True,
    ) -> SwarmMember:
        swarm = await self.get_swarm(swarm_id, org_id)

        # Check max members
        count_result = await self.db.execute(
            select(func.count()).select_from(SwarmMember).where(
                SwarmMember.swarm_id == swarm_id, SwarmMember.is_active == True
            )
        )
        current_count = count_result.scalar() or 0
        if current_count >= swarm.max_members:
            raise ValidationError(f"Swarm is full ({swarm.max_members} members max)")

        # Check duplicate
        existing = await self.db.execute(
            select(SwarmMember).where(
                SwarmMember.swarm_id == swarm_id, SwarmMember.agent_id == agent_id, SwarmMember.is_active == True
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Agent is already a member of this swarm")

        member = SwarmMember(
            swarm_id=swarm_id,
            agent_id=agent_id,
            role=role,
            specialization=specialization,
            is_contestable=is_contestable,
        )
        self.db.add(member)
        await self.db.flush()
        await self.db.refresh(member)
        return member

    async def list_members(self, swarm_id: uuid.UUID, org_id: uuid.UUID) -> list[SwarmMember]:
        await self.get_swarm(swarm_id, org_id)
        result = await self.db.execute(
            select(SwarmMember).where(SwarmMember.swarm_id == swarm_id, SwarmMember.is_active == True)
        )
        return list(result.scalars().all())

    async def remove_member(self, swarm_id: uuid.UUID, org_id: uuid.UUID, agent_id: uuid.UUID) -> None:
        await self.get_swarm(swarm_id, org_id)
        result = await self.db.execute(
            select(SwarmMember).where(
                SwarmMember.swarm_id == swarm_id, SwarmMember.agent_id == agent_id, SwarmMember.is_active == True
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            raise NotFoundError("swarm_member", str(agent_id))
        if member.role == "orchestrator":
            raise ValidationError("Cannot remove the orchestrator from the swarm")
        member.is_active = False
        await self.db.flush()

    # ── Tasks ──

    async def create_task(
        self,
        swarm_id: uuid.UUID,
        org_id: uuid.UUID,
        title: str,
        description: str,
        task_type: str = "general",
        client_agent_id: uuid.UUID | None = None,
    ) -> SwarmTask:
        swarm = await self.get_swarm(swarm_id, org_id)

        task = SwarmTask(
            swarm_id=swarm_id,
            org_id=org_id,
            title=title,
            description=description,
            task_type=task_type,
            client_agent_id=client_agent_id,
            status="pending",
        )
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)

        # Update swarm stats
        swarm.total_tasks += 1
        await self.db.flush()

        return task

    async def get_task(self, task_id: uuid.UUID, org_id: uuid.UUID) -> SwarmTask:
        result = await self.db.execute(
            select(SwarmTask).where(SwarmTask.id == task_id, SwarmTask.org_id == org_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            raise NotFoundError("swarm_task", str(task_id))
        return task

    async def list_tasks(
        self, swarm_id: uuid.UUID, org_id: uuid.UUID, status: str | None = None, limit: int = 20, offset: int = 0
    ) -> tuple[list[SwarmTask], int]:
        query = select(SwarmTask).where(SwarmTask.swarm_id == swarm_id, SwarmTask.org_id == org_id)
        count_query = select(func.count()).select_from(SwarmTask).where(
            SwarmTask.swarm_id == swarm_id, SwarmTask.org_id == org_id
        )
        if status:
            query = query.where(SwarmTask.status == status)
            count_query = count_query.where(SwarmTask.status == status)

        total = (await self.db.execute(count_query)).scalar() or 0
        result = await self.db.execute(query.order_by(SwarmTask.created_at.desc()).limit(limit).offset(offset))
        return list(result.scalars().all()), total

    async def assign_subtask(
        self, task_id: uuid.UUID, org_id: uuid.UUID, subtask_id: str, agent_id: uuid.UUID, description: str
    ) -> SwarmTask:
        task = await self.get_task(task_id, org_id)

        subtasks = list(task.subtasks or [])
        subtasks.append({
            "id": subtask_id,
            "description": description,
            "assigned_agent_id": str(agent_id),
            "status": "assigned",
            "result": None,
        })
        task.subtasks = subtasks
        task.total_subtasks = len(subtasks)
        task.status = "in_progress"
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def complete_subtask(
        self, task_id: uuid.UUID, org_id: uuid.UUID, subtask_id: str, result: dict
    ) -> SwarmTask:
        task = await self.get_task(task_id, org_id)

        subtasks = list(task.subtasks or [])
        found = False
        for st in subtasks:
            if st.get("id") == subtask_id:
                st["status"] = "completed"
                st["result"] = result
                found = True
                break

        if not found:
            raise NotFoundError("subtask", subtask_id)

        task.subtasks = subtasks
        task.completed_subtasks = sum(1 for s in subtasks if s.get("status") == "completed")

        # Auto-complete task if all subtasks done
        if task.completed_subtasks >= task.total_subtasks and task.total_subtasks > 0:
            task.status = "completed"
            task.completed_at = datetime.now(timezone.utc)
            task.aggregated_result = {"subtask_results": [s.get("result") for s in subtasks if s.get("result")]}

            # Update swarm stats
            result_swarm = await self.db.execute(
                select(AgentSwarm).where(AgentSwarm.id == task.swarm_id)
            )
            swarm = result_swarm.scalar_one_or_none()
            if swarm:
                swarm.completed_tasks += 1

        await self.db.flush()
        await self.db.refresh(task)
        return task
