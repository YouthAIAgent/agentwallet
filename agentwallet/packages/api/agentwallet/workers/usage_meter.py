"""Usage meter worker -- count usage for billing."""

from datetime import datetime, timezone

from sqlalchemy import func, select

from ..core.database import get_session_factory
from ..core.logging import get_logger
from ..models.organization import Organization
from ..models.transaction import Transaction
from ..services.billing import BillingService
from .base import BaseWorker

logger = get_logger(__name__)


class UsageMeterWorker(BaseWorker):
    name = "usage_meter"
    interval_seconds = 3600.0  # 1 hour

    async def tick(self) -> None:
        factory = get_session_factory()
        async with factory() as db:
            # Get all active orgs
            result = await db.execute(select(Organization.id).where(Organization.is_active.is_(True)))
            org_ids = [row[0] for row in result.all()]

            billing = BillingService(db)
            now = datetime.now(timezone.utc)
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            for org_id in org_ids:
                # Count transactions this period
                await db.scalar(
                    select(func.count()).where(
                        Transaction.org_id == org_id,
                        Transaction.created_at >= period_start,
                    )
                )
                await db.scalar(
                    select(func.coalesce(func.sum(Transaction.amount_lamports), 0)).where(
                        Transaction.org_id == org_id,
                        Transaction.created_at >= period_start,
                    )
                )

                await billing.increment_usage(
                    org_id=org_id,
                    tx_count=0,  # don't double-count, just sync
                    tx_volume=0,
                )

            await db.commit()
            logger.info("usage_meter_tick", orgs_processed=len(org_ids))
