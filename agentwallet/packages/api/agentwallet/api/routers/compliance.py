"""Compliance router -- audit log, anomaly detection, reports."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...services.compliance_module import ComplianceModule
from ..middleware.auth import AuthContext, get_auth_context
from ..middleware.rate_limit import check_rate_limit
from ..schemas.compliance import AuditEventResponse, AuditLogResponse

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/audit-log", response_model=AuditLogResponse)
async def get_audit_log(
    request: Request,
    event_type: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    module = ComplianceModule(db)
    events, total = await module.get_audit_log(
        org_id=auth.org_id,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        limit=limit,
        offset=offset,
    )
    return AuditLogResponse(
        data=[
            AuditEventResponse(
                id=e.id,
                org_id=e.org_id,
                event_type=e.event_type,
                actor_id=e.actor_id,
                actor_type=e.actor_type,
                resource_type=e.resource_type,
                resource_id=e.resource_id,
                details=e.details,
                ip_address=e.ip_address,
                created_at=e.created_at.isoformat(),
            )
            for e in events
        ],
        total=total,
    )


@router.get("/anomalies")
async def detect_anomalies(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    module = ComplianceModule(db)
    return await module.detect_anomalies(auth.org_id)


@router.get("/reports/{report_type}")
async def generate_report(
    report_type: str,
    request: Request,
    days: int = 30,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    module = ComplianceModule(db)
    return await module.generate_compliance_report(org_id=auth.org_id, report_type=report_type, days=days)
