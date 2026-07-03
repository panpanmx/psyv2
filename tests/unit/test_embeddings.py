from app.rag.embeddings import LocalHashEmbeddingProvider


def test_local_embedding_is_deterministic_and_normalized() -> None:
    provider = LocalHashEmbeddingProvider(dimensions=16)

    first = provider.embed_text("焦虑 睡眠 考试")
    second = provider.embed_text("焦虑 睡眠 考试")

    assert first == second
    assert len(first) == 16
    assert all(-1.0 <= value <= 1.0 for value in first)
