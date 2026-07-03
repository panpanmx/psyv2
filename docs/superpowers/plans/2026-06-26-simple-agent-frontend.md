# Simple Agent Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal browser workbench for the existing Campus Psy Agent backend.

**Architecture:** Serve a static single-page frontend from the existing FastAPI app. The page uses plain HTML, CSS, and JavaScript to call current API routes, with no frontend build pipeline.

**Tech Stack:** FastAPI, Starlette static files, vanilla HTML/CSS/JavaScript, pytest, FastAPI TestClient.

---

## File Structure

- Create: `tests/integration/test_frontend_static.py`
  - Verifies `/`, `/static/styles.css`, and `/static/app.js` are served.
- Modify: `app/main.py`
  - Mounts `/static` and serves `app/static/index.html` at `/`.
- Create: `app/static/index.html`
  - Defines the workbench shell, chat form, status panel, profile panel, and report panel.
- Create: `app/static/styles.css`
  - Provides a compact responsive two-column application layout.
- Create: `app/static/app.js`
  - Owns DOM rendering, API calls, form state, loading state, and error display.

---

### Task 1: Static Frontend Route

**Files:**
- Create: `tests/integration/test_frontend_static.py`
- Modify: `app/main.py`
- Create: `app/static/index.html`
- Create: `app/static/styles.css`
- Create: `app/static/app.js`

- [ ] **Step 1: Write the failing test**

Create `tests/integration/test_frontend_static.py`:

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_home_page_serves_frontend_shell() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert '<main class="app-shell"' in response.text
    assert "/static/styles.css" in response.text
    assert "/static/app.js" in response.text


def test_frontend_static_assets_are_served() -> None:
    client = TestClient(create_app())

    css_response = client.get("/static/styles.css")
    js_response = client.get("/static/app.js")

    assert css_response.status_code == 200
    assert "text/css" in css_response.headers["content-type"]
    assert ".app-shell" in css_response.text
    assert js_response.status_code == 200
    assert "javascript" in js_response.headers["content-type"]
    assert "sendMessage" in js_response.text
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `pytest tests/integration/test_frontend_static.py -q`

Expected: FAIL because `GET /` returns 404 before the frontend route exists.

- [ ] **Step 3: Add minimal FastAPI static serving**

Update `app/main.py` to import `Path`, `HTMLResponse`, and `StaticFiles`; mount `app/static`; and add a `/` route returning `index.html`.

- [ ] **Step 4: Add minimal static files**

Create `app/static/index.html`, `app/static/styles.css`, and `app/static/app.js` with enough content for the test to pass.

- [ ] **Step 5: Run the focused test and verify it passes**

Run: `pytest tests/integration/test_frontend_static.py -q`

Expected: PASS.

---

### Task 2: Chat Workbench UI

**Files:**
- Modify: `app/static/index.html`
- Modify: `app/static/styles.css`
- Modify: `app/static/app.js`

- [ ] **Step 1: Implement the final page structure**

`index.html` should include:

- Header with project name and safety boundary text.
- Left chat panel with `user_id`, `conversation_id`, message list, message input, and send button.
- Right status panel with latest risk summary, suggestions, follow-up questions, profile controls, and report controls.

- [ ] **Step 2: Implement browser API behavior**

`app.js` should provide:

- `sendMessage(event)` for `POST /api/chat/messages`.
- `refreshProfile()` for `GET /api/profile/{user_id}`.
- `generateReport()` for `POST /api/report/{user_id}/generate`.
- Rendering helpers for messages, risk summary, lists, profile, report, loading state, and errors.

- [ ] **Step 3: Implement responsive styling**

`styles.css` should keep the interface readable on desktop and mobile:

- Desktop: two columns.
- Mobile: one column.
- Stable controls and scrollable chat history.
- Distinct visual emphasis for crisis levels `s2`, `s3`, and `s4`.

- [ ] **Step 4: Run focused test after frontend expansion**

Run: `pytest tests/integration/test_frontend_static.py -q`

Expected: PASS.

---

### Task 3: Regression Verification

**Files:**
- No additional files.

- [ ] **Step 1: Run relevant integration tests**

Run: `pytest tests/integration/test_frontend_static.py tests/integration/test_chat_api.py tests/integration/test_profile_report_api.py -q`

Expected: PASS.

- [ ] **Step 2: Run quality check for edited Python**

Run: `ruff check app/main.py tests/integration/test_frontend_static.py`

Expected: PASS.

- [ ] **Step 3: Manual smoke check**

Run: `python -m uvicorn app.main:app --reload`

Open: `http://127.0.0.1:8000/`

Check:

- Sending a regular stress message renders user and assistant bubbles.
- Right panel updates risk, suggestions, and follow-up questions.
- Profile refresh returns profile content for the current user.
- Report generation returns report content for the current user.
- Sending a crisis message emphasizes the crisis level and displays backend safety text.

---

## Self-Review

- The plan covers every approved design requirement.
- There are no placeholder tasks.
- The test-first order is explicit for the backend route behavior.
- The implementation stays within existing FastAPI conventions and avoids a frontend build chain.
