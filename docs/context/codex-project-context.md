# Codex Project Context

最后更新日期：2026-06-25

本文档是当前项目的跨会话恢复文档。它的目标是防止 Codex 上下文溢出后遗忘项目背景，也方便开发者在新会话中快速接手。

## 1. 项目一句话

`campus-psy-agent` 是一个面向青少年与大学生校园场景的心理医生工作流 Agent 后端。它不是普通聊天机器人，而是围绕倾诉、筛查、风险评估、画像、干预建议、危机安全响应和后续持久化审计来构建的 FastAPI 项目。

安全边界必须长期保持：

- 只能输出疑似风险、筛查结果、证据链、干预建议和转介建议。
- 不能输出独立临床诊断。
- 不能给药物处方或停药建议。
- 不能宣称替代心理医生。
- 危机风险场景必须优先安全响应和线下求助建议。

## 2. 仓库位置与分支

工作目录：

```text
/Users/panpan/Documents/myagent
```

当前开发分支：

```text
codex/first-phase-mvp
```

原始总方案：

```text
/Users/panpan/Documents/pp/计划方案.md
```

注意：当前仓库是从空仓库搭起的项目。很多文件仍处于未跟踪状态，因为尚未创建正式提交。不要误以为未跟踪文件是不需要的，它们基本都是当前实现成果。

## 3. 当前完成状态

第一版总技术文档：

```text
docs/technical/first-version-backend-agent-technical-doc.md
```

第一阶段 MVP 已完成，计划文件已全部打勾：

```text
docs/superpowers/plans/2026-06-24-first-phase-mvp.md
```

第一阶段技术文档：

```text
docs/technical/phase-1-mvp-technical-doc.md
```

第二阶段持久化已实现，计划文件已同步勾选：

```text
docs/superpowers/plans/2026-06-24-second-phase-persistence.md
```

第二阶段技术文档：

```text
docs/technical/phase-2-persistence-technical-doc.md
```

第二阶段已把第一阶段内存版 MVP 升级为持久化后端：

- SQLAlchemy async
- Alembic
- PostgreSQL 生产兼容
- SQLite 测试兼容
- Conversation / Message / Profile / Assessment / RiskAssessment / AuditLog 数据模型
- Repository 层
- 聊天、量表、画像、报告、审计事件落库
- 知识库扩展为真实校园心理支持主题资料
- README、Docker Compose 和 Alembic 运行路径更新

第三阶段 RAG/知识库工程化已实现，计划文件已同步勾选：

```text
docs/superpowers/plans/2026-06-25-third-phase-rag-engineering.md
```

第三阶段技术文档：

```text
docs/technical/phase-3-rag-engineering-technical-doc.md
```

第三阶段新增：

- Markdown `KnowledgeChunk` schema 与二级标题切片。
- `LocalHashEmbeddingProvider`，用于测试和离线开发 deterministic embedding。
- `knowledge_chunks` SQLAlchemy model、repository 和 Alembic migration。
- `KnowledgeIngestionService` 与 CLI：`python -m app.rag.cli ingest --path knowledge_base`。
- DB-backed `KnowledgeRetriever.retrieve_async()`，无 DB chunk 时回退 Markdown。
- `rag.retrieve.completed` 审计事件，payload 记录 query hash、chunk ids 和 scores。
- 危机 `s2/s3/s4` 路径继续绕开普通 RAG。

第三阶段针对性验证：

```bash
/Users/panpan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pytest tests/unit/test_config.py::test_settings_exposes_rag_configuration tests/unit/test_chunker.py tests/unit/test_embeddings.py tests/unit/test_knowledge_repository.py tests/unit/test_rag_ingestion.py tests/integration/test_chat_rag_audit.py -q
```

结果：`7 passed, 1 warning`。

第四阶段 LLM Provider 与结构化抽取已实现，计划文件已同步勾选：

```text
docs/superpowers/plans/2026-06-25-fourth-phase-llm-provider.md
```

第四阶段技术文档：

```text
docs/technical/phase-4-llm-provider-technical-doc.md
```

第四阶段新增：

- `app/llm/` provider 层：base、local、OpenAI-compatible、factory、prompt registry。
- `LLM_PROVIDER/LLM_MODEL/LLM_BASE_URL/LLM_API_KEY/LLM_TIMEOUT_SECONDS` 配置。
- `LLMSignalExtractor` 结构化 JSON 抽取与 Pydantic 校验。
- `merge_signals_safely()`：规则信号优先，LLM 只能补充，不能删除危机标记。
- `AgentOrchestrator` 接入规则抽取 + LLM 补充 + 安全合并。
- `llm.call.started/completed/failed` 事件。

第四阶段针对性验证：

```bash
/Users/panpan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pytest tests/unit/test_config.py::test_settings_exposes_llm_configuration tests/unit/test_llm_provider.py tests/unit/test_prompt_registry.py tests/unit/test_llm_signal_extractor.py tests/integration/test_chat_llm_safety.py -q
```

结果：`7 passed, 1 warning`。

第五阶段 Agent 节点化编排与长期记忆已实现，计划文件已同步勾选：

```text
docs/superpowers/plans/2026-06-25-fifth-phase-agent-workflow-memory.md
```

第五阶段技术文档：

```text
docs/technical/phase-5-agent-workflow-memory-technical-doc.md
```

第五阶段新增：

- `AgentState` 扩展为节点共享状态，包含 node trace、建议动作、量表建议和持久化 message id。
- `PipelineRunner` 与 `PipelineNode` 协议。
- 节点：Safety、Memory、Intent、Signal、Risk、Assessment、RAG、Intervention、Response、Persist。
- `AgentOrchestrator` 切换为 pipeline 执行。
- `agent.node.started/completed/failed` 日志事件。
- crisis route 下 RagNode 不检索普通知识，PersistNode 写安全升级审计。

第五阶段针对性验证：

```bash
/Users/panpan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pytest tests/unit/test_pipeline.py tests/unit/test_agent_nodes.py tests/integration/test_agent_flow.py -q
```

结果：`10 passed, 1 warning`。

第六阶段评估集、生产化与交付已实现，计划文件已同步勾选：

```text
docs/superpowers/plans/2026-06-25-sixth-phase-evaluation-production-delivery.md
```

第六阶段技术文档：

```text
docs/technical/phase-6-evaluation-production-delivery-technical-doc.md
```

第六阶段新增：

- 固定评估集：`tests/fixtures/dialogues/*.json`，当前共 55 条合成校园场景样例。
- 指标计算：`app/observability/metrics.py`。
- 评估集集成测试与安全边界测试。
- `scripts/smoke_test.py` 覆盖 health/chat/assessment/profile/report。
- `scripts/check_delivery.py` 覆盖 pytest、ruff、mypy、alembic history。
- 交付文档：API 示例、第一版验收、安全边界。
- 2026-06-25 评估集扩展后完成最小风险规则校准：口语夸张表达不误触发危机，否定“计划/方式”不升级危机，真实计划/准备危机仍保持 `s3/s4`，并补充焦虑频率与低落持续时间升阶。
- 2026-06-25 重新接入真实 LLM API 后，补充 LLM 信号安全合并白名单：LLM 只能补充系统认识的受控标签，避免“未提及”等自由文本被当作压力源或功能受损信号。

第六阶段评估集与安全边界验证：

```bash
/Users/panpan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pytest tests/integration/test_evaluation_cases.py tests/integration/test_safety_boundary.py -q
```

本地/回退路径结果：`2 passed, 1 warning`。

真实外部 LLM API 路径结果：

```bash
/Users/panpan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pytest tests/integration/test_evaluation_cases.py tests/integration/test_safety_boundary.py -q
```

结果：`2 passed, 1 warning in 773.83s (0:12:53)`。当前配置为 OpenAI-compatible provider，经 OpenRouter base URL 调用外部模型；文档不记录 API key。

最终交付验证：

```bash
/Users/panpan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/check_delivery.py
```

结果：`51 passed, 1 warning`，ruff 通过，mypy 通过，Alembic history 显示 `2026_06_25_0002` 为 head。

注意：当前 shell 中 `python` 命令不可用，验证使用项目固定解释器：

```text
/Users/panpan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
```

本地 smoke test：

```bash
/Users/panpan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/smoke_test.py --base-url http://127.0.0.1:8001
```

结果：health、普通 chat、crisis chat、PHQ-9、GAD-7、crisis screen、profile、report 均 `[OK]`。

## 4. 当前技术栈

项目配置：

```text
pyproject.toml
```

当前依赖：

- Python `>=3.11`
- FastAPI
- Pydantic v2
- pydantic-settings
- SQLAlchemy async
- Alembic
- asyncpg
- aiosqlite
- structlog
- uvicorn
- pytest
- pytest-asyncio
- ruff
- mypy

当前使用过的 Python 解释器：

```text
/Users/panpan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
```

VSCode 可配置该解释器作为项目 Python。

## 5. 常用命令

安装依赖：

```bash
python -m pip install -e '.[dev]'
```

运行测试：

```bash
python -m pytest -q
```

Lint：

```bash
python -m ruff check .
```

类型检查：

```bash
python -m mypy app
```

启动服务：

```bash
python -m uvicorn app.main:app --reload
```

健康检查：

```bash
curl http://127.0.0.1:8000/api/health
```

聊天 API 示例：

```bash
curl -X POST http://127.0.0.1:8000/api/chat/messages \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "u-001",
    "conversation_id": "c-001",
    "message": "我最近两周考试压力很大，晚上总是睡不着，白天注意力下降。"
  }'
```

危机 API 示例：

```bash
curl -X POST http://127.0.0.1:8000/api/chat/messages \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "u-crisis",
    "conversation_id": "c-crisis",
    "message": "我不想活了，已经想好了方式，也准备好了工具。"
  }'
```

## 6. 当前目录结构导览

核心代码：

```text
app/
  main.py                     # FastAPI app 工厂与路由注册
  services.py                 # 应用级服务容器
  api/
    deps.py                   # FastAPI 依赖注入
    routes/
      health.py               # 健康检查
      chat.py                 # 聊天 API
      assessment.py           # 量表 API
      profile.py              # 用户画像 API
      report.py               # 报告 API
  core/
    config.py                 # 环境配置
    logging.py                # structlog JSON 日志配置
    middleware.py             # request_id 中间件
  db/
    base.py                   # SQLAlchemy Base 和时间 mixin
    session.py                # async engine/sessionmaker
    models.py                 # User/Conversation/Message/Profile/Assessment/Risk/Audit
    repositories/             # conversation/profile/assessment/risk/audit repositories
  schemas/
    chat.py
    assessment.py
    profile.py
    report.py
    risk.py
  agent/
    orchestrator.py           # pipeline-based Agent 主编排
    pipeline.py               # 节点协议与执行器
    state.py                  # AgentState 节点共享状态
    nodes/                    # Safety/Memory/Intent/Signal/Risk/RAG/Response/Persist
  clinical/
    llm_signal_extractor.py   # LLM 结构化抽取与安全合并
    signal_extractor.py       # 规则型信号抽取
    risk_engine.py            # 多轴风险评估
    scales/                   # PHQ-9/GAD-7/简化危机筛查
    interventions/            # CBT/行为激活/正念/睡眠/转介建议
    policies/safety_policy.py # 危机安全响应
  memory/
    profile_memory.py         # 内存版用户画像与风险时间线
  llm/
    base.py                   # provider 协议与响应模型
    local_provider.py         # 无 key 环境 deterministic provider
    openai_compatible_provider.py
    provider_factory.py
    prompt_registry.py
  rag/
    knowledge_loader.py       # Markdown 知识加载
    chunker.py                # Markdown chunk schema 与切片
    embeddings.py             # 本地 deterministic embedding provider
    ingestion.py              # 知识库入库服务
    vector_store.py           # 向量相似度基础工具
    retriever.py              # DB-backed 优先、Markdown fallback 的检索
  observability/
    audit.py                  # 内存审计事件记录器
    events.py                 # 事件常量
    metrics.py                # 评估指标计算
  scripts/
    smoke_test.py             # 已启动服务 smoke test
    check_delivery.py         # 第一版交付检查
```

知识库：

```text
knowledge_base/
  anxiety.md
  behavioral_activation.md
  campus_resources.md
  cbt_basics.md
  crisis_response.md
  depression.md
  help_seeking.md
  interpersonal_support.md
  mindfulness.md
  sleep.md
  study_stress.md
```

测试：

```text
tests/unit/
  test_alembic_metadata.py
  test_audit_persistence.py
  test_config.py
  test_models.py
  test_profile_persistence.py
  test_repositories.py
  test_scales.py
  test_signal_extractor.py
  test_risk_engine.py
  test_retriever.py

tests/integration/
  test_app_database_lifespan.py
  test_assessment_persistence.py
  test_chat_api.py
  test_chat_persistence.py
  test_profile_report_api.py
```

文档：

```text
docs/superpowers/plans/
  2026-06-24-first-phase-mvp.md
  2026-06-24-second-phase-persistence.md

docs/technical/
  README.md
  phase-1-mvp-technical-doc.md
  phase-2-persistence-technical-doc.md

docs/context/
  README.md
  codex-project-context.md
```

## 7. 第一阶段实现详情

第一阶段是可运行的内存版闭环。核心请求链路在：

```text
app/agent/orchestrator.py
```

`AgentOrchestrator.handle_chat()` 当前流程：

```text
ChatRequest
  -> 生成 agent_run_id
  -> ensure_user / ensure_conversation
  -> 保存 user message
  -> SignalExtractor.extract()
  -> RiskEngine.assess()
  -> select_interventions()
  -> KnowledgeRetriever.retrieve()  # 危机 S2-S4 不走普通知识库
  -> 生成普通回复或危机回复
  -> 保存 risk_assessment
  -> 保存 assistant message
  -> 更新 user_profile
  -> 保存 audit_logs
  -> 返回 ChatResponse
```

危机分支：

- `crisis_level in {"s2", "s3", "s4"}` 时触发。
- 不走普通 RAG。
- 使用 `app/clinical/policies/safety_policy.py` 的 `crisis_response()`。
- 记录 `safety.escalation.triggered`。

## 8. API 当前契约

已实现接口：

- `GET /api/health`
- `POST /api/chat/messages`
- `POST /api/assessments/phq9`
- `POST /api/assessments/gad7`
- `POST /api/assessments/crisis`
- `GET /api/profile/{user_id}`
- `GET /api/profile/{user_id}/timeline`
- `GET /api/report/{user_id}/latest`
- `POST /api/report/{user_id}/generate`

重要响应模型：

- `app/schemas/chat.py`
- `app/schemas/assessment.py`
- `app/schemas/profile.py`
- `app/schemas/report.py`
- `app/schemas/risk.py`

`RiskSummary` 字段：

```text
depression_risk
anxiety_risk
sleep_risk
crisis_level
function_impairment_level
```

## 9. 临床规则当前实现

信号抽取：

```text
app/clinical/signal_extractor.py
```

当前用关键词规则抽取：

- 情绪：焦虑、低落、愤怒、孤独
- 症状：失眠、注意力下降、疲惫、自责、兴趣下降
- 压力源：考试压力、学业压力、人际关系、家庭压力
- 功能受损：学习、社交、睡眠
- 危机标记：主动自杀想法、被动死亡想法、方式、计划、准备工具
- 保护因素：朋友支持、家庭牵挂、求助意愿

风险评估：

```text
app/clinical/risk_engine.py
```

当前规则：

- 焦虑：有焦虑情绪或压力源为 `mild`；伴随持续时间或功能受损升级 `moderate`。
- 抑郁：有低落、自责、兴趣下降为 `mild`；持续两周或多个症状升级 `moderate`。
- 睡眠：有失眠为 `mild`；持续或影响睡眠功能升级 `moderate`。
- 危机：根据 `主动自杀想法 / 被动死亡想法 / 方式 / 计划 / 准备工具` 推导 `s0-s4`。

量表：

- `app/clinical/scales/phq9.py`
- `app/clinical/scales/gad7.py`
- `app/clinical/scales/cssrs_like.py`

PHQ-9 第 9 题阳性必须触发危机复核建议。

## 10. RAG-lite 当前实现

知识加载：

```text
app/rag/knowledge_loader.py
```

检索：

```text
app/rag/retriever.py
```

当前检索是关键词评分：

- query 中存在候选 token 才参与评分。
- 标题命中加 2 分。
- 正文命中加 1 分。
- 返回 top_k。

候选 token：

```text
考试、压力、焦虑、抑郁、低落、睡眠、睡不着、失眠、危机、自杀、CBT、正念、校园
```

已修过一个重要回归：焦虑/失眠 query 应优先命中 `anxiety` 或 `sleep`，不能误把 `depression` 放到第一。

对应测试：

```text
tests/unit/test_retriever.py
```

## 11. 当前测试状态

最后已知验证：

```text
pytest -q: 23 passed
ruff check .: passed
mypy app: passed
alembic history: <base> -> 2026_06_24_0001 (head), initial persistence
```

注意：运行测试后会生成 `__pycache__`、`.pytest_cache` 等缓存。项目已有 `.gitignore` 忽略这些文件。

如果新会话看到缓存目录，不要手动提交它们。

## 12. 当前 Git/文件状态注意事项

当前项目很多文件是未跟踪状态。不要删除这些未跟踪文件。它们包含第一、二阶段实现、文档和计划。

已知未跟踪项可能包括：

```text
.env.example
.gitignore
.vscode/
README.md
app/
alembic/
alembic.ini
docker-compose.yml
docs/
knowledge_base/
pyproject.toml
tests/
README.md
```

`.vscode/` 是用户本地 VSCode 配置，Codex 不应擅自改动，除非用户明确要求。

## 13. 第一版交付还需要几阶段

以“后端 Agent 项目第一版可交付”为目标，当前 Phase 1-6 均已完成：

- Phase 1: MVP API + 规则型临床核心 + 内存画像 + RAG-lite。
- Phase 2: SQLAlchemy/Alembic 持久化 + 审计落库 + 真实主题知识库。
- Phase 3: RAG/知识库工程化。
- Phase 4: LLM Provider 与结构化抽取。
- Phase 5: Agent 节点化编排与长期记忆。
- Phase 6: 评估集、生产化与第一版交付。

计划文档执行顺序与状态：

| 顺序 | 阶段 | 计划文档 | 状态 |
|---|---|---|---|
| 1 | Phase 3: RAG/知识库工程化 | `docs/superpowers/plans/2026-06-25-third-phase-rag-engineering.md` | 已完成 |
| 2 | Phase 4: LLM Provider 与结构化抽取 | `docs/superpowers/plans/2026-06-25-fourth-phase-llm-provider.md` | 已完成 |
| 3 | Phase 5: Agent 节点化编排与长期记忆 | `docs/superpowers/plans/2026-06-25-fifth-phase-agent-workflow-memory.md` | 已完成 |
| 4 | Phase 6: 评估集、生产化与第一版交付 | `docs/superpowers/plans/2026-06-25-sixth-phase-evaluation-production-delivery.md` | 已完成 |

### Phase 3: RAG/知识库工程化

目标：把现在的 Markdown 资料升级为可检索、可审计、可更新的知识库。

范围：

- Markdown chunker。
- Embedding Provider 抽象。
- pgvector 表和 Alembic 迁移。
- 知识库入库/更新脚本。
- 检索返回 `chunk_id`、`source`、`score`、`title`。
- 危机路径继续绕开普通 RAG，使用安全策略库。

交付标准：

- 知识库不是 demo 内容。
- API 回复能基于检索结果选择干预，但不暴露过多专业术语。
- RAG 检索事件记录 query hash、top_k、chunk_ids、score。

### Phase 4: LLM Provider 与结构化抽取

目标：接入真实 LLM，但保留规则型安全兜底。

范围：

- `LLMProvider` 抽象。
- OpenAI/Qwen/DeepSeek/Local provider。
- prompt registry。
- LLM 结构化信号抽取，Pydantic 校验。
- LLM 调用日志：provider、model、latency、token_usage、status、error_type。
- 安全策略：危机关键词规则优先于 LLM 输出。

交付标准：

- 没有 API key 时可用 local/mock provider 跑测试。
- 有 API key 时可切真实模型。
- LLM 不能绕过危机安全流程。

### Phase 5: Agent 编排与长期记忆

目标：把当前单文件 orchestrator 升级为节点化工作流。

范围：

- SafetyNode。
- MemoryNode。
- IntentNode。
- AssessmentNode。
- RagNode。
- InterventionNode。
- ResponseNode。
- PersistNode。
- 可选 LangGraph；若引入成本太高，可先用内部 pipeline 抽象。
- 最近 N 轮对话读取。
- 量表触发建议和随访建议。

交付标准：

- 普通倾诉、焦虑筛查、抑郁筛查、危机表达都有集成测试。
- 每个节点有结构化开始/完成/失败日志。
- S2-S4 路径直接进入安全响应。

### Phase 6: 评估集、生产化与交付文档

目标：让第一版具备可验证、可部署、可演示、可维护的交付形态。

范围：

- 20 条以上校园场景评估集。
- 覆盖普通压力、焦虑、抑郁、失眠、人际、霸凌、自伤表达。
- 指标：风险召回、危机召回、误触发率、回复安全性。
- Docker Compose 验证 PostgreSQL + API。
- README 完整运行路径。
- `.env.example` 完整变量。
- OpenAPI 示例和 smoke test 脚本。
- 第一版交付技术文档。

交付标准：

- `pytest`、`ruff`、`mypy`、关键 smoke test 通过。
- 危机样例 100% 进入安全流程。
- 非诊断、安全边界测试通过。

如果你希望“第一版交付”包含可点击前端或管理后台，还需要额外 Phase 7：

- 学生端简单聊天 UI。
- 报告查看页。
- 管理/演示后台。
- 部署说明和截图级验收。

## 14. 下一阶段执行方式

Phase 1-6 已完成。下一轮建议围绕评估集暴露的问题做针对性优化，例如增加否定语境、口语表达、复合风险、危机分级和 RAG 建议相关性的固定样例，再按失败分类最小修改对应模块。

执行时要遵守 TDD：

- 先写失败测试。
- 确认失败原因正确。
- 再写实现。
- 再跑通过。
- 最后更新技术文档。

## 15. 后续阶段路线

当前后续建议路线：

1. 扩展评估集：从 55 条继续覆盖更多否定语境、口语误触发、复合风险与转介表达，状态：可继续。
2. LLM 抽取优化：让真实 provider 遵守否定语境和危机保守策略，状态：可继续。
3. RAG 建议相关性：为人际、霸凌、家庭压力等场景增加更细知识块和检索评测，状态：可继续。
4. 可选 Phase 7 前端/后台：学生端聊天 UI、报告查看页、管理/演示后台，状态：未规划。

## 16. 新会话恢复 Checklist

新会话开始时，建议按顺序执行：

1. 阅读本文件。
2. 阅读 `docs/technical/phase-1-mvp-technical-doc.md`。
3. 阅读 `docs/technical/phase-2-persistence-technical-doc.md`。
4. 阅读下一阶段计划：`docs/superpowers/plans/2026-06-25-third-phase-rag-engineering.md`。
5. 运行：

```bash
git branch --show-current
git status --short
python -m pytest -q
python -m ruff check .
python -m mypy app
```

6. 如果要继续开发，优先执行 Phase 3 RAG/知识库工程化计划。

## 17. 不要忘记的项目原则

- 所有 API 请求必须有 `request_id`。
- 所有 Agent 执行必须有 `agent_run_id`。
- 普通日志不要记录完整用户原文。
- 风险判断要保留证据链。
- S2-S4 危机事件必须审计。
- PHQ-9 第 9 题阳性必须触发危机复核。
- 系统不能输出独立确诊语句。
- 系统不能输出药物处方建议。
- 危机场景优先安全响应，不能被 RAG 或普通建议覆盖。
- 每轮实现完成后必须生成或更新 `docs/technical/phase-N-...-technical-doc.md`。
- 每轮实现完成后建议更新本上下文文档。
