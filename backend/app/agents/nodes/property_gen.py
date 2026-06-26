import time

from app.agents.state import AuditState
from app.ai.client import chat_json
from app.ai.prompts.property_gen import build_property_gen_prompt
from app.ai.prompts.system import SECURITY_RESEARCHER_SYSTEM_PROMPT


async def property_gen_node(state: AuditState) -> AuditState:
    t0 = time.monotonic()
    source = state["source"]
    ai_findings = state.get("ai_findings", [])

    criticals = [f for f in ai_findings if f.get("severity") == "CRITICAL"]
    highs = [f for f in ai_findings if f.get("severity") == "HIGH"]
    # Give CRITICALs up to 3 slots, HIGHs up to 3 slots independently
    candidates = criticals[:3] + highs[:3]
    cvl_properties: dict[str, str] = {}
    tokens_used = 0

    for finding in candidates:
        prompt = build_property_gen_prompt(source, finding)
        try:
            result, tokens = await chat_json(
                system=SECURITY_RESEARCHER_SYSTEM_PROMPT,
                user=prompt,
                max_tokens=2000,
            )
            stub = result.get("cvl_stub", "")
            if stub:
                cvl_properties[finding["finding_id"]] = stub
            tokens_used += tokens
        except Exception:
            pass  # property gen failure should not abort the scan

    return {
        **state,
        "cvl_properties": cvl_properties,
        "property_gen_latency": time.monotonic() - t0,
        "total_tokens": state.get("total_tokens", 0) + tokens_used,
    }
