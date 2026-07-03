from pathlib import Path

from app.db.repositories.knowledge_repo import KnowledgeRepository
from app.rag.embeddings import LocalHashEmbeddingProvider
from app.rag.ingestion import KnowledgeIngestionService


async def test_ingestion_loads_markdown_files(db_session, tmp_path: Path) -> None:
    kb = tmp_path / "knowledge_base"
    kb.mkdir()
    (kb / "sleep.md").write_text("# 睡眠\n\n## 建议\n\n睡前减少屏幕刺激。", encoding="utf-8")

    service = KnowledgeIngestionService(
        repository=KnowledgeRepository(db_session),
        embedding_provider=LocalHashEmbeddingProvider(dimensions=8),
    )
    result = await service.ingest_directory(kb)
    await db_session.commit()

    assert result.document_count == 1
    assert result.chunk_count >= 1
