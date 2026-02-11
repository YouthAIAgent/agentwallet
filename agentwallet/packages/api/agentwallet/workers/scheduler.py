"""Worker scheduler -- runs all background workers concurrently."""

import asyncio

from ..core.config import get_settings
from ..core.logging import get_logger, setup_logging
from .analytics_aggregator import AnalyticsAggregatorWorker
from .escrow_expiry import EscrowExpiryWorker
from .reputation_sync import ReputationSyncWorker
from .tx_processor import TxProcessorWorker
from .usage_meter import UsageMeterWorker
from .webhook_dispatcher import WebhookDispatcherWorker

logger = get_logger(__name__)


async def run_all_workers() -> None:
    """Start all background workers."""
    settings = get_settings()
    setup_logging(settings.log_level, settings.log_format)

    workers = [
        TxProcessorWorker(),
        WebhookDispatcherWorker(),
        AnalyticsAggregatorWorker(),
        EscrowExpiryWorker(),
        UsageMeterWorker(),
        ReputationSyncWorker(),
    ]

    logger.info("scheduler_starting", workers=[w.name for w in workers])

    tasks = [asyncio.create_task(w.run()) for w in workers]

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


def main() -> None:
    asyncio.run(run_all_workers())


if __name__ == "__main__":
    main()
