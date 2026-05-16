import time

from app.agents.state import AuditState
from app.database import AsyncSessionLocal
from app.memory.vector_search import search, SimilarVuln


async def memory_query_node(state: AuditState) -> AuditState:
    t0 = time.monotonic()
    static_findings = state.get("static_findings", [])

    rag_context: list[dict] = []
    seen_ids: set[str] = set()

    async with AsyncSessionLocal() as db:
        for finding in static_findings[:5]:  # cap at 5 findings to limit API calls
            query = f"{finding['category']} {finding['title']} {finding['description'][:200]}"
            try:
                similar = await search(query, db, k=3, category_filter=finding["category"])
                for v in similar:
                    if v.id not in seen_ids and v.similarity > 0.7:
                        seen_ids.add(v.id)
                        rag_context.append(
                            {
                                "id": v.id,
                                "content": v.content,
                                "source": v.source,
                                "category": v.category,
                                "similarity": v.similarity,
                            }
                        )
            except Exception:
                pass  # DB may not be seeded yet; continue without RAG

    return {
        **state,
        "rag_context": rag_context,
        "memory_latency": time.monotonic() - t0,
    }
