"""Compliance Module -- audit logging, anomaly detection, reporting."""

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import get_logger
from ..models.audit_event import AuditEvent
from ..models.transaction import Transaction

logger = get_logger(__name__)


class ComplianceModule:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(
        self,
        org_id: uuid.UUID,
        event_type: str,
        actor_id: str,
        actor_type: str,
        resource_type: str,
        resource_id: str,
        details: dict | None = None,
        ip_address: str | None = None,
    ) -> AuditEvent:
        """Create an immutable audit event."""
        event = AuditEvent(
            org_id=org_id,
            event_type=event_type,
            actor_id=actor_id,
            actor_type=actor_type,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def get_audit_log(
        self,
        org_id: uuid.UUID,
        event_type: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AuditEvent], int]:
        query = select(AuditEvent).where(AuditEvent.org_id == org_id)
        count_query = select(func.count()).select_from(AuditEvent).where(AuditEvent.org_id == org_id)

        if event_type:
            query = query.where(AuditEvent.event_type == event_type)
            count_query = count_query.where(AuditEvent.event_type == event_type)
        if resource_type:
            query = query.where(AuditEvent.resource_type == resource_type)
            count_query = count_query.where(AuditEvent.resource_type == resource_type)
        if resource_id:
            query = query.where(AuditEvent.resource_id == resource_id)
            count_query = count_query.where(AuditEvent.resource_id == resource_id)

        total = await self.db.scalar(count_query)
        result = await self.db.execute(query.order_by(AuditEvent.created_at.desc()).offset(offset).limit(limit))
        return list(result.scalars().all()), total or 0

    async def detect_anomalies(self, org_id: uuid.UUID) -> list[dict]:
        """Run anomaly detection checks. Returns list of alerts."""
        alerts = []

        # Check 1: Velocity -- too many transactions in short period
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        hourly_count = await self.db.scalar(
            select(func.count()).where(
                Transaction.org_id == org_id,
                Transaction.created_at >= one_hour_ago,
            )
        )
        if hourly_count and hourly_count > 100:
            alerts.append(
                {
                    "alert_type": "high_velocity",
                    "severity": "medium",
                    "description": f"{hourly_count} transactions in the last hour",
                    "details": {"count": hourly_count, "threshold": 100},
                }
            )

        # Check 2: Unusual large amounts
        avg_result = await self.db.execute(
            select(func.avg(Transaction.amount_lamports)).where(
                Transaction.org_id == org_id,
                Transaction.status == "confirmed",
            )
        )
        avg_amount = avg_result.scalar() or 0

        if avg_amount > 0:
            large_txs = await self.db.execute(
                select(Transaction).where(
                    Transaction.org_id == org_id,
                    Transaction.created_at >= one_hour_ago,
                    Transaction.amount_lamports > avg_amount * 10,
                )
            )
            for tx in large_txs.scalars().all():
                alerts.append(
                    {
                        "alert_type": "unusual_amount",
                        "severity": "high",
                        "description": (
                            f"Transaction {tx.amount_lamports} lamports is "
                            f"{tx.amount_lamports / avg_amount:.0f}x the average"
                        ),
                        "details": {
                            "tx_id": str(tx.id),
                            "amount": tx.amount_lamports,
                            "average": int(avg_amount),
                        },
                    }
                )

        # Check 3: High failure rate
        recent_total = await self.db.scalar(
            select(func.count()).where(
                Transaction.org_id == org_id,
                Transaction.created_at >= one_hour_ago,
            )
        )
        recent_failed = await self.db.scalar(
            select(func.count()).where(
                Transaction.org_id == org_id,
                Transaction.created_at >= one_hour_ago,
                Transaction.status == "failed",
            )
        )
        if recent_total and recent_total > 5:
            fail_rate = (recent_failed or 0) / recent_total
            if fail_rate > 0.3:
                alerts.append(
                    {
                        "alert_type": "high_failure_rate",
                        "severity": "high",
                        "description": f"{fail_rate:.0%} failure rate in last hour",
                        "details": {
                            "total": recent_total,
                            "failed": recent_failed,
                            "rate": round(fail_rate, 2),
                        },
                    }
                )

        return alerts

    async def generate_compliance_report(
        self,
        org_id: uuid.UUID,
        report_type: str = "eu_ai_act",
        days: int = 30,
    ) -> dict:
        """Generate a compliance report."""
        start = date.today() - timedelta(days=days)
        end = date.today()

        tx_count = await self.db.scalar(
            select(func.count()).where(
                Transaction.org_id == org_id,
                func.date(Transaction.created_at) >= start,
            )
        )
        total_volume = await self.db.scalar(
            select(func.coalesce(func.sum(Transaction.amount_lamports), 0)).where(
                Transaction.org_id == org_id,
                func.date(Transaction.created_at) >= start,
            )
        )
        audit_count = await self.db.scalar(
            select(func.count()).where(
                AuditEvent.org_id == org_id,
                func.date(AuditEvent.created_at) >= start,
            )
        )

        return {
            "report_type": report_type,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "org_id": str(org_id),
            "period_start": str(start),
            "period_end": str(end),
            "summary": {
                "total_transactions": tx_count or 0,
                "total_volume_lamports": total_volume or 0,
                "total_audit_events": audit_count or 0,
                "compliance_status": "compliant",
            },
            "details": [],
        }
