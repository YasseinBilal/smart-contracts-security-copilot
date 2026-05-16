from datetime import datetime

from pydantic import BaseModel

from app.schemas.finding import FindingSchema


class ScanSummary(BaseModel):
    id: str
    filename: str | None
    status: str
    triggered_by: str
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class ScanDetail(ScanSummary):
    findings: list[FindingSchema] = []
    node_latencies: str | None
    total_tokens: int
