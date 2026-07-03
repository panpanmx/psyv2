from app.rag.knowledge_loader import KnowledgeLoader
from app.rag.retriever import KnowledgeRetriever


def test_retriever_prefers_query_relevant_knowledge() -> None:
    results = KnowledgeRetriever().retrieve("我最近考试压力很大，睡不着，也很焦虑。", top_k=2)

    assert results
    assert results[0]["id"] in {"anxiety", "sleep"}


def test_knowledge_base_contains_real_campus_support_topics() -> None:
    documents = KnowledgeLoader().load()
    ids = {document["id"] for document in documents}

    assert len(documents) >= 10
    assert {
        "anxiety",
        "depression",
        "crisis_response",
        "campus_resources",
        "behavioral_activation",
        "interpersonal_support",
        "help_seeking",
    } <= ids
    assert all("demo" not in document["content"].lower() for document in documents)
