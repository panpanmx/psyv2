# Campus Psy Agent Second Phase Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Upgrade the first-phase in-memory MVP into a persistence-backed backend that stores conversations, messages, profiles, assessments, risk assessments, and high-risk audit events while keeping the existing API behavior stable.

**Architecture:** Add an async SQLAlchemy 2.0 data layer with PostgreSQL-ready models and SQLite-compatible tests. Introduce focused repositories for conversations, profiles, assessments, risks, and audits, then wire them into the existing `AppServices`, `AgentOrchestrator`, assessment routes, profile routes, and report routes. Keep clinical rules deterministic and unchanged in this phase; the goal is durable state and auditability, not LLM or vector-search expansion.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 async, Alembic, aiosqlite for tests, asyncpg for PostgreSQL, structlog, pytest, ruff, mypy, Docker Compose.

---

## Scope Decision

This phase deliberately focuses on persistence and auditability from the overall plan:

- Overall plan Task 2: database and base models.
- Overall plan Task 3: audit logging and event recording.
- Overall plan Task 8: profile and long-term memory persistence.
- Overall plan Task 12: chat API saving user and assistant messages.
- Overall plan Task 13: assessment API saving scale results and refreshing risk data.
- Overall plan Task 14: profile/report API reading durable state.
- Overall plan Task 16: Docker Compose environment variables for PostgreSQL.

This phase does not implement:

- LLM Provider.
- LangGraph node refactor.
- pgvector or true embedding retrieval.
- Redis workers or follow-up reminders.
- Doctor/admin backend.

Those become later phases after the persistence foundation is stable.

## File Structure

Create or modify these files:

- Modify: `pyproject.toml`  
  Add `sqlalchemy`, `alembic`, `asyncpg`, `aiosqlite`, and test helpers.

- Modify: `.env.example`  
  Add `DATABASE_URL`, `TEST_DATABASE_URL`, and persistence mode notes.

- Create: `app/db/base.py`  
  Define SQLAlchemy declarative base and shared timestamp mixin.

- Create: `app/db/session.py`  
  Configure async engine, sessionmaker, and FastAPI lifespan initialization helpers.

- Create: `app/db/models.py`  
  Define `User`, `Conversation`, `Message`, `UserProfile`, `Assessment`, `RiskAssessment`, and `AuditLog`.

- Create: `app/db/repositories/conversation_repo.py`  
  Create/find conversations and save messages with content hashes and risk snapshots.

- Create: `app/db/repositories/profile_repo.py`  
  Read/update `user_profiles.profile_json`, summaries, and risk trends.

- Create: `app/db/repositories/assessment_repo.py`  
  Save PHQ-9, GAD-7, and crisis screening submissions.

- Create: `app/db/repositories/risk_repo.py`  
  Save and fetch risk assessment rows.

- Create: `app/db/repositories/audit_repo.py`  
  Persist audit events, especially S2-S4 crisis events.

- Modify: `app/observability/audit.py`  
  Make `AuditLogger` repository-backed while keeping an in-memory fallback for tests that do not create a DB.

- Modify: `app/services.py`  
  Build repositories from the app sessionmaker and pass persistence services to orchestrator/routes.

- Modify: `app/agent/orchestrator.py`  
  Persist user message, assistant message, risk assessment, profile update, and audit events in the chat flow.

- Modify: `app/api/deps.py`  
  Add async DB session dependency if route-level sessions are needed.

- Modify: `app/api/routes/assessment.py`  
  Persist assessment submissions and create/update risk rows when crisis or PHQ-9 item 9 requires review.

- Modify: `app/api/routes/profile.py`  
  Read profiles and timelines from `ProfileRepository`.

- Modify: `app/api/routes/report.py`  
  Generate reports from persisted profile and latest risk state.

- Create: `alembic.ini`

- Create: `alembic/env.py`

- Create: `alembic/versions/2026_06_24_0001_initial_persistence.py`

- Modify: `docker-compose.yml`  
  Ensure API uses `DATABASE_URL=postgresql+asyncpg://campus:campus@postgres:5432/campus_psy_agent`.

- Create: `tests/conftest.py`  
  Provide an async SQLite test database and app factory fixture.

- Create: `tests/unit/test_models.py`

- Create: `tests/unit/test_repositories.py`

- Create: `tests/unit/test_audit_persistence.py`

- Create: `tests/integration/test_chat_persistence.py`

- Create: `tests/integration/test_assessment_persistence.py`

- Modify: `tests/integration/test_profile_report_api.py`

- Create: `docs/technical/phase-2-persistence-technical-doc.md` at the end of implementation.

---

### Task 1: Add Database Dependencies and Configuration

**Files:**
- Modify: `pyproject.toml`
- Modify: `.env.example`
- Modify: `app/core/config.py`
- Test: `tests/unit/test_config.py`

- [x] **Step 1: Write the failing config test**

Create `tests/unit/test_config.py`:

```python
from app.core.config import Settings


def test_settings_exposes_database_urls() -> None:
    settings = Settings(
        database_url="sqlite+aiosqlite:///./dev.db",
        test_database_url="sqlite+aiosqlite:///:memory:",
    )

    assert settings.database_url == "sqlite+aiosqlite:///./dev.db"
    assert settings.test_database_url == "sqlite+aiosqlite:///:memory:"
```

- [x] **Step 2: Run the config test and verify it fails**

Run:

```bash
python -m pytest tests/unit/test_config.py -q
```

Expected: failure because `Settings` does not yet define `database_url` and `test_database_url`.

- [x] **Step 3: Add dependencies**

Update `pyproject.toml` dependencies:

```toml
dependencies = [
  "alembic>=1.13.0",
  "asyncpg>=0.29.0",
  "fastapi>=0.115.0",
  "httpx>=0.27.0",
  "pydantic>=2.7.0",
  "pydantic-settings>=2.3.0",
  "sqlalchemy>=2.0.0",
  "structlog>=24.1.0",
  "uvicorn[standard]>=0.30.0",
]
```

Update dev dependencies:

```toml
dev = [
  "aiosqlite>=0.20.0",
  "mypy>=1.10.0",
  "pytest>=8.2.0",
  "pytest-asyncio>=0.23.0",
  "ruff>=0.5.0",
]
```

Add pytest asyncio config:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
asyncio_mode = "auto"
```

- [x] **Step 4: Extend settings**

Modify `app/core/config.py`:

```python
class Settings(BaseSettings):
    app_name: str = "Campus Psy Agent"
    app_env: str = "development"
    log_level: str = "INFO"
    audit_log_path: str = "logs/audit.jsonl"
    database_url: str = "sqlite+aiosqlite:///./campus_psy_agent.db"
    test_database_url: str = "sqlite+aiosqlite:///:memory:"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
```

Update `.env.example`:

```env
APP_NAME=Campus Psy Agent
APP_ENV=development
LOG_LEVEL=INFO
AUDIT_LOG_PATH=logs/audit.jsonl
DATABASE_URL=postgresql+asyncpg://campus:campus@localhost:5432/campus_psy_agent
TEST_DATABASE_URL=sqlite+aiosqlite:///:memory:
```

- [x] **Step 5: Run the config test and verify it passes**

Run:

```bash
python -m pytest tests/unit/test_config.py -q
```

Expected: `1 passed`.

- [x] **Step 6: Commit**

```bash
git add pyproject.toml .env.example app/core/config.py tests/unit/test_config.py
git commit -m "chore: add persistence configuration"
```

---

### Task 2: Create SQLAlchemy Base, Session, and Models

**Files:**
- Create: `app/db/__init__.py`
- Create: `app/db/base.py`
- Create: `app/db/session.py`
- Create: `app/db/models.py`
- Test: `tests/unit/test_models.py`

- [x] **Step 1: Write failing model tests**

Create `tests/unit/test_models.py`:

```python
from sqlalchemy import select

from app.db.models import (
    Assessment,
    AuditLog,
    Conversation,
    Message,
    RiskAssessment,
    User,
    UserProfile,
)


def test_models_define_expected_table_names() -> None:
    assert User.__tablename__ == "users"
    assert Conversation.__tablename__ == "conversations"
    assert Message.__tablename__ == "messages"
    assert UserProfile.__tablename__ == "user_profiles"
    assert Assessment.__tablename__ == "assessments"
    assert RiskAssessment.__tablename__ == "risk_assessments"
    assert AuditLog.__tablename__ == "audit_logs"


async def test_models_can_create_related_rows(db_session) -> None:
    user = User(id="u-001", nickname="小安", age_group="undergraduate", school_stage="大一")
    conversation = Conversation(id="c-001", user_id="u-001", title="初次倾诉")
    message = Message(
        id="m-001",
        conversation_id="c-001",
        role="user",
        content="最近睡不着",
        content_hash="hash_001",
        risk_snapshot={"crisis_level": "s0"},
    )
    profile = UserProfile(
        id="p-001",
        user_id="u-001",
        profile_json={"dominant_emotions": ["焦虑"]},
        latest_summary="近期主要情绪：焦虑。",
        risk_trend_json=[],
    )

    db_session.add_all([user, conversation, message, profile])
    await db_session.commit()

    result = await db_session.execute(select(Message).where(Message.id == "m-001"))
    saved = result.scalar_one()
    assert saved.content_hash == "hash_001"
    assert saved.risk_snapshot["crisis_level"] == "s0"
```

- [x] **Step 2: Add async database fixture**

Create `tests/conftest.py`:

```python
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

    await engine.dispose()
```

- [x] **Step 3: Run model tests and verify they fail**

Run:

```bash
python -m pytest tests/unit/test_models.py -q
```

Expected: failure because `app.db` modules do not exist.

- [x] **Step 4: Implement `app/db/base.py`**

```python
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
```

- [x] **Step 5: Implement `app/db/session.py`**

```python
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(settings.database_url, pool_pre_ping=True)


def create_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def session_scope(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with sessionmaker() as session:
        yield session
```

- [x] **Step 6: Implement `app/db/models.py`**

Use string UUIDs for first persistence phase to preserve current API compatibility. Use SQLAlchemy `JSON` rather than PostgreSQL-only `JSONB` so SQLite tests run. PostgreSQL still stores JSON correctly; a later migration can switch to JSONB if needed.

```python
from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    nickname: Mapped[str] = mapped_column(String(120), default="")
    age_group: Mapped[str] = mapped_column(String(40), default="unknown")
    school_stage: Mapped[str] = mapped_column(String(120), default="")


class Conversation(TimestampMixin, Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200), default="心理支持对话")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(128), index=True)
    risk_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[object] = mapped_column()
```

Then complete `Message.created_at` with `DateTime(timezone=True), default=utc_now`, and add the remaining models:

```python
class UserProfile(TimestampMixin, Base):
    __tablename__ = "user_profiles"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    profile_json: Mapped[dict] = mapped_column(JSON, default=dict)
    latest_summary: Mapped[str] = mapped_column(Text, default="")
    risk_trend_json: Mapped[list] = mapped_column(JSON, default=list)
    updated_by_message_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    scale_type: Mapped[str] = mapped_column(String(40), index=True)
    answers: Mapped[dict | list] = mapped_column(JSON)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    severity: Mapped[str] = mapped_column(String(80), default="")
    interpretation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[object] = mapped_column()


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    message_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    depression_risk: Mapped[str] = mapped_column(String(40), default="unknown")
    anxiety_risk: Mapped[str] = mapped_column(String(40), default="unknown")
    sleep_risk: Mapped[str] = mapped_column(String(40), default="unknown")
    crisis_level: Mapped[str] = mapped_column(String(10), default="s0")
    function_impairment_level: Mapped[str] = mapped_column(String(40), default="unknown")
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    recommended_next_step: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[object] = mapped_column()


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(120), index=True)
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(120), index=True)
    event_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[object] = mapped_column()
```

Replace the `created_at: Mapped[object]` placeholders in `Message`, `Assessment`, `RiskAssessment`, and `AuditLog` with the exact DateTime definition used in `TimestampMixin` or make them inherit a `CreatedAtMixin`. Do not leave untyped placeholder fields in final code.

- [x] **Step 7: Run model tests and verify they pass**

Run:

```bash
python -m pytest tests/unit/test_models.py -q
```

Expected: `2 passed`.

- [x] **Step 8: Commit**

```bash
git add app/db tests/conftest.py tests/unit/test_models.py
git commit -m "feat: add persistence models"
```

---

### Task 3: Add Alembic Migration

**Files:**
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/versions/2026_06_24_0001_initial_persistence.py`
- Test: `tests/unit/test_alembic_metadata.py`

- [x] **Step 1: Write failing migration metadata test**

Create `tests/unit/test_alembic_metadata.py`:

```python
from app.db.base import Base


def test_initial_metadata_contains_required_tables() -> None:
    assert {
        "users",
        "conversations",
        "messages",
        "user_profiles",
        "assessments",
        "risk_assessments",
        "audit_logs",
    } <= set(Base.metadata.tables)
```

- [x] **Step 2: Run test and verify table coverage**

Run:

```bash
python -m pytest tests/unit/test_alembic_metadata.py -q
```

Expected: pass after Task 2; if it fails, import `app.db.models` inside `app/db/__init__.py` or the test so metadata is populated.

- [x] **Step 3: Add Alembic config**

Create `alembic.ini` with:

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = sqlite+aiosqlite:///./campus_psy_agent.db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

Create `alembic/env.py` that imports `Base.metadata` and reads `DATABASE_URL` from settings.

- [x] **Step 4: Add initial migration**

Create `alembic/versions/2026_06_24_0001_initial_persistence.py` with `upgrade()` creating all seven tables and `downgrade()` dropping them in reverse dependency order.

- [x] **Step 5: Verify Alembic can inspect the migration**

Run:

```bash
python -m alembic history
```

Expected: output includes `2026_06_24_0001`.

- [x] **Step 6: Commit**

```bash
git add alembic.ini alembic tests/unit/test_alembic_metadata.py
git commit -m "feat: add initial persistence migration"
```

---

### Task 4: Conversation and Message Repository

**Files:**
- Create: `app/db/repositories/__init__.py`
- Create: `app/db/repositories/conversation_repo.py`
- Test: `tests/unit/test_repositories.py`

- [x] **Step 1: Write failing repository tests**

Create `tests/unit/test_repositories.py` with:

```python
from sqlalchemy import select

from app.db.models import Message
from app.db.repositories.conversation_repo import ConversationRepository


async def test_conversation_repo_creates_user_conversation_and_messages(db_session) -> None:
    repo = ConversationRepository(db_session)

    await repo.ensure_user(user_id="u-001")
    await repo.ensure_conversation(user_id="u-001", conversation_id="c-001")
    user_message = await repo.save_message(
        conversation_id="c-001",
        role="user",
        content="我最近睡不着",
        risk_snapshot={"crisis_level": "s0"},
    )
    assistant_message = await repo.save_message(
        conversation_id="c-001",
        role="assistant",
        content="听起来你最近很辛苦。",
        risk_snapshot={"crisis_level": "s0"},
    )
    await db_session.commit()

    assert user_message.content_hash != assistant_message.content_hash
    result = await db_session.execute(select(Message).order_by(Message.created_at))
    messages = list(result.scalars())
    assert [message.role for message in messages] == ["user", "assistant"]
    assert messages[0].content_hash
```

- [x] **Step 2: Run repository tests and verify failure**

Run:

```bash
python -m pytest tests/unit/test_repositories.py -q
```

Expected: import failure for `ConversationRepository`.

- [x] **Step 3: Implement repository**

`ConversationRepository` responsibilities:

- `ensure_user(user_id: str, nickname: str = "", age_group: str = "unknown", school_stage: str = "") -> User`
- `ensure_conversation(user_id: str, conversation_id: str, title: str = "心理支持对话") -> Conversation`
- `save_message(conversation_id: str, role: str, content: str, risk_snapshot: dict) -> Message`
- `recent_messages(conversation_id: str, limit: int = 10) -> list[Message]`

Content hash implementation:

```python
from hashlib import sha256


def content_hash(content: str) -> str:
    return sha256(content.encode("utf-8")).hexdigest()
```

Use `uuid4().hex` for message IDs:

```python
message_id = f"msg_{uuid4().hex}"
```

- [x] **Step 4: Run repository tests and verify pass**

Run:

```bash
python -m pytest tests/unit/test_repositories.py -q
```

Expected: repository tests pass.

- [x] **Step 5: Commit**

```bash
git add app/db/repositories tests/unit/test_repositories.py
git commit -m "feat: add conversation repository"
```

---

### Task 5: Profile Repository and Persistent Profile Memory

**Files:**
- Create: `app/db/repositories/profile_repo.py`
- Modify: `app/memory/profile_memory.py`
- Test: `tests/unit/test_profile_persistence.py`

- [x] **Step 1: Write failing profile persistence test**

Create `tests/unit/test_profile_persistence.py`:

```python
from app.clinical.risk_engine import RiskEngine
from app.clinical.signal_extractor import SignalExtractor
from app.db.repositories.conversation_repo import ConversationRepository
from app.db.repositories.profile_repo import ProfileRepository


async def test_profile_repo_updates_profile_and_risk_timeline(db_session) -> None:
    conversation_repo = ConversationRepository(db_session)
    await conversation_repo.ensure_user("u-profile")

    signals = SignalExtractor().extract("最近两周很低落，也不想见同学，但愿意找朋友聊聊。")
    risk = RiskEngine().assess(signals=signals)

    repo = ProfileRepository(db_session)
    await repo.update_profile(user_id="u-profile", signals=signals, risk=risk, message_id="msg_001")
    await db_session.commit()

    profile = await repo.get_profile("u-profile")
    timeline = await repo.get_timeline("u-profile")

    assert "低落" in profile["dominant_emotions"]
    assert "朋友支持" in profile["protective_factors"]
    assert timeline[-1]["depression_risk"] == "moderate"
```

- [x] **Step 2: Run profile persistence test and verify failure**

Run:

```bash
python -m pytest tests/unit/test_profile_persistence.py -q
```

Expected: import failure for `ProfileRepository`.

- [x] **Step 3: Implement profile repository**

`ProfileRepository` responsibilities:

- `update_profile(user_id: str, signals: ExtractedSignals, risk: RiskResult, message_id: str | None) -> None`
- `get_profile(user_id: str) -> dict[str, list[str]]`
- `get_summary(user_id: str) -> str`
- `get_latest_risk(user_id: str) -> RiskSummary | None`
- `get_timeline(user_id: str) -> list[dict[str, str]]`

Reuse first-phase merge semantics:

```python
def merge_unique(target: list[str], values: list[str]) -> list[str]:
    for value in values:
        if value not in target:
            target.append(value)
    return target
```

Default profile shape must match first phase:

```python
{
    "dominant_emotions": [],
    "stressors": [],
    "symptoms": [],
    "function_impairment": [],
    "protective_factors": [],
    "risk_factors": [],
}
```

- [x] **Step 4: Preserve in-memory fallback**

Keep existing `ProfileMemory` for non-DB tests, but make it optional in services. Do not delete it in this phase. Add a short docstring explaining it is a fallback and fast test utility.

- [x] **Step 5: Run profile persistence test and verify pass**

Run:

```bash
python -m pytest tests/unit/test_profile_persistence.py -q
```

Expected: profile persistence test passes.

- [x] **Step 6: Commit**

```bash
git add app/db/repositories/profile_repo.py app/memory/profile_memory.py tests/unit/test_profile_persistence.py
git commit -m "feat: persist user profiles"
```

---

### Task 6: Risk and Audit Repositories

**Files:**
- Create: `app/db/repositories/risk_repo.py`
- Create: `app/db/repositories/audit_repo.py`
- Modify: `app/observability/audit.py`
- Test: `tests/unit/test_audit_persistence.py`

- [x] **Step 1: Write failing audit and risk persistence tests**

Create `tests/unit/test_audit_persistence.py`:

```python
from sqlalchemy import select

from app.clinical.risk_engine import RiskEngine
from app.clinical.signal_extractor import SignalExtractor
from app.db.models import AuditLog, RiskAssessment
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.conversation_repo import ConversationRepository
from app.db.repositories.risk_repo import RiskRepository


async def test_risk_repo_persists_evidence_and_next_step(db_session) -> None:
    conversation_repo = ConversationRepository(db_session)
    await conversation_repo.ensure_user("u-risk")
    await conversation_repo.ensure_conversation("u-risk", "c-risk")

    signals = SignalExtractor().extract("我不想活了，已经想好了方式。")
    risk = RiskEngine().assess(signals=signals)

    repo = RiskRepository(db_session)
    saved = await repo.save_risk(
        user_id="u-risk",
        conversation_id="c-risk",
        message_id="msg-risk",
        risk=risk,
    )
    await db_session.commit()

    result = await db_session.execute(select(RiskAssessment).where(RiskAssessment.id == saved.id))
    row = result.scalar_one()
    assert row.crisis_level == "s3"
    assert row.recommended_next_step["route"] == "crisis"


async def test_audit_repo_persists_safety_escalation(db_session) -> None:
    repo = AuditRepository(db_session)
    await repo.record_event(
        event_type="safety.escalation.triggered",
        request_id="req_001",
        user_id="u-risk",
        conversation_id="c-risk",
        payload={"crisis_level": "s3"},
    )
    await db_session.commit()

    result = await db_session.execute(select(AuditLog))
    row = result.scalar_one()
    assert row.event_type == "safety.escalation.triggered"
    assert row.event_payload["crisis_level"] == "s3"
```

- [x] **Step 2: Run tests and verify failure**

Run:

```bash
python -m pytest tests/unit/test_audit_persistence.py -q
```

Expected: import failure for `RiskRepository` and `AuditRepository`.

- [x] **Step 3: Implement risk repository**

`RiskRepository` responsibilities:

- `save_risk(user_id, conversation_id, message_id, risk) -> RiskAssessment`
- `latest_for_user(user_id) -> RiskSummary | None`
- `timeline_for_user(user_id) -> list[dict[str, str]]`

Persist:

- all risk enum fields
- `evidence`
- `recommended_next_step`

- [x] **Step 4: Implement audit repository**

`AuditRepository.record_event()` signature:

```python
async def record_event(
    self,
    *,
    event_type: str,
    request_id: str,
    user_id: str | None,
    conversation_id: str | None,
    payload: dict[str, object],
) -> AuditLog:
```

Use `audit_<uuid>` as row ID.

- [x] **Step 5: Adapt `AuditLogger`**

Modify `app/observability/audit.py` so:

- Existing `record_event(event_type, payload)` continues to work synchronously for first-phase tests.
- Add `async_record_event(event_type, payload, repository)` for DB-backed code paths.
- S2-S4 code paths in orchestrator can call async repository directly or through this method.

- [x] **Step 6: Run tests and verify pass**

Run:

```bash
python -m pytest tests/unit/test_audit_persistence.py -q
```

Expected: risk and audit persistence tests pass.

- [x] **Step 7: Commit**

```bash
git add app/db/repositories/risk_repo.py app/db/repositories/audit_repo.py app/observability/audit.py tests/unit/test_audit_persistence.py
git commit -m "feat: persist risk and audit events"
```

---

### Task 7: Wire Database Session into App Services

**Files:**
- Modify: `app/main.py`
- Modify: `app/services.py`
- Modify: `app/api/deps.py`
- Test: `tests/integration/test_app_database_lifespan.py`

- [x] **Step 1: Write failing app database lifespan test**

Create `tests/integration/test_app_database_lifespan.py`:

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_app_exposes_services_with_sessionmaker() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert hasattr(app.state.services, "sessionmaker")
```

- [x] **Step 2: Run test and verify failure**

Run:

```bash
python -m pytest tests/integration/test_app_database_lifespan.py -q
```

Expected: failure because services do not expose `sessionmaker`.

- [x] **Step 3: Update services**

Modify `AppServices` to accept and expose:

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class AppServices:
    def __init__(self, settings: Settings, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self.sessionmaker = sessionmaker
        self.profile_memory = ProfileMemory()
        self.audit_logger = AuditLogger(settings.audit_log_path)
        self.retriever = KnowledgeRetriever()
        self.agent = AgentOrchestrator(
            profile_memory=self.profile_memory,
            retriever=self.retriever,
            audit_logger=self.audit_logger,
            sessionmaker=sessionmaker,
        )
```

- [x] **Step 4: Update app lifespan**

In `create_app()`:

- Create engine from settings.
- Create sessionmaker.
- Create database tables for SQLite development and tests by calling `Base.metadata.create_all` in lifespan when `database_url` starts with `sqlite+`.
- Dispose engine on shutdown.

Keep Alembic as the production migration path for PostgreSQL.

- [x] **Step 5: Add DB session dependency**

In `app/api/deps.py`:

```python
from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    services = get_services(request)
    async with services.sessionmaker() as session:
        yield session
```

- [x] **Step 6: Run lifespan test and verify pass**

Run:

```bash
python -m pytest tests/integration/test_app_database_lifespan.py -q
```

Expected: app exposes services with `sessionmaker`.

- [x] **Step 7: Commit**

```bash
git add app/main.py app/services.py app/api/deps.py tests/integration/test_app_database_lifespan.py
git commit -m "feat: wire database session into app"
```

---

### Task 8: Persist Chat Flow

**Files:**
- Modify: `app/agent/orchestrator.py`
- Modify: `app/api/routes/chat.py`
- Test: `tests/integration/test_chat_persistence.py`

- [x] **Step 1: Write failing chat persistence test**

Create `tests/integration/test_chat_persistence.py`:

```python
from sqlalchemy import select
from fastapi.testclient import TestClient

from app.db.models import AuditLog, Message, RiskAssessment, UserProfile
from app.main import create_app


def test_chat_persists_messages_risk_profile_and_crisis_audit() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/api/chat/messages",
            json={
                "user_id": "u-crisis",
                "conversation_id": "c-crisis",
                "message": "我不想活了，已经想好了方式，也准备好了工具。",
            },
        )
        assert response.status_code == 200

        async def inspect_db() -> tuple[int, int, int, int]:
            async with app.state.services.sessionmaker() as session:
                messages = (await session.execute(select(Message))).scalars().all()
                risks = (await session.execute(select(RiskAssessment))).scalars().all()
                profiles = (await session.execute(select(UserProfile))).scalars().all()
                audits = (await session.execute(select(AuditLog))).scalars().all()
                return len(messages), len(risks), len(profiles), len(audits)

        message_count, risk_count, profile_count, audit_count = client.portal.call(inspect_db)

    assert message_count == 2
    assert risk_count == 1
    assert profile_count == 1
    assert audit_count >= 2
```

If `client.portal.call` is not available in the installed TestClient, replace the inspection block with an async helper run through `anyio.from_thread.run`.

- [x] **Step 2: Run test and verify failure**

Run:

```bash
python -m pytest tests/integration/test_chat_persistence.py -q
```

Expected: failure because chat flow does not persist rows.

- [x] **Step 3: Make orchestrator persistence-aware**

Modify `AgentOrchestrator.__init__` to accept:

```python
sessionmaker: async_sessionmaker[AsyncSession] | None = None
```

Keep `handle_chat()` API stable for current route, but internally call an async implementation through `anyio.run` only if needed, or convert route to async and make `handle_chat()` async. Prefer converting to async:

```python
async def handle_chat(self, request: ChatRequest, *, request_id: str) -> ChatResponse:
    ...
```

Then update route:

```python
@router.post("/messages", response_model=ChatResponse)
async def create_message(...) -> ChatResponse:
    return await services.agent.handle_chat(payload, request_id=request_id)
```

- [x] **Step 4: Persist chat rows**

Within `handle_chat()` DB path:

1. Open session.
2. Ensure user.
3. Ensure conversation.
4. Save user message with empty or preliminary risk snapshot.
5. Extract signals and assess risk.
6. Save risk assessment using user message ID.
7. Generate assistant message.
8. Save assistant message with risk summary snapshot.
9. Update profile using assistant or user message ID.
10. Persist `risk.assessment.completed`.
11. Persist `safety.escalation.triggered` when crisis level is `s2/s3/s4`.
12. Commit once at the end.

If any DB write fails, roll back and raise the exception. Do not swallow persistence failures silently in this phase.

- [x] **Step 5: Keep tests for first-phase behavior passing**

Run:

```bash
python -m pytest tests/integration/test_chat_api.py tests/integration/test_chat_persistence.py -q
```

Expected: existing chat response tests still pass, new persistence test passes.

- [x] **Step 6: Commit**

```bash
git add app/agent/orchestrator.py app/api/routes/chat.py tests/integration/test_chat_persistence.py
git commit -m "feat: persist chat workflow"
```

---

### Task 9: Persist Assessment API Submissions

**Files:**
- Create: `app/db/repositories/assessment_repo.py`
- Modify: `app/api/routes/assessment.py`
- Test: `tests/integration/test_assessment_persistence.py`

- [x] **Step 1: Write failing assessment persistence tests**

Create `tests/integration/test_assessment_persistence.py`:

```python
from sqlalchemy import select
from fastapi.testclient import TestClient

from app.db.models import Assessment, RiskAssessment
from app.main import create_app


def test_phq9_submission_is_persisted_and_item_9_creates_crisis_review_risk() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/api/assessments/phq9",
            json={
                "user_id": "u-scale",
                "conversation_id": "c-scale",
                "answers": [1, 2, 1, 2, 1, 2, 1, 1, 1],
            },
        )
        assert response.status_code == 200

        async def inspect_db() -> tuple[str, int]:
            async with app.state.services.sessionmaker() as session:
                assessment = (await session.execute(select(Assessment))).scalar_one()
                risks = (await session.execute(select(RiskAssessment))).scalars().all()
                return assessment.scale_type, len(risks)

        scale_type, risk_count = client.portal.call(inspect_db)

    assert scale_type == "phq9"
    assert risk_count == 1
```

- [x] **Step 2: Run test and verify failure**

Run:

```bash
python -m pytest tests/integration/test_assessment_persistence.py -q
```

Expected: failure because assessment routes do not persist rows.

- [x] **Step 3: Implement assessment repository**

`AssessmentRepository` responsibilities:

- `save_assessment(user_id, conversation_id, scale_type, answers, score, severity, interpretation) -> Assessment`
- `list_for_user(user_id, limit=20) -> list[Assessment]`
- `latest_for_user(user_id, scale_type) -> Assessment | None`

- [x] **Step 4: Make assessment routes async and DB-backed**

For PHQ-9:

- Score existing answers.
- Ensure user exists.
- Ensure conversation if `conversation_id` is provided.
- Save assessment.
- If `item_9_positive`, save a `RiskAssessment` row with:
  - `crisis_level = "s2"`
  - evidence containing `{"source": "phq9", "detail": "PHQ-9 第 9 题阳性"}`
  - `recommended_next_step.route = "crisis_review"`

For GAD-7:

- Save assessment.
- If severity is `moderate` or `severe`, save or update risk row with anxiety risk at the same level.

For crisis:

- Save assessment with `score=None`.
- Save risk row with returned crisis level and safety next step.
- Persist safety audit for `s2/s3/s4`.

- [x] **Step 5: Run tests and verify pass**

Run:

```bash
python -m pytest tests/integration/test_assessment_persistence.py tests/unit/test_scales.py -q
```

Expected: assessment persistence and scale tests pass.

- [x] **Step 6: Commit**

```bash
git add app/db/repositories/assessment_repo.py app/api/routes/assessment.py tests/integration/test_assessment_persistence.py
git commit -m "feat: persist assessment submissions"
```

---

### Task 10: Read Profile and Reports from Persistent State

**Files:**
- Modify: `app/api/routes/profile.py`
- Modify: `app/api/routes/report.py`
- Modify: `tests/integration/test_profile_report_api.py`

- [x] **Step 1: Update profile/report integration test**

Modify `tests/integration/test_profile_report_api.py` so it still:

1. Sends a chat request.
2. Calls `GET /api/profile/{user_id}`.
3. Calls `GET /api/report/{user_id}/latest`.
4. Asserts profile and report data survive repository reads.

Add an assertion that timeline is persisted:

```python
timeline_response = client.get("/api/profile/u-profile/timeline")
assert timeline_response.status_code == 200
assert timeline_response.json()["risk_timeline"]
```

- [x] **Step 2: Run test and verify failure if routes still use memory only**

Run:

```bash
python -m pytest tests/integration/test_profile_report_api.py -q
```

Expected: failure until profile/report routes use repositories.

- [x] **Step 3: Update profile routes**

Make route handlers async and use `ProfileRepository`:

```python
@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_profile(...) -> UserProfileResponse:
    async with services.sessionmaker() as session:
        repo = ProfileRepository(session)
        return UserProfileResponse(
            user_id=user_id,
            profile=await repo.get_profile(user_id),
            latest_summary=await repo.get_summary(user_id),
        )
```

- [x] **Step 4: Update report routes**

Use:

- `ProfileRepository.get_profile()`
- `ProfileRepository.get_summary()`
- `RiskRepository.latest_for_user()`

Keep response schema unchanged.

- [x] **Step 5: Run tests and verify pass**

Run:

```bash
python -m pytest tests/integration/test_profile_report_api.py -q
```

Expected: profile and report tests pass with persistent reads.

- [x] **Step 6: Commit**

```bash
git add app/api/routes/profile.py app/api/routes/report.py tests/integration/test_profile_report_api.py
git commit -m "feat: read profiles and reports from persistence"
```

---

### Task 11: Docker Compose and README Persistence Updates

**Files:**
- Modify: `docker-compose.yml`
- Modify: `README.md`
- Modify: `.env.example`
- Test: manual command documentation

- [x] **Step 1: Update Compose environment**

In `docker-compose.yml`, add API environment:

```yaml
environment:
  DATABASE_URL: postgresql+asyncpg://campus:campus@postgres:5432/campus_psy_agent
```

Keep PostgreSQL service:

```yaml
postgres:
  image: pgvector/pgvector:pg16
```

- [x] **Step 2: Update README**

Add a "Persistence" section:

```markdown
## Persistence

The app uses SQLAlchemy async. Local development defaults to SQLite if `DATABASE_URL` is not set.
Docker Compose uses PostgreSQL:

```bash
docker compose up api postgres redis
```

Run migrations:

```bash
alembic upgrade head
```
```

- [x] **Step 3: Document local test database**

Add:

```markdown
Tests use `sqlite+aiosqlite:///:memory:` through `tests/conftest.py`.
```

- [x] **Step 4: Commit**

```bash
git add docker-compose.yml README.md .env.example
git commit -m "docs: document persistence runtime"
```

---

### Task 12: Phase 2 Technical Documentation

**Files:**
- Create: `docs/technical/phase-2-persistence-technical-doc.md`
- Modify: `docs/technical/README.md`

- [x] **Step 1: Write phase documentation**

Create `docs/technical/phase-2-persistence-technical-doc.md` with these sections:

- Phase goal and scope.
- Database architecture.
- Table descriptions.
- Repository responsibilities.
- Chat persistence sequence.
- Assessment persistence sequence.
- Audit guarantees.
- Testing strategy.
- How to run migrations.
- Known limitations and next phase recommendations.

- [x] **Step 2: Update technical docs index**

Modify `docs/technical/README.md` to include:

```markdown
- [第二阶段持久化技术文档](./phase-2-persistence-technical-doc.md)
```

- [x] **Step 3: Commit**

```bash
git add docs/technical/README.md docs/technical/phase-2-persistence-technical-doc.md
git commit -m "docs: add phase 2 persistence technical documentation"
```

---

### Task 13: Final Verification

**Files:**
- No new files.

- [x] **Step 1: Run focused persistence tests**

Run:

```bash
python -m pytest \
  tests/unit/test_models.py \
  tests/unit/test_repositories.py \
  tests/unit/test_profile_persistence.py \
  tests/unit/test_audit_persistence.py \
  tests/integration/test_chat_persistence.py \
  tests/integration/test_assessment_persistence.py \
  tests/integration/test_profile_report_api.py \
  -q
```

Expected: all selected tests pass.

- [x] **Step 2: Run full test suite**

Run:

```bash
python -m pytest -q
```

Expected: all tests pass.

- [x] **Step 3: Run lint**

Run:

```bash
python -m ruff check .
```

Expected: `All checks passed!`

- [x] **Step 4: Run type checking**

Run:

```bash
python -m mypy app
```

Expected: `Success: no issues found`.

- [x] **Step 5: Run a manual HTTP smoke test**

Start:

```bash
python -m uvicorn app.main:app --reload
```

Then run:

```bash
curl -sS http://127.0.0.1:8000/api/health
curl -sS -X POST http://127.0.0.1:8000/api/chat/messages \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"u-smoke","conversation_id":"c-smoke","message":"我最近两周考试压力很大，晚上总是睡不着。"}'
curl -sS http://127.0.0.1:8000/api/profile/u-smoke
curl -sS http://127.0.0.1:8000/api/report/u-smoke/latest
```

Expected:

- health returns `{"status":"ok"}`.
- chat returns anxiety and sleep risk.
- profile returns stored emotions/stressors/symptoms.
- report returns latest risk and recommended interventions.

- [x] **Step 6: Commit final plan checkbox updates if needed**

When all implementation tasks pass, update this plan file checkboxes from `[ ]` to `[x]` and commit:

```bash
git add docs/superpowers/plans/2026-06-24-second-phase-persistence.md
git commit -m "docs: mark phase 2 plan complete"
```

---

## Self-Review Notes

- Spec coverage: this plan covers persistence models, audit logs, chat saving, assessment saving, profile/report persistent reads, Docker runtime, and phase technical docs. It intentionally leaves LLM Provider, LangGraph, and pgvector for later phases.
- Placeholder scan: no implementation step is left as an unspecified "add later" item. Where final code choices matter, the plan gives exact signatures, expected behavior, and verification commands.
- Type consistency: repository methods consistently use string IDs, `RiskResult`, `RiskSummary`, `ExtractedSignals`, and SQLAlchemy async sessions.

