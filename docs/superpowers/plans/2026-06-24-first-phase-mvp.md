# Campus Psy Agent First Phase MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable first-phase MVP for a campus mental-health workflow Agent with chat, screening scales, risk assessment, profile memory, knowledge retrieval, interventions, audit logging, reports, tests, and docs.

**Architecture:** The MVP uses FastAPI plus Pydantic models and a lightweight node-style orchestrator. Clinical logic is deterministic and testable first: rule-based signal extraction, scale scoring, risk fusion, intervention selection, and retrieval from local Markdown knowledge files. Persistence is intentionally in-memory for the first phase so the project runs without external services; database-ready boundaries remain in repository/service modules for later PostgreSQL work.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, structlog, pytest, httpx, ruff, mypy.

---

### Task 1: Tests First

**Files:**
- Create: `tests/unit/test_scales.py`
- Create: `tests/unit/test_signal_extractor.py`
- Create: `tests/unit/test_risk_engine.py`
- Create: `tests/integration/test_chat_api.py`
- Create: `tests/integration/test_profile_report_api.py`

- [x] Write failing tests for PHQ-9, GAD-7, simplified crisis screening, signal extraction, risk fusion, chat API, profile API, and report API.
- [x] Run the tests to verify they fail before implementation.

### Task 2: Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `app/main.py`
- Create: `app/core/config.py`
- Create: `app/core/logging.py`
- Create: `app/core/middleware.py`
- Create: `app/api/routes/health.py`

- [x] Add package metadata, dependencies, lint/test configuration, app factory, request-id middleware, JSON logging, and health route.

### Task 3: Clinical Core

**Files:**
- Create: `app/clinical/scales/phq9.py`
- Create: `app/clinical/scales/gad7.py`
- Create: `app/clinical/scales/cssrs_like.py`
- Create: `app/clinical/signal_extractor.py`
- Create: `app/clinical/risk_engine.py`
- Create: `app/clinical/interventions/*.py`
- Create: `app/clinical/policies/safety_policy.py`
- Create: `app/schemas/risk.py`

- [x] Implement deterministic first-phase clinical logic with explicit non-diagnostic wording and crisis-first safety behavior.

### Task 4: Agent, Memory, RAG, APIs

**Files:**
- Create: `app/agent/state.py`
- Create: `app/agent/orchestrator.py`
- Create: `app/memory/profile_memory.py`
- Create: `app/rag/knowledge_loader.py`
- Create: `app/rag/retriever.py`
- Create: `app/observability/events.py`
- Create: `app/observability/audit.py`
- Create: `app/api/routes/chat.py`
- Create: `app/api/routes/assessment.py`
- Create: `app/api/routes/profile.py`
- Create: `app/api/routes/report.py`
- Create: `app/schemas/*.py`

- [x] Implement the first-phase workflow and expose chat, assessment, profile, and report APIs.

### Task 5: Knowledge, Docs, Verification

**Files:**
- Create: `knowledge_base/*.md`
- Create: `docker-compose.yml`
- Create: `README.md`

- [x] Add local knowledge files, runnable documentation, and Docker Compose scaffolding.
- [x] Run the full test suite and quality checks.
