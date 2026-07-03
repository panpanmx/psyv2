from app.clinical.llm_signal_extractor import LLMSignalExtractor, merge_signals_safely
from app.llm.local_provider import LocalProvider
from app.llm.prompt_registry import PromptRegistry
from app.schemas.risk import ExtractedSignals


def test_merge_signals_never_removes_rule_based_crisis_markers() -> None:
    rule = ExtractedSignals(risk_markers=["主动自杀想法", "计划"])
    llm = ExtractedSignals(risk_markers=[], emotions=["低落"])

    merged = merge_signals_safely(rule, llm)

    assert "主动自杀想法" in merged.risk_markers
    assert "计划" in merged.risk_markers
    assert "低落" in merged.emotions


def test_merge_signals_ignores_noncanonical_llm_stressors_and_impairment() -> None:
    rule = ExtractedSignals(symptoms=["自责"])
    llm = ExtractedSignals(
        emotions=["自责", "自卑"],
        symptoms=["负面自我评价"],
        stressors=["未提及"],
        function_impairment=["社交活动兴趣降低"],
    )

    merged = merge_signals_safely(rule, llm)

    assert merged.stressors == []
    assert merged.function_impairment == []
    assert "自责" in merged.symptoms


async def test_llm_signal_extractor_validates_provider_json() -> None:
    extractor = LLMSignalExtractor(
        provider=LocalProvider(model="local-rule-model"),
        prompt_registry=PromptRegistry(),
    )

    signals = await extractor.extract("我最近两周很低落，睡不着。")

    assert "低落" in signals.emotions
    assert "失眠" in signals.symptoms
