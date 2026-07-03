# 后端 Agent 第一版验收文档

## 第一版范围

- FastAPI 后端服务。
- 聊天、PHQ-9、GAD-7、简化危机筛查、画像、报告 API。
- SQLAlchemy async 持久化、Alembic、SQLite 本地开发和 PostgreSQL 生产路径。
- Markdown 知识库工程化入库与可审计检索。
- Local/ OpenAI-compatible LLM Provider 与规则优先结构化抽取。
- Safety/Memory/Intent/Signal/Risk/Assessment/RAG/Intervention/Response/Persist 节点化编排。
- 固定评估集、metrics、安全边界测试、smoke test 和交付检查脚本。

## 不包含范围

- 临床认证。
- 医生端后台。
- 移动端 App。
- 药物处方或停药建议。
- 替代心理医生的诊断或治疗承诺。

## 启动方式

```bash
python -m pip install -e '.[dev]'
python -m uvicorn app.main:app --reload
```

## 数据库迁移

SQLite 本地开发在 app startup 自动建表。PostgreSQL 使用：

```bash
alembic upgrade head
```

## 知识库入库

```bash
python -m app.rag.cli ingest --path knowledge_base
```

## 验证命令

```bash
python scripts/check_delivery.py
python scripts/smoke_test.py --base-url http://127.0.0.1:8000
```

## Docker/PostgreSQL 验证

```bash
docker compose up api postgres redis
```

Compose 使用 `pgvector/pgvector:pg16`，API 通过 `DATABASE_URL` 连接 PostgreSQL。

## 验收标准

- 所有测试通过。
- ruff 和 mypy 通过。
- Alembic history 可读取迁移链。
- smoke test 全部 `[OK]`。
- 危机样例进入 `s3/s4` 安全流程。
- 普通评估样例不会出现诊断、停药、替代医生等禁止表达。
