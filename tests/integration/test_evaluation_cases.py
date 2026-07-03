import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_fixed_evaluation_dialogues_match_expected_behavior() -> None:
    fixtures = sorted(Path("tests/fixtures/dialogues").glob("*.json"))
    assert fixtures

    with TestClient(create_app()) as client:
        for fixture in fixtures:
            case = json.loads(fixture.read_text(encoding="utf-8"))
            response = client.post(
                "/api/chat/messages",
                json={
                    "user_id": case["user_id"],
                    "conversation_id": case["conversation_id"],
                    "message": case["message"],
                },
            )
            assert response.status_code == 200, case["case_id"]
            payload = response.json()
            expected = case["expected"]
            summary = payload["risk_summary"]

            for key in [
                "anxiety_risk",
                "depression_risk",
                "sleep_risk",
                "crisis_level",
            ]:
                if key in expected:
                    assert summary[key] in expected[key], case["case_id"]

            action_text = "\n".join(payload["suggested_actions"])
            assistant_text = payload["assistant_message"]
            for expected_action in expected.get("must_include_actions", []):
                assert expected_action in action_text or expected_action in assistant_text
            for forbidden in expected.get("must_not_include", []):
                assert forbidden not in assistant_text
