from typing import Literal

from app.schemas.risk import AnxietyRisk, DepressionRisk, ExtractedSignals, GenericRisk, RiskResult


class RiskEngine:
    def assess(
        self,
        *,
        signals: ExtractedSignals,
        scale_results: dict[str, object] | None = None,
    ) -> RiskResult:
        scale_results = scale_results or {}
        _ = scale_results
        emotions = set(signals.emotions)
        symptoms = set(signals.symptoms)
        stressors = set(signals.stressors)
        impairment = set(signals.function_impairment)
        markers = set(signals.risk_markers)
        duration = signals.duration
        frequency = signals.frequency
        evidence: list[dict[str, str]] = []

        crisis_level = _crisis_from_markers(markers)
        if crisis_level != "s0":
            evidence.append({"source": "message", "detail": "识别到自伤/自杀相关风险表达"})

        anxiety: AnxietyRisk = "unknown"
        if "焦虑" in emotions or stressors:
            anxiety = "mild"
            evidence.append({"source": "message", "detail": "出现焦虑情绪或校园压力源"})
        if anxiety == "mild" and (
            duration in {"两周", "两周以上", "几周"}
            or frequency in {"每天", "总是", "经常"}
            or impairment
        ):
            anxiety = "moderate"
            evidence.append({"source": "message", "detail": "焦虑相关信号伴随持续时间或功能受损"})

        depression: DepressionRisk = "unknown"
        if "低落" in emotions or {"自责", "兴趣下降"} & symptoms:
            depression = "mild"
            evidence.append({"source": "message", "detail": "出现低落、自责或兴趣下降信号"})
        if depression == "mild" and (
            duration in {"两周", "两周以上", "几周", "一个月", "几个月"} or len(symptoms) >= 2
        ):
            depression = "moderate"
            evidence.append({"source": "message", "detail": "抑郁相关信号持续或伴随多个症状"})

        sleep: GenericRisk = "unknown"
        if "失眠" in symptoms:
            sleep = "mild"
            evidence.append({"source": "message", "detail": "出现睡眠困难"})
        if sleep == "mild" and (
            duration in {"两周", "两周以上", "几周", "几个月"} or "睡眠" in impairment
        ):
            sleep = "moderate"
            evidence.append({"source": "message", "detail": "睡眠困难影响近期功能"})

        function_level: GenericRisk = "none"
        if len(impairment) == 1:
            function_level = "mild"
        elif len(impairment) >= 2:
            function_level = "moderate"

        route = "crisis" if crisis_level in {"s2", "s3", "s4"} else "normal"
        next_step = {
            "route": route,
            "summary": (
                "优先进行安全确认和线下求助"
                if route == "crisis"
                else "继续结构化评估和干预建议"
            ),
        }
        return RiskResult(
            depression_risk=depression,
            anxiety_risk=anxiety,
            sleep_risk=sleep,
            crisis_level=crisis_level,
            function_impairment_level=function_level,
            evidence=evidence,
            recommended_next_step=next_step,
        )


def _crisis_from_markers(markers: set[str]) -> Literal["s0", "s1", "s2", "s3", "s4"]:
    if {"主动自杀想法", "计划", "准备工具"} <= markers:
        return "s4"
    if "主动自杀想法" in markers and ({"方式", "计划", "准备工具"} & markers):
        return "s3"
    if "主动自杀想法" in markers:
        return "s2"
    if "被动死亡想法" in markers:
        return "s1"
    return "s0"
