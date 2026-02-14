"""Agent Swarm sub-resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..types import ListResponse, Swarm, SwarmMember, SwarmTask

if TYPE_CHECKING:
    from ..client import AgentWallet


class SwarmsResource:
    def __init__(self, client: AgentWallet):
        self._client = client

    # ── Swarm CRUD ──

    async def create(
        self,
        name: str,
        description: str,
        orchestrator_agent_id: str,
        swarm_type: str = "general",
        max_members: int = 10,
        is_public: bool = False,
        config: dict | None = None,
    ) -> Swarm:
        body: dict = {
            "name": name,
            "description": description,
            "orchestrator_agent_id": orchestrator_agent_id,
            "swarm_type": swarm_type,
            "max_members": max_members,
            "is_public": is_public,
        }
        if config:
            body["config"] = config
        data = await self._client.post("/swarms", json=body)
        return Swarm(**data)

    async def get(self, swarm_id: str) -> Swarm:
        data = await self._client.get(f"/swarms/{swarm_id}")
        return Swarm(**data)

    async def list(
        self,
        is_public: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ListResponse:
        params: dict = {"limit": limit, "offset": offset}
        if is_public is not None:
            params["is_public"] = is_public
        data = await self._client.get("/swarms", params=params)
        return ListResponse(
            data=[Swarm(**s) for s in data["swarms"]],
            total=data["total"],
        )

    # ── Members ──

    async def add_member(
        self,
        swarm_id: str,
        agent_id: str,
        role: str = "worker",
        specialization: str | None = None,
        is_contestable: bool = True,
    ) -> SwarmMember:
        body: dict = {
            "agent_id": agent_id,
            "role": role,
            "is_contestable": is_contestable,
        }
        if specialization:
            body["specialization"] = specialization
        data = await self._client.post(f"/swarms/{swarm_id}/members", json=body)
        return SwarmMember(**data)

    async def list_members(self, swarm_id: str) -> ListResponse:
        data = await self._client.get(f"/swarms/{swarm_id}/members")
        return ListResponse(
            data=[SwarmMember(**m) for m in data["members"]],
            total=data["total"],
        )

    async def remove_member(self, swarm_id: str, agent_id: str) -> dict:
        return await self._client.delete(f"/swarms/{swarm_id}/members/{agent_id}")

    # ── Tasks ──

    async def create_task(
        self,
        swarm_id: str,
        title: str,
        description: str,
        task_type: str = "general",
        client_agent_id: str | None = None,
    ) -> SwarmTask:
        body: dict = {
            "title": title,
            "description": description,
            "task_type": task_type,
        }
        if client_agent_id:
            body["client_agent_id"] = client_agent_id
        data = await self._client.post(f"/swarms/{swarm_id}/tasks", json=body)
        return SwarmTask(**data)

    async def get_task(self, swarm_id: str, task_id: str) -> SwarmTask:
        data = await self._client.get(f"/swarms/{swarm_id}/tasks/{task_id}")
        return SwarmTask(**data)

    async def list_tasks(
        self,
        swarm_id: str,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ListResponse:
        params: dict = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        data = await self._client.get(f"/swarms/{swarm_id}/tasks", params=params)
        return ListResponse(
            data=[SwarmTask(**t) for t in data["tasks"]],
            total=data["total"],
        )

    async def assign_subtask(
        self,
        swarm_id: str,
        task_id: str,
        subtask_id: str,
        agent_id: str,
        description: str,
    ) -> SwarmTask:
        data = await self._client.post(
            f"/swarms/{swarm_id}/tasks/{task_id}/assign",
            json={
                "subtask_id": subtask_id,
                "agent_id": agent_id,
                "description": description,
            },
        )
        return SwarmTask(**data)

    async def complete_subtask(
        self,
        swarm_id: str,
        task_id: str,
        subtask_id: str,
        result: dict,
    ) -> SwarmTask:
        data = await self._client.post(
            f"/swarms/{swarm_id}/tasks/{task_id}/complete",
            json={"subtask_id": subtask_id, "result": result},
        )
        return SwarmTask(**data)
