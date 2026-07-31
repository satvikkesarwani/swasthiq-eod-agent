# Steps 4–7 Forward Plan: LangChain + NVIDIA Narrative Layer, React UI, QA, and Release

## Current verified baseline

- Step 1 requirements and acceptance criteria are complete.
- Step 2 architecture and API contract are complete.
- Step 3 deterministic Python backend is implemented.
- Backend verification: 14 tests pass; current application coverage is 86%.
- The deterministic calculation modules remain separate from any LLM provider.

## Locked technology stack

### Backend
- Python 3.11+
- FastAPI REST API
- Pydantic v2 request/response schemas
- SQLAlchemy 2.x
- SQLite
- Pytest + pytest-cov

### Agentic narrative layer
- LangChain Python
- `langchain-nvidia-ai-endpoints`
- `ChatNVIDIA`
- NVIDIA API Catalog hosted NIM endpoint
- Open-weight NVIDIA Nemotron model selected through environment configuration

### Frontend
- React
- Vite
- TypeScript
- React Router
- Recharts for the hourly revenue chart
- Plain CSS/CSS modules for close matching to the supplied interface

### Deployment
- Frontend: Vercel
- Backend: Render or Railway
- SQLite persisted on the backend host where supported; otherwise a documented demo persistence limitation

---

# Step 4 — Grounded agentic narrative layer

## Objective

Replace the generic HTTP-based LLM adapter with a first-class LangChain integration using NVIDIA hosted NIM while preserving the deterministic report as the only source of numerical truth.

The narrative layer is intentionally a bounded chain, not a free-running ReAct agent. The model may choose wording and which approved facts to mention, but it may not calculate totals, query the database directly, or emit unapproved numerical literals.

## Model strategy

Environment configuration:

```env
LLM_PROVIDER=nvidia
NVIDIA_API_KEY=<your-nvidia-api-key>
NVIDIA_MODEL=nvidia/nvidia-nemotron-nano-9b-v2
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
LLM_TIMEOUT_SECONDS=20
LLM_MAX_RETRIES=1
LLM_TEMPERATURE=0
LLM_SEED=42
```

The model ID must remain configurable. The application will not depend on one permanently available free endpoint.

Recommended first model:

```text
nvidia/nvidia-nemotron-nano-9b-v2
```

Reason: the task is short-form structured narrative generation, not long-context reasoning. A larger model can be tested as a backup without changing the application architecture.

## Chain design

```text
Deterministic report
    ↓
Fact catalogue builder
    ↓
Allowed placeholder catalogue
    ↓
ChatPromptTemplate
    ↓
ChatNVIDIA.with_structured_output(NarrativeCandidate)
    ↓
Schema validation
    ↓
Placeholder and trace validation
    ↓
Deterministic value renderer
    ↓
Complete-coverage validation
    ↓
Persist narrative against report hash
```

## Grounding guarantee

The model will not be allowed to write raw figures. It returns templates such as:

```json
{
  "sections": [
    {
      "text_template": "Today {{reconciliation.total_billed_paise}} was billed and {{reconciliation.total_collected_paise}} was collected.",
      "trace_keys": [
        "reconciliation.total_billed_paise",
        "reconciliation.total_collected_paise"
      ]
    }
  ],
  "unavailable_metrics": [
    {
      "metric": "profit",
      "reason": "Cost-price data was not provided."
    }
  ]
}
```

The backend replaces placeholders with deterministic formatted values. This ensures that every displayed figure is derived from a report field and automatically creates the Traced Figures panel.

## LangChain implementation structure

```text
backend/app/agent/
├── __init__.py
├── nvidia_client.py
├── prompts.py
├── schemas.py
├── chain.py
├── grounding.py
└── exceptions.py
```

Existing deterministic modules remain under `services/` and must not import anything from `agent/`.

### `nvidia_client.py`
- Construct `ChatNVIDIA` from backend-only environment settings.
- Use the NVIDIA API key only on the server.
- Configure timeout, model, temperature, seed, and retry behaviour.
- Allow dependency injection for tests.

### `prompts.py`
- System prompt: concise clinic-owner tone; no calculations; no literal figures.
- User prompt: deterministic report, approved fact catalogue, and output rules.
- Include explicit handling for normal, empty, refund-only, and partial-ingestion days.

### `schemas.py`
- Continue using strict Pydantic schemas with `extra="forbid"`.
- Limit section and text sizes.
- Preserve `NarrativeCandidate`, `NarrativeSectionCandidate`, and `UnavailableMetric` contracts.

### `chain.py`
- Compose `ChatPromptTemplate | ChatNVIDIA.with_structured_output(...)`.
- Use asynchronous invocation in the FastAPI service.
- Convert provider exceptions to application-level narrative errors.

### `grounding.py`
- Preserve the placeholder-only renderer.
- Reject unknown placeholders.
- Reject literal digits outside placeholders.
- Reject omitted mandatory facts.
- Build trace rows from the report catalogue, not from model-provided values.

## Failure policy

1. First generation attempt using LangChain and NVIDIA.
2. One repair attempt containing only the validation failure and original approved catalogue.
3. Deterministic fallback template when NVIDIA is unavailable, times out, rate-limits, returns malformed output, or violates grounding rules.
4. Return HTTP 200 with `status="fallback"` when a valid deterministic summary was produced.
5. Never expose provider stack traces or API keys.

## Persistence and staleness

- Store model, provider, status, report hash, traces, and unavailable metrics.
- Reuse a stored narrative only when its report hash matches the current deterministic report.
- Invalidate or regenerate the narrative after a clinic-day update.

## Step 4 tests

### Unit tests
- NVIDIA chain returns a valid candidate.
- Unknown placeholder rejected.
- Literal number rejected.
- Duplicate placeholder rejected.
- Missing required trace rejected.
- Profit claim prevented.
- Empty-day output grounded.
- Refund-only output grounded.
- Malformed structured response triggers repair.
- Two failed attempts trigger deterministic fallback.

### Integration tests
- Mock `ChatNVIDIA` rather than calling the live endpoint in CI.
- Verify generated narrative persistence.
- Verify stale narrative behaviour after re-ingestion.
- Verify API response includes provider/model/status/traces.

### Optional live test
- Marked `@pytest.mark.live_nvidia`.
- Runs only when `NVIDIA_API_KEY` exists.
- Never required for normal CI.

## Step 4 completion gate

Step 4 is complete only when:

- LangChain is the actual production integration path.
- NVIDIA credentials remain backend-only.
- All model-produced text passes deterministic trace validation.
- Every number shown in the narrative maps to a report path.
- Fallback works without an API key.
- All existing deterministic tests still pass.
- Agentic-layer coverage is at least 90% for validation and fallback branches.

---

# Step 5 — React production interface

## Objective

Build the exact three-screen interface required by the assignment while connecting it to the implemented REST API.

## Frontend structure

```text
frontend/src/
├── api/
│   ├── client.ts
│   ├── clinicDays.ts
│   └── narratives.ts
├── components/
│   ├── layout/
│   │   ├── AppShell.tsx
│   │   ├── Sidebar.tsx
│   │   └── ReportHeader.tsx
│   ├── common/
│   │   ├── StatusBanner.tsx
│   │   ├── MoneyValue.tsx
│   │   ├── EmptyState.tsx
│   │   ├── ErrorState.tsx
│   │   └── LoadingSkeleton.tsx
│   ├── reconciliation/
│   │   ├── MetricCard.tsx
│   │   └── PaymentModeTable.tsx
│   ├── analytics/
│   │   ├── RevenueByHourChart.tsx
│   │   └── MedicineRanking.tsx
│   └── narrative/
│       ├── NarrativeCard.tsx
│       ├── TracePanel.tsx
│       └── UnavailableMetrics.tsx
├── pages/
│   ├── ReconciliationPage.tsx
│   ├── AnalyticsPage.tsx
│   └── NarrativePage.tsx
├── types/
│   └── api.ts
├── utils/
│   ├── money.ts
│   └── dates.ts
├── App.tsx
└── main.tsx
```

## Routes

```text
/reports/:clinicId/:businessDate/reconciliation
/reports/:clinicId/:businessDate/analytics
/reports/:clinicId/:businessDate/narrative
```

## Shared shell

All three pages use:

- Persistent left sidebar.
- Clinic name and date context.
- Consistent light-grey page background.
- White rounded cards.
- Dark-blue and teal visual language.
- Responsive behaviour without changing required content hierarchy.

## Screen 1 — reconciliation

- Four cards: billed, collected, outstanding, refunds.
- Secondary indicators: accepted visits, collection rate, pending visits, refund count.
- Payment-mode table for cash/card/UPI.
- Partial-import warning with accepted/rejected counts.
- Optional issue drawer to inspect rejected rows.

## Screen 2 — analytics

- Revenue-by-hour bar chart.
- Peak bar visually highlighted.
- Exact peak-hour label and value.
- Distinct ranking cards for quantity and revenue.
- Empty state when no sales exist.
- Refund-only state must not show refunded items as sales leaders.

## Screen 3 — narrative

- Generated/fallback badge.
- Owner-facing WhatsApp-style text card.
- Copy Summary button.
- Traced Figures panel with display value and source field.
- Unavailable metric note for profit.
- Regenerate button with loading and disabled states.
- Clear fallback status when the NVIDIA endpoint was unavailable.

## Data loading policy

- Fetch one clinic-day report and share it between reconciliation and analytics views.
- Fetch narrative separately because generation can be delayed or unavailable.
- Preserve loading, empty, partial-success, and request-error states.
- No monetary calculations in React; frontend only formats or displays backend values.

## Frontend tests

- Metric cards render backend values.
- Payment-mode rows render correctly.
- Peak hour receives highlighted state.
- Quantity and revenue rankings remain separate.
- Refund-only and empty states render correctly.
- Generated and fallback narratives render distinct badges.
- Trace panel maps every narrative figure.
- API failures show useful error UI.

## Step 5 completion gate

- All three required screens match the supplied structure and content.
- Shared sidebar persists across routes.
- No hard-coded report figures.
- Mobile and desktop layouts remain usable.
- Browser console has no errors.
- Narrative and trace values remain consistent after refresh.

---

# Step 6 — End-to-end hardening

- Add remaining backend branch tests, especially row-validation failures.
- Raise overall backend coverage from 86% toward 90%+.
- Add frontend component tests.
- Add request IDs and structured error logging.
- Add file-size and request-record limits.
- Verify CORS and environment configuration.
- Run all supplied clinic-day files through the application locally.
- Run a fresh-clone setup test from README instructions.
- Confirm no assignment PDF, supplied confidential logs, `.env`, API keys, or SQLite runtime files are committed.

# Step 7 — Deployment and submission

## Backend
- Deploy FastAPI with production environment variables.
- Set exact frontend CORS origin.
- Add `/api/v1/health` deployment check.
- Keep NVIDIA key only in backend secrets.

## Frontend
- Deploy React/Vite to Vercel.
- Configure `VITE_API_BASE_URL`.
- Verify all three deep links work after refresh.

## Final submission package
- Public GitHub repository.
- Live application URL.
- API documentation URL.
- README with setup, architecture, formulas, API contracts, assumptions, test instructions, and LLM grounding design.
- Screenshots or short demo video.
- Explicit note that supplied confidential files were not committed.

# Recommended execution order

```text
Verify Step 3 gates
→ Refactor provider to LangChain ChatNVIDIA
→ Add agentic-layer tests
→ Build shared React shell
→ Build reconciliation screen
→ Build analytics screen
→ Build narrative and traces screen
→ End-to-end testing
→ Deployment
→ README and submission review
```
