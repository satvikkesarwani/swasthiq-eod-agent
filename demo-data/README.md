# Synthetic Demo Data

These files are independently created synthetic examples for local demos. They are not copied from the evaluation dataset and contain no real clinic or patient data.

- `normal-day.json`: valid sales rows with cash, card, UPI, discounts and outstanding amounts.
- `partial-import-day.json`: one valid row and safe deliberate schema/domain errors for the validation drawer.
- `refund-only-day.json`: refund rows only.
- `empty-day.json`: an empty clinic day, represented as `[]`.

Suggested clinic/date pairs:

- Normal: `DEMO-NORMAL-001`, `2026-08-01`
- Partial: `DEMO-PARTIAL-001`, `2026-08-02`
- Refund-only: `DEMO-REFUND-001`, `2026-08-03`
- Empty: any clinic ID and business date, because the file has no rows.
