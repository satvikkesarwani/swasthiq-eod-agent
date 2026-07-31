# Persistence and API Contract Report

## 1. Execution Gate

- Prompt 1 final result verified from `docs/implementation/01_BACKEND_STABILIZATION_REPORT.md`: 47 tests passed, 91.67% branch coverage.
- `git status --short`: clean before Prompt 2 implementation.
- `git log -3 --oneline`: latest commit `d543c97 feat: stabilize deterministic backend`.
- Prompt 1 baseline rerun: `python3 -m pytest -q` passed with 47 tests.
- Prompt 1 coverage rerun: `python3 -m pytest --cov=app --cov-branch --cov-report=term-missing --cov-fail-under=90` passed at 91.67%.

## 2. Initial Persistence State

- Current database approach: SQLAlchemy models plus `Base.metadata.create_all()` during app creation.
- Current migration behaviour: no Alembic setup existed under `backend/`.
- Current tables: `clinic_days`, `visits`, `line_items`, `ingestion_errors`, `narratives`.
- Current relationships: clinic-day to visits, clinic-day to ingestion errors, clinic-day to narrative, visit to line items.
- Current transaction behaviour: ingestion service owns commit/rollback and repository flushes IDs.
- Current hashing behaviour: source hash used route clinic/date and records only; report hash used report JSON only.
- Current API paths: required `/api/v1` route family exists.

## 3. Initial Gaps

- Alembic migrations absent.
- App startup silently created tables for all environments.
- Final logical schema fields missing: child `created_at` fields, narrative `generation_ms`, narrative `fallback_reason_code`.
- `clinic_name` and `clinic_location` were non-null defaults rather than nullable optional metadata.
- `ingestion_errors` persisted `code`; final contract calls this `error_code`.
- `line_items` used `visit_id_fk`; final logical model calls this `visit_id`.
- PUT returned `201` on creation and had no `operation` field.
- List endpoint lacked date filters, pagination, and money summary fields.
- Errors endpoint lacked an explicit response model and pagination.
- OpenAPI artifact under `docs/contracts/openapi.json` did not exist.

## 4. Files Expected To Change

- Backend models, repositories, schemas, services, routes, app factory, settings and dependency files.
- Alembic configuration and initial migration.
- Backend tests for migrations, hashing/versioning, transactions, list/query behavior and OpenAPI.
- README and API/data-contract documentation.
- Generated OpenAPI contract artifact.

## 5. Implementation Summary

- Added Alembic under `backend/alembic/` with initial revision `20260731_0001`.
- Added `alembic.ini` and configured Alembic to read `DATABASE_URL` through the existing settings system.
- Updated SQLAlchemy entities to match the final logical model:
  - nullable clinic metadata;
  - child `created_at` fields;
  - `line_items.visit_id`;
  - `ingestion_errors.error_code`;
  - narrative `generation_ms` and `fallback_reason_code`;
  - final indexes and uniqueness constraints.
- Normal app startup no longer silently creates tables. Test apps still use metadata creation for isolated in-memory databases.
- PUT `/api/v1/clinic-days/{clinic_id}/{business_date}` now returns HTTP 200 and an explicit `operation` field.
- List endpoint now supports `clinic_id`, `date_from`, `date_to`, `limit`, and `offset`, and returns money summary fields.
- Errors endpoint now uses an explicit response model with bounded pagination and safe issue fields only.
- OpenAPI artifact generated at `docs/contracts/openapi.json`.

## 6. Database Tables And Relationships

- `clinic_days`: one report per `(clinic_id, business_date)`.
- `visits`: accepted visits only, unique per clinic-day by `visit_id`.
- `line_items`: accepted visit line items, cascaded from visits.
- `ingestion_errors`: safe validation issues, cascaded from clinic-days, with `raw_row_json` null by default.
- `narratives`: one narrative per clinic-day, valid only when `narratives.report_hash == clinic_days.report_hash`.

SQLite foreign-key enforcement is enabled for every application engine connection and Alembic online migration connection.

## 7. Hashing And Versioning

`source_hash` is SHA-256 over canonical JSON containing:

- route `clinic_id`;
- route `business_date`;
- optional `clinic_name`;
- optional `clinic_location`;
- submitted records in submitted order.

`report_hash` is SHA-256 over canonical JSON containing:

- route `clinic_id`;
- route `business_date`;
- accepted/rejected counts;
- deterministic reconciliation, analytics, payment-mode breakdown, and data-quality warnings.

It excludes database IDs, request IDs, timestamps, API URLs, narrative content, LLM metadata, and UI formatting.

Narrative invalidation rule:

- identical source/report: operation `unchanged`, narrative remains valid;
- different source but same deterministic report: `source_hash` changes, `report_hash` remains, narrative remains valid;
- deterministic report change: stale narrative is removed in the same transaction;
- all-invalid non-empty replacement: existing report and narrative remain untouched;
- empty array: valid replacement with zero report.

## 8. Transaction Behaviour

Clinic-day replacement is orchestrated in `IngestionService` as one unit of work:

1. validate request rows in memory;
2. reject non-empty all-invalid payloads before storage changes;
3. compute deterministic report and hashes;
4. replace parent metadata, visits, line items, ingestion issues, and narrative validity in one transaction;
5. commit once or rollback everything on failure.

Repository methods flush when IDs are needed and do not commit.

## 9. Tests Added

- Fresh Alembic upgrade, downgrade, and re-upgrade against temporary SQLite.
- Expected table/index/foreign-key checks.
- Application write after migration without metadata `create_all`.
- Duplicate clinic-day and duplicate visit constraint enforcement.
- Same `visit_id` allowed on different clinic-days.
- Cascade deletion and orphan checks.
- Raw rejected rows null by default.
- Simulated persistence exception rollback.
- Repeated replacement child row counts.
- Hash semantics for unchanged, metadata-only source changes, report changes, all-invalid replacement, and empty replacement.
- List endpoint empty/multiple/filter/date-range/pagination/limit/ordering behavior.
- Detail/errors/missing clinic-day/no raw-row serialization.
- Stale narrative not returned after report change.
- OpenAPI required paths, methods, schemas, integer money fields, `/api/v1` prefix, and absence of `raw_row_json`.
- Health database failure safe envelope.

## 10. Final Verification

Environment note: this machine does not provide a `python` executable on PATH. Exact `python ...` commands fail with `zsh:1: command not found: python`; equivalent `python3 ...` commands were executed.

Commands executed:

```text
git status --short
git log -3 --oneline
python -m pytest -q
python -c "from app.main import create_app; create_app(); print('app import successful')"
python3 -m pytest -q
python3 -m pytest --cov=app --cov-branch --cov-report=term-missing --cov-fail-under=90
python3 -c "from app.main import create_app; create_app(); print('app import successful')"
DATABASE_URL=sqlite:////tmp/swasthiq_prompt2_required_alembic.db alembic upgrade head
DATABASE_URL=sqlite:////tmp/swasthiq_prompt2_required_alembic.db alembic downgrade base
DATABASE_URL=sqlite:////tmp/swasthiq_prompt2_required_alembic.db alembic upgrade head
python3 -c "import json; from pathlib import Path; from app.main import create_app; app = create_app(); path = Path('../docs/contracts/openapi.json'); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True), encoding='utf-8'); print('generated', path)"
```

Final results:

- Full backend suite: 57 passed.
- Branch coverage: 93.05%.
- Coverage gate: passed `--cov-fail-under=90`.
- Clean app import: passed with `python3`.
- Migration gate: upgrade, downgrade, and re-upgrade passed against a temp SQLite database.
- OpenAPI generation: passed.

## 11. Remaining Work Deferred

- LangChain, ChatNVIDIA, NVIDIA provider integration, prompt templates, and repair pipeline.
- React/Vite frontend.
- Authentication, deployment, CI/CD, and production infrastructure.

## 12. Acceptance Criteria

Prompt 2 acceptance criteria are satisfied in the executable repository, with the only environment caveat that the local interpreter command is `python3` rather than `python`.
