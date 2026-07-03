from app.llm.prompt_registry import PromptRegistry


def test_prompt_registry_returns_signal_extraction_prompt() -> None:
    registry = PromptRegistry()
    prompt = registry.get("signal_extraction_v1")

    assert "JSON" in prompt
    assert "不做诊断" in prompt
    assert "risk_markers" in prompt


def test_prompt_registry_returns_response_generation_prompt() -> None:
    registry = PromptRegistry()
    prompt = registry.get("response_generation_v1")

    assert "校园心理支持助手" in prompt
    assert "不要做医学诊断" in prompt
