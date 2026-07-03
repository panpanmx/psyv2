from app.clinical.signal_extractor import SignalExtractor


def test_extracts_campus_anxiety_sleep_and_duration_signals() -> None:
    signals = SignalExtractor().extract(
        "我最近两周考试压力很大，晚上总是睡不着，白天注意力下降，也不太想见同学。"
    )

    assert "焦虑" in signals.emotions
    assert "失眠" in signals.symptoms
    assert "两周" in signals.duration
    assert "考试压力" in signals.stressors
    assert "学习" in signals.function_impairment
    assert "社交" in signals.function_impairment


def test_extracts_crisis_markers_without_echoing_full_message() -> None:
    signals = SignalExtractor().extract("我不想活了，想找个方式结束这一切，但想到朋友又有点犹豫。")

    assert "主动自杀想法" in signals.risk_markers
    assert "方式" in signals.risk_markers
    assert "朋友支持" in signals.protective_factors


def test_ignores_negated_historical_and_third_person_crisis_contexts() -> None:
    extractor = SignalExtractor()

    negated = extractor.extract("我不是想死，只是最近太累了，想找个人说说。")
    historical = extractor.extract("我去年想过自杀，但现在没有这种想法。")
    third_person = extractor.extract("我朋友说他不想活了，我很担心他。")

    assert "主动自杀想法" not in negated.risk_markers
    assert "主动自杀想法" not in historical.risk_markers
    assert "主动自杀想法" not in third_person.risk_markers


def test_plan_and_preparation_imply_active_crisis_markers() -> None:
    signals = SignalExtractor().extract("我已经准备好了药，也想好了时间，我担心自己会冲动。")

    assert "主动自杀想法" in signals.risk_markers
    assert "计划" in signals.risk_markers
    assert "准备工具" in signals.risk_markers
