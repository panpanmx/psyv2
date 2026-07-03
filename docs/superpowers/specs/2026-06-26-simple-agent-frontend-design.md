# Simple Agent Frontend Design

## Goal

Build a minimal browser interface for Campus Psy Agent so a user can try the existing backend without curl or API tooling. The frontend should focus on the agent workflow that is already implemented: conversation, risk summary, suggested actions, follow-up questions, profile lookup, and report generation.

## Scope

The first version is a lightweight single-page workbench. It will not introduce authentication, a user directory, a build pipeline, charting, editable assessment forms, or multi-conversation history. Those can be added later after the core interaction is useful.

In scope:

- A home page served by FastAPI at `/`.
- Static CSS and JavaScript served from `app/static`.
- A chat panel that sends messages to `POST /api/chat/messages`.
- A right-side status panel that displays the latest `risk_summary`, `suggested_actions`, and `follow_up_questions`.
- Buttons to refresh `GET /api/profile/{user_id}` and generate `POST /api/report/{user_id}/generate`.
- Clear loading and error states.
- A small integration test that verifies the HTML page and static assets are served.

Out of scope:

- React, Vue, Vite, or other frontend build tooling.
- Full PHQ-9, GAD-7, or crisis questionnaire UI.
- Authentication or role-based access.
- Persisted browser-side conversation management beyond the currently visible session.

## User Experience

The page uses a two-column workbench layout.

The left column is the conversation area. It contains compact inputs for `user_id` and `conversation_id`, a scrollable message list, and a message composer. Sending a non-empty message appends the user message, calls the chat API, then appends the assistant response.

The right column is the status area. It shows the latest risk levels for depression, anxiety, sleep, crisis, and functional impairment. It also shows backend-provided suggested actions and follow-up questions. When the crisis level is `s2`, `s3`, or `s4`, the crisis field is emphasized while still relying on the backend response text for the actual safety wording.

The status area also contains profile and report controls. Refreshing the profile displays `latest_summary` and profile categories. Generating a report displays `profile_summary`, evidence, recommended interventions, and whether offline help is recommended.

## Architecture

The implementation extends the existing FastAPI app with static file serving and a simple home route. No new service layer is needed because the frontend calls existing API routes from the browser.

Files:

- `app/main.py` mounts static files and registers the home page route.
- `app/static/index.html` contains the semantic page structure.
- `app/static/styles.css` contains responsive workbench styling.
- `app/static/app.js` owns browser state, API calls, rendering, and error handling.
- `tests/integration/test_frontend_static.py` verifies the page and assets are reachable.

The JavaScript keeps a small in-memory state object:

- `userId`
- `conversationId`
- visible messages
- latest chat response
- latest profile response
- latest report response

## Data Flow

Chat flow:

1. User enters a message.
2. Browser validates that the message, `user_id`, and `conversation_id` are non-empty.
3. Browser sends `POST /api/chat/messages` with `{ user_id, conversation_id, message }`.
4. On success, browser renders `assistant_message` and updates the right panel from `risk_summary`, `suggested_actions`, and `follow_up_questions`.
5. On failure, browser shows a concise error banner and leaves existing content intact.

Profile flow:

1. User clicks "Refresh profile".
2. Browser sends `GET /api/profile/{user_id}`.
3. Browser renders `latest_summary` and non-empty profile category lists.

Report flow:

1. User clicks "Generate report".
2. Browser sends `POST /api/report/{user_id}/generate`.
3. Browser renders `profile_summary`, `risk_summary`, `evidence_summary`, `recommended_interventions`, and `offline_help_recommended`.

## Error Handling

The frontend treats backend errors as recoverable UI states. It shows one visible error banner, re-enables controls, and keeps the previous successful data on screen. Empty messages are rejected before any API request. Loading buttons are disabled while their request is in flight.

## Testing

Add integration coverage with FastAPI `TestClient`:

- `GET /` returns HTML containing the app root and references to CSS/JS assets.
- `GET /static/styles.css` returns CSS.
- `GET /static/app.js` returns JavaScript.

Manual smoke check:

- Start the backend with `python -m uvicorn app.main:app --reload`.
- Open `http://127.0.0.1:8000/`.
- Send a low-risk academic stress message and confirm the chat and status panel update.
- Send a high-risk crisis message and confirm crisis emphasis appears and backend safety text is visible.

## Self-Review

- No placeholders remain.
- Scope is intentionally limited to a single-page workbench.
- The architecture uses the existing FastAPI app and current API contracts.
- Crisis handling is visual emphasis only; safety wording stays owned by backend responses.
