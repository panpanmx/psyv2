from dataclasses import dataclass
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import KnowledgeChunkModel
from app.rag.chunker import KnowledgeChunk


@dataclass(frozen=True)
class KnowledgeChunkSearchResult:
    chunk_id: str
    doc_id: str
    title: str
    source_path: str
    section: str
    content: str
    score: float


class KnowledgeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_chunks(self, items: list[tuple[KnowledgeChunk, list[float]]]) -> None:
        for chunk, embedding in items:
            existing = await self.session.get(KnowledgeChunkModel, chunk.chunk_id)
            payload = {
                "doc_id": chunk.doc_id,
                "title": chunk.title,
                "source_path": chunk.source_path,
                "section": chunk.section,
                "content": chunk.content,
                "ordinal": chunk.ordinal,
                "embedding": embedding,
                "content_hash": sha256(chunk.content.encode("utf-8")).hexdigest(),
            }
            if existing is None:
                self.session.add(KnowledgeChunkModel(chunk_id=chunk.chunk_id, **payload))
            else:
                for key, value in payload.items():
                    setattr(existing, key, value)
        await self.session.flush()

    async def search_by_keywords(
        self,
        tokens: list[str],
        *,
        top_k: int,
    ) -> list[KnowledgeChunkSearchResult]:
        chunks = await self.list_chunks()
        scored: list[KnowledgeChunkSearchResult] = []
        for chunk in chunks:
            score = _score_chunk(chunk, tokens)
            if score <= 0:
                continue
            scored.append(
                KnowledgeChunkSearchResult(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    title=chunk.title,
                    source_path=chunk.source_path,
                    section=chunk.section,
                    content=chunk.content,
                    score=score,
                )
            )
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    async def list_chunks(self, doc_id: str | None = None) -> list[KnowledgeChunkModel]:
        statement = select(KnowledgeChunkModel).order_by(
            KnowledgeChunkModel.doc_id,
            KnowledgeChunkModel.ordinal,
        )
        if doc_id is not None:
            statement = statement.where(KnowledgeChunkModel.doc_id == doc_id)
        result = await self.session.execute(statement)
        return list(result.scalars())


def _score_chunk(chunk: KnowledgeChunkModel, tokens: list[str]) -> float:
    score = 0.0
    for token in tokens:
        if not token:
            continue
        if token in chunk.title:
            score += 3.0
        if token in chunk.section:
            score += 2.0
        if token in chunk.content:
            score += 1.0
    return score
