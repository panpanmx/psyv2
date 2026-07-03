from collections import defaultdict

from app.schemas.risk import ExtractedSignals, RiskResult, RiskSummary, summarize_risk


class ProfileMemory:
    def __init__(self) -> None:
        self._profiles: dict[str, dict[str, list[str]]] = defaultdict(
            lambda: {
                "dominant_emotions": [],
                "stressors": [],
                "symptoms": [],
                "function_impairment": [],
                "protective_factors": [],
                "risk_factors": [],
            }
        )
        self._summaries: dict[str, str] = {}
        self._timeline: dict[str, list[RiskSummary]] = defaultdict(list)

    def update(self, user_id: str, signals: ExtractedSignals, risk: RiskResult) -> None:
        profile = self._profiles[user_id]
        _merge(profile["dominant_emotions"], signals.emotions)
        _merge(profile["stressors"], signals.stressors)
        _merge(profile["symptoms"], signals.symptoms)
        _merge(profile["function_impairment"], signals.function_impairment)
        _merge(profile["protective_factors"], signals.protective_factors)
        _merge(profile["risk_factors"], signals.risk_markers)
        self._summaries[user_id] = _summary(profile)
        self._timeline[user_id].append(summarize_risk(risk))

    def get_profile(self, user_id: str) -> dict[str, list[str]]:
        return dict(self._profiles[user_id])

    def get_summary(self, user_id: str) -> str:
        return self._summaries.get(user_id, "尚未形成足够画像。")

    def get_latest_risk(self, user_id: str) -> RiskSummary | None:
        items = self._timeline.get(user_id, [])
        return items[-1] if items else None

    def get_timeline(self, user_id: str) -> list[dict[str, str]]:
        return [item.model_dump() for item in self._timeline.get(user_id, [])]


def _merge(target: list[str], values: list[str]) -> None:
    for value in values:
        if value not in target:
            target.append(value)


def _summary(profile: dict[str, list[str]]) -> str:
    emotions = "、".join(profile["dominant_emotions"]) or "暂无明显情绪主题"
    stressors = "、".join(profile["stressors"]) or "暂无明确压力源"
    return f"近期主要情绪：{emotions}；主要压力源：{stressors}。"
