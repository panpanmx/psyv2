# 第五阶段 Agent 节点化编排与长期记忆 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 将当前单体 `AgentOrchestrator` 重构为节点化工作流，支持安全检查、记忆读取、意图识别、评估触发、RAG、干预、回复生成、持久化等清晰阶段。

**Architecture:** 先实现内部轻量 pipeline 节点接口，避免过早引入复杂依赖；如果后续需要 LangGraph，可将节点映射到 graph node。每个节点只读写 `AgentState`，所有节点记录开始/完成/失败日志。危机 S2-S4 由 SafetyNode 或 RiskNode 直接路由到 crisis response，再进入 PersistNode。

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy async, structlog, pytest, ruff, mypy.

---

## 阶段边界

本阶段实现：

- Node 协议和 PipelineRunner。
- SafetyNode。
- MemoryNode。
- IntentNode。
- SignalExtractionNode。
- AssessmentNode。
- RiskNode。
- RagNode。
- InterventionNode。
- ResponseNode。
- PersistNode。
- 最近 N 轮对话读取。
- 量表触发建议。
- 节点级日志和集成测试。

本阶段不实现：

- 新临床模型。
- 前端对话 UI。
- 复杂随访任务调度。

## 文件结构

- Modify: `app/agent/state.py`
- Create: `app/agent/pipeline.py`
- Create: `app/agent/nodes/__init__.py`
- Create: `app/agent/nodes/safety_node.py`
- Create: `app/agent/nodes/memory_node.py`
- Create: `app/agent/nodes/intent_node.py`
- Create: `app/agent/nodes/signal_node.py`
- Create: `app/agent/nodes/assessment_node.py`
- Create: `app/agent/nodes/risk_node.py`
- Create: `app/agent/nodes/rag_node.py`
- Create: `app/agent/nodes/intervention_node.py`
- Create: `app/agent/nodes/response_node.py`
- Create: `app/agent/nodes/persist_node.py`
- Modify: `app/agent/orchestrator.py`
- Modify: `app/db/repositories/conversation_repo.py`
- Modify: `app/observability/events.py`
- Create: `tests/unit/test_agent_nodes.py`
- Create: `tests/unit/test_pipeline.py`
- Create: `tests/integration/test_agent_flow.py`
- Create: `docs/technical/phase-5-agent-workflow-memory-technical-doc.md`

---

### Task 1: AgentState 扩展

**Files:**
- Modify: `app/agent/state.py`
- Test: `tests/unit/test_agent_nodes.py`

- [x] **Step 1: 写失败测试**

```python
from app.agent.state import AgentState


def test_agent_state_has_node_trace_and_outputs() -> None:
    state = AgentState(
        request_id="req",
        agent_run_id="run",
        user_id="u",
        conversation_id="c",
        user_message="最近睡不着",
    )

    assert state.node_trace == []
    assert state.suggested_actions == []
    assert state.follow_up_questions == []
```

- [x] **Step 2: 实现字段**

`AgentState` 增加：

- `node_trace: list[str]`
- `suggested_actions: list[str]`
- `follow_up_questions: list[str]`
- `assistant_message_id: str | None`
- `user_message_id: str | None`
- `assessment_suggestions: list[str]`

- [x] **Step 3: 验证通过**

Run: `python -m pytest tests/unit/test_agent_nodes.py -q`

---

### Task 2: PipelineRunner

**Files:**
- Create: `app/agent/pipeline.py`
- Test: `tests/unit/test_pipeline.py`

- [x] **Step 1: 写失败测试**

```python
from app.agent.pipeline import PipelineRunner
from app.agent.state import AgentState


class DemoNode:
    name = "demo"

    async def run(self, state: AgentState) -> AgentState:
        state.node_trace.append(self.name)
        return state


async def test_pipeline_runner_executes_nodes_in_order() -> None:
    state = AgentState(request_id="req", agent_run_id="run", user_id="u", conversation_id="c", user_message="hi")
    result = await PipelineRunner([DemoNode(), DemoNode()]).run(state)

    assert result.node_trace == ["demo", "demo"]
```

- [x] **Step 2: 实现**

`PipelineNode` Protocol:

```python
name: str
async def run(self, state: AgentState) -> AgentState: ...
```

`PipelineRunner`:

- 顺序执行节点。
- 记录 `agent.node.started/completed/failed`。
- 节点失败时抛出异常，不静默吞掉。

- [x] **Step 3: 验证通过**

Run: `python -m pytest tests/unit/test_pipeline.py -q`

---

### Task 3: SafetyNode 与危机快速路由

**Files:**
- Create: `app/agent/nodes/safety_node.py`
- Test: `tests/unit/test_agent_nodes.py`

- [x] **Step 1: 写失败测试**

```python
from app.agent.nodes.safety_node import SafetyNode
from app.agent.state import AgentState


async def test_safety_node_routes_crisis_message() -> None:
    state = AgentState(request_id="req", agent_run_id="run", user_id="u", conversation_id="c", user_message="我不想活了")
    result = await SafetyNode().run(state)

    assert result.route == "crisis"
    assert "safety_node" in result.node_trace
```

- [x] **Step 2: 实现**

SafetyNode 使用规则关键词快速判断：

- 不想活、想死、结束这一切、自杀 -> route crisis
- 否则保持 normal

SafetyNode 不生成最终回复，只做快速路由和 trace。

- [x] **Step 3: 验证通过**

Run: `python -m pytest tests/unit/test_agent_nodes.py -q`

---

### Task 4: MemoryNode 与最近对话读取

**Files:**
- Create: `app/agent/nodes/memory_node.py`
- Modify: `app/db/repositories/conversation_repo.py`
- Test: `tests/unit/test_agent_nodes.py`

- [x] **Step 1: 增加测试**

测试 `ConversationRepository.recent_messages()` 返回最近消息，并由 MemoryNode 写入 `state.recent_messages`。

- [x] **Step 2: 实现 MemoryNode**

MemoryNode:

- 从 DB 读取最近 N 条消息。
- 从 ProfileRepository 读取画像。
- 写入 `state.recent_messages` 和 `state.profile`。

若没有 sessionmaker，使用空记忆，不报错。

- [x] **Step 3: 验证通过**

Run: `python -m pytest tests/unit/test_agent_nodes.py -q`

---

### Task 5: Intent / Signal / Risk / Assessment 节点

**Files:**
- Create: `app/agent/nodes/intent_node.py`
- Create: `app/agent/nodes/signal_node.py`
- Create: `app/agent/nodes/assessment_node.py`
- Create: `app/agent/nodes/risk_node.py`
- Test: `tests/unit/test_agent_nodes.py`

- [x] **Step 1: 写节点测试**

覆盖：

- “想做 GAD-7” -> intent assessment。
- 普通倾诉 -> intent support。
- signal node 写入 `state.extracted_signals`。
- risk node 写入 `state.risk_result`。
- assessment node 对焦虑中度建议 GAD-7，对低落中度建议 PHQ-9。

- [x] **Step 2: 实现节点**

复用现有：

- `SignalExtractor`
- `RiskEngine`
- scales 建议不直接评分，除非用户明确提交量表。

- [x] **Step 3: 验证通过**

Run: `python -m pytest tests/unit/test_agent_nodes.py -q`

---

### Task 6: Rag / Intervention / Response / Persist 节点

**Files:**
- Create: `app/agent/nodes/rag_node.py`
- Create: `app/agent/nodes/intervention_node.py`
- Create: `app/agent/nodes/response_node.py`
- Create: `app/agent/nodes/persist_node.py`
- Test: `tests/unit/test_agent_nodes.py`

- [x] **Step 1: 写节点测试**

覆盖：

- crisis route 下 RagNode 不检索普通知识。
- InterventionNode 生成建议行动。
- ResponseNode 普通路径包含非诊断表达。
- ResponseNode crisis 路径包含现实求助建议。
- PersistNode 保存 user/assistant/risk/profile/audit。

- [x] **Step 2: 实现节点**

从当前 `AgentOrchestrator` 拆出逻辑，但保持 API 响应一致。

- [x] **Step 3: 验证通过**

Run: `python -m pytest tests/unit/test_agent_nodes.py -q`

---

### Task 7: Orchestrator 切换到 Pipeline

**Files:**
- Modify: `app/agent/orchestrator.py`
- Test: `tests/integration/test_agent_flow.py`

- [x] **Step 1: 写集成测试**

Create `tests/integration/test_agent_flow.py`，覆盖：

- 普通压力倾诉。
- 焦虑筛查建议。
- 抑郁筛查建议。
- 危机表达进入安全流程。

- [x] **Step 2: 改造 Orchestrator**

`handle_chat()`：

- 创建 AgentState。
- 构建 nodes。
- 执行 PipelineRunner。
- 将最终 state 转为 ChatResponse。

保持 API schema 不变。

- [x] **Step 3: 验证通过**

Run:

```bash
python -m pytest tests/integration/test_agent_flow.py tests/integration/test_chat_api.py -q
```

---

### Task 8: 文档与最终验证

**Files:**
- Create: `docs/technical/phase-5-agent-workflow-memory-technical-doc.md`
- Modify: `docs/technical/README.md`
- Modify: `docs/context/codex-project-context.md`

- [x] **Step 1: 写技术文档**

覆盖：

- AgentState 字段。
- 节点列表。
- 节点输入输出。
- crisis route。
- PersistNode 写库顺序。
- 如何从 pipeline 迁移到 LangGraph。

- [x] **Step 2: 最终验证**

Run:

```bash
python -m pytest -q
python -m ruff check .
python -m mypy app
```

Expected: 全部通过。

- [x] **Step 3: 更新本计划勾选**

所有任务通过后，将本文件复选框从 `[ ]` 更新为 `[x]`。

