# 第四阶段 LLM Provider 与结构化抽取 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 接入真实 LLM Provider 与结构化信号抽取能力，同时保证规则型危机识别和非诊断安全边界始终优先。

**Architecture:** 新增 `app/llm/` provider 层，提供统一 `chat()` 与 `embed()` 接口；新增 prompt registry 与结构化抽取 adapter。临床信号抽取采用“规则兜底 + LLM 补充 + Pydantic 校验 + 安全合并”的架构，任何 LLM 输出都不能降低规则识别出的危机等级。

**Tech Stack:** Python 3.11+, httpx, Pydantic v2, FastAPI, SQLAlchemy async, structlog, pytest, ruff, mypy.

---

## 阶段边界

本阶段实现：

- `LLMProvider` 抽象。
- OpenAI-compatible provider。
- Qwen/DeepSeek provider 通过 OpenAI-compatible base URL 配置复用。
- Local/Mock provider，保证无 API key 时测试可跑。
- Prompt registry。
- LLM 结构化信号抽取。
- LLM 调用日志和审计。
- 与现有 `SignalExtractor` 安全合并。

本阶段不实现：

- 多轮治疗式复杂推理。
- 医嘱或诊断生成。
- 前端模型切换 UI。

## 文件结构

- Modify: `pyproject.toml`
- Modify: `.env.example`
- Modify: `app/core/config.py`
- Create: `app/llm/__init__.py`
- Create: `app/llm/base.py`
- Create: `app/llm/openai_compatible_provider.py`
- Create: `app/llm/local_provider.py`
- Create: `app/llm/provider_factory.py`
- Create: `app/llm/prompt_registry.py`
- Create: `app/clinical/llm_signal_extractor.py`
- Modify: `app/clinical/signal_extractor.py`
- Modify: `app/agent/orchestrator.py`
- Modify: `app/observability/events.py`
- Create: `tests/unit/test_llm_provider.py`
- Create: `tests/unit/test_prompt_registry.py`
- Create: `tests/unit/test_llm_signal_extractor.py`
- Create: `tests/integration/test_chat_llm_safety.py`
- Create: `docs/technical/phase-4-llm-provider-technical-doc.md`

---

### Task 1: LLM 配置

**Files:**
- Modify: `app/core/config.py`
- Modify: `.env.example`
- Test: `tests/unit/test_config.py`

- [x] **Step 1: 写失败测试**

在 `tests/unit/test_config.py` 增加：

```python
def test_settings_exposes_llm_configuration() -> None:
    settings = Settings(
        llm_provider="local",
        llm_model="local-rule-model",
        llm_base_url="https://example.test/v1",
        llm_api_key="test-key",
        llm_timeout_seconds=15,
    )

    assert settings.llm_provider == "local"
    assert settings.llm_model == "local-rule-model"
    assert settings.llm_timeout_seconds == 15
```

- [x] **Step 2: 验证失败**

Run: `python -m pytest tests/unit/test_config.py::test_settings_exposes_llm_configuration -q`

Expected: FAIL。

- [x] **Step 3: 实现配置**

`Settings` 增加：

```python
llm_provider: str = "local"
llm_model: str = "local-rule-model"
llm_base_url: str = ""
llm_api_key: str = ""
llm_timeout_seconds: int = 30
```

`.env.example` 增加同名变量。

- [x] **Step 4: 验证通过**

Run: `python -m pytest tests/unit/test_config.py -q`

Expected: PASS。

---

### Task 2: Provider 抽象与 Local Provider

**Files:**
- Create: `app/llm/base.py`
- Create: `app/llm/local_provider.py`
- Test: `tests/unit/test_llm_provider.py`

- [x] **Step 1: 写失败测试**

Create `tests/unit/test_llm_provider.py`:

```python
from app.llm.local_provider import LocalProvider


async def test_local_provider_returns_deterministic_structured_response() -> None:
    provider = LocalProvider(model="local-rule-model")

    result = await provider.chat_json(
        system_prompt="extract",
        user_prompt="我最近两周很低落，睡不着。",
    )

    assert result["provider"] == "local"
    assert "低落" in result["emotions"]
```

- [x] **Step 2: 验证失败**

Run: `python -m pytest tests/unit/test_llm_provider.py -q`

Expected: FAIL。

- [x] **Step 3: 实现抽象**

`app/llm/base.py`:

- `LLMUsage(prompt_tokens, completion_tokens, total_tokens)`
- `LLMResponse(content, model, provider, usage, raw)`
- `LLMProvider` Protocol:
  - `chat(system_prompt, user_prompt) -> LLMResponse`
  - `chat_json(system_prompt, user_prompt) -> dict[str, object]`

- [x] **Step 4: 实现 LocalProvider**

LocalProvider 通过关键词返回结构化 JSON，用于测试和无 key 环境。

- [x] **Step 5: 验证通过**

Run: `python -m pytest tests/unit/test_llm_provider.py -q`

Expected: PASS。

---

### Task 3: OpenAI-compatible Provider 与 Factory

**Files:**
- Create: `app/llm/openai_compatible_provider.py`
- Create: `app/llm/provider_factory.py`
- Test: `tests/unit/test_llm_provider.py`

- [x] **Step 1: 增加失败测试**

```python
from app.core.config import Settings
from app.llm.provider_factory import create_llm_provider
from app.llm.local_provider import LocalProvider


def test_provider_factory_defaults_to_local_without_key() -> None:
    provider = create_llm_provider(Settings(llm_provider="openai", llm_api_key=""))

    assert isinstance(provider, LocalProvider)
```

- [x] **Step 2: 验证失败**

Run: `python -m pytest tests/unit/test_llm_provider.py -q`

Expected: FAIL。

- [x] **Step 3: 实现 provider**

OpenAI-compatible provider:

- 使用 `httpx.AsyncClient`
- POST `{base_url}/chat/completions`
- 支持 model、messages、temperature=0
- `chat_json()` 从 content 中解析 JSON
- 不记录完整 prompt 到普通日志

- [x] **Step 4: 实现 factory**

规则：

- `llm_provider=local` -> LocalProvider
- `openai/qwen/deepseek` 且有 key -> OpenAICompatibleProvider
- 无 key -> LocalProvider

- [x] **Step 5: 验证通过**

Run: `python -m pytest tests/unit/test_llm_provider.py -q`

Expected: PASS。

---

### Task 4: Prompt Registry

**Files:**
- Create: `app/llm/prompt_registry.py`
- Test: `tests/unit/test_prompt_registry.py`

- [x] **Step 1: 写失败测试**

```python
from app.llm.prompt_registry import PromptRegistry


def test_prompt_registry_returns_signal_extraction_prompt() -> None:
    registry = PromptRegistry()
    prompt = registry.get("signal_extraction_v1")

    assert "JSON" in prompt
    assert "不做诊断" in prompt
    assert "risk_markers" in prompt
```

- [x] **Step 2: 实现 PromptRegistry**

内置 prompt 必须要求：

- 输出 JSON。
- 字段为 `emotions/symptoms/duration/frequency/stressors/function_impairment/risk_markers/protective_factors`。
- 不做诊断。
- 危机表达必须保留。

- [x] **Step 3: 验证通过**

Run: `python -m pytest tests/unit/test_prompt_registry.py -q`

Expected: PASS。

---

### Task 5: LLM 结构化信号抽取与安全合并

**Files:**
- Create: `app/clinical/llm_signal_extractor.py`
- Modify: `app/clinical/signal_extractor.py`
- Test: `tests/unit/test_llm_signal_extractor.py`

- [x] **Step 1: 写失败测试**

```python
from app.clinical.llm_signal_extractor import merge_signals_safely
from app.schemas.risk import ExtractedSignals


def test_merge_signals_never_removes_rule_based_crisis_markers() -> None:
    rule = ExtractedSignals(risk_markers=["主动自杀想法", "计划"])
    llm = ExtractedSignals(risk_markers=[], emotions=["低落"])

    merged = merge_signals_safely(rule, llm)

    assert "主动自杀想法" in merged.risk_markers
    assert "计划" in merged.risk_markers
    assert "低落" in merged.emotions
```

- [x] **Step 2: 实现**

`LLMSignalExtractor`:

- 接收 provider + prompt registry。
- 调用 `chat_json()`。
- 用 `ExtractedSignals.model_validate()` 校验。
- 校验失败时回退空信号，不抛出到用户。

`merge_signals_safely(rule, llm)`:

- 所有 list 字段去重合并。
- `duration/frequency` 优先 rule，缺失时用 llm。
- `risk_markers` 绝不删除 rule 结果。

- [x] **Step 3: 验证通过**

Run: `python -m pytest tests/unit/test_llm_signal_extractor.py -q`

Expected: PASS。

---

### Task 6: Orchestrator 接入 LLM 抽取

**Files:**
- Modify: `app/services.py`
- Modify: `app/agent/orchestrator.py`
- Modify: `app/observability/events.py`
- Test: `tests/integration/test_chat_llm_safety.py`

- [x] **Step 1: 写失败测试**

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_llm_extraction_cannot_downgrade_crisis_flow() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/chat/messages",
        json={
            "user_id": "u-llm-safe",
            "conversation_id": "c-llm-safe",
            "message": "我不想活了，已经想好了方式。",
        },
    )

    assert response.status_code == 200
    assert response.json()["risk_summary"]["crisis_level"] in {"s3", "s4"}
```

- [x] **Step 2: 实现接入**

`AppServices` 创建 provider、registry、LLMSignalExtractor。

`AgentOrchestrator` 流程：

```text
rule_signals = SignalExtractor.extract(message)
llm_signals = await LLMSignalExtractor.extract(message)
signals = merge_signals_safely(rule_signals, llm_signals)
```

记录事件：

- `llm.call.started`
- `llm.call.completed`
- `llm.call.failed`

日志不得记录完整 prompt。

- [x] **Step 3: 验证通过**

Run:

```bash
python -m pytest tests/unit/test_llm_provider.py tests/unit/test_llm_signal_extractor.py tests/integration/test_chat_llm_safety.py -q
```

Expected: PASS。

---

### Task 7: 文档与最终验证

**Files:**
- Create: `docs/technical/phase-4-llm-provider-technical-doc.md`
- Modify: `docs/technical/README.md`
- Modify: `docs/context/codex-project-context.md`
- Modify: `README.md`

- [x] **Step 1: 写技术文档**

覆盖：

- provider 配置。
- provider factory。
- prompt registry。
- 结构化抽取 schema。
- 规则与 LLM 安全合并。
- LLM 日志与隐私边界。

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

