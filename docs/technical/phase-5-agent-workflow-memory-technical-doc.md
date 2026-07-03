# 第五阶段 Agent 节点化编排与长期记忆技术文档

最后更新日期：2026-06-25

## 目标与范围

第五阶段将单体 `AgentOrchestrator` 改造成轻量 pipeline。每个节点只读写 `AgentState`，节点之间通过明确字段传递信号、风险、知识、干预和持久化结果。当前实现不引入 LangGraph，但节点边界可直接映射到后续 graph node。

## AgentState

核心字段：

- `request_id/agent_run_id/user_id/conversation_id/user_message`
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
- `user_message_id/assistant_message_id`
- `assessment_suggestions`

`extracted_signals` 使用 `ExtractedSignals`，`risk_result` 使用 `RiskResult`，避免节点间传裸 dict。

## Pipeline

`app/agent/pipeline.py` 定义：

- `PipelineNode` Protocol：`name` + `async run(state)`。
- `PipelineRunner`：按顺序执行节点，记录 `agent.node.started/completed/failed`。

节点失败会向上抛出，不静默吞掉。

## 节点列表

执行顺序：

1. `SafetyNode`：危机关键词快速路由。
2. `MemoryNode`：读取最近对话和用户画像。
3. `IntentNode`：识别 assessment/support/crisis。
4. `SignalExtractionNode`：规则抽取 + LLM 补充 + 安全合并。
5. `RiskNode`：多轴风险评估，并设置 crisis route。
6. `AssessmentNode`：生成 GAD-7/PHQ-9/crisis screen 建议。
7. `RagNode`：普通路径检索知识库；crisis route 跳过普通 RAG。
8. `InterventionNode`：选择干预动作并合并量表建议。
9. `ResponseNode`：生成非诊断回复或危机安全回复。
10. `PersistNode`：保存 user/assistant message、risk、profile、audit。

## Crisis Route

危机路由有两层：

- `SafetyNode` 对明显表达先设置 `route=crisis`。
- `RiskNode` 根据结构化信号确认 `s2/s3/s4` 后保持 crisis route。

crisis route 下：

- `RagNode` 不检索普通知识。
- `ResponseNode` 使用 `crisis_response()`。
- `PersistNode` 写入 `safety.escalation.triggered` 审计。

## PersistNode 写库顺序

1. ensure user/conversation。
2. 保存 user message。
3. 保存 risk assessment。
4. 保存 assistant message。
5. 更新 profile。
6. 写入 `risk.assessment.completed`。
7. crisis 时写入 `safety.escalation.triggered`。

## LangGraph 迁移路径

当前每个 node 都只有 `AgentState -> AgentState` 的单一接口。迁移 LangGraph 时可以：

- 将 `PipelineNode.run` 映射为 graph node。
- 将 `route` 映射为 conditional edge。
- 保留 `PersistNode` 作为终止前副作用节点。
- 复用 `node_trace` 作为 graph trace 对照。

## 测试覆盖

新增覆盖：

- `tests/unit/test_pipeline.py`
- `tests/unit/test_agent_nodes.py`
- `tests/integration/test_agent_flow.py`

针对性验证命令：

```bash
/Users/panpan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pytest tests/unit/test_pipeline.py tests/unit/test_agent_nodes.py tests/integration/test_agent_flow.py -q
```

当前结果：`10 passed, 1 warning`。

## 已知限制

- 当前 pipeline 为内部轻量实现，尚未接 LangGraph。
- MemoryNode 读取的是最近消息和当前画像，尚未做摘要型长期记忆压缩。
- 节点审计以日志和 DB 关键事件为主，尚未建立完整可视化 trace。
