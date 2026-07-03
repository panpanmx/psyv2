import argparse
import json
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    checks = [
        ("health", "GET", "/api/health", None),
        (
            "chat-normal",
            "POST",
            "/api/chat/messages",
            {
                "user_id": "smoke-user",
                "conversation_id": "smoke-conv",
                "message": "我最近两周考试压力很大，晚上睡不着。",
            },
        ),
        (
            "chat-crisis",
            "POST",
            "/api/chat/messages",
            {
                "user_id": "smoke-crisis",
                "conversation_id": "smoke-crisis-conv",
                "message": "我不想活了，已经想好了方式。",
            },
        ),
        (
            "phq9",
            "POST",
            "/api/assessments/phq9",
            {
                "user_id": "smoke-user",
                "conversation_id": "smoke-conv",
                "answers": [1, 1, 1, 1, 1, 1, 1, 1, 0],
            },
        ),
        (
            "gad7",
            "POST",
            "/api/assessments/gad7",
            {
                "user_id": "smoke-user",
                "conversation_id": "smoke-conv",
                "answers": [2, 2, 2, 1, 1, 1, 1],
            },
        ),
        (
            "crisis-screen",
            "POST",
            "/api/assessments/crisis",
            {
                "user_id": "smoke-crisis",
                "conversation_id": "smoke-crisis-conv",
                "answers": {"active_ideation": True, "plan": True, "means": False},
            },
        ),
        ("profile", "GET", "/api/profile/smoke-user", None),
        ("report", "GET", "/api/report/smoke-user/latest", None),
    ]

    for name, method, path, payload in checks:
        try:
            result = _request(base_url, method, path, payload)
        except (HTTPError, URLError, TimeoutError) as exc:
            print(f"[FAIL] {name}: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        print(f"[OK] {name}: {result.get('status', result.get('scale_type', 'ok'))}")


def _request(
    base_url: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None,
) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        f"{base_url}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=10) as response:
        body = response.read().decode("utf-8")
    parsed = json.loads(body)
    if not isinstance(parsed, dict):
        raise ValueError("response must be a JSON object")
    return parsed


if __name__ == "__main__":
    main()
