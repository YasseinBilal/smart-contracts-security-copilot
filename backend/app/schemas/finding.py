from pydantic import BaseModel


class FindingSchema(BaseModel):
    id: str
    scan_id: str
    filename: str
    category: str
    severity: str
    title: str
    description: str
    affected_lines: list[int]
    affected_code: str | None
    recommendation: str
    exploit_scenario: str
    test_stub: str | None
    false_positive: bool
    confidence: str

    model_config = {"from_attributes": True}
