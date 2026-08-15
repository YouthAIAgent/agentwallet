"""USDC Billing Service -- on-chain subscription billing.

Instead of Stripe, organizations pay for tier upgrades in USDC directly from
their own AgentWallet wallet to the platform wallet, using the exact same
TokenService transfer infrastructure as every other token payment on the
platform. Each payment is a real on-chain SPL token transfer with policy
enforcement and an audit trail in the transactions table.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from ..core.config import get_settings
from ..core.exceptions import NotFoundError, ValidationError
from ..core.logging import get_logger
from ..models.billing_subscription import BillingSubscription
from ..models.organization import Organization
from .token_service import TokenService

logger = get_logger(__name__)

BILLING_PERIOD_DAYS = 30
USDC_DECIMALS = 6


def _as_utc(dt: datetime | None) -> datetime | None:
    """Normalize a DB-loaded datetime to UTC-aware (SQLite returns naive)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


PLANS = {
    "free": {
        "name": "Free",
        "price_usdc": 0.0,
        "agents_limit": 3,
        "wallets_limit": 5,
        "tx_monthly_limit": 1000,
        "features": [
            "3 agents",
            "5 wallets",
            "1,000 transactions / month",
            "Community support",
        ],
    },
    "pro": {
        "name": "Pro",
        "price_usdc": 49.0,
        "agents_limit": 25,
        "wallets_limit": 50,
        "tx_monthly_limit": 50000,
        "features": [
            "25 agents",
            "50 wallets",
            "50,000 transactions / month",
            "90-day analytics",
            "Priority support",
        ],
    },
    "enterprise": {
        "name": "Enterprise",
        "price_usdc": 299.0,
        "agents_limit": None,
        "wallets_limit": None,
        "tx_monthly_limit": None,
        "features": [
            "Unlimited agents & wallets",
            "Unlimited transactions",
            "365-day analytics",
            "Custom policies & compliance",
            "Dedicated support",
        ],
    },
}


class UsdcBillingService:
    """On-chain USDC subscription billing built on TokenService."""

    def __init__(self, db):
        self.db = db
        self.token_service = TokenService(db)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def subscribe(
        self,
        org_id: uuid.UUID,
        org_tier: str,
        tier: str,
        from_wallet_id: uuid.UUID,
    ) -> dict:
        """Upgrade (or downgrade) an org to a tier, charging USDC on-chain.

        The tier price is transferred from the org's wallet to the platform
        wallet in USDC via TokenService. On success the org tier is updated
        immediately so limits, fees and rate limits reflect the new plan.
        """
        if tier not in PLANS:
            raise ValidationError(f"Unknown tier '{tier}'. Available: {', '.join(PLANS)}")

        org = await self.db.get(Organization, org_id)
        if not org:
            raise NotFoundError("Organization not found")

        now = datetime.now(timezone.utc)
        plan = PLANS[tier]

        # Free = downgrade, no charge.
        if tier == "free":
            await self._downgrade(org, now)
            logger.info("subscription_downgraded", org_id=str(org_id))
            return self._to_dict(None, org.tier)

        amount = plan["price_usdc"]
        platform_wallet = get_settings().platform_wallet_address
        if not platform_wallet:
            raise ValidationError(
                "Platform wallet is not configured (PLATFORM_WALLET_ADDRESS). "
                "USDC billing is unavailable until it is set."
            )

        # Pay with the org's own USDC -- the same path as any token transfer.
        tx = await self.token_service.transfer_token(
            org_id=org_id,
            org_tier=org_tier,
            from_wallet_id=from_wallet_id,
            to_address=platform_wallet,
            token_symbol="USDC",
            amount=amount,
            memo=f"AgentWallet {tier} subscription ({BILLING_PERIOD_DAYS} days)",
        )

        sub = BillingSubscription(
            org_id=org_id,
            tier=tier,
            status="active",
            amount_usdc=amount,
            amount_raw=int(amount * (10**USDC_DECIMALS)),
            period_start=now,
            period_end=now + timedelta(days=BILLING_PERIOD_DAYS),
            payment_wallet_id=from_wallet_id,
            payment_tx_id=tx.id,
            payment_signature=tx.signature,
        )
        self.db.add(sub)
        org.tier = tier
        await self.db.flush()

        logger.info(
            "subscription_created",
            org_id=str(org_id),
            tier=tier,
            amount_usdc=amount,
            signature=(tx.signature or "")[:24],
        )
        return self._to_dict(sub, org.tier)

    async def get_subscription(self, org_id: uuid.UUID) -> dict:
        """Return the current subscription state, lazily expiring overdue subs.

        If the paid period has ended the org is downgraded back to free.
        """
        org = await self.db.get(Organization, org_id)
        if not org:
            raise NotFoundError("Organization not found")

        sub = await self._latest(org_id)
        now = datetime.now(timezone.utc)

        period_end = _as_utc(sub.period_end) if sub else None
        if sub and sub.status == "active" and period_end is not None and period_end < now:
            sub.status = "expired"
            org.tier = "free"
            await self.db.flush()
            logger.info(
                "subscription_expired",
                org_id=str(org_id),
                tier=sub.tier,
            )

        return self._to_dict(sub, org.tier)

    async def renew(
        self,
        org_id: uuid.UUID,
        org_tier: str,
        from_wallet_id: uuid.UUID,
    ) -> dict:
        """Renew the active subscription for another billing period."""
        org = await self.db.get(Organization, org_id)
        if not org:
            raise NotFoundError("Organization not found")

        sub = await self._latest(org_id)
        if not sub or sub.status != "active":
            raise ValidationError("No active subscription to renew")

        now = datetime.now(timezone.utc)
        platform_wallet = get_settings().platform_wallet_address
        if not platform_wallet:
            raise ValidationError(
                "Platform wallet is not configured (PLATFORM_WALLET_ADDRESS). "
                "USDC billing is unavailable until it is set."
            )

        amount = sub.amount_usdc
        tx = await self.token_service.transfer_token(
            org_id=org_id,
            org_tier=org_tier,
            from_wallet_id=from_wallet_id,
            to_address=platform_wallet,
            token_symbol="USDC",
            amount=amount,
            memo=f"AgentWallet {sub.tier} subscription renewal ({BILLING_PERIOD_DAYS} days)",
        )

        # New period starts when the current one ends (or now if overdue).
        period_end = _as_utc(sub.period_end)
        base = max(now, period_end) if period_end else now
        sub.period_start = base
        sub.period_end = base + timedelta(days=BILLING_PERIOD_DAYS)
        sub.status = "active"
        sub.payment_wallet_id = from_wallet_id
        sub.payment_tx_id = tx.id
        sub.payment_signature = tx.signature
        org.tier = sub.tier
        await self.db.flush()

        logger.info(
            "subscription_renewed",
            org_id=str(org_id),
            tier=sub.tier,
            amount_usdc=amount,
            signature=(tx.signature or "")[:24],
        )
        return self._to_dict(sub, org.tier)

    async def cancel(self, org_id: uuid.UUID) -> dict:
        """Cancel the subscription, downgrading the org to free immediately."""
        org = await self.db.get(Organization, org_id)
        if not org:
            raise NotFoundError("Organization not found")

        sub = await self._latest(org_id)
        if not sub or sub.status != "active":
            raise ValidationError("No active subscription to cancel")

        sub.status = "cancelled"
        sub.auto_renew = False
        org.tier = "free"
        await self.db.flush()

        logger.info("subscription_cancelled", org_id=str(org_id), tier=sub.tier)
        return self._to_dict(sub, org.tier)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _latest(self, org_id: uuid.UUID) -> BillingSubscription | None:
        return await self.db.scalar(
            select(BillingSubscription)
            .where(BillingSubscription.org_id == org_id)
            .order_by(BillingSubscription.created_at.desc())
            .limit(1)
        )

    async def _downgrade(self, org: Organization, now: datetime) -> None:
        """Mark the active subscription cancelled and drop the org to free."""
        org.tier = "free"
        sub = await self._latest(org.id)
        if sub and sub.status == "active":
            sub.status = "cancelled"
            sub.auto_renew = False

    @staticmethod
    def _to_dict(sub: BillingSubscription | None, org_tier: str) -> dict:
        if sub is None:
            return {
                "id": None,
                "tier": org_tier,
                "status": "none",
                "amount_usdc": 0.0,
                "period_start": None,
                "period_end": None,
                "payment_signature": None,
                "auto_renew": False,
                "org_tier": org_tier,
            }
        return {
            "id": sub.id,
            "tier": sub.tier,
            "status": sub.status,
            "amount_usdc": sub.amount_usdc,
            "period_start": sub.period_start.isoformat() if sub.period_start else None,
            "period_end": sub.period_end.isoformat() if sub.period_end else None,
            "payment_signature": sub.payment_signature,
            "auto_renew": sub.auto_renew,
            "org_tier": org_tier,
        }
