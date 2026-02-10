"""Analytics Engine -- pre-aggregated daily rollups and reporting."""

import uuid
from datetime import date, timedelta

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import get_logger
from ..models.analytics_daily import AnalyticsDaily
from ..models.transaction import Transaction

logger = get_logger(__name__)


class AnalyticsEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_summary(
        self,
        org_id: uuid.UUID,
        days: int = 30,
    ) -> dict:
        """Get org-level analytics summary for the given period."""
        start = date.today() - timedelta(days=days)
        end = date.today()

        result = await self.db.execute(
            select(
                func.coalesce(func.sum(AnalyticsDaily.tx_count), 0),
                func.coalesce(func.sum(AnalyticsDaily.total_spend_lamports), 0),
                func.coalesce(func.sum(AnalyticsDaily.total_fees_lamports), 0),
                func.coalesce(func.sum(AnalyticsDaily.failed_tx_count), 0),
                func.coalesce(func.sum(AnalyticsDaily.unique_destinations), 0),
            ).where(
                AnalyticsDaily.org_id == org_id,
                AnalyticsDaily.date >= start,
                AnalyticsDaily.date <= end,
            )
        )
        row = result.one()

        # Count active agents
        active_agents = await self.db.scalar(
            select(func.count(func.distinct(AnalyticsDaily.agent_id))).where(
                AnalyticsDaily.org_id == org_id,
                AnalyticsDaily.date >= start,
                AnalyticsDaily.agent_id.isnot(None),
            )
        )

        return {
            "total_spend_lamports": row[1],
            "total_fees_lamports": row[2],
            "tx_count": row[0],
            "failed_tx_count": row[3],
            "active_agents": active_agents or 0,
            "unique_destinations": row[4],
            "period_start": str(start),
            "period_end": str(end),
        }

    async def get_daily_metrics(
        self,
        org_id: uuid.UUID,
        days: int = 30,
        agent_id: uuid.UUID | None = None,
    ) -> list[dict]:
        """Get daily metric series for charts."""
        start = date.today() - timedelta(days=days)

        query = select(AnalyticsDaily).where(
            AnalyticsDaily.org_id == org_id,
            AnalyticsDaily.date >= start,
        )
        if agent_id:
            query = query.where(AnalyticsDaily.agent_id == agent_id)
        else:
            query = query.where(AnalyticsDaily.agent_id.is_(None))

        result = await self.db.execute(query.order_by(AnalyticsDaily.date))
        rows = result.scalars().all()

        return [
            {
                "date": str(r.date),
                "tx_count": r.tx_count,
                "total_spend_lamports": r.total_spend_lamports,
                "total_fees_lamports": r.total_fees_lamports,
                "unique_destinations": r.unique_destinations,
                "failed_tx_count": r.failed_tx_count,
            }
            for r in rows
        ]

    async def get_agent_analytics(
        self,
        org_id: uuid.UUID,
        days: int = 30,
    ) -> list[dict]:
        """Get per-agent analytics breakdown."""
        start = date.today() - timedelta(days=days)

        result = await self.db.execute(
            select(
                AnalyticsDaily.agent_id,
                func.sum(AnalyticsDaily.tx_count),
                func.sum(AnalyticsDaily.total_spend_lamports),
                func.sum(AnalyticsDaily.total_fees_lamports),
            )
            .where(
                AnalyticsDaily.org_id == org_id,
                AnalyticsDaily.date >= start,
                AnalyticsDaily.agent_id.isnot(None),
            )
            .group_by(AnalyticsDaily.agent_id)
        )

        return [
            {
                "agent_id": str(row[0]),
                "tx_count": row[1],
                "total_spend_lamports": row[2],
                "total_fees_lamports": row[3],
            }
            for row in result.all()
        ]

    async def aggregate_daily(self, target_date: date | None = None) -> int:
        """Aggregate transaction data into daily rollups.

        Called by analytics_aggregator worker.
        """
        target = target_date or date.today()

        # Aggregate org-level
        org_result = await self.db.execute(
            select(
                Transaction.org_id,
                func.count().label("tx_count"),
                func.coalesce(func.sum(Transaction.amount_lamports), 0),
                func.coalesce(func.sum(Transaction.platform_fee_lamports), 0),
                func.count(func.distinct(Transaction.to_address)),
                func.sum(
                    func.cast(Transaction.status == "failed", type_=func.literal(0).type)
                ),
            )
            .where(func.date(Transaction.created_at) == target)
            .group_by(Transaction.org_id)
        )

        count = 0
        for row in org_result.all():
            # Upsert org-level rollup
            existing = await self.db.scalar(
                select(AnalyticsDaily).where(
                    AnalyticsDaily.org_id == row[0],
                    AnalyticsDaily.date == target,
                    AnalyticsDaily.agent_id.is_(None),
                )
            )
            if existing:
                existing.tx_count = row[1]
                existing.total_spend_lamports = row[2]
                existing.total_fees_lamports = row[3]
                existing.unique_destinations = row[4]
                existing.failed_tx_count = row[5] or 0
            else:
                self.db.add(AnalyticsDaily(
                    org_id=row[0],
                    date=target,
                    tx_count=row[1],
                    total_spend_lamports=row[2],
                    total_fees_lamports=row[3],
                    unique_destinations=row[4],
                    failed_tx_count=row[5] or 0,
                ))
            count += 1

        # Aggregate per-agent
        agent_result = await self.db.execute(
            select(
                Transaction.org_id,
                Transaction.agent_id,
                func.count(),
                func.coalesce(func.sum(Transaction.amount_lamports), 0),
                func.coalesce(func.sum(Transaction.platform_fee_lamports), 0),
                func.count(func.distinct(Transaction.to_address)),
            )
            .where(
                func.date(Transaction.created_at) == target,
                Transaction.agent_id.isnot(None),
            )
            .group_by(Transaction.org_id, Transaction.agent_id)
        )

        for row in agent_result.all():
            existing = await self.db.scalar(
                select(AnalyticsDaily).where(
                    AnalyticsDaily.org_id == row[0],
                    AnalyticsDaily.agent_id == row[1],
                    AnalyticsDaily.date == target,
                )
            )
            if existing:
                existing.tx_count = row[2]
                existing.total_spend_lamports = row[3]
                existing.total_fees_lamports = row[4]
                existing.unique_destinations = row[5]
            else:
                self.db.add(AnalyticsDaily(
                    org_id=row[0],
                    agent_id=row[1],
                    date=target,
                    tx_count=row[2],
                    total_spend_lamports=row[3],
                    total_fees_lamports=row[4],
                    unique_destinations=row[5],
                ))
            count += 1

        await self.db.flush()
        logger.info("analytics_aggregated", date=str(target), rollups=count)
        return count
