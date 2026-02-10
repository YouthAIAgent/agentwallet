"""Base worker class -- tick loop pattern ported from moltfarm autopilot.py."""

import asyncio

from ..core.logging import get_logger

logger = get_logger(__name__)


class BaseWorker:
    """Base class for all background workers.

    Tick loop pattern from moltfarm autopilot.py:
    Each worker has an interval and a tick() method called repeatedly.
    """

    name: str = "base_worker"
    interval_seconds: float = 60.0

    async def setup(self) -> None:
        """Called once before the tick loop starts."""

    async def tick(self) -> None:
        """Called every interval_seconds. Override in subclass."""
        raise NotImplementedError

    async def teardown(self) -> None:
        """Called when the worker stops."""

    async def run(self) -> None:
        """Main run loop."""
        logger.info("worker_starting", worker=self.name, interval=self.interval_seconds)
        await self.setup()
        try:
            while True:
                try:
                    await self.tick()
                except Exception as e:
                    logger.error("worker_tick_error", worker=self.name, error=str(e))
                await asyncio.sleep(self.interval_seconds)
        except asyncio.CancelledError:
            logger.info("worker_stopping", worker=self.name)
        finally:
            await self.teardown()
