"""On-chain reputation scoring for agents."""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import joinedload

from sqlalchemy.ext.asyncio import AsyncSession
from ..core.exceptions import NotFoundError
from ..models.marketplace import AgentReputation, Job, Service
from ..models.agent import Agent


class ReputationService:
    """On-chain reputation scoring for agents."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def calculate_score(self, agent_id: uuid.UUID) -> float:
        """Calculate reputation from: completed jobs, ratings, escrow history, transaction volume."""
        
        # Get or create reputation record
        reputation = await self.get_or_create_reputation(agent_id)
        
        # Gather all metrics
        job_stats = await self._calculate_job_statistics(agent_id)
        rating_stats = await self._calculate_rating_statistics(agent_id)
        financial_stats = await self._calculate_financial_statistics(agent_id)
        performance_stats = await self._calculate_performance_statistics(agent_id)
        
        # Update reputation record
        await self._update_reputation_record(reputation, job_stats, rating_stats, financial_stats, performance_stats)
        
        # Calculate composite score
        score = await self._calculate_composite_score(reputation)
        
        reputation.score = score
        await self.session.flush()

        return score

    async def get_or_create_reputation(self, agent_id: uuid.UUID) -> AgentReputation:
        """Get existing reputation or create new one."""
        
        result = await self.session.execute(
            select(AgentReputation).where(AgentReputation.agent_id == agent_id)
        )
        reputation = result.scalar_one_or_none()
        
        if not reputation:
            # Verify agent exists
            agent_result = await self.session.execute(select(Agent).where(Agent.id == agent_id))
            if not agent_result.scalar_one_or_none():
                raise NotFoundError("Agent", str(agent_id))
            
            reputation = AgentReputation(agent_id=agent_id)
            self.session.add(reputation)
            await self.session.flush()
            await self.session.refresh(reputation)
        
        return reputation

    async def _calculate_job_statistics(self, agent_id: uuid.UUID) -> Dict:
        """Calculate job completion statistics."""
        
        # Jobs as seller (primary reputation factor)
        seller_stats_result = await self.session.execute(
            select(
                func.count(Job.id).label("total"),
                func.count(Job.id).filter(Job.status == "completed").label("completed"),
                func.count(Job.id).filter(Job.status == "cancelled").label("cancelled"),
                func.count(Job.id).filter(Job.status == "disputed").label("disputed"),
                func.min(Job.created_at).label("first_job"),
                func.max(Job.completed_at).label("last_job")
            ).where(Job.seller_agent_id == agent_id)
        )
        
        seller_stats = seller_stats_result.first()
        
        # Jobs as buyer (secondary factor)
        buyer_stats_result = await self.session.execute(
            select(func.count(Job.id).label("total_as_buyer"))
            .where(Job.buyer_agent_id == agent_id)
        )
        
        buyer_stats = buyer_stats_result.first()
        
        return {
            "total_jobs": seller_stats.total or 0,
            "completed_jobs": seller_stats.completed or 0,
            "cancelled_jobs": seller_stats.cancelled or 0,
            "disputed_jobs": seller_stats.disputed or 0,
            "total_as_buyer": buyer_stats.total_as_buyer or 0,
            "first_job_at": seller_stats.first_job,
            "last_job_at": seller_stats.last_job
        }

    async def _calculate_rating_statistics(self, agent_id: uuid.UUID) -> Dict:
        """Calculate rating statistics from completed jobs."""
        
        ratings_result = await self.session.execute(
            select(
                Job.rating,
                func.count(Job.rating).label("count")
            )
            .where(and_(Job.seller_agent_id == agent_id, Job.rating.isnot(None)))
            .group_by(Job.rating)
        )
        
        rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        total_rating_score = 0
        total_ratings = 0
        
        for rating, count in ratings_result.all():
            rating_counts[rating] = count
            total_rating_score += rating * count
            total_ratings += count
        
        avg_rating = total_rating_score / total_ratings if total_ratings > 0 else None
        
        return {
            "avg_rating": avg_rating,
            "rating_count": total_ratings,
            "five_star_count": rating_counts[5],
            "four_star_count": rating_counts[4],
            "three_star_count": rating_counts[3],
            "two_star_count": rating_counts[2],
            "one_star_count": rating_counts[1]
        }

    async def _calculate_financial_statistics(self, agent_id: uuid.UUID) -> Dict:
        """Calculate transaction volume and earnings."""
        
        # Earnings as seller
        seller_financial_result = await self.session.execute(
            select(
                func.sum(Service.price_lamports).label("total_earnings"),
                func.sum(Service.price_lamports).label("total_volume_seller")
            )
            .select_from(Job)
            .join(Service)
            .where(and_(Job.seller_agent_id == agent_id, Job.status == "completed"))
        )
        
        seller_financial = seller_financial_result.first()
        
        # Spending as buyer
        buyer_financial_result = await self.session.execute(
            select(func.sum(Service.price_lamports).label("total_spent"))
            .select_from(Job)
            .join(Service)
            .where(and_(Job.buyer_agent_id == agent_id, Job.status == "completed"))
        )
        
        buyer_financial = buyer_financial_result.first()
        
        earnings = seller_financial.total_earnings or 0
        spent = buyer_financial.total_spent or 0
        volume = earnings + spent
        
        return {
            "total_volume_lamports": volume,
            "total_earnings_lamports": earnings,
            "total_spent_lamports": spent
        }

    async def _calculate_performance_statistics(self, agent_id: uuid.UUID) -> Dict:
        """Calculate performance metrics like delivery time and response rate."""
        
        # Completion time analysis
        completion_times_result = await self.session.execute(
            select(
                Job.created_at,
                Job.started_at,
                Job.completed_at,
                Job.deadline
            )
            .where(and_(Job.seller_agent_id == agent_id, Job.status == "completed"))
        )
        
        completion_times = []
        on_time_count = 0
        total_with_deadline = 0
        response_times = []
        
        for job in completion_times_result.all():
            if job.completed_at and job.created_at:
                # Calculate completion time
                completion_hours = (job.completed_at - job.created_at).total_seconds() / 3600
                completion_times.append(completion_hours)
                
                # Check if delivered on time
                if job.deadline:
                    total_with_deadline += 1
                    if job.completed_at <= job.deadline:
                        on_time_count += 1
                
                # Calculate response time (acceptance time)
                if job.started_at:
                    response_hours = (job.started_at - job.created_at).total_seconds() / 3600
                    response_times.append(response_hours)
        
        avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else None
        on_time_rate = on_time_count / total_with_deadline if total_with_deadline > 0 else 0.0
        avg_response_time = sum(response_times) / len(response_times) if response_times else None
        
        return {
            "avg_completion_time_hours": avg_completion_time,
            "on_time_delivery_rate": on_time_rate,
            "response_time_hours": avg_response_time
        }

    async def _update_reputation_record(
        self,
        reputation: AgentReputation,
        job_stats: Dict,
        rating_stats: Dict,
        financial_stats: Dict,
        performance_stats: Dict
    ):
        """Update the reputation record with calculated statistics."""
        
        # Job statistics
        reputation.total_jobs = job_stats["total_jobs"]
        reputation.completed_jobs = job_stats["completed_jobs"]
        reputation.cancelled_jobs = job_stats["cancelled_jobs"]
        reputation.disputed_jobs = job_stats["disputed_jobs"]
        reputation.first_job_at = job_stats["first_job_at"]
        reputation.last_job_at = job_stats["last_job_at"]
        
        # Rating statistics
        reputation.avg_rating = rating_stats["avg_rating"]
        reputation.rating_count = rating_stats["rating_count"]
        reputation.five_star_count = rating_stats["five_star_count"]
        reputation.four_star_count = rating_stats["four_star_count"]
        reputation.three_star_count = rating_stats["three_star_count"]
        reputation.two_star_count = rating_stats["two_star_count"]
        reputation.one_star_count = rating_stats["one_star_count"]
        
        # Financial statistics
        reputation.total_volume_lamports = financial_stats["total_volume_lamports"]
        reputation.total_earnings_lamports = financial_stats["total_earnings_lamports"]
        reputation.total_spent_lamports = financial_stats["total_spent_lamports"]
        
        # Performance statistics
        reputation.avg_completion_time_hours = performance_stats["avg_completion_time_hours"]
        reputation.on_time_delivery_rate = performance_stats["on_time_delivery_rate"]
        reputation.response_time_hours = performance_stats["response_time_hours"]

    async def _calculate_composite_score(self, reputation: AgentReputation) -> float:
        """Calculate weighted composite reputation score (0.0 to 1.0)."""
        
        # Base score components
        reliability_score = self._calculate_reliability_score(reputation)
        quality_score = self._calculate_quality_score(reputation)
        communication_score = self._calculate_communication_score(reputation)
        experience_score = self._calculate_experience_score(reputation)
        
        # Update individual scores
        reputation.reliability_score = reliability_score
        reputation.quality_score = quality_score
        reputation.communication_score = communication_score
        
        # Weighted average (can be tuned based on business priorities)
        weights = {
            "reliability": 0.35,  # Completion rate, on-time delivery
            "quality": 0.30,      # Ratings, reviews
            "communication": 0.20, # Response times
            "experience": 0.15    # Volume, tenure
        }
        
        composite_score = (
            reliability_score * weights["reliability"] +
            quality_score * weights["quality"] +
            communication_score * weights["communication"] +
            experience_score * weights["experience"]
        )
        
        # Ensure score is between 0.0 and 1.0
        return max(0.0, min(1.0, composite_score))

    def _calculate_reliability_score(self, reputation: AgentReputation) -> float:
        """Calculate reliability based on completion rate and on-time delivery."""
        
        if reputation.total_jobs == 0:
            return 0.5  # Neutral score for new agents
        
        # Completion rate (0.0 to 1.0)
        completion_rate = reputation.completed_jobs / reputation.total_jobs
        
        # Penalize cancellations and disputes
        cancellation_penalty = min(0.2, reputation.cancelled_jobs / reputation.total_jobs * 0.5)
        dispute_penalty = min(0.3, reputation.disputed_jobs / reputation.total_jobs * 1.0)
        
        # On-time delivery bonus
        on_time_bonus = reputation.on_time_delivery_rate * 0.2
        
        reliability = completion_rate - cancellation_penalty - dispute_penalty + on_time_bonus
        return max(0.0, min(1.0, reliability))

    def _calculate_quality_score(self, reputation: AgentReputation) -> float:
        """Calculate quality score based on ratings and review sentiment."""
        
        if not reputation.avg_rating or reputation.rating_count == 0:
            return 0.5  # Neutral score for unrated agents
        
        # Convert 1-5 rating to 0-1 score
        rating_score = (reputation.avg_rating - 1) / 4
        
        # Boost for high ratings with sufficient sample size
        if reputation.rating_count >= 10 and reputation.avg_rating >= 4.5:
            rating_score += 0.1
        elif reputation.rating_count >= 5 and reputation.avg_rating >= 4.0:
            rating_score += 0.05
        
        # Distribution bonus for consistent quality
        if reputation.rating_count >= 5:
            five_star_ratio = reputation.five_star_count / reputation.rating_count
            if five_star_ratio >= 0.7:  # 70%+ five-star ratings
                rating_score += 0.1
            elif five_star_ratio >= 0.5:  # 50%+ five-star ratings
                rating_score += 0.05
        
        return max(0.0, min(1.0, rating_score))

    def _calculate_communication_score(self, reputation: AgentReputation) -> float:
        """Calculate communication score based on response times."""
        
        if reputation.response_time_hours is None:
            return 0.5  # Neutral for agents without response time data
        
        # Score based on response time (lower is better)
        # Excellent: < 1 hour, Good: < 4 hours, Average: < 12 hours, Poor: >= 12 hours
        if reputation.response_time_hours < 1:
            return 1.0
        elif reputation.response_time_hours < 4:
            return 0.8
        elif reputation.response_time_hours < 12:
            return 0.6
        elif reputation.response_time_hours < 24:
            return 0.4
        else:
            return 0.2

    def _calculate_experience_score(self, reputation: AgentReputation) -> float:
        """Calculate experience score based on transaction volume and tenure."""
        
        volume_score = 0.0
        tenure_score = 0.0
        
        # Volume scoring (in USDC)
        volume_usdc = reputation.total_volume_lamports / 1_000_000
        if volume_usdc >= 10000:    # $10K+
            volume_score = 1.0
        elif volume_usdc >= 5000:   # $5K+
            volume_score = 0.8
        elif volume_usdc >= 1000:   # $1K+
            volume_score = 0.6
        elif volume_usdc >= 100:    # $100+
            volume_score = 0.4
        elif volume_usdc > 0:       # Any volume
            volume_score = 0.2
        
        # Tenure scoring
        if reputation.first_job_at:
            days_active = (datetime.utcnow() - reputation.first_job_at).days
            if days_active >= 365:      # 1+ years
                tenure_score = 1.0
            elif days_active >= 180:    # 6+ months
                tenure_score = 0.8
            elif days_active >= 90:     # 3+ months
                tenure_score = 0.6
            elif days_active >= 30:     # 1+ month
                tenure_score = 0.4
            else:                       # < 1 month
                tenure_score = 0.2
        
        # Job count factor
        job_count_factor = min(1.0, reputation.total_jobs / 50)  # Normalize to 50 jobs
        
        return (volume_score * 0.4 + tenure_score * 0.4 + job_count_factor * 0.2)

    async def get_leaderboard(
        self,
        limit: int = 20,
        category: Optional[str] = None,
        min_jobs: int = 5
    ) -> List[Tuple[Agent, AgentReputation]]:
        """Top agents by reputation score."""
        
        stmt = (
            select(Agent, AgentReputation)
            .join(AgentReputation, Agent.id == AgentReputation.agent_id)
            .where(AgentReputation.total_jobs >= min_jobs)
            .order_by(desc(AgentReputation.score), desc(AgentReputation.total_volume_lamports))
            .limit(limit)
        )
        
        # Filter by capability category if specified
        if category:
            stmt = stmt.join(Service, Service.agent_id == Agent.id).where(
                Service.capabilities.contains([category])
            ).distinct()
        
        result = await self.session.execute(stmt)
        return result.all()

    async def update_agent_reputation(self, agent_id: uuid.UUID):
        """Trigger reputation recalculation for an agent."""
        
        await self.calculate_score(agent_id)

    async def get_reputation_summary(self, agent_id: uuid.UUID) -> Dict:
        """Get comprehensive reputation summary for an agent."""
        
        reputation_result = await self.session.execute(
            select(AgentReputation).where(AgentReputation.agent_id == agent_id)
        )
        reputation = reputation_result.scalar_one_or_none()
        
        if not reputation:
            # Calculate initial reputation
            await self.calculate_score(agent_id)
            reputation_result = await self.session.execute(
                select(AgentReputation).where(AgentReputation.agent_id == agent_id)
            )
            reputation = reputation_result.scalar_one()
        
        return {
            "agent_id": str(agent_id),
            "overall_score": reputation.score,
            "reliability_score": reputation.reliability_score,
            "quality_score": reputation.quality_score,
            "communication_score": reputation.communication_score,
            "total_jobs": reputation.total_jobs,
            "completed_jobs": reputation.completed_jobs,
            "success_rate": reputation.completed_jobs / reputation.total_jobs if reputation.total_jobs > 0 else 0,
            "average_rating": reputation.avg_rating,
            "rating_count": reputation.rating_count,
            "total_volume_usdc": reputation.total_volume_lamports / 1_000_000,
            "total_earnings_usdc": reputation.total_earnings_lamports / 1_000_000,
            "on_time_delivery_rate": reputation.on_time_delivery_rate,
            "avg_response_time_hours": reputation.response_time_hours,
            "tenure_days": (datetime.utcnow() - reputation.first_job_at).days if reputation.first_job_at else 0,
            "last_active": reputation.last_job_at
        }