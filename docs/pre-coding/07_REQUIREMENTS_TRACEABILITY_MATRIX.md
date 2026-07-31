# Requirements Traceability Matrix

## Legend

- **Implemented**: exists in current backend.
- **Planned**: fully specified but coding remains.
- **Verify**: implemented but requires a regression test/final acceptance check.

| ID | Requirement | Implementation location | UI evidence | Test evidence | Status |
|---|---|---|---|---|---|
| DET-01 | Parse and validate rows | `schemas/ingestion.py`, `services/row_validator.py` | Import status/issues | row validator + API tests | Implemented/expand tests |
| DET-02 | Actionable malformed-row errors | row issues + error serializer | Validation drawer | partial-ingestion API test | Implemented |
| DET-03 | Total billed | reconciliation service | Billed card | deterministic report tests | Implemented |
| DET-04 | Total collected | reconciliation service | Collected card | deterministic report tests | Implemented |
| DET-05 | Outstanding | reconciliation service | Outstanding card | deterministic report tests | Implemented |
| DET-06 | Refunds | reconciliation service | Refund card | refund-only test | Implemented |
| DET-07 | Split by cash/card/UPI | reconciliation service | Payment table | invariant tests to expand | Implemented/verify |
| DET-08 | Money as integer paise | schemas/services/models | money formatter | type/calculation tests | Implemented |
| DET-09 | Deterministic layer never calls LLM | module boundary | n/a | import architecture review | Implemented/verify |
| ANA-01 | Revenue by hour | analytics service | bar chart | hourly/tie tests | Implemented/expand |
| ANA-02 | Peak hour | analytics service | peak callout | peak test | Implemented |
| ANA-03 | Top medicine quantity | analytics service | quantity list | ranking test | Implemented |
| ANA-04 | Top medicine revenue separate | analytics service | revenue list | ranking test | Implemented |
| LLM-01 | Owner-facing WhatsApp summary | narrative service + LangChain chain | narrative card | provider/integration tests | Planned |
| LLM-02 | Every figure grounded | trace catalogue/validator | Traced Figures panel | grounding tests | Implemented core; integrate NVIDIA |
| LLM-03 | No invented unavailable metrics | profit unavailable rule | unavailable note | narrative tests | Implemented core |
| LLM-04 | Malformed model output safe | repair + fallback | fallback badge | repair/fallback tests | Planned extension |
| UI-01 | Reconciliation screen | React page | exact screen | component/E2E | Planned |
| UI-02 | Analytics screen | React page | exact screen | component/E2E | Planned |
| UI-03 | Narrative + traces screen | React page | exact screen | component/E2E | Planned |
| UI-04 | Persistent sidebar | App shell | all screens | route test | Planned |
| EDGE-01 | Empty day | deterministic report | empty states | existing test | Implemented |
| EDGE-02 | Refund-only day | deterministic report | refund-only states | existing test | Implemented |
| EDGE-03 | Malformed sample row | row validator | issue drawer | existing test | Implemented |
| EDGE-04 | Medicine typo not merged | warning service | warning card | existing test | Implemented |
| CONS-01 | SQLite/in-memory only | SQLAlchemy SQLite | n/a | integration tests | Implemented |
| CONS-02 | Python REST API | FastAPI | Swagger | API tests | Implemented |
| CONS-03 | React frontend | Vite React | live UI | build/tests | Planned |
| SUB-01 | `/backend` + `/frontend` | repository layout | n/a | repository audit | Partial |
| SUB-02 | Public live link | Vercel/Railway | live app | smoke test | Planned |
| SUB-03 | README/API explanation | root README/docs | n/a | doc audit | Planned finalization |
| EVAL-01 | Code structure | layered backend/frontend | n/a | review | Backend strong; frontend planned |
| EVAL-02 | Error handling | structured errors/fallback | error states | tests | Backend present; expand |
| EVAL-03 | Test coverage | pytest/Vitest/Playwright | n/a | CI | 86% backend; target 90%+ |

## Acceptance rule

No requirement may be marked complete in the final README unless its mapped automated test or manual acceptance check has passed.
