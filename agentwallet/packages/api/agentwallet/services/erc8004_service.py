"""ERC-8004 Service -- on-chain identity registration, feedback, and reputation.

Bridges Solana agent wallets with Ethereum ERC-8004 identity on Base L2.
"""

import uuid

import httpx
from eth_account import Account
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.evm import (
    IDENTITY_ABI,
    REPUTATION_ABI,
    build_and_sign_tx,
    decode_function_result,
    encode_function_call,
    eth_call,
    get_transaction_receipt,
    send_raw_transaction,
)
from ..core.exceptions import ERC8004Error, NotFoundError, ValidationError
from ..core.kms import get_key_manager
from ..core.logging import get_logger
from ..models.agent import Agent
from ..models.erc8004_identity import ERC8004Feedback, ERC8004Identity, EVMWallet

logger = get_logger(__name__)


class ERC8004Service:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.km = get_key_manager()

    # ------------------------------------------------------------------
    # EVM Wallet Management
    # ------------------------------------------------------------------

    async def create_evm_wallet(
        self, agent_id: uuid.UUID, org_id: uuid.UUID, label: str | None = None
    ) -> EVMWallet:
        """Generate an ETH keypair for an agent. Encrypts private key at rest."""
        # Verify agent exists and belongs to org
        agent = await self._get_agent(agent_id, org_id)

        # Check if agent already has an EVM wallet
        existing = await self.db.scalar(
            select(EVMWallet).where(EVMWallet.agent_id == agent_id)
        )
        if existing:
            return existing

        # Generate keypair
        account = Account.create()
        encrypted_key = self.km.encrypt(bytes.fromhex(account.key.hex().removeprefix("0x")))

        wallet = EVMWallet(
            org_id=org_id,
            agent_id=agent_id,
            address=account.address,
            encrypted_key=encrypted_key,
            chain_id=get_settings().evm_chain_id,
            label=label or f"evm-{account.address[:10]}",
        )
        self.db.add(wallet)
        await self.db.flush()

        # Update agent's evm_address
        agent.evm_address = account.address
        await self.db.flush()

        logger.info("evm_wallet_created", agent_id=str(agent_id), address=account.address[:16])
        return wallet

    async def get_evm_wallet(self, agent_id: uuid.UUID, org_id: uuid.UUID) -> EVMWallet:
        """Get an agent's EVM wallet."""
        wallet = await self.db.scalar(
            select(EVMWallet).where(EVMWallet.agent_id == agent_id)
        )
        if not wallet or wallet.org_id != org_id:
            raise NotFoundError("EVMWallet", str(agent_id))
        return wallet

    # ------------------------------------------------------------------
    # Identity Registration
    # ------------------------------------------------------------------

    async def register_identity(
        self,
        agent_id: uuid.UUID,
        org_id: uuid.UUID,
        metadata_uri: str | None = None,
    ) -> ERC8004Identity:
        """Register an agent on-chain via ERC-8004 Identity Registry."""
        agent = await self._get_agent(agent_id, org_id)
        settings = get_settings()

        # Check if already registered
        existing = await self.db.scalar(
            select(ERC8004Identity).where(ERC8004Identity.agent_id == agent_id)
        )
        if existing and existing.status == "confirmed":
            raise ERC8004Error(f"Agent {agent_id} already has a confirmed ERC-8004 identity")
        if existing and existing.status == "pending":
            return existing  # Return pending registration

        # Ensure agent has an EVM wallet
        evm_wallet = await self.db.scalar(
            select(EVMWallet).where(EVMWallet.agent_id == agent_id)
        )
        if not evm_wallet:
            evm_wallet = await self.create_evm_wallet(agent_id, org_id)

        # Build and submit registration tx
        metadata_uri = metadata_uri or ""
        calldata = encode_function_call(
            IDENTITY_ABI, "registerAgent", [agent.name, metadata_uri]
        )

        identity = ERC8004Identity(
            org_id=org_id,
            agent_id=agent_id,
            evm_address=evm_wallet.address,
            chain_id=settings.evm_chain_id,
            metadata_uri=metadata_uri,
            status="pending",
        )
        self.db.add(identity)
        await self.db.flush()

        # Sign with platform key (platform pays gas)
        if not settings.evm_platform_private_key:
            logger.warning("evm_platform_key_not_set", msg="Cannot submit on-chain tx without EVM_PLATFORM_PRIVATE_KEY")
            return identity

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                raw_tx = await build_and_sign_tx(
                    client=client,
                    private_key=settings.evm_platform_private_key,
                    to=settings.erc8004_identity_address,
                    data=calldata,
                )
                tx_hash = await send_raw_transaction(client, raw_tx)
                identity.tx_hash = tx_hash

                # Poll for receipt
                receipt = await get_transaction_receipt(client, tx_hash)
                if receipt and int(receipt.get("status", "0x0"), 16) == 1:
                    identity.status = "confirmed"
                    # Try to extract token ID from logs (first topic after event sig)
                    logs = receipt.get("logs", [])
                    if logs:
                        # Transfer event topic for ERC-721
                        for log in logs:
                            topics = log.get("topics", [])
                            if len(topics) >= 4:
                                token_id = int(topics[3], 16)
                                identity.token_id = token_id
                                agent.erc8004_token_id = token_id
                                break
                else:
                    identity.status = "failed"

        except Exception as e:
            logger.error("erc8004_register_failed", agent_id=str(agent_id), error=str(e))
            identity.status = "failed"

        await self.db.flush()
        logger.info(
            "erc8004_identity_registered",
            agent_id=str(agent_id),
            status=identity.status,
            tx_hash=identity.tx_hash,
        )
        return identity

    async def get_identity(self, agent_id: uuid.UUID, org_id: uuid.UUID) -> ERC8004Identity:
        """Get an agent's ERC-8004 identity."""
        identity = await self.db.scalar(
            select(ERC8004Identity).where(ERC8004Identity.agent_id == agent_id)
        )
        if not identity or identity.org_id != org_id:
            raise NotFoundError("ERC8004Identity", str(agent_id))
        return identity

    # ------------------------------------------------------------------
    # Feedback
    # ------------------------------------------------------------------

    async def submit_feedback(
        self,
        from_agent_id: uuid.UUID,
        to_agent_id: uuid.UUID,
        org_id: uuid.UUID,
        rating: int,
        comment: str = "",
        task_reference: str | None = None,
    ) -> ERC8004Feedback:
        """Submit on-chain feedback for an agent via ERC-8004 Reputation Registry."""
        if not 1 <= rating <= 5:
            raise ValidationError("Rating must be between 1 and 5")

        if from_agent_id == to_agent_id:
            raise ValidationError("Cannot submit feedback for yourself")

        # Verify both agents exist
        from_agent = await self._get_agent(from_agent_id, org_id)
        to_agent = await self._get_agent(to_agent_id, org_id)

        # Verify recipient has ERC-8004 identity
        to_identity = await self.db.scalar(
            select(ERC8004Identity).where(
                ERC8004Identity.agent_id == to_agent_id,
                ERC8004Identity.status == "confirmed",
            )
        )
        if not to_identity:
            raise ERC8004Error(f"Agent {to_agent_id} does not have a confirmed ERC-8004 identity")

        settings = get_settings()

        feedback = ERC8004Feedback(
            org_id=org_id,
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            rating=rating,
            comment=comment,
            task_reference=task_reference,
            status="pending",
        )
        self.db.add(feedback)
        await self.db.flush()

        # Submit on-chain if platform key is set
        if not settings.evm_platform_private_key:
            logger.warning("evm_platform_key_not_set", msg="Feedback stored locally only")
            return feedback

        try:
            calldata = encode_function_call(
                REPUTATION_ABI,
                "submitFeedback",
                [to_identity.token_id, rating, comment],
            )

            async with httpx.AsyncClient(timeout=15) as client:
                raw_tx = await build_and_sign_tx(
                    client=client,
                    private_key=settings.evm_platform_private_key,
                    to=settings.erc8004_reputation_address,
                    data=calldata,
                )
                tx_hash = await send_raw_transaction(client, raw_tx)
                feedback.tx_hash = tx_hash

                receipt = await get_transaction_receipt(client, tx_hash)
                if receipt and int(receipt.get("status", "0x0"), 16) == 1:
                    feedback.status = "confirmed"
                else:
                    feedback.status = "failed"

        except Exception as e:
            logger.error("erc8004_feedback_failed", error=str(e))
            feedback.status = "failed"

        await self.db.flush()
        logger.info(
            "erc8004_feedback_submitted",
            from_agent=str(from_agent_id),
            to_agent=str(to_agent_id),
            rating=rating,
            status=feedback.status,
        )
        return feedback

    # ------------------------------------------------------------------
    # Reputation
    # ------------------------------------------------------------------

    async def get_reputation(self, agent_id: uuid.UUID, org_id: uuid.UUID) -> dict:
        """Get on-chain reputation for an agent."""
        agent = await self._get_agent(agent_id, org_id)
        settings = get_settings()

        result = {
            "agent_id": str(agent_id),
            "erc8004_token_id": agent.erc8004_token_id,
            "evm_address": agent.evm_address,
            "reputation_score": agent.erc8004_reputation,
            "feedback_count": agent.erc8004_feedback_count,
            "on_chain_score": None,
        }

        # Try to read from chain
        if agent.erc8004_token_id is not None:
            try:
                calldata = encode_function_call(
                    REPUTATION_ABI, "getReputation", [agent.erc8004_token_id]
                )
                async with httpx.AsyncClient(timeout=15) as client:
                    raw_result = await eth_call(
                        client, settings.erc8004_reputation_address, calldata
                    )
                    if raw_result and raw_result != "0x":
                        decoded = decode_function_result(
                            REPUTATION_ABI, "getReputation", raw_result
                        )
                        result["on_chain_score"] = decoded[0]
                        result["feedback_count"] = decoded[1]
            except Exception as e:
                logger.warning("erc8004_reputation_read_failed", error=str(e))

        return result

    async def sync_reputation(self, agent_id: uuid.UUID, org_id: uuid.UUID) -> dict:
        """Fetch on-chain reputation and update local agent record."""
        reputation = await self.get_reputation(agent_id, org_id)
        agent = await self._get_agent(agent_id, org_id)

        if reputation["on_chain_score"] is not None:
            agent.erc8004_reputation = float(reputation["on_chain_score"])
            agent.erc8004_feedback_count = reputation["feedback_count"]
            await self.db.flush()

        return reputation

    # ------------------------------------------------------------------
    # Escrow Bridge
    # ------------------------------------------------------------------

    async def bridge_escrow_feedback(
        self,
        escrow_id: uuid.UUID,
        org_id: uuid.UUID,
        rating: int,
        comment: str = "",
    ) -> ERC8004Feedback | None:
        """Submit feedback after escrow release, linking to the escrow as task_reference."""
        from ..models.escrow import Escrow

        escrow = await self.db.get(Escrow, escrow_id)
        if not escrow or escrow.org_id != org_id:
            raise NotFoundError("Escrow", str(escrow_id))

        if escrow.status != "released":
            raise ERC8004Error("Escrow must be released before submitting feedback")

        # Find agents involved via wallets
        from ..models.wallet import Wallet

        funder_wallet = await self.db.get(Wallet, escrow.funder_wallet_id)
        if not funder_wallet or not funder_wallet.agent_id:
            raise ERC8004Error("Funder wallet has no associated agent")

        # Find recipient agent by address
        recipient_wallet = await self.db.scalar(
            select(Wallet).where(Wallet.address == escrow.recipient_address)
        )
        if not recipient_wallet or not recipient_wallet.agent_id:
            raise ERC8004Error("Recipient address has no associated agent wallet")

        return await self.submit_feedback(
            from_agent_id=funder_wallet.agent_id,
            to_agent_id=recipient_wallet.agent_id,
            org_id=org_id,
            rating=rating,
            comment=comment,
            task_reference=str(escrow_id),
        )

    # ------------------------------------------------------------------
    # Feedback Listing
    # ------------------------------------------------------------------

    async def list_feedback(
        self,
        agent_id: uuid.UUID,
        org_id: uuid.UUID,
        direction: str = "received",  # "received" or "given"
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ERC8004Feedback], int]:
        """List feedback given or received by an agent."""
        await self._get_agent(agent_id, org_id)

        if direction == "received":
            condition = ERC8004Feedback.to_agent_id == agent_id
        else:
            condition = ERC8004Feedback.from_agent_id == agent_id

        query = select(ERC8004Feedback).where(condition, ERC8004Feedback.org_id == org_id)
        count_query = select(func.count()).select_from(ERC8004Feedback).where(
            condition, ERC8004Feedback.org_id == org_id
        )

        total = await self.db.scalar(count_query)
        result = await self.db.execute(
            query.order_by(ERC8004Feedback.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total or 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _get_agent(self, agent_id: uuid.UUID, org_id: uuid.UUID) -> Agent:
        agent = await self.db.get(Agent, agent_id)
        if not agent or agent.org_id != org_id:
            raise NotFoundError("Agent", str(agent_id))
        return agent
