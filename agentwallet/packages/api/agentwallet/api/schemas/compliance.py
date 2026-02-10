"""Compliance request/response schemas."""

import uuid

from pydantic import BaseModel


class AuditEventResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    event_type: str
    actor_id: str
    actor_type: str
    resource_type: str
    resource_id: str
    details: dict
    ip_address: str | None
    created_at: str

    model_config = {"from_attributes": True}


class AuditLogResponse(BaseModel):
    data: list[AuditEventResponse]
    total: int


class ComplianceReportResponse(BaseModel):
    report_type: str
    generated_at: str
    org_id: uuid.UUID
    period_start: str
    period_end: str
    summary: dict
    details: list[dict]


class AnomalyAlertResponse(BaseModel):
    id: str
    alert_type: str
    severity: str  # low, medium, high, critical
    description: str
    agent_id: uuid.UUID | None
    wallet_id: uuid.UUID | None
    details: dict
    created_at: str
