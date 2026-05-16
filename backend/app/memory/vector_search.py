from dataclasses import dataclass

from pgvector.sqlalchemy import Vector
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.embedding import VulnerabilityEmbedding
from app.memory.embedder import embed_text


@dataclass
class SimilarVuln:
    id: str
    content: str
    source: str
    category: str | None
    similarity: float


async def search(
    query: str,
    db: AsyncSession,
    k: int = 5,
    category_filter: str | None = None,
) -> list[SimilarVuln]:
    """Find the k most similar vulnerability entries to the query string."""
    query_embedding = await embed_text(query)

    stmt = (
        select(
            VulnerabilityEmbedding,
            (1 - VulnerabilityEmbedding.embedding.cosine_distance(query_embedding)).label("similarity"),
        )
        .order_by(VulnerabilityEmbedding.embedding.cosine_distance(query_embedding))
        .limit(k)
    )

    if category_filter:
        stmt = stmt.where(VulnerabilityEmbedding.category == category_filter)

    result = await db.execute(stmt)
    rows = result.all()

    return [
        SimilarVuln(
            id=row.VulnerabilityEmbedding.id,
            content=row.VulnerabilityEmbedding.content,
            source=row.VulnerabilityEmbedding.source,
            category=row.VulnerabilityEmbedding.category,
            similarity=float(row.similarity),
        )
        for row in rows
    ]
