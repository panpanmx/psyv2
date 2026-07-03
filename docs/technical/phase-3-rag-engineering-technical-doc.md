# 第三阶段 RAG/知识库工程化技术文档

最后更新日期：2026-06-25

## 目标与范围

第三阶段将第二阶段的 Markdown RAG-lite 升级为可入库、可检索、可审计的知识库工程化路径。保留 `knowledge_base/*.md` 作为知识源，同时新增 Markdown chunk、local deterministic embedding、`knowledge_chunks` 表、ingestion service、DB-backed retriever 和 RAG 检索审计。

危机风险仍然优先安全策略：当风险等级为 `s2/s3/s4` 时，聊天链路不执行普通知识库检索，也不写入 `rag.retrieve.completed` 事件。

## 模块职责

- `app/rag/chunker.py`：定义 `KnowledgeChunk` 和 `MarkdownChunker`，按 Markdown 二级标题拆分，超长段落按 `max_chars` 聚合切片。
- `app/rag/embeddings.py`：定义 `EmbeddingProvider` 协议和 `LocalHashEmbeddingProvider`。本地 provider 只用于测试与离线开发，不代表真实语义 embedding 质量。
- `app/db/models.py`：新增 `KnowledgeChunkModel`。
- `app/db/repositories/knowledge_repo.py`：提供 chunk upsert、按关键词搜索、按文档列出 chunk。
- `app/rag/ingestion.py`：读取目录下 Markdown，chunk 后生成 embedding 并入库。
- `app/rag/cli.py`：提供 `python -m app.rag.cli ingest --path knowledge_base`。
- `app/rag/retriever.py`：优先使用 DB chunk 检索；无 DB chunk 时回退 Markdown loader。

## Chunk Schema

`KnowledgeChunk` 字段：

- `chunk_id`：格式为 `{doc_id}:{ordinal}`。
- `doc_id`：Markdown 文件名 stem。
- `title`：文档一级标题。
- `source_path`：源文件路径。
- `section`：二级标题，缺省时使用文档标题。
- `content`：chunk 正文。
- `ordinal`：同一文档内递增序号。

数据库表 `knowledge_chunks` 额外保存：

- `embedding`：JSON 数组，本地与 SQLite 测试路径使用。
- `content_hash`：chunk 内容 hash，便于后续增量更新和审计比对。
- `created_at/updated_at`：继承时间字段。

## pgvector 与 SQLite 兼容策略

Alembic 迁移 `2026_06_25_0002_knowledge_chunks.py` 在 PostgreSQL 下执行：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

当前第一版为保持 SQLite 测试和本地开发稳定，实际 embedding 存储使用 JSON。后续接真实 semantic embedding 后，可在 PostgreSQL 迁移中增加 vector column 与索引，并让 repository 按向量距离排序。

## Retriever 数据流

普通聊天路径：

1. `AgentOrchestrator` 完成规则信号抽取与风险评估。
2. 若 `crisis_level` 不在 `s2/s3/s4`，调用 `KnowledgeRetriever.retrieve_async()`。
3. retriever 优先通过 `KnowledgeRepository.search_by_keywords()` 搜索 DB chunk。
4. 若 DB 没有 chunk，回退 `KnowledgeLoader` 读取 Markdown。
5. 回复生成阶段使用首个知识标题生成“参考...”提示。

返回字段包含 `id/chunk_id/title/source_path/section/content/score`。

## RAG 审计

新增事件：

```text
rag.retrieve.completed
```

数据库审计写入 `audit_logs`，本地审计写入 `AuditLogger`。payload 包含 `agent_run_id/query_hash/top_k/chunk_ids/scores`。审计只记录 query hash，不保存完整用户原文。

## 测试覆盖

新增覆盖：

- `tests/unit/test_chunker.py`
- `tests/unit/test_embeddings.py`
- `tests/unit/test_knowledge_repository.py`
- `tests/unit/test_rag_ingestion.py`
- `tests/integration/test_chat_rag_audit.py`

针对性验证命令：

```bash
/Users/panpan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pytest tests/unit/test_config.py::test_settings_exposes_rag_configuration tests/unit/test_chunker.py tests/unit/test_embeddings.py tests/unit/test_knowledge_repository.py tests/unit/test_rag_ingestion.py tests/integration/test_chat_rag_audit.py -q
```

当前结果：`7 passed, 1 warning`。

## 已知限制

- 当前检索排序为关键词评分，不是向量相似度排序。
- `LocalHashEmbeddingProvider` 仅保证 deterministic 和本地可测。
- 暂未提供后台知识库管理 API；第一版通过 CLI ingestion。
