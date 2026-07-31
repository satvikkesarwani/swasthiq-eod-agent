# Ordered Implementation Backlog

## Priority rules

- P0 blocks correctness or assignment compliance.
- P1 is required for a strong submission.
- P2 is polish that may be dropped if the deadline is at risk.

## Phase A — Stabilize existing backend

| Task | Priority | Definition of done |
|---|---|---|
| Fix unique rejected-row count on replacement | P0 | regression test covers multiple issues on one row during replacement |
| Accept zero unit price | P1 | validator and analytics test pass |
| Disable raw rejected-row persistence by default | P1 | config + repository test |
| Add 5 MB request-body protection | P1 | 413 integration test |
| Raise coverage to 90%+ | P1 | CI coverage gate passes |

## Phase B — LangChain + NVIDIA

| Task | Priority | Definition of done |
|---|---|---|
| Add LangChain/NVIDIA dependencies | P0 | locked dependencies install from clean environment |
| Add NVIDIA settings | P0 | `.env.example` documented; key backend-only |
| Implement async `ChatNVIDIA` provider | P0 | fake provider test verifies `ainvoke` |
| Compose structured chain | P0 | valid candidate parses to Pydantic model |
| Preserve placeholder validator | P0 | all grounding tests pass |
| Add one repair attempt | P1 | first invalid/second valid test |
| Add fallback reason and timing | P1 | response/persistence tests |
| Add optional live NVIDIA test | P2 | skipped without key, passes with key |

## Phase C — Frontend foundation

| Task | Priority | Definition of done |
|---|---|---|
| Scaffold Vite React TypeScript | P0 | `npm run build` passes |
| Add Router and API client | P0 | deep routes and error envelope work |
| Add strict API types | P0 | no `any` for business payloads |
| Add global tokens and app shell | P0 | desktop/mobile navigation present |
| Add import page/modal | P0 | valid file creates report and redirects |

## Phase D — Required screens

| Task | Priority | Definition of done |
|---|---|---|
| Reconciliation cards/table | P0 | exact fields and payment rows render |
| Import warning/issues drawer | P1 | partial input inspectable |
| Hourly revenue chart/peak callout | P0 | peak visually and textually identified |
| Separate ranking cards | P0 | quantity and revenue never combined |
| Narrative card/status/actions | P0 | generate, fallback, copy, regenerate work |
| Traced Figures panel | P0 | exact server traces displayed |
| Edge/empty/error states | P0 | all test fixtures covered |
| Data-quality warning | P1 | typo warning visible without merge |

## Phase E — Hardening

| Task | Priority | Definition of done |
|---|---|---|
| Frontend unit/component tests | P0 | agreed coverage and key state tests pass |
| Playwright normal-day smoke | P1 | local CI flow passes |
| Narrative rate limit | P1 | excess request gets safe 429 |
| Security headers/CORS review | P1 | production settings verified |
| Structured request/provider logs | P1 | no sensitive payload logging |
| Accessibility review | P1 | keyboard/labels/contrast verified |

## Phase F — Delivery

| Task | Priority | Definition of done |
|---|---|---|
| GitHub Actions | P0 | green backend and frontend jobs |
| Railway deployment + volume | P0 | report survives redeploy/restart check |
| Vercel deployment + SPA rewrite | P0 | direct route refresh works |
| README finalization | P0 | all required sections and live links |
| Demo fixtures | P0 | synthetic, non-confidential, reproducible |
| Demo video | P1 | under five minutes, no secret shown |
| Final acceptance matrix | P0 | every P0 requirement passes |

## Three-day execution plan

### Day 1

- Complete Phase A.
- Complete LangChain/NVIDIA provider and grounding tests.
- Confirm fallback with missing key.

### Day 2

- Scaffold frontend and app shell.
- Build all three required screens.
- Connect import and narrative flows.

### Day 3

- Complete tests, security review, and responsive polish.
- Deploy backend/frontend.
- Finalize README, screenshots, and demo.

## Stop conditions

Drop P2 work immediately if any P0 item is incomplete. Do not add broader SwasthiQ features until all required screens, edge cases, tests, and deployment checks pass.
