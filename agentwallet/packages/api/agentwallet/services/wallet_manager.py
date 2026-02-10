"""Wallet Manager -- create, fund, query custodial Solana wallets.

Never exposes private keys through the API layer.
"""

import uuid

import httpx
from solders.keypair import Keypair
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.exceptions import NotFoundError, TierLimitError
from ..core.kms import get_key_manager
from ..core.logging import get_logger
from ..core.redis_client import CacheService
from ..core.solana import get_balance, get_balance_sol, get_token_accounts
from ..models.wallet import Wallet

logger = get_logger(__name__)

TIER_WALLET_LIMITS = {"free": 5, "pro": 50, "enterprise": 999999}


class WalletManager:
    def __init__(self, db: AsyncSession, cache: CacheService | None = None):
        self.db = db
        self.cache = cache
        self.km = get_key_manager()

    async def create_wallet(
        self,
        org_id: uuid.UUID,
        org_tier: str = "free",
        agent_id: uuid.UUID | None = None,
        wallet_type: str = "agent",
        label: str | None = None,
    ) -> Wallet:
        """Create a new custodial Solana wallet. Keypair is encrypted at rest."""
        # Check tier limit
        count = await self.db.scalar(
            select(func.count()).where(Wallet.org_id == org_id)
        )
        limit = TIER_WALLET_LIMITS.get(org_tier, 5)
        if count >= limit:
            raise TierLimitError("wallets", limit, org_tier)

        # Generate keypair
        kp = Keypair()
        address = str(kp.pubkey())
        encrypted_key = self.km.encrypt(bytes(kp))

        wallet = Wallet(
            org_id=org_id,
            agent_id=agent_id,
            address=address,
            wallet_type=wallet_type,
            encrypted_key=encrypted_key,
            label=label or f"{wallet_type}-{address[:8]}",
        )
        self.db.add(wallet)
        await self.db.flush()

        logger.info("wallet_created", wallet_id=str(wallet.id), address=address[:16], type=wallet_type)
        return wallet

    async def get_wallet(self, wallet_id: uuid.UUID, org_id: uuid.UUID) -> Wallet:
        """Get wallet by ID, scoped to org."""
        wallet = await self.db.get(Wallet, wallet_id)
        if not wallet or wallet.org_id != org_id:
            raise NotFoundError("Wallet", str(wallet_id))
        return wallet

    async def list_wallets(
        self,
        org_id: uuid.UUID,
        agent_id: uuid.UUID | None = None,
        wallet_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Wallet], int]:
        """List wallets for an org with optional filters."""
        query = select(Wallet).where(Wallet.org_id == org_id, Wallet.is_active.is_(True))
        count_query = select(func.count()).select_from(Wallet).where(
            Wallet.org_id == org_id, Wallet.is_active.is_(True)
        )

        if agent_id:
            query = query.where(Wallet.agent_id == agent_id)
            count_query = count_query.where(Wallet.agent_id == agent_id)
        if wallet_type:
            query = query.where(Wallet.wallet_type == wallet_type)
            count_query = count_query.where(Wallet.wallet_type == wallet_type)

        total = await self.db.scalar(count_query)
        result = await self.db.execute(query.offset(offset).limit(limit))
        return list(result.scalars().all()), total or 0

    async def get_balance(self, wallet_id: uuid.UUID, org_id: uuid.UUID) -> dict:
        """Get SOL + SPL token balances for a wallet. Uses Redis cache."""
        wallet = await self.get_wallet(wallet_id, org_id)

        # Check cache
        if self.cache:
            import json
            cached = await self.cache.get(f"bal:{wallet.address}")
            if cached:
                return json.loads(cached)

        async with httpx.AsyncClient(timeout=15) as client:
            lamports = await get_balance(client, wallet.address)
            tokens = await get_token_accounts(client, wallet.address)

        result = {
            "address": wallet.address,
            "sol_balance": lamports / 1e9,
            "lamports": lamports,
            "tokens": tokens,
        }

        # Cache for 30 seconds
        if self.cache:
            import json
            await self.cache.set(f"bal:{wallet.address}", json.dumps(result), ttl=30)

        return result

    def _decrypt_keypair(self, wallet: Wallet) -> Keypair:
        """Decrypt wallet private key. Internal only -- never expose via API."""
        raw = self.km.decrypt(wallet.encrypted_key)
        return Keypair.from_bytes(raw)
