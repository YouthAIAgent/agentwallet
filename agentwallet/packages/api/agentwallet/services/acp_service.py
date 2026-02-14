"""ACP (Agent Commerce Protocol) service — 4-phase job lifecycle."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import NotFoundError, ValidationError, EscrowStateError
from ..models.acp import AcpJob, AcpMemo, ResourceOffering

# Valid phase transitions
PHASE_TRANSITIONS = {
    "request": ["negotiation", "cancelled"],
    "negotiation": ["transaction", "cancelled"],
    "transaction": ["evaluation", "cancelled", "disputed"],
    "evaluation": ["completed", "disputed"],
    "disputed": ["resolved", "cancelled"],
}


class AcpService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_job(
        self,
        org_id: uuid.UUID,
        buyer_agent_id: uuid.UUID,
        seller_agent_id: uuid.UUID,
        title: str,
        description: str,
        price_lamports: int,
        service_id: uuid.UUID | None = None,
        evaluator_agent_id: uuid.UUID | None = None,
        requirements: dict | None = None,
        deliverables: dict | None = None,
        fund_transfer: bool = False,
        principal_amount_lamports: int | None = None,
    ) -> AcpJob:
        job = AcpJob(
            org_id=org_id,
            buyer_agent_id=buyer_agent_id,
            seller_agent_id=seller_agent_id,
            evaluator_agent_id=evaluator_agent_id,
            service_id=service_id,
            title=title,
            description=description,
            agreed_price_lamports=price_lamports,
            requirements=requirements or {},
            deliverables=deliverables or {},
            fund_transfer=fund_transfer,
            principal_amount_lamports=principal_amount_lamports,
            phase="request",
        )
        self.db.add(job)
        await self.db.flush()
        await self.db.refresh(job)

        # Auto-create initial memo
        memo = AcpMemo(
            job_id=job.id,
            sender_agent_id=buyer_agent_id,
            memo_type="job_request",
            content={"title": title, "description": description, "price": price_lamports},
            advances_phase=False,
        )
        self.db.add(memo)
        await self.db.flush()

        return job

    async def get_job(self, job_id: uuid.UUID, org_id: uuid.UUID) -> AcpJob:
        result = await self.db.execute(
            select(AcpJob).where(AcpJob.id == job_id, AcpJob.org_id == org_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            raise NotFoundError("acp_job", str(job_id))
        return job

    async def list_jobs(
        self,
        org_id: uuid.UUID,
        agent_id: uuid.UUID | None = None,
        phase: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[AcpJob], int]:
        query = select(AcpJob).where(AcpJob.org_id == org_id)
        count_query = select(func.count()).select_from(AcpJob).where(AcpJob.org_id == org_id)

        if agent_id:
            agent_filter = (AcpJob.buyer_agent_id == agent_id) | (AcpJob.seller_agent_id == agent_id)
            query = query.where(agent_filter)
            count_query = count_query.where(agent_filter)
        if phase:
            query = query.where(AcpJob.phase == phase)
            count_query = count_query.where(AcpJob.phase == phase)

        total = (await self.db.execute(count_query)).scalar() or 0
        result = await self.db.execute(
            query.order_by(AcpJob.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all()), total

    async def advance_phase(
        self,
        job_id: uuid.UUID,
        org_id: uuid.UUID,
        agent_id: uuid.UUID,
        target_phase: str,
        memo_type: str,
        content: dict,
    ) -> AcpJob:
        job = await self.get_job(job_id, org_id)

        valid_targets = PHASE_TRANSITIONS.get(job.phase, [])
        if target_phase not in valid_targets:
            raise EscrowStateError(
                f"Cannot transition from '{job.phase}' to '{target_phase}'. "
                f"Valid transitions: {valid_targets}"
            )

        now = datetime.now(timezone.utc)
        job.phase = target_phase
        job.updated_at = now

        if target_phase == "negotiation":
            job.negotiated_at = now
        elif target_phase == "transaction":
            job.transacted_at = now
        elif target_phase == "evaluation":
            job.evaluated_at = now
        elif target_phase == "completed":
            job.completed_at = now

        # Create phase-advancing memo
        memo = AcpMemo(
            job_id=job.id,
            sender_agent_id=agent_id,
            memo_type=memo_type,
            content=content,
            advances_phase=True,
        )
        self.db.add(memo)
        await self.db.flush()
        await self.db.refresh(job)
        return job

    async def negotiate(
        self, job_id: uuid.UUID, org_id: uuid.UUID, seller_agent_id: uuid.UUID, terms: dict, price_lamports: int | None = None
    ) -> AcpJob:
        job = await self.get_job(job_id, org_id)
        if job.seller_agent_id != seller_agent_id:
            raise ValidationError("Only the seller agent can negotiate")

        job.agreed_terms = terms
        if price_lamports is not None:
            job.agreed_price_lamports = price_lamports

        return await self.advance_phase(
            job_id, org_id, seller_agent_id, "negotiation", "agreement", terms
        )

    async def start_transaction(
        self, job_id: uuid.UUID, org_id: uuid.UUID, buyer_agent_id: uuid.UUID
    ) -> AcpJob:
        job = await self.get_job(job_id, org_id)
        if job.buyer_agent_id != buyer_agent_id:
            raise ValidationError("Only the buyer agent can fund the transaction")

        return await self.advance_phase(
            job_id, org_id, buyer_agent_id, "transaction", "transaction",
            {"funded": True, "amount": job.agreed_price_lamports}
        )

    async def deliver(
        self, job_id: uuid.UUID, org_id: uuid.UUID, seller_agent_id: uuid.UUID, result_data: dict, notes: str | None = None
    ) -> AcpJob:
        job = await self.get_job(job_id, org_id)
        if job.seller_agent_id != seller_agent_id:
            raise ValidationError("Only the seller agent can deliver")

        job.result_data = result_data
        return await self.advance_phase(
            job_id, org_id, seller_agent_id, "evaluation", "deliverable",
            {"result": result_data, "notes": notes}
        )

    async def evaluate(
        self, job_id: uuid.UUID, org_id: uuid.UUID, evaluator_id: uuid.UUID, approved: bool, notes: str | None = None, rating: int | None = None
    ) -> AcpJob:
        job = await self.get_job(job_id, org_id)

        # Evaluator must be the designated evaluator or the buyer
        if job.evaluator_agent_id and job.evaluator_agent_id != evaluator_id:
            if job.buyer_agent_id != evaluator_id:
                raise ValidationError("Only the evaluator or buyer can evaluate")
        elif not job.evaluator_agent_id and job.buyer_agent_id != evaluator_id:
            raise ValidationError("Only the buyer can evaluate (no evaluator assigned)")

        job.evaluation_approved = approved
        job.evaluation_notes = notes
        job.rating = rating

        if approved:
            return await self.advance_phase(
                job_id, org_id, evaluator_id, "completed", "evaluation",
                {"approved": True, "notes": notes, "rating": rating}
            )
        else:
            return await self.advance_phase(
                job_id, org_id, evaluator_id, "disputed", "evaluation",
                {"approved": False, "notes": notes}
            )

    # ── Memos ──

    async def send_memo(
        self, job_id: uuid.UUID, org_id: uuid.UUID, sender_id: uuid.UUID, memo_type: str, content: dict, signature: str | None = None
    ) -> AcpMemo:
        await self.get_job(job_id, org_id)  # Validate job exists

        memo = AcpMemo(
            job_id=job_id,
            sender_agent_id=sender_id,
            memo_type=memo_type,
            content=content,
            signature=signature,
            advances_phase=False,
        )
        self.db.add(memo)
        await self.db.flush()
        await self.db.refresh(memo)
        return memo

    async def list_memos(self, job_id: uuid.UUID, org_id: uuid.UUID) -> list[AcpMemo]:
        await self.get_job(job_id, org_id)
        result = await self.db.execute(
            select(AcpMemo).where(AcpMemo.job_id == job_id).order_by(AcpMemo.created_at)
        )
        return list(result.scalars().all())

    # ── Resource Offerings ──

    async def create_offering(
        self, org_id: uuid.UUID, agent_id: uuid.UUID, name: str, description: str, endpoint_path: str, parameters: dict, response_schema: dict
    ) -> ResourceOffering:
        offering = ResourceOffering(
            org_id=org_id,
            agent_id=agent_id,
            name=name,
            description=description,
            endpoint_path=endpoint_path,
            parameters=parameters,
            response_schema=response_schema,
        )
        self.db.add(offering)
        await self.db.flush()
        await self.db.refresh(offering)
        return offering

    async def list_offerings(
        self, org_id: uuid.UUID | None = None, agent_id: uuid.UUID | None = None, limit: int = 20, offset: int = 0
    ) -> tuple[list[ResourceOffering], int]:
        query = select(ResourceOffering).where(ResourceOffering.is_active == True)
        count_query = select(func.count()).select_from(ResourceOffering).where(ResourceOffering.is_active == True)

        if org_id:
            query = query.where(ResourceOffering.org_id == org_id)
            count_query = count_query.where(ResourceOffering.org_id == org_id)
        if agent_id:
            query = query.where(ResourceOffering.agent_id == agent_id)
            count_query = count_query.where(ResourceOffering.agent_id == agent_id)

        total = (await self.db.execute(count_query)).scalar() or 0
        result = await self.db.execute(query.limit(limit).offset(offset))
        return list(result.scalars().all()), total
