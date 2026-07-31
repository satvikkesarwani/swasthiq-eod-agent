# Step 6 Plan — QA, Security, Performance, and Observability

## 1. Quality objective

The final product must be demonstrably correct on the supplied edge cases, resilient to model/provider failure, understandable to a reviewer, and safe enough for a synthetic public demo.

## 2. Test pyramid

```text
Many deterministic unit tests
        ↓
Backend service/API integration tests
        ↓
Frontend component/integration tests
        ↓
One or two end-to-end smoke flows
        ↓
Manual visual and deployment acceptance review
```

## 3. Backend unit test matrix

### Row validation

- Non-object row.
- Missing each required field.
- Unknown field.
- Non-UTC timestamp.
- Business-date mismatch.
- Clinic ID mismatch.
- Duplicate visit ID.
- Empty line-items array.
- Zero quantity.
- Negative price.
- Zero price accepted.
- Discount exceeds gross.
- Negative non-refund payment.
- Positive/zero refund payment.
- Payment exceeds billed.
- Multiple errors on one row count as one rejected row.

### Reconciliation

- Normal paid visit.
- Partial payment.
- Discount.
- Refund.
- Multiple payment modes.
- All totals equal payment-mode sums.
- Outstanding equals billed minus collected.
- Collection rate null when billed zero.

### Analytics

- 24 hourly buckets.
- UTC hour bucketing.
- Peak-hour earliest tie-break.
- Refunds excluded.
- Rejected rows excluded.
- Quantity/revenue rankings differ correctly.
- Ranking alphabetical tie-break.
- Ranking limit five.
- Typo variants remain separate and warn.

### Hashing/persistence

- Canonical source hash independent of dictionary order.
- Same report yields same report hash.
- Re-import replaces children atomically.
- All-invalid replacement preserves previous report.
- Changed report invalidates narrative.
- Identical report may reuse valid narrative.

## 4. Agentic tests

Covered in the Step 4 specification; they are mandatory for CI and use a fake `ChatNVIDIA` runnable.

No normal CI job calls the live NVIDIA endpoint.

## 5. Frontend tests

### Component/integration

- Import form parses valid JSON and rejects invalid syntax locally.
- Reconciliation cards and payment table.
- Partial-ingestion drawer.
- Analytics chart/callout/rankings.
- Empty/refund-only states.
- Generated/fallback narrative states.
- Trace panel and unavailable metric.
- Copy action.
- API error envelope.
- Responsive navigation class/layout behavior.

### Playwright smoke flow

```text
Open app
→ import synthetic normal-day file
→ see reconciliation totals
→ open Analytics
→ verify peak hour and two rankings
→ open AI Summary
→ generate or receive fallback
→ verify trace panel
```

A second optional flow covers the malformed row and issue drawer.

## 6. Coverage gates

- Backend overall: at least 90% line coverage.
- Deterministic services: at least 95%.
- Agentic grounding/fallback modules: at least 90%.
- Frontend: at least 80% statements on business components.
- All tests and builds must pass from a clean checkout.

Coverage is a guardrail, not a substitute for edge-case assertions.

## 7. Security plan

### Secrets

- NVIDIA key only in backend environment.
- `.env` ignored.
- `.env.example` contains no real key.
- CI uses no live key.
- Repository secret scan before submission.

### Input controls

- 5 MB maximum body.
- 10,000 maximum records.
- Strict Pydantic schemas.
- Unknown fields rejected at row level.
- Maximum strings, quantities, prices, and line-item counts.
- No user-controlled SQL.

### Output controls

- Structured error envelopes.
- No stack traces sent to users.
- No raw rejected rows returned.
- No provider raw error text returned.
- No HTML rendering of narrative text; React escapes text by default.

### CORS and headers

- Exact production frontend origin.
- No wildcard with credentials.
- `X-Content-Type-Options: nosniff`.
- `Referrer-Policy: no-referrer` or `strict-origin-when-cross-origin`.
- Reasonable Content Security Policy on frontend deployment.

### Abuse protection

- Rate-limit narrative generation per client/IP on the single backend instance.
- Suggested demo limit: 10 generation attempts per hour per IP.
- Reuse cached narrative unless `force_regenerate=true`.
- Disable repeated frontend clicks while a request is running.

### Scope disclosure

The public demo has no authentication because it processes synthetic evaluation data. The README must state that real clinic deployment would require authentication, authorization, audit logs, consent/privacy controls, encryption policy, and compliance review.

## 8. Privacy/data minimization

- Do not commit the assignment PDF or supplied logs.
- Public tests use independently created synthetic fixtures.
- Raw rejected rows not stored by default.
- Production logs contain IDs/counts/status, not transaction payloads.
- Model prompt receives report aggregates, not raw visits.

## 9. Performance targets

Targets are for a single-instance take-home deployment:

| Operation | Target |
|---|---|
| GET stored report | p95 under 250 ms after warm-up |
| Ingest 1,000 simple records | under 1 second locally |
| Ingest max 10,000 records | under 5 seconds locally |
| Generate fallback narrative | under 100 ms excluding DB |
| NVIDIA narrative request | timeout at 20 seconds |
| Frontend production build | passes without warnings treated as errors |

The API should remain usable when the NVIDIA request times out because fallback is local.

## 10. Logging

Structured fields:

- timestamp.
- level.
- event.
- request ID.
- method/path/status.
- duration.
- clinic ID and business date where applicable.
- accepted/rejected counts.
- provider/model/status/generation duration.

Never log:

- API keys.
- full request bodies.
- raw rows.
- prompts.
- raw model outputs.

## 11. Health and diagnostics

`GET /api/v1/health` verifies:

- API process alive.
- SQLite query succeeds.
- version returned.

It should not call NVIDIA. Provider outages must not mark the core deterministic API unhealthy.

## 12. Manual acceptance checklist

- Fresh browser/incognito works.
- Deep links work after refresh.
- All supplied day types produce correct states.
- One malformed row is excluded everywhere.
- No console error.
- No failed network request during normal fallback operation.
- Mobile width 320 px usable.
- Keyboard can navigate all actions.
- Copy Summary copies only narrative text.
- Provider key absent still gives complete fallback narrative.
