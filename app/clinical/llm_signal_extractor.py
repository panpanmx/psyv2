from app.llm.base import LLMProvider
from app.llm.prompt_registry import PromptRegistry
from app.schemas.risk import ExtractedSignals

ALLOWED_EMOTIONS = {"焦虑", "低落", "愤怒", "孤独"}
ALLOWED_SYMPTOMS = {"失眠", "注意力下降", "疲惫", "自责", "兴趣下降"}
ALLOWED_STRESSORS = {"考试压力", "学业压力", "人际关系", "家庭压力"}
ALLOWED_IMPAIRMENT = {"学习", "社交", "睡眠"}
ALLOWED_RISK_MARKERS = {"主动自杀想法", "被动死亡想法", "方式", "计划", "准备工具"}
ALLOWED_PROTECTIVE_FACTORS = {"朋友支持", "家庭牵挂", "求助意愿"}


class LLMSignalExtractor:
    def __init__(self, *, provider: LLMProvider, prompt_registry: PromptRegistry) -> None:
        self.provider = provider
        self.prompt_registry = prompt_registry
        self.last_error: Exception | None = None

    async def extract(self, message: str) -> ExtractedSignals:
        prompt = self.prompt_registry.get("signal_extraction_v1")
        self.last_error = None
        try:
            payload = await self.provider.chat_json(system_prompt=prompt, user_prompt=message)
            return ExtractedSignals.model_validate(payload)
        except Exception as exc:
            self.last_error = exc
            return ExtractedSignals()


def merge_signals_safely(rule: ExtractedSignals, llm: ExtractedSignals) -> ExtractedSignals:
    return ExtractedSignals(
        emotions=_merge_allowed(rule.emotions, llm.emotions, ALLOWED_EMOTIONS),
        symptoms=_merge_allowed(rule.symptoms, llm.symptoms, ALLOWED_SYMPTOMS),
        duration=rule.duration or llm.duration,
        frequency=rule.frequency or llm.frequency,
        stressors=_merge_allowed(rule.stressors, llm.stressors, ALLOWED_STRESSORS),
        function_impairment=_merge_allowed(
            rule.function_impairment,
            llm.function_impairment,
            ALLOWED_IMPAIRMENT,
        ),
        risk_markers=_merge_allowed(rule.risk_markers, llm.risk_markers, ALLOWED_RISK_MARKERS),
        protective_factors=_merge_allowed(
            rule.protective_factors,
            llm.protective_factors,
            ALLOWED_PROTECTIVE_FACTORS,
        ),
    )


def _merge_allowed(left: list[str], right: list[str], allowed: set[str]) -> list[str]:
    return list(dict.fromkeys([*left, *(value for value in right if value in allowed)]))
