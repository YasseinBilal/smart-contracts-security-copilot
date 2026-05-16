import re
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.embedder import embed_batch
from app.models.embedding import VulnerabilityEmbedding

_FUNCTION_SPLIT = re.compile(r"\bfunction\s+\w+", re.IGNORECASE)


def _chunk_by_function(source: str, filename: str) -> list[dict]:
    """Split a Solidity file into chunks by function boundary."""
    lines = source.splitlines()
    chunks = []
    current_chunk: list[str] = []
    current_func = "contract_header"
    depth = 0

    for line in lines:
        m = _FUNCTION_SPLIT.search(line)
        if m and depth == 0:
            if current_chunk:
                chunks.append(
                    {"text": "\n".join(current_chunk), "name": current_func, "filename": filename}
                )
            current_func = re.search(r"function\s+(\w+)", line).group(1)  # type: ignore
            current_chunk = [line]
            depth = line.count("{") - line.count("}")
        else:
            current_chunk.append(line)
            depth += line.count("{") - line.count("}")
            if depth < 0:
                depth = 0

    if current_chunk:
        chunks.append({"text": "\n".join(current_chunk), "name": current_func, "filename": filename})

    return chunks


async def ingest_solidity_file(
    filepath: Path,
    repo_id: str,
    db: AsyncSession,
) -> int:
    source = filepath.read_text(encoding="utf-8", errors="ignore")
    chunks = _chunk_by_function(source, filepath.name)

    if not chunks:
        return 0

    texts = [c["text"] for c in chunks]
    embeddings = await embed_batch(texts)

    for chunk, embedding in zip(chunks, embeddings):
        entry = VulnerabilityEmbedding(
            id=str(uuid.uuid4()),
            content=chunk["text"][:4000],
            embedding=embedding,
            source="repo",
            category=None,
            metadata_={"repo_id": repo_id, "filename": chunk["filename"], "function": chunk["name"]},
        )
        db.add(entry)

    await db.commit()
    return len(chunks)
