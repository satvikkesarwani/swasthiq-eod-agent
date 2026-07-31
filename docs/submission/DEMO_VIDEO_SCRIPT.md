# Demo Video Script

Target length: 3 to 5 minutes.

1. Introduce SwasthiQ EOD: a clinic-day billing import, reconciliation, analytics, and grounded owner-summary tool.
2. Open the Reports page and import `demo-data/normal-day.json` with clinic `DEMO-NORMAL-001` and date `2026-08-01`.
3. Show the Reconciliation page: billed, collected, outstanding, refunds, and payment-mode breakdown.
4. Open Analytics: show revenue-by-hour, backend peak hour, quantity ranking, and revenue ranking.
5. Open AI Narrative Summary and click Generate Summary.
6. Show the owner summary, Traced Figures, and unavailable profit metric.
7. Import `demo-data/partial-import-day.json` with clinic `DEMO-PARTIAL-001` and date `2026-08-02`; open the validation issues drawer.
8. Import `demo-data/refund-only-day.json` with clinic `DEMO-REFUND-001` and date `2026-08-03`; show refund-only handling.
9. Briefly explain that deterministic calculations never call the LLM, and every narrative figure comes from backend traces.
10. Close with repository, frontend URL, backend health URL, and fallback behavior when NVIDIA is not configured.

Do not show `.env`, API keys, confidential assignment files, original evaluation data, prompts, raw model output, or personal browser credentials.
