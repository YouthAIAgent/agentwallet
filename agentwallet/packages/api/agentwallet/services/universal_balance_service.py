"""Unified cross-chain balance aggregation."""

import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..core.exceptions import NotFoundError
from ..core.logging import get_logger
from ..models.agent import Agent
from ..models.escrow import Escrow
from ..models.policy import Policy
from ..models.transaction import Transaction
from ..models.wallet import Wallet

logger = get_logger(__name__)


class UniversalBalanceService:
    """Unified cross-chain balance aggregation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_universal_balance(self, agent_id: uuid.UUID) -> Dict[str, Any]:
        """Get unified balance across all wallets and tokens.
        Returns total USD value + per-chain breakdown."""

        # Verify agent exists
        agent_result = await self.session.execute(
            select(Agent).options(joinedload(Agent.wallets)).where(Agent.id == agent_id)
        )
        agent = agent_result.scalar_one_or_none()
        if not agent:
            raise NotFoundError("Agent", str(agent_id))

        total_balance_usd = Decimal("0")
        chain_balances = {}
        token_balances = {}

        # Get Solana balances
        solana_data = await self._get_solana_balances(agent.wallets)
        if solana_data:
            total_balance_usd += solana_data["total_usd"]
            chain_balances["solana"] = solana_data
            for token, balance in solana_data["tokens"].items():
                if token not in token_balances:
                    token_balances[token] = {"total_amount": Decimal("0"), "total_usd": Decimal("0"), "chains": {}}
                token_balances[token]["total_amount"] += balance["amount"]
                token_balances[token]["total_usd"] += balance["usd_value"]
                token_balances[token]["chains"]["solana"] = balance

        # Get EVM balances (Ethereum, Polygon, etc.)
        evm_data = await self._get_evm_balances(agent)
        for chain_name, chain_data in evm_data.items():
            if chain_data:
                total_balance_usd += chain_data["total_usd"]
                chain_balances[chain_name] = chain_data
                for token, balance in chain_data["tokens"].items():
                    if token not in token_balances:
                        token_balances[token] = {"total_amount": Decimal("0"), "total_usd": Decimal("0"), "chains": {}}
                    token_balances[token]["total_amount"] += balance["amount"]
                    token_balances[token]["total_usd"] += balance["usd_value"]
                    token_balances[token]["chains"][chain_name] = balance

        # Get pending transactions that might affect balance
        pending_txs = await self._get_pending_transactions(agent_id)

        # Calculate available vs locked balances
        locked_balances = await self._get_locked_balances(agent_id)

        return {
            "agent_id": str(agent_id),
            "total_balance_usd": float(total_balance_usd),
            "available_balance_usd": float(total_balance_usd - locked_balances.get("total_usd", Decimal("0"))),
            "locked_balance_usd": float(locked_balances.get("total_usd", Decimal("0"))),
            "chain_breakdown": {
                chain: {
                    "total_usd": float(data["total_usd"]),
                    "native_token": data.get("native_token", {}),
                    "token_count": len(data["tokens"]),
                    "tokens": {
                        token: {
                            "amount": float(balance["amount"]),
                            "usd_value": float(balance["usd_value"]),
                            "symbol": balance.get("symbol", token),
                            "decimals": balance.get("decimals", 18),
                        }
                        for token, balance in data["tokens"].items()
                    },
                }
                for chain, data in chain_balances.items()
            },
            "token_summary": {
                token: {
                    "total_amount": float(data["total_amount"]),
                    "total_usd": float(data["total_usd"]),
                    "chain_distribution": {
                        chain: {"amount": float(balance["amount"]), "usd_value": float(balance["usd_value"])}
                        for chain, balance in data["chains"].items()
                    },
                }
                for token, data in token_balances.items()
            },
            "pending_transactions": pending_txs,
            "locked_balances": locked_balances,
            "last_updated": agent.updated_at.isoformat(),
        }

    async def get_spending_power(self, agent_id: uuid.UUID) -> Dict[str, Any]:
        """How much can this agent spend (considering policies)?"""

        # Get universal balance first
        balance_data = await self.get_universal_balance(agent_id)

        # Get spending policies for the agent
        policies = await self._get_spending_policies(agent_id)

        # Calculate spending limits per token/chain
        spending_limits = {}
        available_spending = {}

        for token, token_data in balance_data["token_summary"].items():
            available_amount = token_data["total_amount"]
            available_usd = token_data["total_usd"]

            # Apply policy limits
            token_limits = await self._apply_policy_limits(agent_id, token, available_amount, available_usd, policies)

            spending_limits[token] = token_limits
            available_spending[token] = {
                "max_amount": min(available_amount, token_limits["daily_limit_amount"]),
                "max_usd": min(available_usd, token_limits["daily_limit_usd"]),
                "remaining_today": token_limits["remaining_today"],
                "chain_distribution": token_data["chain_distribution"],
            }

        # Calculate total spending power in USD
        total_spending_power_usd = sum(spending["max_usd"] for spending in available_spending.values())

        return {
            "agent_id": str(agent_id),
            "total_spending_power_usd": total_spending_power_usd,
            "available_spending": available_spending,
            "spending_limits": spending_limits,
            "policies_applied": [
                {"policy_id": str(policy.id), "name": policy.name, "type": policy.type, "is_active": policy.is_active}
                for policy in policies
            ],
            "balance_snapshot": {
                "total_balance_usd": balance_data["total_balance_usd"],
                "available_balance_usd": balance_data["available_balance_usd"],
                "locked_balance_usd": balance_data["locked_balance_usd"],
            },
        }

    async def _get_solana_balances(self, wallets: List[Wallet]) -> Optional[Dict[str, Any]]:
        """Get balances for all Solana wallets."""

        solana_wallets = [w for w in wallets if w.chain == "solana"]
        if not solana_wallets:
            return None

        total_usd = Decimal("0")
        all_tokens = {}
        native_sol = Decimal("0")

        for wallet in solana_wallets:
            try:
                # Get SOL balance
                sol_balance = await self.solana_client.get_balance(wallet.address)
                sol_usd = await self._get_token_price("SOL") * Decimal(str(sol_balance))
                native_sol += Decimal(str(sol_balance))
                total_usd += sol_usd

                # Get SPL token balances
                token_balances = await self.solana_client.get_token_balances(wallet.address)

                for token_mint, balance_data in token_balances.items():
                    token_symbol = await self._get_token_symbol(token_mint, "solana")
                    amount = Decimal(str(balance_data["amount"]))
                    decimals = balance_data["decimals"]

                    # Convert to human readable amount
                    readable_amount = amount / (10**decimals)

                    # Get USD value
                    token_price = await self._get_token_price(token_symbol)
                    usd_value = readable_amount * token_price

                    if token_symbol not in all_tokens:
                        all_tokens[token_symbol] = {
                            "amount": Decimal("0"),
                            "usd_value": Decimal("0"),
                            "symbol": token_symbol,
                            "decimals": decimals,
                            "mint": token_mint,
                        }

                    all_tokens[token_symbol]["amount"] += readable_amount
                    all_tokens[token_symbol]["usd_value"] += usd_value
                    total_usd += usd_value

            except Exception as e:
                # Log error but continue with other wallets
                logger.warning("balance_fetch_error", wallet=wallet.address[:16], error=str(e))
                continue

        # Add SOL to tokens if there's any balance
        if native_sol > 0:
            sol_price = await self._get_token_price("SOL")
            sol_usd = native_sol * sol_price
            all_tokens["SOL"] = {
                "amount": native_sol,
                "usd_value": sol_usd,
                "symbol": "SOL",
                "decimals": 9,
                "mint": "native",
            }

        return {
            "total_usd": total_usd,
            "native_token": {
                "symbol": "SOL",
                "amount": float(native_sol),
                "usd_value": float(native_sol * await self._get_token_price("SOL")),
            },
            "tokens": all_tokens,
            "wallet_count": len(solana_wallets),
        }

    async def _get_evm_balances(self, agent: Agent) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get balances for all EVM-compatible chains."""

        evm_balances = {}

        # Check if agent has EVM addresses
        if not agent.evm_address:
            return {}

        # Supported EVM chains
        chains = ["ethereum", "polygon", "bsc", "arbitrum", "optimism"]

        for chain in chains:
            try:
                chain_data = await self._get_chain_balances(agent.evm_address, chain)
                evm_balances[chain] = chain_data
            except Exception as e:
                logger.warning("evm_balance_fetch_error", chain=chain, error=str(e))
                evm_balances[chain] = None

        return evm_balances

    async def _get_chain_balances(self, address: str, chain: str) -> Dict[str, Any]:
        """Get balances for a specific EVM chain."""

        total_usd = Decimal("0")
        tokens = {}

        # Get native token balance (ETH, MATIC, BNB, etc.)
        native_symbol = self._get_native_token_symbol(chain)
        native_balance = await self.evm_client.get_balance(address, chain)
        native_price = await self._get_token_price(native_symbol)
        native_usd = Decimal(str(native_balance)) * native_price

        total_usd += native_usd
        tokens[native_symbol] = {
            "amount": Decimal(str(native_balance)),
            "usd_value": native_usd,
            "symbol": native_symbol,
            "decimals": 18,
            "contract": "native",
        }

        # Get ERC-20 token balances
        erc20_balances = await self.evm_client.get_erc20_balances(address, chain)

        for contract_address, balance_data in erc20_balances.items():
            symbol = balance_data["symbol"]
            amount = Decimal(str(balance_data["balance"]))
            decimals = balance_data["decimals"]

            # Convert to human readable
            readable_amount = amount / (10**decimals)

            # Get price and USD value
            token_price = await self._get_token_price(symbol)
            usd_value = readable_amount * token_price

            tokens[symbol] = {
                "amount": readable_amount,
                "usd_value": usd_value,
                "symbol": symbol,
                "decimals": decimals,
                "contract": contract_address,
            }

            total_usd += usd_value

        return {
            "total_usd": total_usd,
            "native_token": {"symbol": native_symbol, "amount": float(native_balance), "usd_value": float(native_usd)},
            "tokens": tokens,
        }

    def _get_native_token_symbol(self, chain: str) -> str:
        """Get the native token symbol for a chain."""

        native_tokens = {
            "ethereum": "ETH",
            "polygon": "MATIC",
            "bsc": "BNB",
            "arbitrum": "ETH",
            "optimism": "ETH",
            "avalanche": "AVAX",
        }
        return native_tokens.get(chain, "ETH")

    async def _get_pending_transactions(self, agent_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get pending transactions that might affect balance."""

        result = await self.session.execute(
            select(Transaction)
            .join(Wallet, Transaction.wallet_id == Wallet.id)
            .where(Wallet.agent_id == agent_id, Transaction.status.in_(["pending", "processing"]))
            .order_by(Transaction.created_at.desc())
            .limit(10)
        )

        pending_txs = result.scalars().all()

        return [
            {
                "transaction_id": str(tx.id),
                "type": tx.type,
                "amount_lamports": tx.amount_lamports,
                "token_mint": tx.token_mint,
                "status": tx.status,
                "created_at": tx.created_at.isoformat(),
                "estimated_completion": tx.created_at + tx.estimated_completion_time
                if hasattr(tx, "estimated_completion_time")
                else None,
            }
            for tx in pending_txs
        ]

    async def _get_locked_balances(self, agent_id: uuid.UUID) -> Dict[str, Any]:
        """Get balances locked in escrows and pending transactions."""

        # Get locked balances from active escrows
        escrow_result = await self.session.execute(
            select(
                func.sum(Escrow.amount_lamports).label("total_locked"),
                Escrow.token_mint,
                func.count(Escrow.id).label("escrow_count"),
            )
            .join(Wallet, Escrow.funder_wallet_id == Wallet.id)
            .where(Wallet.agent_id == agent_id, Escrow.status.in_(["created", "funded"]))
            .group_by(Escrow.token_mint)
        )

        locked_by_token = {}
        total_locked_usd = Decimal("0")

        for row in escrow_result.all():
            token_mint = row.token_mint or "SOL"
            token_symbol = await self._get_token_symbol(token_mint, "solana")
            amount_lamports = row.total_locked or 0

            # Convert to human readable amount
            if token_symbol == "SOL":
                readable_amount = Decimal(str(amount_lamports)) / Decimal("1000000000")  # 9 decimals
            else:
                readable_amount = Decimal(str(amount_lamports)) / Decimal(
                    "1000000"
                )  # Assume 6 decimals for most tokens

            # Get USD value
            token_price = await self._get_token_price(token_symbol)
            usd_value = readable_amount * token_price

            locked_by_token[token_symbol] = {
                "amount": float(readable_amount),
                "amount_lamports": amount_lamports,
                "usd_value": float(usd_value),
                "escrow_count": row.escrow_count,
            }

            total_locked_usd += usd_value

        return {
            "total_usd": total_locked_usd,
            "by_token": locked_by_token,
            "total_escrows": sum(data["escrow_count"] for data in locked_by_token.values()),
        }

    async def _get_spending_policies(self, agent_id: uuid.UUID) -> List[Policy]:
        """Get active spending policies for an agent."""

        result = await self.session.execute(
            select(Policy)
            .join(Agent, Policy.agent_id == Agent.id)
            .where(Agent.id == agent_id, Policy.is_active, Policy.type.in_(["spending_limit", "daily_limit"]))
        )

        return result.scalars().all()

    async def _apply_policy_limits(
        self, agent_id: uuid.UUID, token: str, available_amount: float, available_usd: float, policies: List[Policy]
    ) -> Dict[str, Any]:
        """Apply policy limits to determine actual spending power."""

        daily_limit_amount = available_amount
        daily_limit_usd = available_usd

        # Apply each policy
        for policy in policies:
            rules = policy.rules or {}

            # Token-specific limits
            if "tokens" in rules and token in rules["tokens"]:
                token_rules = rules["tokens"][token]
                if "daily_limit" in token_rules:
                    daily_limit_amount = min(daily_limit_amount, token_rules["daily_limit"])

            # USD limits
            if "daily_usd_limit" in rules:
                daily_limit_usd = min(daily_limit_usd, rules["daily_usd_limit"])

        # Calculate remaining daily limit (would need to track daily spending)
        daily_spent = await self._get_daily_spending(agent_id, token)
        remaining_today = max(0, daily_limit_amount - daily_spent["amount"])

        return {
            "daily_limit_amount": daily_limit_amount,
            "daily_limit_usd": daily_limit_usd,
            "daily_spent_amount": daily_spent["amount"],
            "daily_spent_usd": daily_spent["usd"],
            "remaining_today": remaining_today,
            "reset_time": "00:00:00 UTC",  # Daily limits reset at midnight UTC
        }

    async def _get_daily_spending(self, agent_id: uuid.UUID, token: str) -> Dict[str, float]:
        """Get today's spending for an agent in a specific token."""

        from datetime import date

        date.today()

        # This would query transaction history for today
        # Simplified implementation - would need proper date filtering
        return {
            "amount": 0.0,  # Amount of token spent today
            "usd": 0.0,  # USD value spent today
        }

    async def _get_token_price(self, symbol: str) -> Decimal:
        """Get current token price in USD."""

        # This would integrate with a price API like CoinGecko, CoinMarketCap, or Jupiter
        # For now, return mock prices
        mock_prices = {
            "SOL": Decimal("100.0"),
            "USDC": Decimal("1.0"),
            "ETH": Decimal("3000.0"),
            "MATIC": Decimal("0.8"),
            "BNB": Decimal("300.0"),
            "AVAX": Decimal("35.0"),
        }

        return mock_prices.get(symbol, Decimal("0.0"))

    async def _get_token_symbol(self, mint_address: str, chain: str) -> str:
        """Get token symbol from mint address."""

        # This would query a token registry or on-chain data
        # For now, return the mint address or a known symbol
        known_tokens = {
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC",  # USDC on Solana
            "So11111111111111111111111111111111111111112": "SOL",  # Wrapped SOL
        }

        return known_tokens.get(mint_address, mint_address[:8] + "...")

    async def refresh_balance_cache(self, agent_id: uuid.UUID) -> Dict[str, Any]:
        """Force refresh of cached balance data."""

        # This could implement caching with Redis to avoid repeated RPC calls
        # For now, just return fresh data
        return await self.get_universal_balance(agent_id)
