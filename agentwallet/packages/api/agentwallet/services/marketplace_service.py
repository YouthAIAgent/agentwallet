"""Agent-to-agent service marketplace."""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import joinedload

from ..core.database import AsyncSession, get_session
from ..core.exceptions import NotFoundError, ValidationError, ConflictError
from ..models.marketplace import Service, Job, AgentReputation, ServiceCategory, JobMessage
from ..models.agent import Agent
from ..models.escrow import Escrow
from ..services.escrow_service import EscrowService
from ..services.reputation_service import ReputationService


class MarketplaceService:
    """Agent-to-agent service marketplace."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.escrow_service = EscrowService(session)
        self.reputation_service = ReputationService(session)

    async def register_service(
        self,
        agent_id: uuid.UUID,
        service_name: str,
        description: str,
        price_usdc: float,
        capabilities: List[str],
        estimated_duration_hours: Optional[int] = None,
        max_concurrent_jobs: int = 1,
        requirements: Optional[Dict[str, Any]] = None,
        delivery_format: Optional[str] = None
    ) -> Service:
        """Register a service that an agent offers."""
        
        # Verify agent exists
        agent_result = await self.session.execute(select(Agent).where(Agent.id == agent_id))
        agent = agent_result.scalar_one_or_none()
        if not agent:
            raise NotFoundError(f"Agent {agent_id} not found")
        
        # Check for duplicate service names for this agent
        existing_result = await self.session.execute(
            select(Service).where(
                and_(Service.agent_id == agent_id, Service.name == service_name, Service.is_active == True)
            )
        )
        if existing_result.scalar_one_or_none():
            raise ConflictError(f"Active service '{service_name}' already exists for this agent")
        
        # Convert price to lamports (assuming 6 decimals for USDC)
        price_lamports = int(price_usdc * 1_000_000)
        
        service = Service(
            agent_id=agent_id,
            name=service_name,
            description=description,
            price_lamports=price_lamports,
            token_symbol="USDC",
            capabilities=capabilities,
            estimated_duration_hours=estimated_duration_hours,
            max_concurrent_jobs=max_concurrent_jobs,
            requirements=requirements or {},
            delivery_format=delivery_format,
            is_active=True
        )
        
        self.session.add(service)
        await self.session.commit()
        await self.session.refresh(service)
        
        return service

    async def discover_services(
        self,
        query: Optional[str] = None,
        capability: Optional[str] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        agent_id: Optional[uuid.UUID] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Service]:
        """Search for agent services by keyword, capability, price, or rating."""
        
        stmt = select(Service).options(joinedload(Service.agent)).where(Service.is_active == True)
        
        # Keyword search in name and description
        if query:
            search_term = f"%{query.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Service.name).contains(search_term),
                    func.lower(Service.description).contains(search_term)
                )
            )
        
        # Filter by capability
        if capability:
            stmt = stmt.where(Service.capabilities.contains([capability]))
        
        # Filter by max price
        if max_price:
            max_price_lamports = int(max_price * 1_000_000)
            stmt = stmt.where(Service.price_lamports <= max_price_lamports)
        
        # Filter by minimum rating
        if min_rating:
            stmt = stmt.where(Service.avg_rating >= min_rating)
        
        # Filter by specific agent
        if agent_id:
            stmt = stmt.where(Service.agent_id == agent_id)
        
        # Order by reputation score and rating
        stmt = stmt.order_by(desc(Service.avg_rating), desc(Service.success_rate))
        stmt = stmt.limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def hire_agent(
        self,
        buyer_agent_id: uuid.UUID,
        seller_agent_id: uuid.UUID,
        service_id: uuid.UUID,
        wallet_id: uuid.UUID,
        input_data: Optional[Dict[str, Any]] = None,
        buyer_notes: Optional[str] = None,
        deadline_hours: Optional[int] = None
    ) -> Job:
        """Hire an agent — creates escrow, locks payment, notifies seller."""
        
        # Verify service exists and is active
        service_result = await self.session.execute(
            select(Service).options(joinedload(Service.agent))
            .where(and_(Service.id == service_id, Service.is_active == True))
        )
        service = service_result.scalar_one_or_none()
        if not service:
            raise NotFoundError(f"Service {service_id} not found or inactive")
        
        # Verify seller agent matches service
        if service.agent_id != seller_agent_id:
            raise ValidationError(f"Service does not belong to seller agent {seller_agent_id}")
        
        # Verify buyer agent exists
        buyer_result = await self.session.execute(select(Agent).where(Agent.id == buyer_agent_id))
        buyer_agent = buyer_result.scalar_one_or_none()
        if not buyer_agent:
            raise NotFoundError(f"Buyer agent {buyer_agent_id} not found")
        
        # Check seller's concurrent job limit
        active_jobs_result = await self.session.execute(
            select(func.count(Job.id)).where(
                and_(Job.seller_agent_id == seller_agent_id, Job.status.in_(["pending", "active"]))
            )
        )
        active_jobs_count = active_jobs_result.scalar_one()
        
        if active_jobs_count >= service.max_concurrent_jobs:
            raise ConflictError(f"Seller agent has reached maximum concurrent jobs ({service.max_concurrent_jobs})")
        
        # Calculate deadline
        deadline = None
        if deadline_hours:
            deadline = datetime.utcnow() + timedelta(hours=deadline_hours)
        elif service.estimated_duration_hours:
            deadline = datetime.utcnow() + timedelta(hours=service.estimated_duration_hours)
        
        # Create escrow for payment
        escrow_conditions = {
            "job_type": "marketplace_service",
            "service_id": str(service_id),
            "service_name": service.name,
            "buyer_agent_id": str(buyer_agent_id),
            "seller_agent_id": str(seller_agent_id),
            "completion_criteria": "Seller must deliver agreed-upon results and buyer must confirm receipt"
        }
        
        escrow = await self.escrow_service.create_escrow(
            org_id=buyer_agent.org_id,
            funder_wallet_id=wallet_id,
            recipient_address=service.agent.default_wallet.address if service.agent.default_wallet else "",
            amount_lamports=service.price_lamports,
            token_mint=None,  # USDC mint will be set by escrow service
            conditions=escrow_conditions,
            expires_hours=72  # Default 3 days to complete
        )
        
        # Create the job
        job = Job(
            service_id=service_id,
            buyer_agent_id=buyer_agent_id,
            seller_agent_id=seller_agent_id,
            escrow_id=escrow.id,
            status="pending",
            input_data=input_data or {},
            buyer_notes=buyer_notes,
            deadline=deadline
        )
        
        self.session.add(job)
        
        # Create initial system message
        system_message = JobMessage(
            job_id=job.id,
            sender_agent_id=buyer_agent_id,
            message_type="system",
            content=f"Job created for service '{service.name}'. Escrow established with {service.price_lamports / 1_000_000:.2f} USDC.",
            is_system_message=True
        )
        
        self.session.add(system_message)
        
        await self.session.commit()
        await self.session.refresh(job)
        
        # Update service metrics
        service.total_jobs += 1
        await self.session.commit()
        
        return job

    async def accept_job(self, job_id: uuid.UUID, seller_agent_id: uuid.UUID, seller_notes: Optional[str] = None) -> Job:
        """Seller accepts a pending job."""
        
        job_result = await self.session.execute(
            select(Job).options(joinedload(Job.service))
            .where(and_(Job.id == job_id, Job.seller_agent_id == seller_agent_id))
        )
        job = job_result.scalar_one_or_none()
        if not job:
            raise NotFoundError(f"Job {job_id} not found for seller agent {seller_agent_id}")
        
        if job.status != "pending":
            raise ValidationError(f"Job is not in pending status, current status: {job.status}")
        
        job.status = "active"
        job.started_at = datetime.utcnow()
        job.seller_notes = seller_notes
        
        # Create acceptance message
        if seller_notes:
            message = JobMessage(
                job_id=job_id,
                sender_agent_id=seller_agent_id,
                message_type="update",
                content=f"Job accepted. {seller_notes}"
            )
            self.session.add(message)
        
        await self.session.commit()
        return job

    async def complete_job(
        self,
        job_id: uuid.UUID,
        seller_agent_id: uuid.UUID,
        result_data: Optional[Dict[str, Any]] = None,
        completion_notes: Optional[str] = None
    ) -> Job:
        """Seller marks job complete — triggers escrow release."""
        
        job_result = await self.session.execute(
            select(Job).options(joinedload(Job.escrow), joinedload(Job.service))
            .where(and_(Job.id == job_id, Job.seller_agent_id == seller_agent_id))
        )
        job = job_result.scalar_one_or_none()
        if not job:
            raise NotFoundError(f"Job {job_id} not found for seller agent {seller_agent_id}")
        
        if job.status != "active":
            raise ValidationError(f"Job is not active, current status: {job.status}")
        
        # Update job
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.result_data = result_data or {}
        job.seller_notes = completion_notes
        
        # Release escrow payment
        if job.escrow_id:
            await self.escrow_service.release_escrow(job.escrow_id, seller_agent_id)
        
        # Update service metrics
        job.service.completed_jobs += 1
        job.service.success_rate = job.service.completed_jobs / job.service.total_jobs
        
        # Create completion message
        message = JobMessage(
            job_id=job_id,
            sender_agent_id=seller_agent_id,
            message_type="delivery",
            content=f"Job completed successfully. {completion_notes or 'Results delivered.'}",
            attachments={"result_data": result_data} if result_data else {}
        )
        self.session.add(message)
        
        await self.session.commit()
        
        # Update reputation asynchronously
        await self.reputation_service.update_agent_reputation(seller_agent_id)
        
        return job

    async def cancel_job(
        self,
        job_id: uuid.UUID,
        requester_agent_id: uuid.UUID,
        reason: str
    ) -> Job:
        """Cancel a job (buyer or seller can cancel with different implications)."""
        
        job_result = await self.session.execute(
            select(Job).options(joinedload(Job.escrow))
            .where(
                and_(
                    Job.id == job_id,
                    or_(Job.buyer_agent_id == requester_agent_id, Job.seller_agent_id == requester_agent_id)
                )
            )
        )
        job = job_result.scalar_one_or_none()
        if not job:
            raise NotFoundError(f"Job {job_id} not found for agent {requester_agent_id}")
        
        if job.status in ["completed", "cancelled"]:
            raise ValidationError(f"Cannot cancel job with status: {job.status}")
        
        job.status = "cancelled"
        job.completed_at = datetime.utcnow()
        
        # Refund escrow if applicable
        if job.escrow_id:
            await self.escrow_service.refund_escrow(job.escrow_id, requester_agent_id)
        
        # Create cancellation message
        message = JobMessage(
            job_id=job_id,
            sender_agent_id=requester_agent_id,
            message_type="system",
            content=f"Job cancelled. Reason: {reason}",
            is_system_message=True
        )
        self.session.add(message)
        
        await self.session.commit()
        
        # Update reputation for cancellations
        if requester_agent_id == job.seller_agent_id:
            await self.reputation_service.update_agent_reputation(job.seller_agent_id)
        
        return job

    async def rate_agent(
        self,
        job_id: uuid.UUID,
        buyer_agent_id: uuid.UUID,
        rating: int,
        review: Optional[str] = None
    ) -> Job:
        """Rate an agent after job completion. Updates reputation score."""
        
        if not (1 <= rating <= 5):
            raise ValidationError("Rating must be between 1 and 5")
        
        job_result = await self.session.execute(
            select(Job).options(joinedload(Job.service))
            .where(and_(Job.id == job_id, Job.buyer_agent_id == buyer_agent_id))
        )
        job = job_result.scalar_one_or_none()
        if not job:
            raise NotFoundError(f"Job {job_id} not found for buyer agent {buyer_agent_id}")
        
        if job.status != "completed":
            raise ValidationError("Can only rate completed jobs")
        
        if job.rating is not None:
            raise ConflictError("Job has already been rated")
        
        # Update job with rating and review
        job.rating = rating
        job.review = review
        
        # Update service average rating
        service_ratings_result = await self.session.execute(
            select(func.avg(Job.rating), func.count(Job.rating))
            .where(and_(Job.service_id == job.service_id, Job.rating.isnot(None)))
        )
        avg_rating, rating_count = service_ratings_result.first()
        
        if rating_count > 0:
            job.service.avg_rating = float(avg_rating)
        
        await self.session.commit()
        
        # Update seller's reputation
        await self.reputation_service.update_agent_reputation(job.seller_agent_id)
        
        return job

    async def get_job_messages(
        self,
        job_id: uuid.UUID,
        agent_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[JobMessage]:
        """Get messages for a job."""
        
        # Verify agent is part of this job
        job_result = await self.session.execute(
            select(Job).where(
                and_(
                    Job.id == job_id,
                    or_(Job.buyer_agent_id == agent_id, Job.seller_agent_id == agent_id)
                )
            )
        )
        if not job_result.scalar_one_or_none():
            raise NotFoundError(f"Job {job_id} not found for agent {agent_id}")
        
        stmt = (
            select(JobMessage)
            .options(joinedload(JobMessage.sender))
            .where(JobMessage.job_id == job_id)
            .order_by(JobMessage.created_at)
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def send_job_message(
        self,
        job_id: uuid.UUID,
        sender_agent_id: uuid.UUID,
        content: str,
        message_type: str = "chat",
        attachments: Optional[Dict[str, Any]] = None
    ) -> JobMessage:
        """Send a message in a job conversation."""
        
        # Verify agent is part of this job
        job_result = await self.session.execute(
            select(Job).where(
                and_(
                    Job.id == job_id,
                    or_(Job.buyer_agent_id == sender_agent_id, Job.seller_agent_id == sender_agent_id)
                )
            )
        )
        if not job_result.scalar_one_or_none():
            raise NotFoundError(f"Job {job_id} not found for agent {sender_agent_id}")
        
        message = JobMessage(
            job_id=job_id,
            sender_agent_id=sender_agent_id,
            message_type=message_type,
            content=content,
            attachments=attachments or {}
        )
        
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        
        return message

    async def get_agent_jobs(
        self,
        agent_id: uuid.UUID,
        status: Optional[str] = None,
        as_buyer: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Job]:
        """Get jobs for an agent (as buyer, seller, or both)."""
        
        conditions = []
        
        if as_buyer is True:
            conditions.append(Job.buyer_agent_id == agent_id)
        elif as_buyer is False:
            conditions.append(Job.seller_agent_id == agent_id)
        else:
            conditions.append(or_(Job.buyer_agent_id == agent_id, Job.seller_agent_id == agent_id))
        
        if status:
            conditions.append(Job.status == status)
        
        stmt = (
            select(Job)
            .options(joinedload(Job.service), joinedload(Job.buyer_agent), joinedload(Job.seller_agent))
            .where(and_(*conditions))
            .order_by(desc(Job.created_at))
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_service_analytics(self, service_id: uuid.UUID) -> Dict[str, Any]:
        """Get analytics for a service."""
        
        service_result = await self.session.execute(select(Service).where(Service.id == service_id))
        service = service_result.scalar_one_or_none()
        if not service:
            raise NotFoundError(f"Service {service_id} not found")
        
        # Job statistics
        jobs_result = await self.session.execute(
            select(
                func.count(Job.id).label("total_jobs"),
                func.count(Job.id).filter(Job.status == "completed").label("completed"),
                func.count(Job.id).filter(Job.status == "cancelled").label("cancelled"),
                func.count(Job.id).filter(Job.status == "active").label("active"),
                func.avg(Job.rating).label("avg_rating"),
                func.sum(Service.price_lamports).label("total_revenue")
            )
            .select_from(Job)
            .join(Service)
            .where(Service.id == service_id)
        )
        
        stats = jobs_result.first()
        
        return {
            "service_id": str(service_id),
            "total_jobs": stats.total_jobs or 0,
            "completed_jobs": stats.completed or 0,
            "cancelled_jobs": stats.cancelled or 0,
            "active_jobs": stats.active or 0,
            "success_rate": (stats.completed / stats.total_jobs * 100) if stats.total_jobs else 0,
            "average_rating": float(stats.avg_rating) if stats.avg_rating else None,
            "total_revenue_usdc": (stats.total_revenue or 0) / 1_000_000,
            "price_usdc": service.price_lamports / 1_000_000
        }