import json
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import audit_workflow
from app.agents.nodes.report import _persist
from app.database import get_db
from app.models.scan import Scan
from app.schemas.ingest import AnalyzeRequest

router = APIRouter()

# Map LangGraph node names to SSE stage labels
_NODE_TO_STAGE = {
    "parse": ("parsing", "Parsing Solidity source..."),
    "static_scan": ("static_scan", "Running static detectors..."),
    "memory_query": ("memory_query", "Querying vulnerability memory..."),
    "ai_reason": ("ai_reasoning", "GPT-4o reasoning over findings..."),
    "test_gen": ("test_gen", "Generating Foundry test stubs..."),
    "property_gen": ("property_gen", "Generating Certora CVL property stubs..."),
    "explain": ("explain", "Building plain-English explanation..."),
    "report": ("report", "Compiling final report..."),
}


@router.post("/analyze")
async def analyze_contract(
    body: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
):
    scan_id = str(uuid.uuid4())

    scan = Scan(
        id=scan_id,
        filename=body.filename,
        status="running",
        triggered_by="manual",
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(scan)
    await db.commit()

    async def event_stream():
        def sse(data: dict) -> str:
            return f"data: {json.dumps(data)}\n\n"

        try:
            initial_state = {
                "source": body.source,
                "filename": body.filename,
                "scan_id": scan_id,
            }

            # Single-pass: astream yields {node_name: node_output} for each completed node.
            # We accumulate state in-place and send SSE progress after each node.
            final_state: dict = dict(initial_state)

            async for chunk in audit_workflow.astream(initial_state, stream_mode="updates"):
                for node_name, node_output in chunk.items():
                    # Accumulate state
                    final_state.update(node_output)

                    # Emit progress event
                    stage_info = _NODE_TO_STAGE.get(node_name)
                    if stage_info:
                        yield sse({"stage": stage_info[0], "message": stage_info[1]})

            report = final_state.get("report", {})
            ai_findings = final_state.get("ai_findings", [])
            test_stubs = final_state.get("test_stubs", {})
            cvl_properties = final_state.get("cvl_properties", {})
            latencies = report.get("node_latencies", {})
            severity_counts = report.get("severity_counts", {})

            await _persist(db, scan_id, final_state, ai_findings, test_stubs, cvl_properties, severity_counts, latencies)

            # Merge test stubs and CVL properties into findings sent to the frontend
            for f in report.get("findings", []):
                fid = f.get("finding_id", "")
                if fid in test_stubs:
                    f["test_stub"] = test_stubs[fid]
                if fid in cvl_properties:
                    f["cvl_property"] = cvl_properties[fid]

            yield sse({"stage": "done", "scan_id": scan_id, "report": report})

        except Exception as e:
            yield sse({"stage": "error", "message": str(e)})

            scan_obj = await db.get(Scan, scan_id)
            if scan_obj:
                scan_obj.status = "failed"
                await db.commit()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
