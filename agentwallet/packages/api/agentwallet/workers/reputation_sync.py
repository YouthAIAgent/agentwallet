"""Reputation sync worker -- periodically syncs ERC-8004 on-chain reputation to local DB."""

from sqlalchemy import select

from ..core.database import get_session_factory
from ..core.logging import get_logger
from ..models.erc8004_identity import ERC8004Identity
from ..services.erc8004_service import ERC8004Service
from .base import BaseWorker

logger = get_logger(__name__)


class ReputationSyncWorker(BaseWorker):
    name = "reputation_sync"
    interval_seconds = 1800.0  # 30 minutes

    async def tick(self) -> None:
        factory = get_session_factory()
        async with factory() as db:
            # Find all confirmed identities
            result = await db.execute(
                select(ERC8004Identity).where(ERC8004Identity.status == "confirmed")
            )
            identities = result.scalars().all()

            if not identities:
                return

            svc = ERC8004Service(db)
            synced = 0
            for identity in identities:
                try:
                    await svc.sync_reputation(identity.agent_id, identity.org_id)
                    synced += 1
                except Exception as e:
                    logger.warning(
                        "reputation_sync_failed",
                        agent_id=str(identity.agent_id),
                        error=str(e),
                    )

            await db.commit()
            if synced:
                logger.info("reputation_sync_tick", synced=synced, total=len(identities))
