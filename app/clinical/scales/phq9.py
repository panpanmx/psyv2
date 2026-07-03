from pydantic import BaseModel


class PHQ9Result(BaseModel):
    score: int
    severity: str
    item_9_positive: bool
    interpretation: str
    recommended_next_step: str


def _validate_answers(answers: list[int]) -> None:
    if len(answers) != 9:
        raise ValueError("PHQ-9 requires exactly 9 answers.")
    if any(answer < 0 or answer > 3 for answer in answers):
        raise ValueError("PHQ-9 answers must be integers from 0 to 3.")


def _severity(score: int) -> str:
    if score <= 4:
        return "none"
    if score <= 9:
        return "mild"
    if score <= 14:
        return "moderate"
    if score <= 19:
        return "moderately_severe"
    return "severe"


def score_phq9(answers: list[int]) -> PHQ9Result:
    _validate_answers(answers)
    score = sum(answers)
    severity = _severity(score)
    item_9_positive = answers[8] > 0
    if item_9_positive:
        next_step = "建议进行危机复核，并联系学校心理中心或专业人员进一步评估。"
    elif severity in {"moderate", "moderately_severe", "severe"}:
        next_step = "建议联系学校心理中心或专业医生进一步评估。"
    elif severity == "mild":
        next_step = "建议进行情绪记录、行为激活练习，并在一到两周后复测。"
    else:
        next_step = "暂未见明显抑郁风险，可继续观察情绪和作息变化。"
    return PHQ9Result(
        score=score,
        severity=severity,
        item_9_positive=item_9_positive,
        interpretation=f"PHQ-9 筛查结果提示 {severity} 抑郁相关风险。",
        recommended_next_step=next_step,
    )

