"""Public router — unauthenticated endpoints for landing page stats and feed."""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.logging import get_logger
from ...core.redis_client import get_redis
from ...models.acp import AcpJob
from ...models.agent import Agent
from ...models.escrow import Escrow
from ...models.swarm import AgentSwarm
from ...models.transaction import Transaction
from ...models.wallet import Wallet
from ..middleware.rate_limit import check_rate_limit
from ..schemas.public import FeedItem, PublicFeed, PublicStats

logger = get_logger(__name__)

router = APIRouter(prefix="/public", tags=["public"])

LAMPORTS_PER_SOL = 1_000_000_000


def _truncate_address(addr: str) -> str:
    """Anonymize address: show first 4 + last 4 chars."""
    if len(addr) <= 10:
        return addr
    return f"{addr[:4]}...{addr[-4:]}"


@router.get("/stats", response_model=PublicStats)
async def get_public_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Aggregate platform statistics. Cached 60s in Redis."""
    await check_rate_limit(request, "public", "free")

    # Try cache first
    cache_key = "public:stats"
    try:
        r = await get_redis()
        cached = await r.get(cache_key)
        if cached:
            return PublicStats(**json.loads(cached))
    except Exception:
        pass  # Redis fail-open

    # Query counts
    agents_q = await db.execute(select(func.count(Agent.id)))
    wallets_q = await db.execute(select(func.count(Wallet.id)))
    txns_q = await db.execute(select(func.count(Transaction.id)))
    escrows_q = await db.execute(select(func.count(Escrow.id)))
    acp_q = await db.execute(select(func.count(AcpJob.id)))
    swarms_q = await db.execute(select(func.count(AgentSwarm.id)))

    # Total volume (sum of confirmed transaction amounts)
    vol_q = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount_lamports), 0)).where(
            Transaction.status == "confirmed"
        )
    )

    total_agents = agents_q.scalar_one()
    total_wallets = wallets_q.scalar_one()
    total_transactions = txns_q.scalar_one()
    total_escrows = escrows_q.scalar_one()
    total_acp_jobs = acp_q.scalar_one()
    total_swarms = swarms_q.scalar_one()
    total_volume_lamports = vol_q.scalar_one()

    stats = PublicStats(
        total_agents=total_agents,
        total_wallets=total_wallets,
        total_transactions=total_transactions,
        total_escrows=total_escrows,
        total_acp_jobs=total_acp_jobs,
        total_swarms=total_swarms,
        total_volume_sol=round(total_volume_lamports / LAMPORTS_PER_SOL, 4),
    )

    # Cache result
    try:
        r = await get_redis()
        await r.set(cache_key, stats.model_dump_json(), ex=60)
    except Exception:
        pass  # Redis fail-open

    return stats


@router.get("/feed", response_model=PublicFeed)
async def get_public_feed(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Recent anonymized activity feed. Cached 30s in Redis."""
    await check_rate_limit(request, "public", "free")

    # Try cache first
    cache_key = "public:feed"
    try:
        r = await get_redis()
        cached = await r.get(cache_key)
        if cached:
            data = json.loads(cached)
            return PublicFeed(**data)
    except Exception:
        pass  # Redis fail-open

    items: list[FeedItem] = []

    # Recent transactions (last 30 confirmed)
    txns = await db.execute(
        select(Transaction)
        .where(Transaction.status == "confirmed")
        .order_by(Transaction.created_at.desc())
        .limit(30)
    )
    for tx in txns.scalars().all():
        amount_sol = round(tx.amount_lamports / LAMPORTS_PER_SOL, 4)
        items.append(
            FeedItem(
                type="transfer",
                action="transferred",
                address=_truncate_address(tx.from_address),
                amount=f"{amount_sol} SOL",
                timestamp=tx.created_at,
            )
        )

    # Recent ACP jobs (last 10)
    acp_jobs = await db.execute(
        select(AcpJob).order_by(AcpJob.created_at.desc()).limit(10)
    )
    for job in acp_jobs.scalars().all():
        action = f"ACP {job.phase}"
        amount = None
        if job.agreed_price_lamports:
            amount = f"{round(job.agreed_price_lamports / LAMPORTS_PER_SOL, 4)} SOL"
        items.append(
            FeedItem(
                type="acp",
                action=action,
                address=_truncate_address(str(job.buyer_agent_id)),
                amount=amount,
                timestamp=job.created_at,
            )
        )

    # Recent escrows (last 10)
    escrows = await db.execute(
        select(Escrow).order_by(Escrow.created_at.desc()).limit(10)
    )
    for esc in escrows.scalars().all():
        action = f"escrow {esc.status}"
        amount_sol = round(esc.amount_lamports / LAMPORTS_PER_SOL, 4)
        items.append(
            FeedItem(
                type="escrow",
                action=action,
                address=_truncate_address(esc.recipient_address),
                amount=f"{amount_sol} SOL",
                timestamp=esc.created_at,
            )
        )

    # Sort by timestamp descending, limit 50
    items.sort(key=lambda x: x.timestamp, reverse=True)
    items = items[:50]

    now = datetime.now(timezone.utc)
    feed = PublicFeed(items=items, generated_at=now)

    # Cache result
    try:
        r = await get_redis()
        await r.set(cache_key, feed.model_dump_json(), ex=30)
    except Exception:
        pass  # Redis fail-open

    return feed
