from app.db.repositories.knowledge_repo import KnowledgeRepository
from app.rag.knowledge_loader import KnowledgeLoader


class KnowledgeRetriever:
    def __init__(self, loader: KnowledgeLoader | None = None, *, top_k: int = 5) -> None:
        self.loader = loader or KnowledgeLoader()
        self.top_k = top_k

    def retrieve(self, query: str, *, top_k: int | None = None) -> list[dict[str, str]]:
        top_k = top_k or self.top_k
        documents = self.loader.load()
        tokens = _tokens(query)
        scored: list[tuple[int, dict[str, str]]] = []
        for doc in documents:
            score = sum(2 for token in tokens if token and token in doc["title"])
            score += sum(1 for token in tokens if token and token in doc["content"])
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            doc
            | {
                "chunk_id": doc["id"],
                "source_path": "",
                "section": doc["title"],
                "score": str(score),
            }
            for score, doc in scored[:top_k]
        ]

    async def retrieve_async(
        self,
        query: str,
        *,
        repository: KnowledgeRepository | None = None,
        top_k: int | None = None,
    ) -> list[dict[str, str]]:
        top_k = top_k or self.top_k
        tokens = _tokens(query)
        if repository is not None:
            rows = await repository.search_by_keywords(tokens, top_k=top_k)
            if rows:
                return [
                    {
                        "id": row.doc_id,
                        "chunk_id": row.chunk_id,
                        "title": row.title,
                        "source_path": row.source_path,
                        "section": row.section,
                        "content": row.content,
                        "score": str(row.score),
                    }
                    for row in rows
                ]
        return self.retrieve(query, top_k=top_k)


def _tokens(query: str) -> list[str]:
    candidates = [
        "考试",
        "压力",
        "焦虑",
        "抑郁",
        "低落",
        "睡眠",
        "睡不着",
        "失眠",
        "危机",
        "自杀",
        "CBT",
        "正念",
        "校园",
        "求助",
        "宿舍",
        "室友",
        "霸凌",
        "人际",
        "行为激活",
        "危机",
        "热线",
    ]
    return [token for token in candidates if token in query]
