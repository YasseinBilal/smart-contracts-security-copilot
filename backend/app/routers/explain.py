from fastapi import APIRouter
from app.schemas.ingest import ExplainRequest, ExplainResponse
from app.ai.client import chat_json
from app.ai.prompts.system import SECURITY_RESEARCHER_SYSTEM_PROMPT
from app.ai.prompts.explain import build_explain_prompt

router = APIRouter()


@router.post("/explain", response_model=ExplainResponse)
async def explain_contract(body: ExplainRequest):
    prompt = build_explain_prompt(body.source, body.filename, [])
    result, _ = await chat_json(
        system=SECURITY_RESEARCHER_SYSTEM_PROMPT,
        user=prompt,
        max_tokens=1500,
    )
    return ExplainResponse(
        filename=body.filename,
        summary=result.get("summary", ""),
        privileged_functions=result.get("privileged_functions", []),
        trust_assumptions=result.get("trust_assumptions", []),
    )
