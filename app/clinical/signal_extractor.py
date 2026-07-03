from app.schemas.risk import ExtractedSignals


class SignalExtractor:
    def extract(self, message: str) -> ExtractedSignals:
        text = message.strip()
        colloquial_non_crisis = _is_colloquial_non_crisis(text)
        contextual_non_self_crisis = _is_contextual_non_self_crisis(text)
        suppress_direct_crisis = colloquial_non_crisis or contextual_non_self_crisis
        negated_plan = _contains(text, ["没有任何计划", "没有计划", "还没有任何计划"])
        negated_method = _contains(text, ["没有想过怎么做", "没有具体打算", "没有想过方式"])
        crisis_related_worry = _contains(text, ["担心自己会冲动", "担心自己会伤害"])
        emotions: list[str] = []
        symptoms: list[str] = []
        stressors: list[str] = []
        impairment: list[str] = []
        risk_markers: list[str] = []
        protective: list[str] = []

        if _contains(text, ["焦虑", "紧张", "心慌", "很慌", "害怕", "压力很大"]) or (
            "担心" in text and not crisis_related_worry
        ):
            emotions.append("焦虑")
        if _contains(text, ["低落", "难过", "沮丧", "空", "麻木", "没意思"]):
            emotions.append("低落")
        if _contains(text, ["愤怒", "生气"]):
            emotions.append("愤怒")
        if _contains(text, ["孤独", "没人懂"]):
            emotions.append("孤独")

        if _contains(text, ["睡不着", "失眠", "凌晨", "睡不好"]):
            symptoms.append("失眠")
        if _contains(text, ["注意力下降", "注意力不集中", "学不进去"]):
            symptoms.append("注意力下降")
        if _contains(text, ["疲惫", "很累", "没力气"]):
            symptoms.append("疲惫")
        if _contains(text, ["自责", "没用", "废物"]):
            symptoms.append("自责")
        if _contains(text, ["兴趣下降", "不想做", "没兴趣"]):
            symptoms.append("兴趣下降")

        if _contains(text, ["考试", "升学"]):
            stressors.append("考试压力")
        if _contains(text, ["作业", "论文", "绩点", "学业"]):
            stressors.append("学业压力")
        if _has_interpersonal_stressor(text):
            stressors.append("人际关系")
        if _contains(text, ["父母", "家庭", "家里"]):
            stressors.append("家庭压力")

        if _contains(text, ["注意力下降", "学不进去", "成绩", "学习效率"]):
            impairment.append("学习")
        if _contains(text, ["不想见同学", "不太想见同学", "不想见人", "躲着", "退缩"]):
            impairment.append("社交")
        if _contains(text, ["睡不着", "失眠", "睡不好"]):
            impairment.append("睡眠")

        if not suppress_direct_crisis and (
            _contains(text, ["不想活", "想死", "结束这一切", "自杀"])
            or _has_plan_and_preparation(text)
        ):
            risk_markers.append("主动自杀想法")
        if not suppress_direct_crisis and _contains(text, ["消失", "睡着不醒"]):
            risk_markers.append("被动死亡想法")
        if not negated_method and _contains(text, ["方式", "办法", "怎么做"]):
            risk_markers.append("方式")
        if not negated_plan and _contains(text, ["计划", "想好了"]):
            risk_markers.append("计划")
        if _contains(text, ["准备好了", "准备都已经", "工具", "药", "刀"]):
            risk_markers.append("准备工具")

        if _contains(text, ["朋友", "同伴"]):
            protective.append("朋友支持")
        if _contains(text, ["妈妈", "爸爸", "父母", "家人"]):
            protective.append("家庭牵挂")
        if _contains(text, ["愿意", "想求助", "心理中心", "老师"]):
            protective.append("求助意愿")

        duration = _extract_duration(text)
        frequency = _extract_frequency(text)
        return ExtractedSignals(
            emotions=_unique(emotions),
            symptoms=_unique(symptoms),
            duration=duration,
            frequency=frequency,
            stressors=_unique(stressors),
            function_impairment=_unique(impairment),
            risk_markers=_unique(risk_markers),
            protective_factors=_unique(protective),
        )


def _contains(text: str, words: list[str]) -> bool:
    return any(word in text for word in words)


def _has_interpersonal_stressor(text: str) -> bool:
    if _contains(text, ["宿舍", "室友"]):
        return True
    return _contains(text, ["同学", "朋友"]) and _contains(
        text,
        ["排挤", "排斥", "霸凌", "冷嘲热讽", "阴阳怪气", "起外号", "到处说", "害怕碰见"],
    )


def _is_colloquial_non_crisis(text: str) -> bool:
    if _contains(text, ["只是夸张", "夸张表达", "只是吐槽"]):
        return True
    return _contains(text, ["原地消失", "想死", "结束生命"]) and _contains(
        text,
        ["不是真的", "意思是太尴尬", "社死"],
    )


def _is_contextual_non_self_crisis(text: str) -> bool:
    if _contains(text, ["不是想死", "不是真的想死", "没有自杀想法", "没有自伤想法"]):
        return True
    if _contains(text, ["以前", "去年", "过去", "之前"]) and _contains(
        text,
        ["现在没有", "现在没", "目前没有", "现在不"],
    ):
        return True
    if _contains(text, ["朋友说他", "朋友说她", "同学说他", "同学说她"]):
        return True
    return False


def _has_plan_and_preparation(text: str) -> bool:
    return _contains(text, ["准备好了", "准备都已经", "工具", "药", "刀"]) and _contains(
        text,
        ["计划", "想好了", "时间", "担心自己会冲动"],
    )


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _extract_duration(text: str) -> str | None:
    for marker in ["两周以上", "两周", "几周", "一个月", "几个月", "最近"]:
        if marker in text:
            return marker
    return None


def _extract_frequency(text: str) -> str | None:
    for marker in ["每天", "总是", "经常", "每周", "偶尔"]:
        if marker in text:
            return marker
    return None
