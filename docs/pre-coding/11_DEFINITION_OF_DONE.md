# Definition of Done and Final Acceptance Gates

## 1. A feature is done only when

- Code is implemented in the agreed module.
- Success and failure behavior are tested.
- API/type contract is updated.
- No secret or confidential data is introduced.
- UI has loading, empty, and error behavior where relevant.
- Documentation reflects actual behavior.
- CI passes from a clean checkout.

## 2. Backend gate

- All deterministic formulas match locked requirements.
- All sample-day oracles pass.
- Invalid rows never affect any report output.
- Rejected row count is unique by row.
- Re-import is atomic.
- Backend coverage at least 90%.
- Health and Swagger work.
- No unhandled stack trace exposed.

## 3. Agentic gate

- Production path uses LangChain `ChatNVIDIA`.
- NVIDIA key is backend-only.
- Model receives aggregates/placeholders, not raw visits.
- Literal figures cannot pass validation.
- Required figures cannot be omitted.
- Profit is explicitly unavailable.
- One repair attempt is bounded.
- Deterministic fallback always remains usable.
- Stored narrative report hash matches current report.

## 4. Frontend gate

- Three specified screens exist.
- Persistent navigation exists.
- Reconciliation cards/table match required structure.
- Analytics has chart, peak callout, and two separate rankings.
- Narrative has summary and Traced Figures side-by-side on desktop.
- Import and validation issue flow works.
- Mobile layout works at 320 px.
- No business calculation is duplicated in React.
- Lint, tests, and build pass.

## 5. Deployment gate

- Frontend and backend use HTTPS.
- Vercel direct route refresh works.
- Railway health check passes.
- SQLite volume is mounted and persistence tested.
- CORS is exact.
- NVIDIA generation and no-key fallback both tested.
- No secret in repository or browser bundle.

## 6. Submission gate

- Public repository clean.
- Live frontend link.
- Swagger/backend link.
- README complete.
- Architecture diagram included.
- Test results included.
- Known limitations stated.
- Demo video recorded without confidential files or secrets.
- Final traceability matrix has no incomplete P0 row.

## 7. Final reviewer test

A reviewer with no local context must be able to:

1. Open the live application.
2. Import a valid synthetic file.
3. Understand the reconciliation immediately.
4. See the peak hour and two rankings.
5. Generate/read a grounded summary.
6. Verify each figure in the trace panel.
7. Inspect one rejected row's actionable error.
8. Clone the repository and run tests using README instructions.
