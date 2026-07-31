# SwasthiQ EOD Billing & Analytics Agent

Implementation workspace for a Python REST API and React interface that converts a clinic-day billing log into deterministic reconciliation, analytics, and a figure-traced owner-facing narrative.

## Current status

- Step 1: Requirements specification complete.
- Step 2: Architecture, API contract, data model, and user flows complete.
- Step 3: Deterministic backend stabilized for Prompt 1.
- Prompt 2: Persistence, Alembic migrations, hashing/versioning, REST contract, and OpenAPI artifact finalized.
- Prompt 3: LangChain + NVIDIA `ChatNVIDIA` narrative provider integrated behind deterministic grounding and safe fallback.
- Pre-coding package for Steps 4–7: complete.
- Remaining coding: React interface, CI, deployment, and production hardening outside Prompt 1 scope.

## Locked stack

- Backend: Python, FastAPI, Pydantic v2, SQLAlchemy 2, SQLite.
- Agentic layer: LangChain, `langchain-nvidia-ai-endpoints`, `ChatNVIDIA`, NVIDIA Nemotron.
- Frontend: React, Vite, TypeScript, React Router, Recharts.
- Deployment plan: Vercel frontend and Railway backend with a persistent volume for SQLite.

## Backend configuration

The deterministic backend uses integer paise for all money calculations and does not call an LLM. Important local settings are documented in [`backend/.env.example`](backend/.env.example):

- `MAX_RECORDS_PER_REQUEST=10000`
- `MAX_REQUEST_BODY_BYTES=5242880`
- `STORE_REJECTED_RAW_ROWS=false`
- `LLM_ENABLED=true`
- `LLM_PROVIDER=nvidia`
- `NVIDIA_API_KEY=`
- `NVIDIA_MODEL=nvidia/nemotron-3-nano-30b-a3b`
- `NVIDIA_BASE_URL=`
- `LLM_TIMEOUT_SECONDS=25`
- `LLM_MAX_TOKENS=700`
- `LLM_TEMPERATURE=0`
- `LLM_TRANSPORT_RETRIES=1`

Rejected-row API responses expose only safe, actionable issue fields. Complete malformed source rows are not persisted unless `STORE_REJECTED_RAW_ROWS=true` is explicitly enabled for local development/testing.

Missing NVIDIA credentials do not block app startup. Narrative generation falls back to deterministic, trace-validated text until credentials are configured.

## Backend verification

From `backend/`, run:

```bash
python3 -m pytest -q
python3 -m pytest -m "not live_nvidia" -q
python3 -m pytest --cov=app --cov-branch --cov-report=term-missing --cov-fail-under=90
python3 -c "from app.main import create_app; create_app()"
```

On this machine, `python` is not available on `PATH`; use `python3`.

Prompt 1 stabilization details are recorded in [`docs/implementation/01_BACKEND_STABILIZATION_REPORT.md`](docs/implementation/01_BACKEND_STABILIZATION_REPORT.md).

Prompt 2 persistence and API contract details are recorded in [`docs/implementation/02_PERSISTENCE_AND_API_CONTRACT_REPORT.md`](docs/implementation/02_PERSISTENCE_AND_API_CONTRACT_REPORT.md).

Prompt 3 LangChain + NVIDIA provider details are recorded in [`docs/implementation/03_LANGCHAIN_NVIDIA_INTEGRATION_REPORT.md`](docs/implementation/03_LANGCHAIN_NVIDIA_INTEGRATION_REPORT.md).

## Database and Migrations

SQLite is the persistence engine. The app uses Alembic for local/production schema creation and upgrades; normal app startup no longer silently creates tables outside the test environment.

From `backend/`, initialize or upgrade a configured database:

```bash
DATABASE_URL=sqlite:///./swasthiq_eod.db python3 -m alembic upgrade head
```

Migration verification used for Prompt 2:

```bash
DATABASE_URL=sqlite:////tmp/swasthiq_prompt2_migration_gate.db python3 -m alembic upgrade head
DATABASE_URL=sqlite:////tmp/swasthiq_prompt2_migration_gate.db python3 -m alembic downgrade base
DATABASE_URL=sqlite:////tmp/swasthiq_prompt2_migration_gate.db python3 -m alembic upgrade head
```

The final schema contains `clinic_days`, `visits`, `line_items`, `ingestion_errors`, and `narratives`. Foreign keys are enabled for SQLite connections. Replacing a clinic-day is a single transaction: valid replacements swap child visits, line items, and safe validation issues together; all-invalid non-empty replacements leave existing data and narratives untouched.

## REST Contract

Base path: `/api/v1`.

- `GET /health`
- `GET /clinic-days`
- `PUT /clinic-days/{clinic_id}/{business_date}`
- `GET /clinic-days/{clinic_id}/{business_date}`
- `GET /clinic-days/{clinic_id}/{business_date}/errors`
- `GET /clinic-days/{clinic_id}/{business_date}/narrative`
- `POST /clinic-days/{clinic_id}/{business_date}/narrative`

`PUT` returns HTTP 200 for created, replaced, and unchanged idempotent writes, with `operation` set to `created`, `replaced`, or `unchanged`.

Generated OpenAPI: [`docs/contracts/openapi.json`](docs/contracts/openapi.json).

## Core design documents

- [`docs/STEP_1_REQUIREMENTS.md`](docs/STEP_1_REQUIREMENTS.md)
- [`docs/STEP_2_SYSTEM_DESIGN.md`](docs/STEP_2_SYSTEM_DESIGN.md)
- [`docs/STEP_4_5_FORWARD_PLAN.md`](docs/STEP_4_5_FORWARD_PLAN.md)

## Complete pre-coding package

Start here:

- [`docs/pre-coding/00_MASTER_READINESS.md`](docs/pre-coding/00_MASTER_READINESS.md)

Detailed specifications:

- [`01_STEP_3_BASELINE_AUDIT.md`](docs/pre-coding/01_STEP_3_BASELINE_AUDIT.md)
- [`02_AGENTIC_LANGCHAIN_NVIDIA_SPEC.md`](docs/pre-coding/02_AGENTIC_LANGCHAIN_NVIDIA_SPEC.md)
- [`03_FRONTEND_UI_UX_SPEC.md`](docs/pre-coding/03_FRONTEND_UI_UX_SPEC.md)
- [`04_API_AND_DATA_CONTRACTS.md`](docs/pre-coding/04_API_AND_DATA_CONTRACTS.md)
- [`05_QA_SECURITY_OBSERVABILITY_PLAN.md`](docs/pre-coding/05_QA_SECURITY_OBSERVABILITY_PLAN.md)
- [`06_DEPLOYMENT_RELEASE_SUBMISSION_PLAN.md`](docs/pre-coding/06_DEPLOYMENT_RELEASE_SUBMISSION_PLAN.md)
- [`07_REQUIREMENTS_TRACEABILITY_MATRIX.md`](docs/pre-coding/07_REQUIREMENTS_TRACEABILITY_MATRIX.md)
- [`08_IMPLEMENTATION_BACKLOG.md`](docs/pre-coding/08_IMPLEMENTATION_BACKLOG.md)
- [`09_RISK_REGISTER.md`](docs/pre-coding/09_RISK_REGISTER.md)
- [`10_UI_COPY_DECK.md`](docs/pre-coding/10_UI_COPY_DECK.md)
- [`11_DEFINITION_OF_DONE.md`](docs/pre-coding/11_DEFINITION_OF_DONE.md)
- [`contracts/`](docs/pre-coding/contracts/) — current OpenAPI baseline and synthetic response examples.

## Repository policy

The original assignment PDF and supplied evaluation billing files are intentionally excluded from the public repository. Public tests and demo data must use independently created synthetic fixtures.
