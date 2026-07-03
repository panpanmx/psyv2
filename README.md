# Campus Psy Agent

面向青少年与大学生校园场景的心理医生工作流 Agent 后端。系统提供日常倾诉 API、PHQ-9/GAD-7/简化危机筛查、规则优先的 LLM 结构化抽取、风险评估、用户画像更新、可审计知识库检索、干预建议、简单报告和持久化基础设施。

> 重要边界：本项目只输出疑似风险、筛查结果和求助建议，不提供独立临床诊断、药物建议，也不能替代心理医生。

## 快速开始

```bash
python3.12 -m pip install -e '.[dev]'
python -m uvicorn app.main:app --reload
```

默认 `DATABASE_URL` 是本地 SQLite：

```text
sqlite+aiosqlite:///./campus_psy_agent.db
```

这使项目无需外部服务即可启动。生产或 Docker Compose 环境使用 PostgreSQL。

健康检查：

```bash
curl http://127.0.0.1:8000/api/health
```

聊天示例：

```bash
curl -X POST http://127.0.0.1:8000/api/chat/messages \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "u-001",
    "conversation_id": "c-001",
    "message": "我最近两周考试压力很大，晚上总是睡不着，白天注意力下降。"
  }'
```

危机样例：

```bash
curl -X POST http://127.0.0.1:8000/api/chat/messages \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "u-crisis",
    "conversation_id": "c-crisis",
    "message": "我不想活了，已经想好了方式，也准备好了工具。"
  }'
```

## API

- `GET /api/health`
- `POST /api/chat/messages`
- `POST /api/assessments/phq9`
- `POST /api/assessments/gad7`
- `POST /api/assessments/crisis`
- `GET /api/profile/{user_id}`
- `GET /api/profile/{user_id}/timeline`
- `GET /api/report/{user_id}/latest`
- `POST /api/report/{user_id}/generate`

## Persistence

第二阶段引入 SQLAlchemy async 和 Alembic。核心表包括：

- `users`
- `conversations`
- `messages`
- `user_profiles`
- `assessments`
- `risk_assessments`
- `audit_logs`
- `knowledge_chunks`

本地开发默认 SQLite 会在应用启动时自动建表。PostgreSQL 环境应通过 Alembic 管理迁移：

```bash
alembic upgrade head
```

知识库入库：

```bash
python -m app.rag.cli ingest --path knowledge_base
```

交付检查：

```bash
python scripts/check_delivery.py
python scripts/smoke_test.py --base-url http://127.0.0.1:8000
```

Docker Compose 使用 PostgreSQL：

```bash
docker compose up api postgres redis
```

测试使用 `tests/conftest.py` 中的内存 SQLite 数据库。

## 测试与质量检查

```bash
pytest -q
ruff check .
mypy app
```

## 当前实现范围

已完成：

- FastAPI 应用、request_id 中间件、JSON 结构化日志。
- SQLAlchemy async 数据模型、repository 和 Alembic 初始迁移。
- 规则型信号抽取：情绪、症状、持续时间、压力源、功能受损、危机标记和保护因素。
- PHQ-9、GAD-7、简化危机筛查评分。
- 多轴风险评估：抑郁、焦虑、睡眠、危机、功能受损。
- 危机场景优先安全响应。
- Markdown 知识库 chunk、embedding 入库、DB-backed 检索和 `rag.retrieve.completed` 审计。
- 可插拔 LLM Provider、OpenAI-compatible 接口、local fallback、prompt registry 和安全合并式结构化抽取。
- Agent pipeline 节点化编排：Safety、Memory、Intent、Signal、Risk、Assessment、RAG、Intervention、Response、Persist。
- 固定评估集、metrics、安全边界测试、smoke test、交付检查脚本和第一版验收文档。
- 聊天、量表、画像、报告的持久化基础。
- 聊天、量表、画像、报告 API。

后续阶段建议：

- 扩大评估集规模、接入后台任务和生产监控。
