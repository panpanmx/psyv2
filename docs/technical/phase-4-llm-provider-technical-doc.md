# 第四阶段 LLM Provider 与结构化抽取技术文档

最后更新日期：2026-06-25

## 目标与范围

第四阶段新增可插拔 LLM Provider 层和结构化信号抽取能力。系统可接 OpenAI-compatible API，也可在没有 API key 的测试和本地环境回退到 `LocalProvider`。

安全原则保持不变：规则型危机识别优先，LLM 结果只能补充，不能删除或降低规则抽取出的危机标记。

## 模块职责

- `app/llm/base.py`：定义 `LLMUsage`、`LLMResponse` 和 `LLMProvider` 协议。
- `app/llm/local_provider.py`：基于现有规则抽取器返回 deterministic JSON，用于测试和无 key 环境。
- `app/llm/openai_compatible_provider.py`：通过 `/chat/completions` 接入 OpenAI-compatible 服务，支持 OpenAI/Qwen/DeepSeek 等 base URL。
- `app/llm/provider_factory.py`：根据 settings 创建 provider；无 key 自动回退 local。
- `app/llm/prompt_registry.py`：集中管理结构化抽取 prompt。
- `app/clinical/llm_signal_extractor.py`：调用 provider、Pydantic 校验 JSON，并与规则信号安全合并。

## 配置

`.env.example` 新增：

```env
LLM_PROVIDER=local
LLM_MODEL=local-rule-model
LLM_BASE_URL=
LLM_API_KEY=
LLM_TIMEOUT_SECONDS=30
```

Provider factory 规则：

- `LLM_PROVIDER=local`：使用 `LocalProvider`。
- `openai/qwen/deepseek` 且有 `LLM_API_KEY`：使用 `OpenAICompatibleProvider`。
- 无 API key：回退 `LocalProvider`。

## Prompt Registry

`signal_extraction_v1` 要求：

- 只输出 JSON。
- 不做诊断。
- 不给药物建议。
- 不声称替代专业人员。
- 字段包含 `emotions/symptoms/duration/frequency/stressors/function_impairment/risk_markers/protective_factors`。
- 危机表达必须保留到 `risk_markers`。

## 结构化抽取与安全合并

`LLMSignalExtractor.extract()` 执行：

1. 读取 prompt。
2. 调用 `provider.chat_json()`。
3. 使用 `ExtractedSignals.model_validate()` 校验。
4. 失败时返回空 `ExtractedSignals`，不向用户抛出异常。

`merge_signals_safely(rule, llm)` 策略：

- list 字段去重合并，但 LLM 补充项必须落在系统受控标签白名单内。
- `duration/frequency` 优先规则结果，规则缺失时使用 LLM。
- `risk_markers` 使用合并策略，规则识别出的危机标记不会被删除。
- 对 LLM 输出的自由文本标签，例如“未提及”“社交活动兴趣降低”等，不写入 `stressors/function_impairment` 等风险引擎字段，避免真实模型输出导致风险误触发。

## Orchestrator 接入

聊天路径中：

```text
rule_signals = SignalExtractor.extract(message)
llm_signals = LLMSignalExtractor.extract(message)
signals = merge_signals_safely(rule_signals, llm_signals)
risk = RiskEngine.assess(signals)
```

记录事件：

- `llm.call.started`
- `llm.call.completed`
- `llm.call.failed`

日志和审计不记录完整 prompt。

## 测试覆盖

新增覆盖：

- `tests/unit/test_llm_provider.py`
- `tests/unit/test_prompt_registry.py`
- `tests/unit/test_llm_signal_extractor.py`
- `tests/integration/test_chat_llm_safety.py`

针对性验证命令：

```bash
/Users/panpan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pytest tests/unit/test_config.py::test_settings_exposes_llm_configuration tests/unit/test_llm_provider.py tests/unit/test_prompt_registry.py tests/unit/test_llm_signal_extractor.py tests/integration/test_chat_llm_safety.py -q
```

当前结果：`7 passed, 1 warning`。

2026-06-25 重新接入真实 OpenAI-compatible LLM API 后，补充验证：

```bash
/Users/panpan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pytest tests/integration/test_evaluation_cases.py tests/integration/test_safety_boundary.py -q
```

结果：`2 passed, 1 warning in 773.83s (0:12:53)`。当前配置经 OpenRouter base URL 调用外部模型；API key 不记录在文档中。

## 已知限制

- 真实外部模型输出可能使用非系统受控标签，合并层会过滤这些补充项；后续可继续改进 prompt 和标签归一化。
- OpenAI-compatible provider 假定返回 content 为 JSON 字符串。
- 本阶段只做结构化抽取，不做复杂治疗式推理或诊断生成。
