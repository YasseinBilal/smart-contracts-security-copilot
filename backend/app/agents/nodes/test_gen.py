import time

from app.agents.state import AuditState
from app.ai.client import chat_json
from app.ai.prompts.system import SECURITY_RESEARCHER_SYSTEM_PROMPT
from app.ai.prompts.test_gen import build_test_gen_prompt


async def test_gen_node(state: AuditState) -> AuditState:
    t0 = time.monotonic()
    source = state["source"]
    ai_findings = state.get("ai_findings", [])

    # Only generate tests for CRITICAL and HIGH findings
    high_priority = [f for f in ai_findings if f.get("severity") in ("CRITICAL", "HIGH")]
    test_stubs: dict[str, str] = {}
    tokens_used = 0

    for finding in high_priority[:3]:  # cap at 3 to limit cost
        prompt = build_test_gen_prompt(source, finding)
        try:
            result, tokens = await chat_json(
                system=SECURITY_RESEARCHER_SYSTEM_PROMPT,
                user=prompt,
                max_tokens=2000,
            )
            stub = result.get("test_stub", "")
            if stub:
                test_stubs[finding["finding_id"]] = stub
            tokens_used += tokens
        except Exception:
            pass  # test gen failure should not abort the scan

    return {
        **state,
        "test_stubs": test_stubs,
        "test_gen_latency": time.monotonic() - t0,
        "total_tokens": state.get("total_tokens", 0) + tokens_used,
    }
