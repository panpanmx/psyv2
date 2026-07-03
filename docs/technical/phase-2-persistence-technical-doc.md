# 第二阶段持久化技术文档

生成日期：2026-06-25

本文档记录第二阶段实现：将第一阶段内存版校园心理工作流 Agent 升级为持久化后端，并将知识库扩展为更接近实际使用的校园心理支持资料。

## 1. 本阶段目标

第二阶段目标是让项目从“可演示 MVP”推进到“可实际运行和保存关键业务数据”的后端基础：

- 保存用户、会话、消息、画像、量表结果、风险评估和审计事件。
- 保持第一阶段 API 响应兼容。
- 本地无需外部服务即可用 SQLite 运行。
- Docker/PostgreSQL 环境通过 Alembic 管理迁移。
- 危机风险和 PHQ-9 第 9 题阳性具备持久化审计路径。
- 知识库不再是短 demo 文本，而是覆盖焦虑、抑郁、危机、睡眠、行为激活、人际、求助等实际校园场景。

## 2. 新增依赖

配置文件：[pyproject.toml](/Users/panpan/Documents/myagent/pyproject.toml)

新增运行依赖：

- `sqlalchemy`
- `alembic`
- `asyncpg`
- `aiosqlite`
- `greenlet`

新增开发依赖：

- `pytest-asyncio`

`greenlet` 是 SQLAlchemy async 执行路径需要的运行依赖。

## 3. 配置

配置文件：[app/core/config.py](/Users/panpan/Documents/myagent/app/core/config.py)

新增字段：

- `database_url`
- `test_database_url`

默认数据库：

```text
sqlite+aiosqlite:///./campus_psy_agent.db
```

`.env.example` 中 PostgreSQL 示例：

```text
DATABASE_URL=postgresql+asyncpg://campus:campus@localhost:5432/campus_psy_agent
TEST_DATABASE_URL=sqlite+aiosqlite:///:memory:
```

## 4. 数据库架构

数据库包：

```text
app/db/
  base.py
  session.py
  models.py
  repositories/
```

### 4.1 Base 与时间字段

文件：[app/db/base.py](/Users/panpan/Documents/myagent/app/db/base.py)

- `Base`: SQLAlchemy declarative base。
- `CreatedAtMixin`: 提供 `created_at`。
- `TimestampMixin`: 提供 `created_at` 和 `updated_at`。
- `utc_now()`: 统一生成 timezone-aware UTC 时间。

### 4.2 Session

文件：[app/db/session.py](/Users/panpan/Documents/myagent/app/db/session.py)

提供：

- `create_engine(settings)`
- `create_sessionmaker(engine)`
- `session_scope(session_maker)`

`create_app()` 会创建 async engine 和 sessionmaker，并挂到 `AppServices`。

## 5. 数据模型

文件：[app/db/models.py](/Users/panpan/Documents/myagent/app/db/models.py)

当前使用 string ID，保持与第一阶段 API 的 `user_id`、`conversation_id` 字符串兼容。

### users

字段：

- `id`
- `nickname`
- `age_group`
- `school_stage`
- `created_at`
- `updated_at`

### conversations

字段：

- `id`
- `user_id`
- `title`
- `created_at`
- `updated_at`

### messages

字段：

- `id`
- `conversation_id`
- `role`
- `content`
- `content_hash`
- `risk_snapshot`
- `created_at`

`content_hash` 使用 SHA-256，便于日志和审计中引用摘要，减少直接依赖原文。

### user_profiles

字段：

- `id`
- `user_id`
- `profile_json`
- `latest_summary`
- `risk_trend_json`
- `updated_by_message_id`
- `created_at`
- `updated_at`

`profile_json` 延续第一阶段结构：

```json
{
  "dominant_emotions": [],
  "stressors": [],
  "symptoms": [],
  "function_impairment": [],
  "protective_factors": [],
  "risk_factors": []
}
```

### assessments

字段：

- `id`
- `user_id`
- `conversation_id`
- `scale_type`
- `answers`
- `score`
- `severity`
- `interpretation`
- `created_at`

### risk_assessments

字段：

- `id`
- `user_id`
- `conversation_id`
- `message_id`
- `depression_risk`
- `anxiety_risk`
- `sleep_risk`
- `crisis_level`
- `function_impairment_level`
- `evidence`
- `recommended_next_step`
- `created_at`

### audit_logs

字段：

- `id`
- `request_id`
- `user_id`
- `conversation_id`
- `event_type`
- `event_payload`
- `created_at`

## 6. Alembic

文件：

- [alembic.ini](/Users/panpan/Documents/myagent/alembic.ini)
- [alembic/env.py](/Users/panpan/Documents/myagent/alembic/env.py)
- [alembic/versions/2026_06_24_0001_initial_persistence.py](/Users/panpan/Documents/myagent/alembic/versions/2026_06_24_0001_initial_persistence.py)

验证命令：

```bash
python -m alembic history
```

应看到：

```text
<base> -> 2026_06_24_0001 (head), initial persistence
```

生产或 PostgreSQL 环境迁移：

```bash
alembic upgrade head
```

SQLite 本地开发环境目前在 FastAPI lifespan 中自动 `create_all`，便于开箱即跑。

## 7. Repository 层

### ConversationRepository

文件：[app/db/repositories/conversation_repo.py](/Users/panpan/Documents/myagent/app/db/repositories/conversation_repo.py)

职责：

- `ensure_user()`
- `ensure_conversation()`
- `save_message()`
- `recent_messages()`

消息保存时会写入：

- `role`
- `content`
- `content_hash`
- `risk_snapshot`

### ProfileRepository

文件：[app/db/repositories/profile_repo.py](/Users/panpan/Documents/myagent/app/db/repositories/profile_repo.py)

职责：

- `update_profile()`
- `get_profile()`
- `get_summary()`
- `get_latest_risk()`
- `get_timeline()`

它复用第一阶段画像合并语义：每类信号去重追加，不覆盖既有画像。

### AssessmentRepository

文件：[app/db/repositories/assessment_repo.py](/Users/panpan/Documents/myagent/app/db/repositories/assessment_repo.py)

职责：

- `save_assessment()`
- `list_for_user()`
- `latest_for_user()`

### RiskRepository

文件：[app/db/repositories/risk_repo.py](/Users/panpan/Documents/myagent/app/db/repositories/risk_repo.py)

职责：

- `save_risk()`
- `latest_for_user()`
- `timeline_for_user()`

### AuditRepository

文件：[app/db/repositories/audit_repo.py](/Users/panpan/Documents/myagent/app/db/repositories/audit_repo.py)

职责：

- `record_event()`

用于持久化 `risk.assessment.completed`、`safety.escalation.triggered` 等事件。

## 8. FastAPI 生命周期

文件：[app/main.py](/Users/panpan/Documents/myagent/app/main.py)

`create_app(settings: Settings | None = None)` 支持测试注入数据库 URL。

启动时：

1. 读取 settings。
2. 创建 async engine。
3. 创建 sessionmaker。
4. 创建 `AppServices(settings, sessionmaker)`。
5. SQLite 环境自动建表。
6. 应用关闭时 dispose engine。

## 9. 聊天持久化流程

文件：[app/agent/orchestrator.py](/Users/panpan/Documents/myagent/app/agent/orchestrator.py)

`handle_chat()` 已改为 async。

持久化路径：

```text
POST /api/chat/messages
  -> ensure_user
  -> ensure_conversation
  -> save user message
  -> extract signals
  -> assess risk
  -> save risk_assessment
  -> generate assistant message
  -> save assistant message
  -> update user_profile
  -> save risk.assessment.completed audit
  -> if S2-S4: save safety.escalation.triggered audit
  -> commit
```

同时仍保留第一阶段 `ProfileMemory` 和 `AuditLogger` 的内存记录，作为快速测试和兼容层。对外 API 已优先读取持久化数据。

## 10. 量表持久化流程

文件：[app/api/routes/assessment.py](/Users/panpan/Documents/myagent/app/api/routes/assessment.py)

### PHQ-9

- 保存 assessment。
- 若第 9 题阳性，写入 `risk_assessments`：
  - `crisis_level = s2`
  - evidence 来源为 `phq9`
  - next step route 为 `crisis_review`

### GAD-7

- 保存 assessment。
- 若中度或重度，写入 anxiety risk。

### 简化危机筛查

- 保存 assessment。
- 保存 crisis risk。
- S2-S4 写入 `safety.escalation.triggered` 审计事件。

## 11. Profile 与 Report 持久化读取

文件：

- [app/api/routes/profile.py](/Users/panpan/Documents/myagent/app/api/routes/profile.py)
- [app/api/routes/report.py](/Users/panpan/Documents/myagent/app/api/routes/report.py)

画像接口现在从 `ProfileRepository` 读取。

报告接口现在读取：

- `ProfileRepository.get_profile()`
- `ProfileRepository.get_summary()`
- `RiskRepository.latest_for_user()`

如果没有风险记录，回退到 `RiskResult()` 的 unknown/s0 默认值。

## 12. 知识库升级

知识库目录：[knowledge_base](/Users/panpan/Documents/myagent/knowledge_base)

当前主题：

- `anxiety.md`
- `depression.md`
- `cbt_basics.md`
- `mindfulness.md`
- `sleep.md`
- `campus_resources.md`
- `behavioral_activation.md`
- `crisis_response.md`
- `study_stress.md`
- `interpersonal_support.md`
- `help_seeking.md`

这些文档覆盖真实校园心理支持场景，不再是短演示文本。文档包含安全边界、可抽取信号、干预建议、转介建议和参考资料。

参考过的官方资料：

- NIMH Suicide Prevention: https://www.nimh.nih.gov/health/topics/suicide-prevention
- NHS CBT: https://www.nhs.uk/tests-and-treatments/cognitive-behavioural-therapy-cbt/
- CDC Managing Stress: https://www.cdc.gov/mental-health/living-with/index.html
- WHO Adolescent mental health: https://www.who.int/news-room/fact-sheets/detail/adolescent-mental-health

注意：本阶段仍是 RAG-lite 关键词检索，不是 pgvector。向量库、embedding、chunk 引用和可审计 source span 应作为下一阶段实现。

## 13. 测试覆盖

新增测试：

- `tests/unit/test_config.py`
- `tests/unit/test_models.py`
- `tests/unit/test_alembic_metadata.py`
- `tests/unit/test_repositories.py`
- `tests/unit/test_profile_persistence.py`
- `tests/unit/test_audit_persistence.py`
- `tests/integration/test_app_database_lifespan.py`
- `tests/integration/test_chat_persistence.py`
- `tests/integration/test_assessment_persistence.py`

更新测试：

- `tests/integration/test_profile_report_api.py`
- `tests/unit/test_retriever.py`

关键验证点：

- 数据库配置存在。
- 七张核心表可建表和写入。
- Alembic 能识别初始迁移。
- 聊天后持久化 2 条 message、1 条 risk、1 条 profile、多条 audit。
- PHQ-9 第 9 题阳性持久化 crisis review risk。
- 清空内存画像后，profile/report API 仍能从数据库读到数据。
- 知识库至少 10 篇，并覆盖真实校园支持主题。

## 14. 运行与验证

聚焦测试：

```bash
python -m pytest \
  tests/unit/test_config.py \
  tests/unit/test_models.py \
  tests/unit/test_alembic_metadata.py \
  tests/unit/test_repositories.py \
  tests/unit/test_profile_persistence.py \
  tests/unit/test_audit_persistence.py \
  tests/integration/test_app_database_lifespan.py \
  tests/integration/test_chat_persistence.py \
  tests/integration/test_assessment_persistence.py \
  tests/integration/test_profile_report_api.py \
  tests/unit/test_retriever.py \
  -q
```

完整验证：

```bash
python -m pytest -q
python -m ruff check .
python -m mypy app
```

## 15. 已知限制

- SQLite 本地自动建表仅用于开发便利；生产应使用 Alembic。
- 当前 ID 仍使用字符串，以兼容第一阶段 API；后续可迁移到 UUID 类型。
- 量表 API 已落库，但还没有完整的量表历史报告页面。
- RAG-lite 仍是关键词评分，不是向量检索。
- LLM Provider、LangGraph、Redis workers 尚未实现。

## 16. 下一阶段建议

建议第三阶段做 RAG/知识库工程化：

1. Markdown chunker。
2. Embedding Provider。
3. pgvector 表和迁移。
4. 知识 chunk 入库脚本。
5. 检索返回 chunk_id、source、score。
6. 回复保留后台引用证据，不向用户暴露过多专业术语。
7. 危机路径继续绕开普通 RAG，使用安全策略库。

