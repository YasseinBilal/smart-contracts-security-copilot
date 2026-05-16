import time
from dataclasses import asdict

from app.agents.state import AuditState
from app.detectors.registry import run_all_detectors


async def static_scan_node(state: AuditState) -> AuditState:
    t0 = time.monotonic()
    source = state["source"]
    filename = state.get("filename", "contract.sol")

    findings = run_all_detectors(source, filename)

    return {
        **state,
        "static_findings": [asdict(f) for f in findings],
        "static_latency": time.monotonic() - t0,
    }
