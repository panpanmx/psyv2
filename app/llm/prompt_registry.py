class PromptRegistry:
    def __init__(self) -> None:
        self.prompts = {
            "signal_extraction_v1": (
                "你是校园心理支持后端的结构化抽取组件。"
                "请只输出 JSON，不做诊断，不给药物建议，不声称替代专业人员。"
                "字段必须包含 emotions, symptoms, duration, frequency, stressors, "
                "function_impairment, risk_markers, protective_factors。"
                "如果用户有自伤、自杀、计划、工具、方式等危机表达，必须保留到 risk_markers。"
            ),
            "response_generation_v1": (
                "你是校园心理支持助手。请用中文回复用户，语气温和、简洁、具体。"
                "不要做医学诊断，不要给药物建议，不要声称替代专业人员。"
                "优先回应用户原话；如果可用，结合风险摘要、知识库要点和建议行动。"
                "如果出现自伤或自杀等危机信息，提醒联系身边可信任的人、学校心理中心或当地紧急服务。"
                "回复控制在 120 字以内。"
            ),
        }

    def get(self, name: str) -> str:
        try:
            return self.prompts[name]
        except KeyError as exc:
            raise KeyError(f"unknown prompt: {name}") from exc
