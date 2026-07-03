from app.db.repositories.knowledge_repo import KnowledgeRepository
from app.rag.chunker import KnowledgeChunk


async def test_knowledge_repository_upserts_and_searches_chunks(db_session) -> None:
    repo = KnowledgeRepository(db_session)
    chunk = KnowledgeChunk(
        chunk_id="anxiety:0",
        doc_id="anxiety",
        title="焦虑与校园压力",
        source_path="knowledge_base/anxiety.md",
        section="适用场景",
        content="考试压力和睡眠困难可能与焦虑相关。",
        ordinal=0,
    )

    await repo.upsert_chunks([(chunk, [0.1, 0.2, 0.3])])
    await db_session.commit()

    rows = await repo.search_by_keywords(["焦虑", "睡眠"], top_k=3)
    assert rows[0].chunk_id == "anxiety:0"
    assert rows[0].title == "焦虑与校园压力"
