from typing import TypedDict, Any


class AuditState(TypedDict, total=False):
    # Input
    source: str
    filename: str
    scan_id: str

    # Node 1: parse
    ast: dict[str, Any]
    parse_error: str | None
    parse_latency: float

    # Node 2: static_scan
    static_findings: list[dict]
    static_latency: float

    # Node 3: memory_query
    rag_context: list[dict]
    memory_latency: float

    # Node 4: ai_reason
    ai_findings: list[dict]
    ai_latency: float
    total_tokens: int

    # Node 5: test_gen
    test_stubs: dict[str, str]
    test_gen_latency: float

    # Node 6: property_gen
    cvl_properties: dict[str, str]
    property_gen_latency: float

    # Node 7: explain
    explanation: dict
    explain_latency: float

    # Node 8: report
    report: dict
    report_latency: float
