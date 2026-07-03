# 后端 Agent 第一版总技术文档

最后更新日期：2026-06-25

## 1. 项目定位

`Campus Psy Agent` 是一个面向青少年与大学生校园场景的心理支持工作流 Agent 后端。它不是普通聊天机器人，也不承担独立临床诊断职责，而是围绕以下工作流提供工程化支持：

- 日常倾诉与共情回应。
- 情绪、症状、压力源、持续时间、功能受损和保护因素抽取。
- PHQ-9、GAD-7、简化危机筛查。
- 焦虑、抑郁、睡眠、危机和功能受损风险评估。
- 校园心理支持知识库检索。
- 循证干预建议。
- 危机安全响应。
- 用户画像、风险趋势、审计和报告持久化。

系统长期安全边界：

- 只输出疑似风险、筛查建议、证据链、干预建议和转介建议。
- 不输出独立临床诊断。
- 不提供药物处方或停药建议。
- 不宣称替代心理医生。
- 危机风险场景优先安全确认、线下求助和紧急资源。

## 2. 当前交付范围

第一版已完成：

- FastAPI 后端服务。
- SQLite 本地开发路径与 PostgreSQL/Docker Compose 生产路径。
- SQLAlchemy async 数据模型和 repository。
- Alembic 迁移。
- Markdown 知识库、chunk、embedding、本地 ingestion、DB-backed retriever。
- Local/ OpenAI-compatible LLM Provider。
- 规则优先、LLM 补充的结构化抽取。
- Agent pipeline 节点化编排。
- PHQ-9、GAD-7、简化危机筛查。
- 用户画像、风险记录、审计日志、报告 API。
- 固定评估集、安全边界测试、smoke test、交付检查脚本。

第一版不包含：

- 前端 UI。
- 临床认证。
- 医生端管理后台。
- 移动端 App。
- 真实短信/邮件/通知 API。
- 真实外部学校心理中心系统集成。
- 生产级鉴权、限流和监控告警。

## 3. 技术栈

- Python 3.11+
- FastAPI
- Pydantic v2
- pydantic-settings
- SQLAlchemy async
- Alembic
- PostgreSQL + pgvector
- SQLite 测试与本地开发 fallback
- httpx
- structlog
- pytest / pytest-asyncio
- ruff
- mypy
- Docker Compose

## 4. 总体架构

```text
Client / Swagger / Smoke Script
        |
        v
FastAPI Routes
        |
        v
AppServices
        |
        v
AgentOrchestrator
        |
        v
PipelineRunner
        |
        +--> SafetyNode
        +--> MemoryNode
        +--> IntentNode
        +--> SignalExtractionNode
        +--> RiskNode
        +--> AssessmentNode
        +--> RagNode
        +--> InterventionNode
        +--> ResponseNode
        +--> PersistNode
        |
        v
ChatResponse
```

外围模块：

```text
clinical/       规则抽取、风险引擎、量表、干预、安全策略
llm/            Provider 抽象、local fallback、OpenAI-compatible provider、prompt registry
rag/            知识加载、chunk、embedding、ingestion、retriever
db/             SQLAlchemy models、session、repositories
observability/  事件常量、审计、metrics
tests/          单元测试、集成测试、评估集、安全边界
docs/           技术文档、交付文档、上下文文档
scripts/        smoke test、delivery check
```

## 5. 一次聊天请求的完整流程

入口：

```text
POST /api/chat/messages
```

请求字段：

- `user_id`
- `conversation_id`
- `message`

执行链路：

1. `RequestIdMiddleware` 注入 request id。
2. `AppServices` 提供 orchestrator、sessionmaker、retriever、LLM provider、audit logger。
3. `AgentOrchestrator.handle_chat()` 创建 `AgentState`。
4. `PipelineRunner` 顺序执行节点。
5. `SafetyNode` 对明显危机表达做快速路由。
6. `MemoryNode` 读取最近对话和用户画像。
7. `IntentNode` 判断当前意图。
8. `SignalExtractionNode` 运行规则抽取和 LLM 补充抽取。
9. `RiskNode` 生成多轴风险结果。
10. `AssessmentNode` 生成 GAD-7、PHQ-9 或 crisis screen 建议。
11. `RagNode` 普通路径检索知识库；危机路径跳过普通 RAG。
12. `InterventionNode` 选择干预建议。
13. `ResponseNode` 生成普通支持回复或危机安全回复。
14. `PersistNode` 保存消息、风险、画像和审计。
15. 返回 `ChatResponse`。

响应字段：

- `message_id`
- `assistant_message`
- `risk_summary`
- `suggested_actions`
- `follow_up_questions`

## 6. AgentState 设计

`AgentState` 是节点之间唯一共享状态，核心字段包括：

- `request_id`
- `agent_run_id`
- `user_id`
- `conversation_id`
- `user_message`
- `intent`
- `recent_messages`
- `profile`
- `extracted_signals`
- `risk_result`
- `retrieved_knowledge`
- `intervention_plan`
- `response_text`
- `route`
- `node_trace`
- `suggested_actions`
- `follow_up_questions`
- `user_message_id`
- `assistant_message_id`
- `assessment_suggestions`

设计原则：

- 每个节点只读写 `AgentState`。
- 节点内部依赖通过构造函数注入。
- `extracted_signals` 使用 `ExtractedSignals`。
- `risk_result` 使用 `RiskResult`。
- `node_trace` 用于审计和调试。

## 7. 节点设计

### 7.1 SafetyNode

职责：

- 快速识别明显危机表达。
- 将 `route` 设置为 `crisis`。

当前规则覆盖：

- 不想活
- 想死
- 结束这一切
- 自杀

### 7.2 MemoryNode

职责：

- 读取最近 N 轮对话。
- 读取用户画像。
- 写入 `state.recent_messages` 和 `state.profile`。

当前记忆策略偏轻量，尚未做长期摘要压缩。

### 7.3 IntentNode

职责：

- 判断当前意图。

当前意图：

- `support`
- `assessment`
- `crisis`

用户明确提到 GAD-7、PHQ-9、量表或筛查时，进入 assessment intent。

### 7.4 SignalExtractionNode

职责：

- 规则型信号抽取。
- LLM 结构化抽取。
- 安全合并。

规则抽取覆盖：

- 情绪
- 症状
- 持续时间
- 频率
- 压力源
- 功能受损
- 危机标记
- 保护因素

LLM 输出经过 `ExtractedSignals.model_validate()` 校验，失败时返回空信号。

### 7.5 RiskNode

职责：

- 将 `ExtractedSignals` 转换为 `RiskResult`。

风险维度：

- `depression_risk`
- `anxiety_risk`
- `sleep_risk`
- `crisis_level`
- `function_impairment_level`

危机等级：

- `s0`：未识别危机
- `s1`：被动死亡想法
- `s2`：主动自杀想法
- `s3`：主动想法 + 方式或计划
- `s4`：主动想法 + 计划 + 准备工具

### 7.6 AssessmentNode

职责：

- 根据风险结果生成筛查建议。

当前规则：

- 中度及以上焦虑风险建议 GAD-7。
- 中度及以上抑郁风险建议 PHQ-9。
- 危机相关等级建议 crisis screen。

### 7.7 RagNode

职责：

- 普通路径检索知识库。
- 危机路径跳过普通 RAG。
- 记录 `rag.retrieve.completed` 审计事件。

返回字段：

- `id`
- `chunk_id`
- `title`
- `source_path`
- `section`
- `content`
- `score`

### 7.8 InterventionNode

职责：

- 根据风险结果选择干预动作。
- 合并量表建议。

干预来源：

- CBT
- 行为激活
- 正念
- 睡眠卫生
- 转介建议

### 7.9 ResponseNode

职责：

- 生成用户可读回复。
- 保持非诊断表达。
- 危机场景调用安全响应模板。

普通回复包含：

- 共情
- 观察到的风险信号
- “不是诊断”说明
- 一个小行动建议
- 线下专业资源建议

危机回复优先：

- 当前安全
- 可信任的人
- 学校心理中心
- 紧急服务

### 7.10 PersistNode

职责：

- 持久化 user message。
- 持久化 risk assessment。
- 持久化 assistant message。
- 更新 profile。
- 写入审计事件。

写库顺序：

1. ensure user/conversation
2. save user message
3. save risk assessment
4. save assistant message
5. update profile
6. audit risk assessment
7. crisis 时 audit safety escalation

## 8. LLM Provider 设计

目录：

```text
app/llm/
```

模块：

- `base.py`
- `local_provider.py`
- `openai_compatible_provider.py`
- `provider_factory.py`
- `prompt_registry.py`

配置：

```env
LLM_PROVIDER=local
LLM_MODEL=local-rule-model
LLM_BASE_URL=
LLM_API_KEY=
LLM_TIMEOUT_SECONDS=30
```

Provider 规则：

- `LLM_PROVIDER=local` 使用本地规则 provider。
- `openai/qwen/deepseek` 且存在 `LLM_API_KEY` 时，使用 OpenAI-compatible provider。
- 没有 key 时自动回退 local provider。

当前真实大模型接入状态：

- 代码已支持 OpenAI-compatible 接入。
- 默认未调用真实模型。
- 需要配置 `LLM_PROVIDER/LLM_MODEL/LLM_BASE_URL/LLM_API_KEY` 后才会调用外部服务。

## 9. LLM 与规则安全合并

信号抽取流程：

```text
rule_signals = SignalExtractor.extract(message)
llm_signals = LLMSignalExtractor.extract(message)
signals = merge_signals_safely(rule_signals, llm_signals)
```

合并规则：

- list 字段去重合并。
- `duration/frequency` 优先规则结果。
- `risk_markers` 绝不删除规则结果。
- LLM 不能降低危机等级。
- LLM 输出校验失败时返回空信号。

## 10. RAG 与知识库设计

知识源：

```text
knowledge_base/*.md
```

核心模块：

- `knowledge_loader.py`
- `chunker.py`
- `embeddings.py`
- `ingestion.py`
- `retriever.py`
- `vector_store.py`

chunk schema：

- `chunk_id`
- `doc_id`
- `title`
- `source_path`
- `section`
- `content`
- `ordinal`

数据库表：

```text
knowledge_chunks
```

字段包括：

- `chunk_id`
- `doc_id`
- `title`
- `source_path`
- `section`
- `content`
- `ordinal`
- `embedding`
- `content_hash`
- `created_at`
- `updated_at`

入库命令：

```bash
python -m app.rag.cli ingest --path knowledge_base
```

当前检索策略：

- 优先 DB-backed chunk 检索。
- DB 无 chunk 时回退 Markdown loader。
- 当前评分为关键词评分。
- pgvector 已预留迁移扩展，但第一版尚未做真实向量相似度排序。

审计事件：

```text
rag.retrieve.completed
```

payload 包含：

- `agent_run_id`
- `query_hash`
- `top_k`
- `chunk_ids`
- `scores`

## 11. 临床规则模块设计

目录：

```text
app/clinical/
```

### 11.1 signal_extractor

负责从用户消息中抽取：

- 情绪
- 症状
- 压力源
- 功能受损
- 危机标记
- 保护因素
- 持续时间
- 频率

### 11.2 risk_engine

负责生成 `RiskResult`：

- 焦虑风险
- 抑郁风险
- 睡眠风险
- 危机等级
- 功能受损等级
- 证据链
- 推荐下一步

### 11.3 scales

量表模块：

- PHQ-9
- GAD-7
- 简化危机筛查

### 11.4 interventions

干预模块：

- CBT
- 行为激活
- 正念
- 睡眠卫生
- 转介建议

### 11.5 policies

安全策略：

- 危机响应模板。
- 非诊断边界。
- 线下求助建议。

## 12. API 设计

### 12.1 Health

```text
GET /api/health
```

### 12.2 Chat

```text
POST /api/chat/messages
```

### 12.3 Assessments

```text
POST /api/assessments/phq9
POST /api/assessments/gad7
POST /api/assessments/crisis
```

### 12.4 Profile

```text
GET /api/profile/{user_id}
GET /api/profile/{user_id}/timeline
```

### 12.5 Report

```text
GET /api/report/{user_id}/latest
POST /api/report/{user_id}/generate
```

完整 curl 示例见：

```text
docs/delivery/api-examples.md
```

## 13. 数据模型设计

核心表：

- `users`
- `conversations`
- `messages`
- `user_profiles`
- `assessments`
- `risk_assessments`
- `audit_logs`
- `knowledge_chunks`

### 13.1 messages

保存：

- role
- content
- content hash
- risk snapshot

### 13.2 user_profiles

保存：

- profile json
- latest summary
- risk trend
- updated message id

### 13.3 risk_assessments

保存：

- depression risk
- anxiety risk
- sleep risk
- crisis level
- function impairment level
- evidence
- recommended next step

### 13.4 audit_logs

保存：

- request id
- user id
- conversation id
- event type
- event payload

### 13.5 knowledge_chunks

保存工程化知识库 chunk 和 embedding JSON。

## 14. 审计与可观测性

事件常量位于：

```text
app/observability/events.py
```

关键事件：

- `api.request.started`
- `api.request.completed`
- `agent.run.started`
- `agent.run.completed`
- `agent.node.started`
- `agent.node.completed`
- `agent.node.failed`
- `llm.call.started`
- `llm.call.completed`
- `llm.call.failed`
- `rag.retrieve.completed`
- `risk.assessment.completed`
- `safety.escalation.triggered`

审计策略：

- 普通日志不记录完整 prompt。
- RAG 审计记录 query hash，不保存完整用户原文。
- 风险和安全升级事件落库。

## 15. 安全边界设计

允许表达：

- “存在焦虑/低落相关风险信号。”
- “建议完成 GAD-7 或 PHQ-9 进一步筛查。”
- “这不是诊断。”
- “建议联系学校心理中心或专业人员进一步评估。”

禁止表达：

- “你已经患有抑郁症。”
- “你不需要看医生。”
- “按我说的停药。”
- “我可以替代心理医生。”

危机路径要求：

- 优先确认当前安全。
- 建议联系可信任的人。
- 建议联系学校心理中心、危机热线或紧急服务。
- 跳过普通 RAG。
- 写入安全升级审计。

## 16. 评估集与测试设计

固定评估集：

```text
tests/fixtures/dialogues/*.json
```

每条样例包含：

- `case_id`
- `user_id`
- `conversation_id`
- `message`
- `expected`

评估测试：

```bash
python -m pytest tests/integration/test_evaluation_cases.py -q
```

安全边界测试：

```bash
python -m pytest tests/integration/test_safety_boundary.py -q
```

指标计算：

```text
app/observability/metrics.py
```

指标：

- case count
- risk recall
- crisis recall
- false positive rate
- safe response rate

## 17. 交付验证

完整检查：

```bash
python scripts/check_delivery.py
```

脚本执行：

```bash
python -m pytest -q
python -m ruff check .
python -m mypy app
python -m alembic history
```

Smoke test：

```bash
python -m uvicorn app.main:app --reload
python scripts/smoke_test.py --base-url http://127.0.0.1:8000
```

Smoke 覆盖：

- health
- 普通 chat
- crisis chat
- PHQ-9
- GAD-7
- crisis screen
- profile
- report

当前已验证结果：

- `pytest -q`：50 passed
- `ruff check .`：通过
- `mypy app`：通过
- `alembic history`：通过
- `scripts/check_delivery.py`：通过
- `scripts/smoke_test.py`：通过

## 18. 部署与运行

本地开发：

```bash
python -m pip install -e '.[dev]'
python -m uvicorn app.main:app --reload
```

PostgreSQL 迁移：

```bash
alembic upgrade head
```

Docker Compose：

```bash
docker compose up api postgres redis
```

Compose 服务：

- API
- PostgreSQL + pgvector
- Redis

## 19. 当前 API Key 配置

当前代码真正读取的外部模型 key：

```env
LLM_API_KEY=
```

配套字段：

```env
LLM_PROVIDER=
LLM_MODEL=
LLM_BASE_URL=
LLM_TIMEOUT_SECONDS=
```

当前没有：

- embedding API key
- 短信 API key
- 邮件 API key
- 外部学校资源 API key
- JWT secret
- 第三方监控平台 key

## 20. 已知限制

- 当前没有前端。
- 默认未接真实大模型 API。
- 默认 embedding 是 local hash embedding。
- RAG 还不是语义向量检索。
- 没有生产级鉴权和限流。
- 没有真实短信、邮件或外部危机资源 API。
- 评估集规模仍较小。
- 当前不是临床认证系统。

## 21. 下一步建议

优先级从高到低：

1. 配置真实 LLM API 并做 live smoke test。
2. 扩充评估集到 50-100 条。
3. 用评估集驱动风险规则、回复策略和 RAG 检索优化。
4. 接真实 embedding provider 和 pgvector 相似度检索。
5. 增加 API 鉴权、限流和日志脱敏策略。
6. 增加最小前端或运营测试控制台。
7. 增加生产监控、告警和错误追踪。
