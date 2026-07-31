# Step 3 Baseline Audit

## 1. Audit result

The deterministic backend is real and executable, not merely planned. The current test suite passes:

```text
14 passed
Overall application coverage: 86%
```

The following capabilities are already present:

- FastAPI application factory and API versioning.
- Request IDs and structured errors.
- Pydantic request schemas.
- Row-level validation.
- Integer-paise calculations.
- Refund exclusion from sales analytics.
- UTC hourly bucketing and deterministic tie-breaking.
- Separate medicine rankings.
- Possible medicine-name typo warnings.
- SQLite foreign-key enforcement.
- Atomic clinic-day replacement.
- Report/source hashes.
- Narrative persistence and report-hash invalidation.
- Placeholder-only trace validation.
- Deterministic narrative fallback.

## 2. Corrections required before feature coding

### P0-1: Rejected-row count is inconsistent on replacement

Creation stores the number of unique rejected row indices:

```text
len({issue.row_index for issue in rejected})
```

Replacement currently stores the number of error objects:

```text
len(rejected)
```

A single malformed row can contain multiple field errors, so replacing an existing clinic-day can report more rejected rows than were actually rejected.

**Locked correction:** always calculate `rejected_row_count = len({issue.row_index for issue in rejected})` once in the ingestion service and pass that count to persistence.

### P0-2: LangChain/NVIDIA has not replaced the generic HTTP provider

The existing provider is an OpenAI-compatible direct HTTP adapter. This does not satisfy the user-selected implementation requirement.

**Locked correction:** replace the production provider path with `ChatNVIDIA` through `langchain-nvidia-ai-endpoints`. Keep the provider protocol so tests can inject fakes.

### P0-3: Narrative generation is synchronous

The current provider interface and FastAPI narrative route are synchronous. A hosted LLM call can occupy a worker thread for the duration of the request.

**Locked correction:** convert the provider method to `async generate(...)`, use `ChatNVIDIA.ainvoke`, and make the POST narrative route asynchronous.

### P1-1: Raw rejected rows are persisted

`raw_row_json` is stored in SQLite for every issue. The UI does not return it, but retaining full source rows is unnecessary for this assignment and would be undesirable with real clinic data.

**Locked correction:** default to `STORE_REJECTED_RAW_ROWS=false`. Persist `null` unless explicitly enabled in local development.

### P1-2: Request size is limited by row count only

The backend limits records but not raw request-body bytes.

**Locked correction:** add a maximum request-body limit of 5 MB and keep the 10,000-row limit. Return `413 REQUEST_TOO_LARGE`.

### P1-3: Zero-priced line items are rejected

The requirements specification permits non-negative unit prices; the current schema uses `gt=0`.

**Locked correction:** use `ge=0`. A zero-priced item remains visible in quantity analytics but contributes zero medicine revenue.

### P1-4: No model/provider metadata timing information

The narrative response exposes provider/model, but not generation timing or fallback reason.

**Locked correction:** persist and return `generation_ms` and a safe `fallback_reason_code` such as `PROVIDER_TIMEOUT`, never raw provider error text.

### P1-5: Missing CI and deployment checks

The repository has no automated pipeline.

**Locked correction:** add GitHub Actions jobs for backend tests/coverage and frontend lint/test/build.

## 3. Deliberately accepted decisions

The following are not defects:

- SQLite is required/allowed by the assignment.
- `Base.metadata.create_all` is acceptable for the take-home scope; Alembic is not necessary unless schema churn begins.
- No authentication is acceptable for a synthetic evaluation application, provided the README explicitly states it.
- Clinic name/location defaults are acceptable for the supplied clinic, while still allowing request overrides.
- All-invalid non-empty uploads are rejected without overwriting existing stored data.
- Empty arrays are valid clinic-days because date/clinic context comes from the route.

## 4. Coverage priorities

Current weak areas should be targeted first:

| Area | Current concern | Planned tests |
|---|---|---|
| Row validator | Multiple domain/schema branches | timestamp offset, duplicate IDs, overpayment, discount, refund sign, non-object row |
| Narrative service | repair/fallback branches | timeout, invalid schema, missing trace, stale report, provider success |
| Provider integration | generic adapter mostly uncovered | fake ChatNVIDIA, safe exception mapping, async call |
| Serializers | stale/current narrative branches | generated, fallback, stale/not-generated |
| Health/error handlers | low branch coverage | DB failure simulation, unexpected error envelope |

## 5. Step 3 exit gate

Step 3 is considered fully stabilized when:

- The rejected-row replacement bug is fixed.
- Unit price accepts zero.
- Raw-row retention is disabled by default.
- Body-size protection exists.
- Existing 14 tests still pass.
- New regression tests pass.
- Overall backend coverage is at least 90%, with deterministic services at least 95%.
