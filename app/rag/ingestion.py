from dataclasses import dataclass
from pathlib import Path

from app.db.repositories.knowledge_repo import KnowledgeRepository
from app.rag.chunker import MarkdownChunker
from app.rag.embeddings import EmbeddingProvider


@dataclass(frozen=True)
class KnowledgeIngestionResult:
    document_count: int
    chunk_count: int


class KnowledgeIngestionService:
    def __init__(
        self,
        *,
        repository: KnowledgeRepository,
        embedding_provider: EmbeddingProvider,
        chunker: MarkdownChunker | None = None,
    ) -> None:
        self.repository = repository
        self.embedding_provider = embedding_provider
        self.chunker = chunker or MarkdownChunker()

    async def ingest_directory(self, path: Path) -> KnowledgeIngestionResult:
        documents = sorted(path.glob("*.md"))
        chunk_count = 0
        for document in documents:
            content = document.read_text(encoding="utf-8")
            title = _title(content, document.stem)
            chunks = self.chunker.chunk_document(
                doc_id=document.stem,
                title=title,
                source_path=str(document),
                content=content,
            )
            await self.repository.upsert_chunks(
                [(chunk, self.embedding_provider.embed_text(chunk.content)) for chunk in chunks]
            )
            chunk_count += len(chunks)
        return KnowledgeIngestionResult(document_count=len(documents), chunk_count=chunk_count)


def _title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback
