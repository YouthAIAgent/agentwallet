"""ACP (Agent Commerce Protocol) sub-resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..types import AcpJob, AcpMemo, ListResponse, ResourceOffering

if TYPE_CHECKING:
    from ..client import AgentWallet


class AcpResource:
    def __init__(self, client: AgentWallet):
        self._client = client

    # ── Jobs ──

    async def create_job(
        self,
        buyer_agent_id: str,
        seller_agent_id: str,
        title: str,
        description: str,
        price_usdc: float,
        service_id: str | None = None,
        evaluator_agent_id: str | None = None,
        requirements: dict | None = None,
        deliverables: dict | None = None,
        fund_transfer: bool = False,
        principal_amount_usdc: float | None = None,
    ) -> AcpJob:
        body: dict = {
            "buyer_agent_id": buyer_agent_id,
            "seller_agent_id": seller_agent_id,
            "title": title,
            "description": description,
            "price_usdc": price_usdc,
            "fund_transfer": fund_transfer,
        }
        if service_id:
            body["service_id"] = service_id
        if evaluator_agent_id:
            body["evaluator_agent_id"] = evaluator_agent_id
        if requirements:
            body["requirements"] = requirements
        if deliverables:
            body["deliverables"] = deliverables
        if principal_amount_usdc is not None:
            body["principal_amount_usdc"] = principal_amount_usdc
        data = await self._client.post("/acp/jobs", json=body)
        return AcpJob(**data)

    async def get_job(self, job_id: str) -> AcpJob:
        data = await self._client.get(f"/acp/jobs/{job_id}")
        return AcpJob(**data)

    async def list_jobs(
        self,
        agent_id: str | None = None,
        phase: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ListResponse:
        params: dict = {"limit": limit, "offset": offset}
        if agent_id:
            params["agent_id"] = agent_id
        if phase:
            params["phase"] = phase
        data = await self._client.get("/acp/jobs", params=params)
        return ListResponse(
            data=[AcpJob(**j) for j in data["jobs"]],
            total=data["total"],
        )

    async def negotiate(
        self,
        job_id: str,
        seller_agent_id: str,
        agreed_terms: dict,
        agreed_price_usdc: float | None = None,
    ) -> AcpJob:
        body: dict = {"agreed_terms": agreed_terms}
        if agreed_price_usdc is not None:
            body["agreed_price_usdc"] = agreed_price_usdc
        data = await self._client._request(
            "POST", f"/acp/jobs/{job_id}/negotiate",
            json=body, params={"seller_agent_id": seller_agent_id},
        )
        return AcpJob(**data)

    async def fund(self, job_id: str, buyer_agent_id: str) -> AcpJob:
        data = await self._client._request(
            "POST", f"/acp/jobs/{job_id}/fund",
            params={"buyer_agent_id": buyer_agent_id},
        )
        return AcpJob(**data)

    async def deliver(
        self,
        job_id: str,
        seller_agent_id: str,
        result_data: dict,
        notes: str | None = None,
    ) -> AcpJob:
        body: dict = {"result_data": result_data}
        if notes:
            body["notes"] = notes
        data = await self._client._request(
            "POST", f"/acp/jobs/{job_id}/deliver",
            json=body, params={"seller_agent_id": seller_agent_id},
        )
        return AcpJob(**data)

    async def evaluate(
        self,
        job_id: str,
        evaluator_agent_id: str,
        approved: bool,
        evaluation_notes: str | None = None,
        rating: int | None = None,
    ) -> AcpJob:
        body: dict = {"approved": approved}
        if evaluation_notes:
            body["evaluation_notes"] = evaluation_notes
        if rating is not None:
            body["rating"] = rating
        data = await self._client._request(
            "POST", f"/acp/jobs/{job_id}/evaluate",
            json=body, params={"evaluator_agent_id": evaluator_agent_id},
        )
        return AcpJob(**data)

    # ── Memos ──

    async def send_memo(
        self,
        job_id: str,
        sender_agent_id: str,
        memo_type: str,
        content: dict,
        signature: str | None = None,
    ) -> AcpMemo:
        body: dict = {"memo_type": memo_type, "content": content}
        if signature:
            body["signature"] = signature
        data = await self._client._request(
            "POST", f"/acp/jobs/{job_id}/memos",
            json=body, params={"sender_agent_id": sender_agent_id},
        )
        return AcpMemo(**data)

    async def list_memos(self, job_id: str) -> ListResponse:
        data = await self._client.get(f"/acp/jobs/{job_id}/memos")
        return ListResponse(
            data=[AcpMemo(**m) for m in data["memos"]],
            total=data["total"],
        )

    # ── Resource Offerings ──

    async def create_offering(
        self,
        agent_id: str,
        name: str,
        description: str,
        endpoint_path: str,
        parameters: dict | None = None,
        response_schema: dict | None = None,
    ) -> ResourceOffering:
        data = await self._client.post("/acp/offerings", json={
            "agent_id": agent_id,
            "name": name,
            "description": description,
            "endpoint_path": endpoint_path,
            "parameters": parameters or {},
            "response_schema": response_schema or {},
        })
        return ResourceOffering(**data)

    async def list_offerings(
        self,
        agent_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ListResponse:
        params: dict = {"limit": limit, "offset": offset}
        if agent_id:
            params["agent_id"] = agent_id
        data = await self._client.get("/acp/offerings", params=params)
        return ListResponse(
            data=[ResourceOffering(**o) for o in data["offerings"]],
            total=data["total"],
        )
