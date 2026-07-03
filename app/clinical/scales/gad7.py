from pydantic import BaseModel


class GAD7Result(BaseModel):
    score: int
    severity: str
    interpretation: str
    recommended_next_step: str


def _validate_answers(answers: list[int]) -> None:
    if len(answers) != 7:
        raise ValueError("GAD-7 requires exactly 7 answers.")
    if any(answer < 0 or answer > 3 for answer in answers):
        raise ValueError("GAD-7 answers must be integers from 0 to 3.")


def _severity(score: int) -> str:
    if score <= 4:
        return "none"
    if score <= 9:
        return "mild"
    if score <= 14:
        return "moderate"
    return "severe"


def score_gad7(answers: list[int]) -> GAD7Result:
    _validate_answers(answers)
    score = sum(answers)
    severity = _severity(score)
    if severity == "severe":
        next_step = "建议联系学校心理中心或专业评估，并减少独自承受压力。"
    elif severity == "moderate":
        next_step = "建议完成进一步专业评估，并尝试担忧记录与呼吸练习。"
    elif severity == "mild":
        next_step = "建议观察焦虑变化，尝试短时放松练习和规律作息。"
    else:
        next_step = "暂未见明显焦虑风险，可继续观察。"
    return GAD7Result(
        score=score,
        severity=severity,
        interpretation=f"GAD-7 筛查结果提示 {severity} 焦虑相关风险。",
        recommended_next_step=next_step,
    )

