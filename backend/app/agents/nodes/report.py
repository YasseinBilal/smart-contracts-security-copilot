import json
import time
import uuid
from datetime import UTC, datetime

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import AuditState
from app.models.finding import Finding
from app.models.scan import Scan


async def report_node(state: AuditState, db: AsyncSession | None = None) -> AuditState:
    t0 = time.monotonic()
    ai_findings = state.get("ai_findings", [])
    test_stubs = state.get("test_stubs", {})
    cvl_properties = state.get("cvl_properties", {})
    scan_id = state.get("scan_id", str(uuid.uuid4()))

    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for f in ai_findings:
        sev = f.get("severity", "INFO")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    latencies = {
        "parse": round(state.get("parse_latency", 0), 3),
        "static_scan": round(state.get("static_latency", 0), 3),
        "memory_query": round(state.get("memory_latency", 0), 3),
        "ai_reason": round(state.get("ai_latency", 0), 3),
        "test_gen": round(state.get("test_gen_latency", 0), 3),
        "property_gen": round(state.get("property_gen_latency", 0), 3),
        "explain": round(state.get("explain_latency", 0), 3),
    }

    report = {
        "scan_id": scan_id,
        "filename": state.get("filename", ""),
        "findings": ai_findings,
        "cvl_properties": cvl_properties,
        "explanation": state.get("explanation", {}),
        "severity_counts": severity_counts,
        "node_latencies": latencies,
        "total_tokens": state.get("total_tokens", 0),
    }

    # Persist to DB if session provided
    if db is not None:
        await _persist(db, scan_id, state, ai_findings, test_stubs, cvl_properties, severity_counts, latencies)

    return {
        **state,
        "report": report,
        "report_latency": time.monotonic() - t0,
    }


async def _persist(
    db: AsyncSession,
    scan_id: str,
    state: AuditState,
    ai_findings: list[dict],
    test_stubs: dict[str, str],
    cvl_properties: dict[str, str],
    severity_counts: dict,
    latencies: dict,
) -> None:
    scan = await db.get(Scan, scan_id)
    if scan:
        scan.status = "completed"
        scan.completed_at = datetime.now(UTC).replace(tzinfo=None)
        scan.critical_count = severity_counts.get("CRITICAL", 0)
        scan.high_count = severity_counts.get("HIGH", 0)
        scan.medium_count = severity_counts.get("MEDIUM", 0)
        scan.low_count = severity_counts.get("LOW", 0)
        scan.info_count = severity_counts.get("INFO", 0)
        scan.node_latencies = json.dumps(latencies)
        scan.total_tokens = state.get("total_tokens", 0)
        await db.flush()

    for f in ai_findings:
        finding_id = f.get("finding_id", str(uuid.uuid4()))
        stub = test_stubs.get(finding_id)
        cvl_stub = cvl_properties.get(finding_id)
        stmt = pg_insert(Finding).values(
            id=finding_id,
            scan_id=scan_id,
            filename=state.get("filename", ""),
            category=f.get("category", ""),
            severity=f.get("severity", "INFO"),
            title=f.get("title", ""),
            description=f.get("description", ""),
            affected_lines=f.get("affected_lines", []),
            affected_code=f.get("affected_code"),
            recommendation=f.get("recommendation", ""),
            exploit_scenario=f.get("exploit_scenario", ""),
            test_stub=stub,
            cvl_property=cvl_stub,
            false_positive=f.get("false_positive", False),
            confidence=f.get("confidence", "MEDIUM"),
        ).on_conflict_do_update(
            index_elements=["id"],
            set_={
                "scan_id": scan_id,
                "severity": f.get("severity", "INFO"),
                "test_stub": stub,
                "cvl_property": cvl_stub,
            },
        )
        await db.execute(stmt)

    await db.commit()
