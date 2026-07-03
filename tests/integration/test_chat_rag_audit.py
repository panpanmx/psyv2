import asyncio
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import Settings
from app.db.models import AuditLog
from app.db.repositories.knowledge_repo import KnowledgeRepository
from app.main import create_app
from app.rag.embeddings import LocalHashEmbeddingProvider
from app.rag.ingestion import KnowledgeIngestionService


def test_chat_uses_ingested_rag_and_records_retrieval_audit(tmp_path: Path) -> None:
    db_path = tmp_path / "rag.db"
    kb = tmp_path / "knowledge_base"
    kb.mkdir()
    (kb / "sleep.md").write_text(
        "# 睡眠支持\n\n## 考试压力与睡眠\n\n睡前减少屏幕刺激，安排放松练习。",
        encoding="utf-8",
    )
    app = create_app(
        Settings(database_url=f"sqlite+aiosqlite:///{db_path}", knowledge_base_dir=str(kb))
    )

    with TestClient(app) as client:
        services = app.state.services

        async def ingest() -> None:
            async with services.sessionmaker() as session:
                service = KnowledgeIngestionService(
                    repository=KnowledgeRepository(session),
                    embedding_provider=LocalHashEmbeddingProvider(dimensions=8),
                )
                await service.ingest_directory(kb)
                await session.commit()

        asyncio.run(ingest())
        response = client.post(
            "/api/chat/messages",
            json={
                "user_id": "u-rag",
                "conversation_id": "c-rag",
                "message": "我考试压力很大，晚上睡不着。",
            },
        )
        assert response.status_code == 200
        assert "参考" in response.json()["assistant_message"]

        async def fetch_audits() -> list[AuditLog]:
            async with services.sessionmaker() as session:
                result = await session.execute(select(AuditLog))
                return list(result.scalars())

        audits = asyncio.run(fetch_audits())

    assert any(row.event_type == "rag.retrieve.completed" for row in audits)


def test_crisis_chat_skips_regular_rag_audit(tmp_path: Path) -> None:
    app = create_app(Settings(database_url=f"sqlite+aiosqlite:///{tmp_path / 'crisis.db'}"))

    with TestClient(app) as client:
        response = client.post(
            "/api/chat/messages",
            json={
                "user_id": "u-crisis-rag",
                "conversation_id": "c-crisis-rag",
                "message": "我不想活了，已经想好了方式。",
            },
        )
        assert response.status_code == 200

        services = app.state.services

        async def fetch_audits() -> list[AuditLog]:
            async with services.sessionmaker() as session:
                result = await session.execute(select(AuditLog))
                return list(result.scalars())

        audits = asyncio.run(fetch_audits())

    assert not any(row.event_type == "rag.retrieve.completed" for row in audits)
