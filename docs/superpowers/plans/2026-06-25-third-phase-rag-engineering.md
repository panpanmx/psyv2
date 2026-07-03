# 第三阶段 RAG/知识库工程化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 将当前 Markdown RAG-lite 升级为可入库、可检索、可审计、可持续更新的校园心理支持知识库系统。

**Architecture:** 保留现有 `knowledge_base/*.md` 作为源文档，新增 chunker、embedding provider、vector store、ingestion service 和检索审计日志。开发和测试环境使用 deterministic/local embedding，生产环境预留真实 embedding provider；PostgreSQL + pgvector 作为正式向量存储。危机路径继续绕开普通 RAG，只允许使用安全策略库。

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy async, Alembic, PostgreSQL + pgvector, local deterministic embeddings for tests, pytest, ruff, mypy.

---

## 阶段边界

本阶段实现：

- Markdown 文档切片。
- 知识 chunk 元数据 schema。
- Embedding Provider 抽象和本地 deterministic provider。
- pgvector 迁移和 vector store repository。
- 知识库入库命令。
- 检索返回 `chunk_id/source/title/score/content`。
- RAG 检索审计事件。
- Chat API 使用新 retriever，但危机 S2-S4 仍绕开普通 RAG。

本阶段不实现：

- LLM Provider。
- LangGraph 编排。
- 前端知识库管理界面。

## 文件结构

- Modify: `pyproject.toml`
- Modify: `.env.example`
- Modify: `app/core/config.py`
- Create: `app/rag/chunker.py`
- Create: `app/rag/embeddings.py`
- Create: `app/rag/vector_store.py`
- Modify: `app/rag/retriever.py`
- Create: `app/rag/ingestion.py`
- Create: `app/rag/cli.py`
- Modify: `app/db/models.py`
- Create: `app/db/repositories/knowledge_repo.py`
- Create: `alembic/versions/2026_06_25_0002_knowledge_chunks.py`
- Modify: `app/observability/events.py`
- Modify: `app/agent/orchestrator.py`
- Create: `tests/unit/test_chunker.py`
- Create: `tests/unit/test_embeddings.py`
- Create: `tests/unit/test_knowledge_repository.py`
- Create: `tests/unit/test_rag_ingestion.py`
- Modify: `tests/unit/test_retriever.py`
- Create: `tests/integration/test_chat_rag_audit.py`
- Create: `docs/technical/phase-3-rag-engineering-technical-doc.md`

---

### Task 1: RAG 配置与依赖

**Files:**
- Modify: `pyproject.toml`
- Modify: `.env.example`
- Modify: `app/core/config.py`
- Test: `tests/unit/test_config.py`

- [x] **Step 1: 写失败测试**

在 `tests/unit/test_config.py` 增加：

```python
def test_settings_exposes_rag_configuration() -> None:
    settings = Settings(
        knowledge_base_dir="knowledge_base",
        embedding_provider="local",
        rag_top_k=5,
    )

    assert settings.knowledge_base_dir == "knowledge_base"
    assert settings.embedding_provider == "local"
    assert settings.rag_top_k == 5
```

- [x] **Step 2: 验证失败**

Run: `python -m pytest tests/unit/test_config.py::test_settings_exposes_rag_configuration -q`

Expected: FAIL，因为 settings 尚无 RAG 字段。

- [x] **Step 3: 实现配置**

在 `Settings` 增加：

```python
knowledge_base_dir: str = "knowledge_base"
embedding_provider: str = "local"
rag_top_k: int = 5
```

`.env.example` 增加：

```env
KNOWLEDGE_BASE_DIR=knowledge_base
EMBEDDING_PROVIDER=local
RAG_TOP_K=5
```

- [x] **Step 4: 验证通过**

Run: `python -m pytest tests/unit/test_config.py -q`

Expected: PASS。

---

### Task 2: Markdown Chunker

**Files:**
- Create: `app/rag/chunker.py`
- Test: `tests/unit/test_chunker.py`

- [x] **Step 1: 写失败测试**

Create `tests/unit/test_chunker.py`:

```python
from app.rag.chunker import MarkdownChunker


def test_chunker_splits_sections_with_metadata() -> None:
    text = "# 焦虑\n\n## 适用场景\n\n考试压力。\n\n## 干预\n\n呼吸练习。"

    chunks = MarkdownChunker(max_chars=40).chunk_document(
        doc_id="anxiety",
        title="焦虑",
        source_path="knowledge_base/anxiety.md",
        content=text,
    )

    assert len(chunks) >= 2
    assert chunks[0].doc_id == "anxiety"
    assert chunks[0].title == "焦虑"
    assert chunks[0].source_path == "knowledge_base/anxiety.md"
    assert chunks[0].section
    assert chunks[0].content
```

- [x] **Step 2: 验证失败**

Run: `python -m pytest tests/unit/test_chunker.py -q`

Expected: FAIL because `app.rag.chunker` does not exist.

- [x] **Step 3: 实现 chunker**

实现：

- `KnowledgeChunk` Pydantic model: `chunk_id/doc_id/title/source_path/section/content/ordinal`
- `MarkdownChunker(max_chars: int = 1200)`
- 按 Markdown 二级标题切片。
- 超长 section 按段落累积到 `max_chars`。
- `chunk_id` 使用 `doc_id:ordinal`。

- [x] **Step 4: 验证通过**

Run: `python -m pytest tests/unit/test_chunker.py -q`

Expected: PASS。

---

### Task 3: Embedding Provider

**Files:**
- Create: `app/rag/embeddings.py`
- Test: `tests/unit/test_embeddings.py`

- [x] **Step 1: 写失败测试**

Create `tests/unit/test_embeddings.py`:

```python
from app.rag.embeddings import LocalHashEmbeddingProvider


def test_local_embedding_is_deterministic_and_normalized() -> None:
    provider = LocalHashEmbeddingProvider(dimensions=16)

    first = provider.embed_text("焦虑 睡眠 考试")
    second = provider.embed_text("焦虑 睡眠 考试")

    assert first == second
    assert len(first) == 16
    assert all(-1.0 <= value <= 1.0 for value in first)
```

- [x] **Step 2: 验证失败**

Run: `python -m pytest tests/unit/test_embeddings.py -q`

Expected: FAIL because provider does not exist.

- [x] **Step 3: 实现 provider**

实现：

- `EmbeddingProvider` Protocol，方法 `embed_text(text: str) -> list[float]`
- `LocalHashEmbeddingProvider(dimensions: int = 384)`
- 通过 hashlib 将 token hash 到固定维度，归一化到 `[-1.0, 1.0]`
- 本 provider 只用于测试和离线开发，不宣称语义质量。

- [x] **Step 4: 验证通过**

Run: `python -m pytest tests/unit/test_embeddings.py -q`

Expected: PASS。

---

### Task 4: KnowledgeChunk 数据模型与迁移

**Files:**
- Modify: `app/db/models.py`
- Create: `app/db/repositories/knowledge_repo.py`
- Create: `alembic/versions/2026_06_25_0002_knowledge_chunks.py`
- Test: `tests/unit/test_knowledge_repository.py`

- [x] **Step 1: 写失败测试**

Create `tests/unit/test_knowledge_repository.py`:

```python
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
```

- [x] **Step 2: 验证失败**

Run: `python -m pytest tests/unit/test_knowledge_repository.py -q`

Expected: FAIL because repository/model does not exist.

- [x] **Step 3: 实现模型**

新增 SQLAlchemy model `KnowledgeChunkModel`:

- `chunk_id`: primary key
- `doc_id`
- `title`
- `source_path`
- `section`
- `content`
- `ordinal`
- `embedding`: JSON, SQLite fallback
- `content_hash`
- `updated_at`

说明：PostgreSQL + pgvector 迁移中预留 vector column；SQLite 测试使用 JSON embedding。

- [x] **Step 4: 实现 repository**

`KnowledgeRepository`:

- `upsert_chunks(items: list[tuple[KnowledgeChunk, list[float]]])`
- `search_by_keywords(tokens: list[str], top_k: int) -> list[KnowledgeChunkSearchResult]`
- `list_chunks(doc_id: str | None = None)`

- [x] **Step 5: 添加 Alembic migration**

迁移创建 `knowledge_chunks` 表。若 PostgreSQL 环境支持 pgvector，迁移中执行：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

SQLite 路径不执行该 SQL。

- [x] **Step 6: 验证通过**

Run: `python -m pytest tests/unit/test_knowledge_repository.py -q`

Expected: PASS。

---

### Task 5: Knowledge Ingestion

**Files:**
- Create: `app/rag/ingestion.py`
- Create: `app/rag/cli.py`
- Test: `tests/unit/test_rag_ingestion.py`

- [x] **Step 1: 写失败测试**

Create `tests/unit/test_rag_ingestion.py`:

```python
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
```

- [x] **Step 2: 验证失败**

Run: `python -m pytest tests/unit/test_rag_ingestion.py -q`

Expected: FAIL because ingestion service does not exist.

- [x] **Step 3: 实现 ingestion service**

实现：

- `KnowledgeIngestionResult(document_count, chunk_count)`
- `ingest_directory(path: Path) -> KnowledgeIngestionResult`
- 读取 `*.md`
- chunk
- embedding
- upsert 到 repository

- [x] **Step 4: 实现 CLI**

`app/rag/cli.py` 支持：

```bash
python -m app.rag.cli ingest --path knowledge_base
```

命令读取 settings/database_url，打开 session，执行 ingestion。

- [x] **Step 5: 验证通过**

Run: `python -m pytest tests/unit/test_rag_ingestion.py -q`

Expected: PASS。

---

### Task 6: Retriever 切换为 DB-backed RAG

**Files:**
- Modify: `app/rag/retriever.py`
- Modify: `app/services.py`
- Modify: `app/agent/orchestrator.py`
- Modify: `app/observability/events.py`
- Test: `tests/integration/test_chat_rag_audit.py`

- [x] **Step 1: 写失败测试**

Create `tests/integration/test_chat_rag_audit.py`:

```python
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import Settings
from app.db.models import AuditLog
from app.main import create_app


def test_chat_uses_ingested_rag_and_records_retrieval_audit(tmp_path: Path) -> None:
    app = create_app(Settings(database_url=f"sqlite+aiosqlite:///{tmp_path / 'rag.db'}"))

    with TestClient(app) as client:
        client.post("/api/admin/knowledge/ingest")
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
```

如果不做 admin ingest API，则测试直接调用 ingestion service fixture。最终必须验证 `rag.retrieve.completed` 审计事件存在。

- [x] **Step 2: 验证失败**

Run: `python -m pytest tests/integration/test_chat_rag_audit.py -q`

Expected: FAIL because chat does not use DB-backed retriever/audit.

- [x] **Step 3: 实现 DB-backed retriever**

新增或改造：

- `KnowledgeRetriever.retrieve(query: str, top_k: int) -> list[dict[str, str]]`
- 若传入 repository，优先查 DB chunks。
- 若 DB 无 chunks，回退现有 Markdown keyword retriever。
- 返回字段包含 `chunk_id/title/source_path/section/content/score`。

- [x] **Step 4: 记录 RAG 审计**

新增事件常量：

```python
RAG_RETRIEVE_COMPLETED = "rag.retrieve.completed"
```

审计 payload 包含：

- `query_hash`
- `top_k`
- `chunk_ids`
- `scores`

- [x] **Step 5: 保持危机绕开普通 RAG**

在 `AgentOrchestrator` 中保持：

```python
knowledge = [] if risk.crisis_level in {"s2", "s3", "s4"} else retriever.retrieve(...)
```

并增加危机样例测试，确认不会记录普通 RAG 检索。

- [x] **Step 6: 验证通过**

Run:

```bash
python -m pytest tests/unit/test_retriever.py tests/integration/test_chat_rag_audit.py -q
```

Expected: PASS。

---

### Task 7: 文档与最终验证

**Files:**
- Create: `docs/technical/phase-3-rag-engineering-technical-doc.md`
- Modify: `docs/technical/README.md`
- Modify: `docs/context/codex-project-context.md`
- Modify: `README.md`

- [x] **Step 1: 写技术文档**

文档必须覆盖：

- chunk schema
- embedding provider
- ingestion 命令
- pgvector/SQLite 兼容策略
- retriever 数据流
- RAG 审计字段
- 危机绕开普通 RAG 的规则

- [x] **Step 2: 更新 README**

新增：

```bash
python -m app.rag.cli ingest --path knowledge_base
```

- [x] **Step 3: 最终验证**

Run:

```bash
python -m pytest -q
python -m ruff check .
python -m mypy app
python -m alembic history
```

Expected:

- all tests pass
- ruff clean
- mypy clean
- Alembic shows phase 2 and phase 3 migrations

- [x] **Step 4: 更新本计划勾选**

所有任务通过后，将本文件复选框从 `[ ]` 更新为 `[x]`。

