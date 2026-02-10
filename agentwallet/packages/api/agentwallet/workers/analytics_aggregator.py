"""Analytics aggregator worker -- roll up daily transaction metrics."""

from datetime import date

from ..core.database import get_session_factory
from ..core.logging import get_logger
from ..services.analytics_engine import AnalyticsEngine
from .base import BaseWorker

logger = get_logger(__name__)


class AnalyticsAggregatorWorker(BaseWorker):
    name = "analytics_aggregator"
    interval_seconds = 60.0  # 1 minute

    async def tick(self) -> None:
        factory = get_session_factory()
        async with factory() as db:
            engine = AnalyticsEngine(db)
            count = await engine.aggregate_daily(date.today())
            await db.commit()
            if count:
                logger.info("analytics_tick", rollups=count)
