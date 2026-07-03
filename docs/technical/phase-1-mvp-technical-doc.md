# 第一阶段 MVP 技术文档

生成日期：2026-06-24

本文档对应第一阶段实现：校园专业心理医生工作流 Agent 的可运行 MVP。目标读者是继续开发该项目的工程师。阅读后应能理解当前所有核心模块、请求链路、规则实现、测试覆盖和后续扩展方向。

> 安全边界：当前系统只做非诊断性风险提示、筛查建议和干预建议，不提供临床诊断、药物建议，也不能替代专业心理医生。

## 1. 本阶段交付范围

已实现：

- FastAPI 应用入口、路由注册、生命周期启动日志。
- `request_id` 中间件，为每个 HTTP 请求注入并返回 `x-request-id`。
- 结构化 JSON 日志，覆盖 API 请求和 Agent 执行关键事件。
- 日常聊天 API：`POST /api/chat/messages`。
- 量表 API：PHQ-9、GAD-7、简化危机筛查。
- 画像 API：查询用户画像和风险时间线。
- 报告 API：生成或查询最新用户心理风险报告。
- 规则型信号抽取：情绪、症状、压力源、功能受损、危机标记、保护因素。
- 规则型风险评估：抑郁、焦虑、睡眠、危机、功能受损。
- 危机场景优先安全响应。
- 干预策略推荐：CBT、行为激活、正念、睡眠卫生、转介建议。
- 本地 Markdown 知识库检索，也就是 RAG-lite。
- 内存版用户画像和风险时间线。
- 单元测试和集成测试。
- `README.md`、`.env.example`、`docker-compose.yml` 和开发配置。

未实现但保留扩展方向：

- PostgreSQL、SQLAlchemy、Alembic 持久化。
- pgvector 与真实 embedding 检索。
- LLM Provider 和结构化 LLM 抽取。
- LangGraph 节点编排。
- 后台任务、随访提醒和真实学校资源集成。

## 2. 技术栈与运行环境

项目配置文件：[pyproject.toml](/Users/panpan/Documents/myagent/pyproject.toml)

核心依赖：

- Python `>=3.11`
- FastAPI
- Pydantic v2
- pydantic-settings
- structlog
- uvicorn
- pytest
- ruff
- mypy

当前开发中使用的 Python 解释器：

```text
/Users/panpan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
```

常用命令：

```bash
python -m pytest -q
python -m ruff check .
python -m mypy app
python -m uvicorn app.main:app --reload
```

## 3. 目录结构

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
    logging.py                # structlog 配置
    middleware.py             # request_id 中间件
  schemas/
    chat.py                   # 聊天请求/响应模型
    assessment.py             # 量表请求/响应模型
    profile.py                # 画像响应模型
    report.py                 # 报告响应模型
    risk.py                   # 风险相关模型和 Literal 类型
  agent/
    orchestrator.py           # Agent 主编排
    state.py                  # 未来 LangGraph 状态模型
  clinical/
    signal_extractor.py       # 规则型对话信号抽取
    risk_engine.py            # 多轴风险评估
    scales/                   # PHQ-9/GAD-7/简化危机筛查
    interventions/            # 干预策略
    policies/safety_policy.py # 危机安全响应策略
  memory/
    profile_memory.py         # 内存用户画像和风险时间线
  rag/
    knowledge_loader.py       # Markdown 知识库加载
    retriever.py              # 关键词评分检索
  observability/
    audit.py                  # 内存审计事件记录器
    events.py                 # 事件名常量
knowledge_base/               # 首批可控知识库文档
tests/                        # 单元测试和集成测试
docs/technical/               # 阶段技术文档
```

## 4. 应用启动与依赖注入

入口文件：[app/main.py](/Users/panpan/Documents/myagent/app/main.py)

`create_app()` 完成以下工作：

1. 通过 `get_settings()` 加载配置。
2. 调用 `configure_logging()` 初始化 structlog。
3. 创建 FastAPI 实例，使用 lifespan 输出 `app.startup` 日志。
4. 创建 `AppServices` 并挂载到 `app.state.services`。
5. 注册 `RequestIdMiddleware`。
6. 注册 health、chat、assessment、profile、report 路由。

服务容器：[app/services.py](/Users/panpan/Documents/myagent/app/services.py)

`AppServices` 当前持有：

- `ProfileMemory`
- `AuditLogger`
- `KnowledgeRetriever`
- `AgentOrchestrator`

这是第一阶段的轻量依赖注入方式。后续引入数据库、LLM Provider、真实向量库时，优先在 `AppServices` 内新增服务实例，再通过 `app/api/deps.py` 暴露给路由。

## 5. 请求 ID 与结构化日志

中间件：[app/core/middleware.py](/Users/panpan/Documents/myagent/app/core/middleware.py)

`RequestIdMiddleware` 行为：

- 如果请求头带 `x-request-id`，复用该值。
- 否则生成 `req_<uuid>`。
- 写入 `request.state.request_id`。
- 响应头返回 `x-request-id`。
- 请求开始记录 `api.request.started`。
- 请求成功记录 `api.request.completed`，包含状态码和耗时。
- 请求异常记录 `api.request.failed`，包含错误类型。

日志配置：[app/core/logging.py](/Users/panpan/Documents/myagent/app/core/logging.py)

日志格式为 JSON，包含：

- `timestamp`
- `level`
- `event`
- 业务字段，如 `request_id`、`agent_run_id`、`path`、`status_code`

当前不会在普通日志中记录完整用户消息。聊天链路只记录风险等级、用户 ID、会话 ID、事件类型等摘要信息。

## 6. API 契约

### 6.1 健康检查

路由：[app/api/routes/health.py](/Users/panpan/Documents/myagent/app/api/routes/health.py)

```http
GET /api/health
```

响应：

```json
{"status": "ok"}
```

### 6.2 聊天 API

路由：[app/api/routes/chat.py](/Users/panpan/Documents/myagent/app/api/routes/chat.py)

```http
POST /api/chat/messages
```

请求模型：[app/schemas/chat.py](/Users/panpan/Documents/myagent/app/schemas/chat.py)

```json
{
  "user_id": "u-001",
  "conversation_id": "c-001",
  "message": "我最近两周考试压力很大，晚上总是睡不着"
}
```

响应字段：

- `message_id`: 本轮助手消息 ID，格式为 `msg_<uuid>`。
- `assistant_message`: 面向用户的回复。
- `risk_summary`: 多轴风险摘要。
- `suggested_actions`: 建议行动。
- `follow_up_questions`: 跟进问题。

示例风险摘要：

```json
{
  "depression_risk": "unknown",
  "anxiety_risk": "moderate",
  "sleep_risk": "moderate",
  "crisis_level": "s0",
  "function_impairment_level": "moderate"
}
```

### 6.3 量表 API

路由：[app/api/routes/assessment.py](/Users/panpan/Documents/myagent/app/api/routes/assessment.py)

接口：

- `POST /api/assessments/phq9`
- `POST /api/assessments/gad7`
- `POST /api/assessments/crisis`

PHQ-9/GAD-7 请求：

```json
{
  "user_id": "u-001",
  "conversation_id": "c-001",
  "answers": [1, 2, 1, 2, 1, 2, 1, 1, 0]
}
```

简化危机筛查请求：

```json
{
  "user_id": "u-001",
  "conversation_id": "c-001",
  "answers": {
    "passive_ideation": true,
    "active_ideation": true,
    "method": true,
    "plan": true,
    "intent": true,
    "preparation": true,
    "recent_attempt": false,
    "protective_factors": ["想到妈妈会担心"]
  }
}
```

量表接口当前只返回评分结果，不写入持久化存储。后续接数据库时，应在该路由中写入 `assessments` 和 `risk_assessments`。

### 6.4 画像 API

路由：[app/api/routes/profile.py](/Users/panpan/Documents/myagent/app/api/routes/profile.py)

接口：

- `GET /api/profile/{user_id}`
- `GET /api/profile/{user_id}/timeline`

画像来自 `ProfileMemory`，字段包括：

- `dominant_emotions`
- `stressors`
- `symptoms`
- `function_impairment`
- `protective_factors`
- `risk_factors`

### 6.5 报告 API

路由：[app/api/routes/report.py](/Users/panpan/Documents/myagent/app/api/routes/report.py)

接口：

- `GET /api/report/{user_id}/latest`
- `POST /api/report/{user_id}/generate`

报告响应字段：

- `profile_summary`
- `risk_summary`
- `evidence_summary`
- `recommended_interventions`
- `offline_help_recommended`

`offline_help_recommended` 当前规则：

- `crisis_level` 为 `s2/s3/s4` 时为 `true`。
- `depression_risk` 为 `moderate/moderately_severe/severe` 时为 `true`。

## 7. 聊天主流程

核心编排：[app/agent/orchestrator.py](/Users/panpan/Documents/myagent/app/agent/orchestrator.py)

`AgentOrchestrator.handle_chat()` 调用链：

```text
ChatRequest
  -> 生成 agent_run_id
  -> SignalExtractor.extract()
  -> RiskEngine.assess()
  -> AuditLogger.record_event(risk.assessment.completed)
  -> select_interventions()
  -> KnowledgeRetriever.retrieve()  # 危机 S2-S4 不检索普通知识库
  -> 生成普通回复或危机回复
  -> ProfileMemory.update()
  -> 返回 ChatResponse
```

普通路径：

1. 抽取信号。
2. 评估风险。
3. 选择干预建议。
4. 检索知识库。
5. 生成非诊断式回复。
6. 更新用户画像。

危机路径：

1. 抽取到 `s2/s3/s4` 危机风险。
2. 不走普通 RAG。
3. 使用 `crisis_response()`。
4. 写入 `safety.escalation.triggered` 审计事件。
5. 返回安全确认类追问。

## 8. 信号抽取规则

实现文件：[app/clinical/signal_extractor.py](/Users/panpan/Documents/myagent/app/clinical/signal_extractor.py)

当前是确定性关键词规则，输出模型为 `ExtractedSignals`：

```python
class ExtractedSignals(BaseModel):
    emotions: list[str]
    symptoms: list[str]
    duration: str | None
    frequency: str | None
    stressors: list[str]
    function_impairment: list[str]
    risk_markers: list[str]
    protective_factors: list[str]
```

关键映射：

| 类别 | 当前识别示例 | 输出 |
|---|---|---|
| 情绪 | 焦虑、紧张、心慌、压力很大 | `焦虑` |
| 情绪 | 低落、难过、沮丧、麻木、没意思 | `低落` |
| 症状 | 睡不着、失眠、凌晨、睡不好 | `失眠` |
| 症状 | 注意力下降、注意力不集中、学不进去 | `注意力下降` |
| 压力源 | 考试、升学 | `考试压力` |
| 压力源 | 作业、论文、绩点、学业 | `学业压力` |
| 功能受损 | 注意力下降、学不进去、成绩、学习效率 | `学习` |
| 功能受损 | 不想见同学、不太想见同学、不想见人、躲着、退缩 | `社交` |
| 危机标记 | 不想活、想死、结束这一切、自杀 | `主动自杀想法` |
| 危机标记 | 消失、睡着不醒 | `被动死亡想法` |
| 保护因素 | 朋友、同伴 | `朋友支持` |
| 保护因素 | 妈妈、爸爸、父母、家人 | `家庭牵挂` |

持续时间识别：

- `两周以上`
- `两周`
- `几周`
- `一个月`
- `几个月`
- `最近`

频率识别：

- `每天`
- `总是`
- `经常`
- `每周`
- `偶尔`

开发注意：

- 当前规则适合 MVP 和测试可解释性。
- 扩展关键词时要同步补测试。
- 后续接 LLM 结构化抽取时，仍建议保留规则层作为安全兜底，尤其是危机标记。

## 9. 量表评分规则

### 9.1 PHQ-9

文件：[app/clinical/scales/phq9.py](/Users/panpan/Documents/myagent/app/clinical/scales/phq9.py)

输入要求：

- 必须 9 个答案。
- 每个答案为 `0-3`。

严重程度：

| 分数 | severity |
|---|---|
| 0-4 | `none` |
| 5-9 | `mild` |
| 10-14 | `moderate` |
| 15-19 | `moderately_severe` |
| 20-27 | `severe` |

特殊规则：

- 第 9 题 `answers[8] > 0` 时，`item_9_positive = true`。
- 第 9 题阳性时，`recommended_next_step` 必须包含危机复核建议。

### 9.2 GAD-7

文件：[app/clinical/scales/gad7.py](/Users/panpan/Documents/myagent/app/clinical/scales/gad7.py)

输入要求：

- 必须 7 个答案。
- 每个答案为 `0-3`。

严重程度：

| 分数 | severity |
|---|---|
| 0-4 | `none` |
| 5-9 | `mild` |
| 10-14 | `moderate` |
| 15-21 | `severe` |

### 9.3 简化危机筛查

文件：[app/clinical/scales/cssrs_like.py](/Users/panpan/Documents/myagent/app/clinical/scales/cssrs_like.py)

输入维度：

- `passive_ideation`
- `active_ideation`
- `method`
- `plan`
- `intent`
- `preparation`
- `recent_attempt`
- `protective_factors`

分级规则：

| 条件 | crisis_level |
|---|---|
| 无相关信号 | `s0` |
| 被动死亡想法 | `s1` |
| 主动自杀想法或方式 | `s2` |
| 主动想法且伴随计划、意图或准备之一 | `s3` |
| 近期尝试，或主动想法 + 计划 + 意图 + 准备 | `s4` |

`s2/s3/s4` 时：

- `safety_response_required = true`
- 推荐立即联系可信成年人、学校心理中心或当地紧急援助。

## 10. 风险评估规则

实现文件：[app/clinical/risk_engine.py](/Users/panpan/Documents/myagent/app/clinical/risk_engine.py)

输入：

- `ExtractedSignals`
- 预留 `scale_results` 参数，当前未参与规则融合。

输出：

- `depression_risk`
- `anxiety_risk`
- `sleep_risk`
- `crisis_level`
- `function_impairment_level`
- `evidence`
- `recommended_next_step`

### 10.1 危机风险

由 `risk_markers` 推导：

| markers | crisis_level |
|---|---|
| `主动自杀想法` + `计划` + `准备工具` | `s4` |
| `主动自杀想法` + `方式/计划/准备工具` 任一 | `s3` |
| `主动自杀想法` | `s2` |
| `被动死亡想法` | `s1` |
| 无 | `s0` |

`s2/s3/s4` 时，`recommended_next_step.route = "crisis"`。

### 10.2 焦虑风险

规则：

- 出现 `焦虑` 情绪或任意压力源，先标为 `mild`。
- 若同时有两周、两周以上、几周等持续时间，或任意功能受损，升级为 `moderate`。

当前不会自动输出 `severe`，后续应结合 GAD-7 和更强规则升级。

### 10.3 抑郁风险

规则：

- 出现 `低落`，或症状包含 `自责/兴趣下降`，先标为 `mild`。
- 若持续两周、两周以上、几周，或症状数不少于 2，升级为 `moderate`。

当前不会自动输出 `moderately_severe/severe`，后续应结合 PHQ-9 和危机风险升级。

### 10.4 睡眠风险

规则：

- 出现 `失眠`，先标为 `mild`。
- 若持续两周、几周、几个月，或功能受损包含 `睡眠`，升级为 `moderate`。

### 10.5 功能受损

规则：

- 0 个功能受损：`none`
- 1 个功能受损：`mild`
- 2 个及以上：`moderate`

## 11. 干预策略

入口：[app/clinical/interventions/selector.py](/Users/panpan/Documents/myagent/app/clinical/interventions/selector.py)

策略优先级：

1. 危机 `s2/s3/s4`：只返回转介和紧急求助建议。
2. 焦虑风险：返回 GAD-7、CBT 担忧记录、呼吸练习。
3. 抑郁风险：返回行为激活、认知重构。
4. 睡眠风险：返回睡眠卫生建议。
5. 无明显风险：返回情绪、睡眠、学习状态记录建议。

具体模块：

- [cbt.py](/Users/panpan/Documents/myagent/app/clinical/interventions/cbt.py)
- [behavioral_activation.py](/Users/panpan/Documents/myagent/app/clinical/interventions/behavioral_activation.py)
- [mindfulness.py](/Users/panpan/Documents/myagent/app/clinical/interventions/mindfulness.py)
- [sleep_hygiene.py](/Users/panpan/Documents/myagent/app/clinical/interventions/sleep_hygiene.py)
- [referral.py](/Users/panpan/Documents/myagent/app/clinical/interventions/referral.py)

## 12. 危机安全响应

文件：[app/clinical/policies/safety_policy.py](/Users/panpan/Documents/myagent/app/clinical/policies/safety_policy.py)

`crisis_response()` 的特点：

- 先表达重视和担心。
- 建议不要独处。
- 建议移开可能伤害自己的工具。
- 建议立即联系可信成年人或学校心理中心。
- 如有马上伤害自己的风险，建议拨打当地急救电话或去最近急诊。
- 不做长篇分析。
- 不给复杂任务。

触发位置：

- [app/agent/orchestrator.py](/Users/panpan/Documents/myagent/app/agent/orchestrator.py) 中，`risk.crisis_level in {"s2", "s3", "s4"}`。

审计事件：

- `risk.assessment.completed`
- `safety.escalation.triggered`

## 13. RAG-lite 知识库

知识库目录：[knowledge_base](/Users/panpan/Documents/myagent/knowledge_base)

当前文档：

- `anxiety.md`
- `depression.md`
- `cbt_basics.md`
- `mindfulness.md`
- `sleep.md`
- `campus_resources.md`

加载器：[app/rag/knowledge_loader.py](/Users/panpan/Documents/myagent/app/rag/knowledge_loader.py)

- 读取 `knowledge_base/*.md`。
- 提取一级标题作为 `title`。
- 返回 `id/title/content`。

检索器：[app/rag/retriever.py](/Users/panpan/Documents/myagent/app/rag/retriever.py)

当前检索规则：

1. 从用户 query 中抽取候选 token。
2. 标题命中每个 token 加 2 分。
3. 正文命中每个 token 加 1 分。
4. 按分数降序返回 top_k。

候选 token：

```text
考试、压力、焦虑、抑郁、低落、睡眠、睡不着、失眠、危机、自杀、CBT、正念、校园
```

重要实现细节：

- 危机 `s2/s3/s4` 不走普通知识库检索，避免用普通心理教育覆盖安全响应。
- 已加入回归测试，确保焦虑/失眠 query 优先命中 `anxiety` 或 `sleep`，不误命中 `depression`。

## 14. 用户画像与报告

画像实现：[app/memory/profile_memory.py](/Users/panpan/Documents/myagent/app/memory/profile_memory.py)

当前为进程内内存存储，服务重启后数据会丢失。结构：

```python
{
    "dominant_emotions": [],
    "stressors": [],
    "symptoms": [],
    "function_impairment": [],
    "protective_factors": [],
    "risk_factors": [],
}
```

更新逻辑：

- 每次聊天完成后调用 `ProfileMemory.update(user_id, signals, risk)`。
- 对每类信号做去重追加。
- 生成 `latest_summary`。
- 将 `RiskSummary` 追加到用户风险时间线。

报告生成：[app/api/routes/report.py](/Users/panpan/Documents/myagent/app/api/routes/report.py)

报告依据：

- 最新风险摘要。
- 当前画像字段。
- 基于画像的证据摘要。
- 基于最新风险和失眠症状的干预建议。

## 15. Schema 与类型设计

核心模型：[app/schemas/risk.py](/Users/panpan/Documents/myagent/app/schemas/risk.py)

Literal 类型：

- `CrisisLevel = "s0" | "s1" | "s2" | "s3" | "s4"`
- `DepressionRisk = "none" | "mild" | "moderate" | "moderately_severe" | "severe" | "unknown"`
- `AnxietyRisk = "none" | "mild" | "moderate" | "severe" | "unknown"`
- `GenericRisk = "none" | "mild" | "moderate" | "severe" | "unknown"`

`RiskResult` 是内部完整风险结果，包含证据和下一步建议。

`RiskSummary` 是 API 返回和画像时间线使用的简化风险摘要。

设计原因：

- 用 Literal 限制输出枚举，避免 API 返回拼写漂移。
- 内部结果和外部摘要拆开，方便后续把证据链写入数据库，而不强迫所有接口暴露完整证据。

## 16. 审计与可观测性

事件常量：[app/observability/events.py](/Users/panpan/Documents/myagent/app/observability/events.py)

当前事件：

- `api.request.started`
- `api.request.completed`
- `agent.run.started`
- `agent.run.completed`
- `risk.assessment.completed`
- `safety.escalation.triggered`

审计记录器：[app/observability/audit.py](/Users/panpan/Documents/myagent/app/observability/audit.py)

当前 `AuditLogger`：

- 在内存中保存 `events`。
- 同时输出结构化日志。
- `path` 参数已保留，但第一阶段未写文件。

后续数据库实现时建议：

- 将 `AuditLogger.record_event()` 改为同时写入 `audit_logs` 表。
- 对 S2-S4 危机事件强制持久化。
- 对 LLM/RAG/风险判断补充 `model_version`、`rule_version`、`evidence_id`。

## 17. 测试覆盖

测试目录：[tests](/Users/panpan/Documents/myagent/tests)

当前测试数量：11 个。

单元测试：

- [tests/unit/test_scales.py](/Users/panpan/Documents/myagent/tests/unit/test_scales.py)
  - PHQ-9 中度评分。
  - PHQ-9 第 9 题阳性触发危机复核建议。
  - GAD-7 重度评分。
  - 简化危机筛查 S4。

- [tests/unit/test_signal_extractor.py](/Users/panpan/Documents/myagent/tests/unit/test_signal_extractor.py)
  - 校园压力、失眠、持续时间、学习和社交受损抽取。
  - 自杀相关危机标记和保护因素抽取。

- [tests/unit/test_risk_engine.py](/Users/panpan/Documents/myagent/tests/unit/test_risk_engine.py)
  - 焦虑、睡眠、功能受损风险融合。
  - 危机风险优先路线。

- [tests/unit/test_retriever.py](/Users/panpan/Documents/myagent/tests/unit/test_retriever.py)
  - 焦虑/睡眠 query 优先命中相关知识。

集成测试：

- [tests/integration/test_chat_api.py](/Users/panpan/Documents/myagent/tests/integration/test_chat_api.py)
  - 普通聊天 API 返回风险、行动和追问。
  - 高危消息进入危机回复。

- [tests/integration/test_profile_report_api.py](/Users/panpan/Documents/myagent/tests/integration/test_profile_report_api.py)
  - 聊天后画像更新。
  - 报告 API 返回最新风险和推荐干预。

验证命令：

```bash
python -m pytest -q
python -m ruff check .
python -m mypy app
```

## 18. 开发注意事项

### 18.1 每次新增规则必须加测试

示例：

- 新增一个危机关键词，补 `test_signal_extractor.py`。
- 改风险分层，补 `test_risk_engine.py`。
- 改检索排序，补 `test_retriever.py`。
- 改 API 响应结构，补集成测试。

### 18.2 危机路径优先级最高

任何后续功能都不能绕过：

```python
risk.crisis_level in {"s2", "s3", "s4"}
```

只要进入该区间：

- 不走普通 RAG。
- 不输出复杂心理教育。
- 不输出“你没事”“不用看医生”等表达。
- 必须返回安全确认和线下求助建议。
- 必须记录安全升级审计事件。

### 18.3 当前内存状态不适合生产

`ProfileMemory` 是 MVP 级内存存储。它适合演示和测试，但：

- 服务重启后丢数据。
- 多进程部署时状态不共享。
- 无并发写入保护。
- 无数据删除、脱敏、权限控制。

第二阶段应优先替换为数据库模型和 repository。

### 18.4 当前 RAG-lite 不是真正向量检索

它只做关键词评分，优点是可解释、稳定、无需外部依赖。缺点：

- 语义召回能力有限。
- 不支持 chunk 级引用。
- 不支持来源可信度和版本控制。

下一阶段接 pgvector 时，要保留当前测试作为排序回归样例。

## 19. 后续阶段建议

建议第二阶段优先顺序：

1. 数据库层：SQLAlchemy async、Alembic、PostgreSQL。
2. 持久化模型：User、Conversation、Message、UserProfile、Assessment、RiskAssessment、AuditLog。
3. Repository 层：chat/profile/assessment/audit。
4. 把 `ProfileMemory` 替换为数据库画像服务。
5. 让量表 API 写入 assessments，并刷新 risk_assessments。
6. 审计事件落库，特别是 S2-S4。
7. 引入真实 RAG：chunker、embedding、vector_store、retriever。
8. 引入 LLM Provider，但保留规则安全兜底。

## 20. 快速源码阅读路径

如果你要快速掌握项目，建议按这个顺序读：

1. [README.md](/Users/panpan/Documents/myagent/README.md)
2. [app/main.py](/Users/panpan/Documents/myagent/app/main.py)
3. [app/services.py](/Users/panpan/Documents/myagent/app/services.py)
4. [app/api/routes/chat.py](/Users/panpan/Documents/myagent/app/api/routes/chat.py)
5. [app/agent/orchestrator.py](/Users/panpan/Documents/myagent/app/agent/orchestrator.py)
6. [app/clinical/signal_extractor.py](/Users/panpan/Documents/myagent/app/clinical/signal_extractor.py)
7. [app/clinical/risk_engine.py](/Users/panpan/Documents/myagent/app/clinical/risk_engine.py)
8. [app/clinical/interventions/selector.py](/Users/panpan/Documents/myagent/app/clinical/interventions/selector.py)
9. [app/memory/profile_memory.py](/Users/panpan/Documents/myagent/app/memory/profile_memory.py)
10. [app/rag/retriever.py](/Users/panpan/Documents/myagent/app/rag/retriever.py)
11. [tests](/Users/panpan/Documents/myagent/tests)

