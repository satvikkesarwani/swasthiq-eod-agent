# Backend Stabilization Report

## 1. Initial Baseline

- Date: 2026-07-31.
- Environment: macOS local workspace, backend run from `swasthiq-eod-agent/backend`.
- Python executable used: `python3`.
- Python version observed in coverage output: 3.13.5.
- Exact requested `python -m pytest -q`: failed because `python` is not on this shell PATH.
- Initial runnable test command: `python3 -m pytest -q`.
- Initial runnable result: 14 passed.
- Initial coverage command: `python3 -m pytest --cov=app --cov-branch --cov-report=term-missing`.
- Initial coverage result: 86% total backend coverage.

## 2. Existing Capabilities Confirmed

- FastAPI application factory and versioned API routes.
- SQLite persistence through SQLAlchemy.
- Atomic create/replace flow for clinic-days.
- Integer-paise deterministic reconciliation and analytics.
- Empty-day, refund-only, partial-ingestion, and narrative fallback paths.
- Structured error envelopes with request IDs.
- API serialization already omitted raw rejected rows.

## 3. Defects Fixed

- Replacement stored `rejected_rows=len(rejected_issues)` instead of unique rejected row indices.
- Zero-priced line items were rejected despite the locked non-negative price contract.
- Malformed source rows were persisted by default in `ingestion_errors.raw_row_json`.
- Request size was limited by row count only; oversized raw bodies were not rejected before parsing.
- Deterministic validation branch coverage was too narrow for the locked edge-case matrix.

## 4. Implementation Decisions

- The service layer now calculates `rejected_row_count = len({issue.row_index for issue in ingestion.rejected})` exactly once and passes it into persistence.
- `STORE_REJECTED_RAW_ROWS=false` is the default. The repository receives the storage policy as an explicit argument and does not read environment variables directly.
- A FastAPI middleware enforces `MAX_REQUEST_BODY_BYTES=5242880` using both early `Content-Length` rejection and actual streamed body-size enforcement.
- Oversized requests return `413 REQUEST_TOO_LARGE` in the existing structured error envelope and do not modify the database.
- `unit_price_paise=0` is valid; negative prices remain invalid.
- LangChain/NVIDIA and frontend implementation were intentionally not performed in this prompt.

## 5. Files Modified Or Created

- `backend/.env.example`
- `backend/app/api/routes_clinic_days.py`
- `backend/app/core/config.py`
- `backend/app/main.py`
- `backend/app/repositories/clinic_day_repository.py`
- `backend/app/schemas/ingestion.py`
- `backend/app/services/ingestion_service.py`
- `backend/tests/integration/test_api.py`
- `backend/tests/unit/test_api_supporting_branches.py`
- `backend/tests/unit/test_validation_and_invariants.py`
- `README.md`
- `docs/implementation/01_BACKEND_STABILIZATION_REPORT.md`

## 6. Tests Added

- Regression coverage for replacement rejected-row counting with multiple issues on one row.
- All-invalid replacement preservation of the previously stored report.
- Zero-priced line item acceptance, quantity analytics inclusion, zero medicine revenue, and negative-price rejection.
- Raw rejected-row persistence disabled by default and enabled only when explicitly configured.
- Oversized body rejection using `Content-Length` and actual streamed body-size enforcement.
- Under-limit ingestion success.
- Deterministic validation branches for non-object rows, missing/invalid payment mode, clinic/date mismatch, duplicate visits, discount/payment/refund rules, non-UTC timestamps, and multiple row issues.
- Deterministic invariants for payment-mode totals, non-refund financial formulas, refund exclusion, rejected-row exclusion, peak-hour tie-breaking, separate medicine rankings, and medicine-name warnings.
- Supporting safe-error, health, provider, and config branch tests.

## 7. Final Commands Executed

```text
python -m pytest -q
python3 -m pytest -q
python3 -m pytest --cov=app --cov-branch --cov-report=term-missing
python3 -m pytest --cov=app --cov-branch --cov-report=term-missing --cov-fail-under=90
python3 -c "from app.main import create_app; create_app()"
find . -type f \( -name '*.pdf' -o -name '*assignment*' -o -name '*.xlsx' -o -name '*.xls' -o -name '*.csv' \) -print
rg -n "(sk-[A-Za-z0-9]|NVIDIA_API_KEY=.+|LLM_API_KEY=.+|BEGIN (RSA|OPENSSH|PRIVATE) KEY)" .
```

## 8. Final Results

- Final full test suite: 47 passed.
- Final coverage gate: 91.67% total backend coverage with branch coverage enabled.
- Coverage gate status: passed `--cov-fail-under=90`.
- Clean application import: passed.
- Repository content scan: no assignment PDF/evaluation data files found; only documented placeholder secret strings were matched.

## 9. Remaining Work Deferred

- LangChain, `ChatNVIDIA`, NVIDIA model configuration, async provider flow, and narrative repair pipeline.
- React/Vite frontend and the three required UI screens.
- CI/CD, deployment, production CORS/header hardening, rate limiting, and live hosting checks.
- Authentication, authorization, audit logging, and compliance controls for any real clinic deployment.

## 10. Acceptance Criteria

Prompt 1 deterministic backend acceptance criteria are satisfied: the backend is stable, uses integer-paise deterministic calculations, avoids LLM calls in the deterministic layer, handles the required edge cases, has safe raw-row storage defaults, enforces request body limits, and passes the required test and coverage gates.
