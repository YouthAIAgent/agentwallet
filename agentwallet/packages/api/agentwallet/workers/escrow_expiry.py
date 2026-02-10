"""Escrow expiry worker -- expire stale escrows past their deadline."""

from ..core.database import get_session_factory
from ..core.logging import get_logger
from ..services.escrow_service import EscrowService
from .base import BaseWorker

logger = get_logger(__name__)


class EscrowExpiryWorker(BaseWorker):
    name = "escrow_expiry"
    interval_seconds = 300.0  # 5 minutes

    async def tick(self) -> None:
        factory = get_session_factory()
        async with factory() as db:
            svc = EscrowService(db)
            count = await svc.expire_stale_escrows()
            await db.commit()
            if count:
                logger.info("escrow_expiry_tick", expired=count)
