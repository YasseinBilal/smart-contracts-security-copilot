import time

from app.agents.state import AuditState
from app.ai.client import chat_json
from app.ai.prompts.system import SECURITY_RESEARCHER_SYSTEM_PROMPT
from app.ai.prompts.explain import build_explain_prompt


async def explain_node(state: AuditState) -> AuditState:
    t0 = time.monotonic()
    source = state["source"]
    filename = state.get("filename", "contract.sol")
    ai_findings = state.get("ai_findings", [])

    finding_titles = [f.get("title", "") for f in ai_findings]

    prompt = build_explain_prompt(source, filename, finding_titles)
    tokens_used = 0

    try:
        result, tokens = await chat_json(
            system=SECURITY_RESEARCHER_SYSTEM_PROMPT,
            user=prompt,
            max_tokens=1500,
        )
        explanation = result
        tokens_used = tokens
    except Exception as e:
        explanation = {
            "summary": f"Explanation unavailable: {e}",
            "privileged_functions": [],
            "trust_assumptions": [],
            "risk_notes": "",
        }

    return {
        **state,
        "explanation": explanation,
        "explain_latency": time.monotonic() - t0,
        "total_tokens": state.get("total_tokens", 0) + tokens_used,
    }
