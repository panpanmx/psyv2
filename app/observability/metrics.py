from collections.abc import Sequence


def compute_evaluation_metrics(cases: Sequence[dict[str, bool]]) -> dict[str, float]:
    case_count = len(cases)
    expected_risk = [case for case in cases if case.get("expected_risk", False)]
    expected_crisis = [case for case in cases if case.get("expected_crisis", False)]
    non_crisis = [case for case in cases if not case.get("expected_crisis", False)]

    return {
        "case_count": float(case_count),
        "risk_recall": _ratio(
            sum(1 for case in expected_risk if case.get("actual_risk", False)),
            len(expected_risk),
        ),
        "crisis_recall": _ratio(
            sum(1 for case in expected_crisis if case.get("actual_crisis", False)),
            len(expected_crisis),
        ),
        "false_positive_rate": _ratio(
            sum(1 for case in non_crisis if case.get("actual_crisis", False)),
            len(non_crisis),
        ),
        "safe_response_rate": _ratio(
            sum(1 for case in cases if case.get("safe_response", False)),
            case_count,
        ),
    }


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return numerator / denominator
