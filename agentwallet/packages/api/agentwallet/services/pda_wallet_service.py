"""PDA Wallet Service -- create, query, transfer, and manage on-chain PDA wallets."""

import uuid

import base58
import httpx
from solders.hash import Hash
from solders.keypair import Keypair
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.exceptions import NotFoundError, TransactionFailedError, ValidationError
from ..core.kms import get_key_manager
from ..core.logging import get_logger
from ..core.pda import (
    build_create_agent_wallet_ix,
    build_transfer_with_limit_ix,
    build_update_limits_ix,
    derive_pda,
    get_pda_account_info,
)
from ..core.solana import confirm_transaction, get_balance
from ..models.pda_wallet import PDAWallet
from ..models.wallet import Wallet

logger = get_logger(__name__)


def _rpc_url() -> str:
    return get_settings().solana_rpc_url


def _rpc_timeout() -> int:
    return get_settings().rpc_timeout


class PDAWalletService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.km = get_key_manager()

    def _decrypt_keypair(self, wallet: Wallet) -> Keypair:
        """Decrypt wallet private key. Internal only."""
        raw = self.km.decrypt(wallet.encrypted_key)
        return Keypair.from_bytes(raw)

    async def _get_authority_wallet(self, wallet_id: uuid.UUID, org_id: uuid.UUID) -> Wallet:
        """Get and validate the authority wallet."""
        wallet = await self.db.get(Wallet, wallet_id)
        if not wallet or wallet.org_id != org_id:
            raise NotFoundError("Wallet", str(wallet_id))
        if not wallet.is_active:
            raise ValidationError("Authority wallet is not active")
        return wallet

    async def _get_latest_blockhash(self, client: httpx.AsyncClient) -> Hash:
        """Fetch latest blockhash from RPC."""
        resp = await client.post(
            _rpc_url(),
            json={"jsonrpc": "2.0", "id": 1, "method": "getLatestBlockhash"},
            timeout=_rpc_timeout(),
        )
        resp.raise_for_status()
        bh_data = resp.json()
        if "error" in bh_data:
            raise TransactionFailedError(f"Blockhash RPC error: {bh_data['error']}")
        return Hash.from_string(bh_data["result"]["value"]["blockhash"])

    async def _send_transaction(
        self, client: httpx.AsyncClient, tx: Transaction
    ) -> str:
        """Sign and send a transaction, return signature."""
        tx_b58 = base58.b58encode(bytes(tx)).decode()
        resp = await client.post(
            _rpc_url(),
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "sendTransaction",
                "params": [tx_b58, {"encoding": "base58"}],
            },
            timeout=_rpc_timeout(),
        )
        resp.raise_for_status()
        result = resp.json()
        if result.get("error"):
            raise TransactionFailedError(f"sendTransaction error: {result['error']}")
        sig = result.get("result")
        if not sig:
            raise TransactionFailedError(f"sendTransaction returned no signature: {result}")
        return sig

    # -----------------------------------------------------------------
    # Create PDA wallet
    # -----------------------------------------------------------------

    async def create_pda_wallet(
        self,
        org_id: uuid.UUID,
        authority_wallet_id: uuid.UUID,
        agent_id_seed: str,
        spending_limit_per_tx: int,
        daily_limit: int,
        agent_id: uuid.UUID | None = None,
    ) -> PDAWallet:
        """Create a PDA wallet on-chain and save to DB."""
        authority_wallet = await self._get_authority_wallet(authority_wallet_id, org_id)
        authority_kp = self._decrypt_keypair(authority_wallet)
        authority_pubkey = authority_kp.pubkey()
        org_pubkey = authority_pubkey  # use authority as org pubkey for derivation

        # Build instruction
        ix, pda, bump = build_create_agent_wallet_ix(
            authority=authority_pubkey,
            org_pubkey=org_pubkey,
            agent_id_seed=agent_id_seed,
            spending_limit_per_tx=spending_limit_per_tx,
            daily_limit=daily_limit,
        )

        # Build, sign, send transaction
        async with httpx.AsyncClient(timeout=_rpc_timeout()) as client:
            bh = await self._get_latest_blockhash(client)
            msg = Message([ix], authority_pubkey)
            tx = Transaction([authority_kp], msg, bh)
            sig = await self._send_transaction(client, tx)

            # Confirm
            confirmed = await confirm_transaction(client, sig)
            if not confirmed:
                logger.warning("pda_create_unconfirmed", signature=sig[:24])

        # Save to DB
        pda_wallet = PDAWallet(
            org_id=org_id,
            agent_id=agent_id,
            pda_address=str(pda),
            authority_wallet_id=authority_wallet_id,
            org_pubkey=str(org_pubkey),
            agent_id_seed=agent_id_seed,
            spending_limit_per_tx=spending_limit_per_tx,
            daily_limit=daily_limit,
            bump=bump,
            is_active=True,
            tx_signature=sig,
        )
        self.db.add(pda_wallet)
        await self.db.flush()
        await self.db.refresh(pda_wallet)

        logger.info(
            "pda_wallet_created",
            pda_address=str(pda)[:16],
            authority=str(authority_pubkey)[:16],
            signature=sig[:24],
        )
        return pda_wallet

    # -----------------------------------------------------------------
    # Read on-chain state
    # -----------------------------------------------------------------

    async def get_pda_state(self, pda_address: str) -> dict:
        """Read PDA account data from on-chain and return deserialized state + SOL balance."""
        async with httpx.AsyncClient(timeout=_rpc_timeout()) as client:
            state = await get_pda_account_info(client, pda_address)
            if state is None:
                raise NotFoundError("PDA account", pda_address)

            balance = await get_balance(client, pda_address)
            state["sol_balance"] = balance / 1e9
            state["pda_address"] = pda_address

        return state

    # -----------------------------------------------------------------
    # Transfer with limit
    # -----------------------------------------------------------------

    async def transfer_from_pda(
        self,
        pda_wallet_id: uuid.UUID,
        org_id: uuid.UUID,
        recipient: str,
        amount_lamports: int,
    ) -> dict:
        """Execute a transfer_with_limit through the PDA wallet."""
        pda_wallet = await self.get_pda_wallet(pda_wallet_id, org_id)
        authority_wallet = await self._get_authority_wallet(pda_wallet.authority_wallet_id, org_id)
        authority_kp = self._decrypt_keypair(authority_wallet)

        pda_pubkey = Pubkey.from_string(pda_wallet.pda_address)
        recipient_pubkey = Pubkey.from_string(recipient)

        ix = build_transfer_with_limit_ix(
            authority=authority_kp.pubkey(),
            agent_wallet_pda=pda_pubkey,
            recipient=recipient_pubkey,
            amount=amount_lamports,
        )

        async with httpx.AsyncClient(timeout=_rpc_timeout()) as client:
            bh = await self._get_latest_blockhash(client)
            msg = Message([ix], authority_kp.pubkey())
            tx = Transaction([authority_kp], msg, bh)
            sig = await self._send_transaction(client, tx)
            confirmed = await confirm_transaction(client, sig)

        logger.info(
            "pda_transfer",
            pda=pda_wallet.pda_address[:16],
            recipient=recipient[:16],
            lamports=amount_lamports,
            signature=sig[:24],
        )
        return {"signature": sig, "confirmed": confirmed}

    # -----------------------------------------------------------------
    # Update limits
    # -----------------------------------------------------------------

    async def update_pda_limits(
        self,
        pda_wallet_id: uuid.UUID,
        org_id: uuid.UUID,
        spending_limit_per_tx: int | None = None,
        daily_limit: int | None = None,
        is_active: bool | None = None,
    ) -> PDAWallet:
        """Update PDA wallet limits on-chain and in DB."""
        pda_wallet = await self.get_pda_wallet(pda_wallet_id, org_id)
        authority_wallet = await self._get_authority_wallet(pda_wallet.authority_wallet_id, org_id)
        authority_kp = self._decrypt_keypair(authority_wallet)

        new_spending = spending_limit_per_tx if spending_limit_per_tx is not None else pda_wallet.spending_limit_per_tx
        new_daily = daily_limit if daily_limit is not None else pda_wallet.daily_limit
        new_active = is_active if is_active is not None else pda_wallet.is_active

        pda_pubkey = Pubkey.from_string(pda_wallet.pda_address)

        ix = build_update_limits_ix(
            authority=authority_kp.pubkey(),
            agent_wallet_pda=pda_pubkey,
            spending_limit_per_tx=new_spending,
            daily_limit=new_daily,
            is_active=new_active,
        )

        async with httpx.AsyncClient(timeout=_rpc_timeout()) as client:
            bh = await self._get_latest_blockhash(client)
            msg = Message([ix], authority_kp.pubkey())
            tx = Transaction([authority_kp], msg, bh)
            sig = await self._send_transaction(client, tx)
            await confirm_transaction(client, sig)

        # Update DB
        pda_wallet.spending_limit_per_tx = new_spending
        pda_wallet.daily_limit = new_daily
        pda_wallet.is_active = new_active
        await self.db.flush()
        await self.db.refresh(pda_wallet)

        logger.info(
            "pda_limits_updated",
            pda=pda_wallet.pda_address[:16],
            spending_limit=new_spending,
            daily_limit=new_daily,
            is_active=new_active,
            signature=sig[:24],
        )
        return pda_wallet

    # -----------------------------------------------------------------
    # Pure derivation (no DB/RPC)
    # -----------------------------------------------------------------

    @staticmethod
    def derive_pda_address(org_pubkey: str, agent_id_seed: str) -> tuple[str, int]:
        """Derive PDA address without DB or RPC. Returns (address, bump)."""
        pubkey = Pubkey.from_string(org_pubkey)
        pda, bump = derive_pda(pubkey, agent_id_seed)
        return str(pda), bump

    # -----------------------------------------------------------------
    # DB queries
    # -----------------------------------------------------------------

    async def list_pda_wallets(
        self,
        org_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[PDAWallet], int]:
        """List PDA wallets for an org."""
        query = select(PDAWallet).where(PDAWallet.org_id == org_id)
        count_query = select(func.count()).select_from(PDAWallet).where(PDAWallet.org_id == org_id)

        total = await self.db.scalar(count_query)
        result = await self.db.execute(query.offset(offset).limit(limit))
        return list(result.scalars().all()), total or 0

    async def get_pda_wallet(self, wallet_id: uuid.UUID, org_id: uuid.UUID) -> PDAWallet:
        """Get PDA wallet by ID, scoped to org."""
        pda_wallet = await self.db.get(PDAWallet, wallet_id)
        if not pda_wallet or pda_wallet.org_id != org_id:
            raise NotFoundError("PDA Wallet", str(wallet_id))
        return pda_wallet
