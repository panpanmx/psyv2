from app.clinical.scales.cssrs_like import score_crisis_screen
from app.clinical.scales.gad7 import score_gad7
from app.clinical.scales.phq9 import score_phq9


def test_phq9_scores_moderate_and_flags_item_9_crisis_review() -> None:
    result = score_phq9([1, 2, 1, 2, 1, 2, 1, 1, 1])

    assert result.score == 12
    assert result.severity == "moderate"
    assert result.item_9_positive is True
    assert "危机复核" in result.recommended_next_step


def test_gad7_scores_severe_anxiety() -> None:
    result = score_gad7([3, 3, 2, 2, 2, 2, 2])

    assert result.score == 16
    assert result.severity == "severe"
    assert "专业评估" in result.recommended_next_step


def test_crisis_screen_escalates_to_s4_for_plan_intent_and_preparation() -> None:
    result = score_crisis_screen(
        {
            "passive_ideation": True,
            "active_ideation": True,
            "method": True,
            "plan": True,
            "intent": True,
            "preparation": True,
            "recent_attempt": False,
            "protective_factors": ["想到妈妈会担心"],
        }
    )

    assert result.crisis_level == "s4"
    assert result.safety_response_required is True
    assert result.immediacy == "current"
