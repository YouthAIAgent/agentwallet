"""Transaction processor worker -- confirm pending transactions."""

from datetime import datetime, timezone

import httpx
from sqlalchemy import select

from ..core.database import get_session_factory
from ..core.logging import get_logger
from ..core.solana import confirm_transaction
from ..models.transaction import Transaction
from .base import BaseWorker

logger = get_logger(__name__)


class TxProcessorWorker(BaseWorker):
    name = "tx_processor"
    interval_seconds = 5.0

    async def tick(self) -> None:
        factory = get_session_factory()
        async with factory() as db:
            result = await db.execute(
                select(Transaction)
                .where(Transaction.status == "submitted")
                .limit(50)
            )
            pending = result.scalars().all()

            if not pending:
                return

            logger.info("processing_pending_txs", count=len(pending))

            async with httpx.AsyncClient(timeout=15) as client:
                for tx in pending:
                    if not tx.signature:
                        continue
                    confirmed = await confirm_transaction(client, tx.signature)
                    if confirmed:
                        tx.status = "confirmed"
                        tx.confirmed_at = datetime.now(timezone.utc)
                    # Don't mark as failed yet -- might still be processing

            await db.commit()
