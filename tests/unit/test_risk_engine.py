from app.clinical.risk_engine import RiskEngine
from app.clinical.signal_extractor import SignalExtractor


def test_risk_engine_combines_signals_into_moderate_anxiety_and_sleep_risk() -> None:
    signals = SignalExtractor().extract("最近两周考试压力很大，睡不着，注意力下降，心里很慌。")

    result = RiskEngine().assess(signals=signals)

    assert result.anxiety_risk == "moderate"
    assert result.sleep_risk == "moderate"
    assert result.crisis_level == "s0"
    assert result.function_impairment_level == "moderate"
    assert result.evidence


def test_risk_engine_prioritizes_crisis_flow() -> None:
    signals = SignalExtractor().extract("我不想活了，已经想好了方式，也准备好了工具。")

    result = RiskEngine().assess(signals=signals)

    assert result.crisis_level in {"s3", "s4"}
    assert result.recommended_next_step["route"] == "crisis"
