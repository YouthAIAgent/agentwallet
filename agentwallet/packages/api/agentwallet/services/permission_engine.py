"""Permission Engine -- evaluate transaction requests against policies.

Outcomes: allow, deny, require_approval.
"""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import get_logger
from ..models.approval_request import ApprovalRequest
from ..models.policy import Policy
from ..models.transaction import Transaction

logger = get_logger(__name__)


class PolicyEvaluation:
    """Result of evaluating a transaction against all applicable policies."""

    def __init__(self):
        self.allowed = True
        self.requires_approval = False
        self.denied_by: str | None = None
        self.denial_reason: str | None = None
        self.approval_policy_id: uuid.UUID | None = None

    @property
    def outcome(self) -> str:
        if not self.allowed:
            return "deny"
        if self.requires_approval:
            return "require_approval"
        return "allow"


class PermissionEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def evaluate(
        self,
        org_id: uuid.UUID,
        agent_id: uuid.UUID | None,
        wallet_id: uuid.UUID,
        to_address: str,
        amount_lamports: int,
        token_mint: str | None = None,
    ) -> PolicyEvaluation:
        """Evaluate a transaction request against all applicable policies.

        Policies are checked in priority order (lower number = higher priority).
        First deny wins. require_approval accumulates.
        """
        evaluation = PolicyEvaluation()

        # Load applicable policies (org-level + agent-level + wallet-level)
        policies = await self._load_policies(org_id, agent_id, wallet_id)

        for policy in policies:
            rules = policy.rules or {}

            # Check per-transaction spending limit
            limit = rules.get("spending_limit_lamports")
            if limit is not None and amount_lamports > limit:
                evaluation.allowed = False
                evaluation.denied_by = policy.name
                evaluation.denial_reason = f"Amount {amount_lamports} exceeds per-tx limit {limit}"
                return evaluation

            # Check daily spending limit
            daily_limit = rules.get("daily_limit_lamports")
            if daily_limit is not None:
                daily_spent = await self._get_daily_spend(org_id, agent_id, wallet_id)
                if daily_spent + amount_lamports > daily_limit:
                    evaluation.allowed = False
                    evaluation.denied_by = policy.name
                    evaluation.denial_reason = (
                        f"Daily spend {daily_spent + amount_lamports} would exceed limit {daily_limit}"
                    )
                    return evaluation

            # Check destination whitelist
            whitelist = rules.get("destination_whitelist")
            if whitelist and to_address not in whitelist:
                evaluation.allowed = False
                evaluation.denied_by = policy.name
                evaluation.denial_reason = f"Destination {to_address[:16]}... not in whitelist"
                return evaluation

            # Check destination blacklist
            blacklist = rules.get("destination_blacklist")
            if blacklist and to_address in blacklist:
                evaluation.allowed = False
                evaluation.denied_by = policy.name
                evaluation.denial_reason = f"Destination {to_address[:16]}... is blacklisted"
                return evaluation

            # Check token whitelist
            token_whitelist = rules.get("token_whitelist")
            if token_whitelist:
                token_id = token_mint or "SOL"
                if token_id not in token_whitelist:
                    evaluation.allowed = False
                    evaluation.denied_by = policy.name
                    evaluation.denial_reason = f"Token {token_id} not in whitelist"
                    return evaluation

            # Check time window
            time_window = rules.get("time_window")
            if time_window:
                now = datetime.now(timezone.utc)
                tz_name = time_window.get("timezone", "UTC")
                start_h, start_m = map(int, time_window.get("start", "00:00").split(":"))
                end_h, end_m = map(int, time_window.get("end", "23:59").split(":"))
                current_minutes = now.hour * 60 + now.minute
                start_minutes = start_h * 60 + start_m
                end_minutes = end_h * 60 + end_m
                if not (start_minutes <= current_minutes <= end_minutes):
                    evaluation.allowed = False
                    evaluation.denied_by = policy.name
                    evaluation.denial_reason = (
                        f"Outside allowed time window {time_window['start']}-{time_window['end']} {tz_name}"
                    )
                    return evaluation

            # Check approval threshold
            approval_threshold = rules.get("require_approval_above_lamports")
            if approval_threshold is not None and amount_lamports > approval_threshold:
                evaluation.requires_approval = True
                evaluation.approval_policy_id = policy.id

        return evaluation

    async def create_approval_request(
        self,
        org_id: uuid.UUID,
        transaction_request: dict,
        policy_id: uuid.UUID | None = None,
    ) -> ApprovalRequest:
        """Create a pending approval request."""
        req = ApprovalRequest(
            org_id=org_id,
            transaction_request=transaction_request,
            policy_id=policy_id,
            required_approvals=1,
        )
        self.db.add(req)
        await self.db.flush()
        logger.info("approval_request_created", id=str(req.id), org_id=str(org_id))
        return req

    async def _load_policies(
        self,
        org_id: uuid.UUID,
        agent_id: uuid.UUID | None,
        wallet_id: uuid.UUID,
    ) -> list[Policy]:
        """Load all applicable policies in priority order."""
        query = (
            select(Policy)
            .where(
                Policy.org_id == org_id,
                Policy.enabled.is_(True),
            )
            .order_by(Policy.priority)
        )
        result = await self.db.execute(query)
        all_policies = result.scalars().all()

        applicable = []
        for p in all_policies:
            if p.scope_type == "org":
                applicable.append(p)
            elif p.scope_type == "agent" and p.scope_id == agent_id:
                applicable.append(p)
            elif p.scope_type == "wallet" and p.scope_id == wallet_id:
                applicable.append(p)
        return applicable

    async def _get_daily_spend(
        self,
        org_id: uuid.UUID,
        agent_id: uuid.UUID | None,
        wallet_id: uuid.UUID,
    ) -> int:
        """Sum today's confirmed transaction amounts for the given wallet/agent."""
        today = date.today()
        query = select(func.coalesce(func.sum(Transaction.amount_lamports), 0)).where(
            Transaction.org_id == org_id,
            Transaction.wallet_id == wallet_id,
            Transaction.status.in_(["confirmed", "submitted"]),
            func.date(Transaction.created_at) == today,
        )
        if agent_id:
            query = query.where(Transaction.agent_id == agent_id)
        return await self.db.scalar(query)
