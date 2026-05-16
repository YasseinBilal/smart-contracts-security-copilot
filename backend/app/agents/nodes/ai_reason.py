import time
from dataclasses import asdict

from app.agents.state import AuditState
from app.ai.client import chat_json
from app.ai.prompts.system import SECURITY_RESEARCHER_SYSTEM_PROMPT
from app.ai.prompts.analysis import build_analysis_prompt
from app.detectors.base import StaticFinding
from app.memory.vector_search import SimilarVuln


async def ai_reason_node(state: AuditState) -> AuditState:
    t0 = time.monotonic()
    source = state["source"]
    filename = state.get("filename", "contract.sol")
    static_dicts = state.get("static_findings", [])
    rag_dicts = state.get("rag_context", [])

    static_findings = [_dict_to_finding(d) for d in static_dicts]
    rag_context = [_dict_to_vuln(d) for d in rag_dicts]

    user_prompt = build_analysis_prompt(source, filename, static_findings, rag_context)

    result, tokens = await chat_json(
        system=SECURITY_RESEARCHER_SYSTEM_PROMPT,
        user=user_prompt,
        max_tokens=6000,
    )

    ai_findings = result.get("findings", [])
    # Filter out confirmed false positives
    ai_findings = [f for f in ai_findings if not f.get("false_positive", False)]

    return {
        **state,
        "ai_findings": ai_findings,
        "ai_latency": time.monotonic() - t0,
        "total_tokens": state.get("total_tokens", 0) + tokens,
    }


def _dict_to_finding(d: dict) -> StaticFinding:
    return StaticFinding(
        category=d.get("category", "REENTRANCY"),
        severity=d.get("severity", "MEDIUM"),
        title=d.get("title", ""),
        description=d.get("description", ""),
        affected_lines=d.get("affected_lines", []),
        affected_code=d.get("affected_code", ""),
        confidence=d.get("confidence", "MEDIUM"),
        filename=d.get("filename", ""),
        finding_id=d.get("finding_id", ""),
    )


def _dict_to_vuln(d: dict) -> SimilarVuln:
    return SimilarVuln(
        id=d.get("id", ""),
        content=d.get("content", ""),
        source=d.get("source", ""),
        category=d.get("category"),
        similarity=d.get("similarity", 0.0),
    )
