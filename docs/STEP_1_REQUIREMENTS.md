# Step 1 — Final Requirements Specification

## 1. Product goal

Build an End-of-Day Billing & Analytics Agent for a clinic owner. A user imports one clinic-day billing log and receives:

1. Deterministic reconciliation.
2. Deterministic analytics.
3. A short owner-facing AI narrative.
4. Figure-level traceability proving that every number in the narrative came from the deterministic report.

The deterministic Python layer is the sole numerical source of truth. The LLM may explain existing report values but must never calculate or invent business metrics.

## 2. Locked technology and submission constraints

- Backend: Python REST API.
- Frontend: React.
- Storage: SQLite or in-memory only.
- LLM: any API, isolated behind a provider interface.
- Repository: one repository with `/backend`, `/frontend`, and root `README.md`.
- Deployment: publicly accessible working application.
- UI: three required screens with one persistent sidebar.
- Money: integer paise in all backend models and calculations.

## 3. Primary user

- Clinic owner.
- Clinic administrator.
- Front-desk manager.

The user should not need to inspect raw JSON or use a spreadsheet.

## 4. Required user outcome

For a selected clinic and business date, answer:

- How much was billed?
- How much was collected?
- How much is outstanding?
- How much was refunded?
- Which hour produced the highest billed revenue?
- Which medicines moved the most by quantity?
- Which medicines produced the most gross line-item revenue?
- What concise summary can be shared/read on WhatsApp?

## 5. Input contract

The API receives explicit clinic-day context and an array of records:

```json
{
  "clinic_id": "CLN-KNP-014",
  "business_date": "2026-07-27",
  "records": []
}
```

Explicit context is mandatory because an empty records array contains no clinic or date information.

### Record fields

- `clinic_id`: non-empty string; must match request clinic.
- `visit_id`: non-empty string; unique within the clinic-day.
- `timestamp`: ISO-8601 UTC timestamp; date must match `business_date`.
- `doctor_id`: non-empty string.
- `line_items`: non-empty array.
- `line_items[].drug_name`: non-empty string.
- `line_items[].qty`: positive integer.
- `line_items[].unit_price_paise`: non-negative integer.
- `payment_mode`: one of `cash`, `card`, `upi`.
- `amount_paid_paise`: integer.
- `discount_paise`: non-negative integer.
- `is_refund`: boolean.

## 6. Validation policy

### 6.1 Fatal request errors

Reject the entire request without changing stored data when:

- Request body is not valid JSON.
- Required clinic-day context is missing.
- `records` is not an array.
- Record clinic/date conflicts with request context.
- More than one clinic or business date is present.
- File/request exceeds configured safety limits.
- No row can be processed and the request is structurally invalid.

### 6.2 Row-level recoverable errors

Reject only the affected row and continue with valid rows when:

- A required row field is missing.
- `payment_mode` is absent or unsupported.
- Timestamp is invalid.
- Visit ID is duplicated.
- Line items are malformed.
- Quantity or price is invalid.
- Discount exceeds gross line total.
- Non-refund payment is negative.
- Refund payment is zero or positive.
- Non-refund payment exceeds the amount due.

The response must report `received_rows`, `accepted_rows`, `rejected_rows`, and actionable field-level errors.

## 7. Deterministic financial definitions

### 7.1 Non-refund transaction

```text
gross_line_total_paise = sum(qty * unit_price_paise)
billed_paise = gross_line_total_paise - discount_paise
collected_paise = amount_paid_paise
outstanding_paise = billed_paise - collected_paise
```

Required invariants:

```text
0 <= discount_paise <= gross_line_total_paise
0 <= amount_paid_paise <= billed_paise
outstanding_paise >= 0
```

### 7.2 Refund transaction

```text
is_refund = true
amount_paid_paise < 0
refund_paise = abs(amount_paid_paise)
```

Refund rows do not add to billed, collected, outstanding, hourly sales revenue, or top-selling medicine rankings.

### 7.3 Clinic-day reconciliation

```text
total_billed_paise = sum(non-refund billed_paise)
total_collected_paise = sum(non-refund collected_paise)
total_outstanding_paise = total_billed_paise - total_collected_paise
total_refunds_paise = sum(valid refund_paise)
```

The same values must be grouped by `cash`, `card`, and `upi`.

### 7.4 Collection rate

```text
collection_rate = total_collected_paise / total_billed_paise
```

Return `null` when total billed is zero.

## 8. Deterministic analytics definitions

### 8.1 Revenue by hour

- Bucket using the UTC hour from `timestamp`.
- Use non-refund `billed_paise` after visit-level discount.
- Exclude rejected rows and refund rows.
- Peak hour is the bucket with the greatest value.
- Tie-breaker: earliest UTC hour.
- Return `null` peak hour when every bucket is zero.

### 8.2 Top medicines by quantity

```text
quantity = sum(qty) across valid non-refund line items
```

Sort by quantity descending, then normalized drug name ascending.

### 8.3 Top medicines by revenue

```text
gross_medicine_revenue_paise = sum(qty * unit_price_paise)
```

A visit-level discount is not allocated across medicines because the source data does not provide a defensible allocation rule. This ranking is therefore explicitly gross line-item revenue.

Sort by revenue descending, then normalized drug name ascending.

### 8.4 Medicine-name handling

Allowed deterministic normalization:

- Trim leading/trailing spaces.
- Collapse repeated whitespace.
- Convert to uppercase.

Do not fuzzy-correct or silently merge suspected spelling variants. Emit a non-blocking data-quality warning instead.

## 9. AI narrative rules

- Input is the completed deterministic report only.
- The LLM cannot access raw billing rows.
- Output must satisfy a strict response schema.
- Every numeric statement must include a trace to a deterministic report path.
- The backend re-renders/validates display values from integer paise.
- Untraceable numbers invalidate the model response.
- Unknown metrics such as profit must be declared unavailable.
- Malformed output triggers one repair/retry, then a deterministic fallback narrative.
- A fallback summary must still include valid traces and must not depend on the LLM.

## 10. Required UI

### Screen 1 — EOD Reconciliation

- Clinic and date context.
- Cards for billed, collected, outstanding, refunds.
- Visit/refund/pending counts.
- Collection rate.
- Payment-mode breakdown table.
- Import status and validation issue access.

### Screen 2 — Analytics

- Revenue-by-hour chart.
- Highlighted peak hour and exact amount.
- Separate ranking cards for quantity and gross medicine revenue.
- Empty states for no sales/refund-only days.

### Screen 3 — AI Narrative Summary

- Owner-facing WhatsApp-style narrative.
- AI/fallback status.
- Copy-summary action.
- Traced Figures panel mapping displayed figures to report paths.
- Explicit unavailable-metric message where relevant.

### Shared layout

- Persistent sidebar across all three required screens.
- Clinic/date context remains visible.
- Responsive desktop and mobile behavior.

## 11. Dataset acceptance oracle

### 25 July 2026

- Received: 3.
- Accepted: 3.
- Rejected: 0.
- Billed: 0 paise.
- Collected: 0 paise.
- Outstanding: 0 paise.
- Refunds: 49,000 paise.
- Card refunds: 24,000 paise.
- UPI refunds: 25,000 paise.
- No peak hour.
- Empty sales medicine rankings.

### 26 July 2026

- Valid empty clinic-day.
- Received/accepted/rejected: 0/0/0.
- Every money metric: 0 paise.
- No peak hour.
- Empty rankings.

### 27 July 2026

The final row is rejected because `payment_mode` is missing.

- Received: 19.
- Accepted: 18.
- Rejected: 1.
- Gross line total: 326,000 paise.
- Discounts: 7,000 paise.
- Billed: 319,000 paise.
- Collected: 317,200 paise.
- Outstanding: 1,800 paise.
- Refunds: 0 paise.
- Peak hour: 13:00–14:00 UTC, 76,000 paise.

Payment-mode totals:

| Mode | Billed | Collected | Outstanding |
|---|---:|---:|---:|
| Cash | 127,500 | 127,000 | 500 |
| Card | 83,500 | 82,700 | 800 |
| UPI | 108,000 | 107,500 | 500 |

Top quantity:

1. OMEPRAZOLE — 18
2. METFORMIN — 14
3. AMOXICILLIN — 11
4. PARACETAMOL — 11
5. ATORVASTATIN — 10

Top gross medicine revenue:

1. ATORVASTATIN — 120,000 paise
2. OMEPRAZOLE — 72,000 paise
3. AMOXICILLIN — 66,000 paise
4. METFORMIN — 42,000 paise
5. PARACETAMOL — 22,000 paise

## 12. Non-functional acceptance criteria

- No floating-point money in backend calculations.
- No generic 500 for foreseeable input errors.
- Deterministic services have no LLM imports/dependencies.
- Update operation is atomic.
- Same accepted row set feeds every derived metric.
- Narrative is invalidated when the report changes.
- Tests cover normal, empty, refund-only, malformed, duplicate, overpayment, bad refund sign, and LLM schema failures.
- Browser console contains no significant errors.
- README explains formulas, assumptions, API contract, setup, tests, deployment, and known limitations.

## 13. Deliberately excluded scope

- Full EMR/clinic management.
- Patient records and appointments.
- Inventory purchasing.
- ABHA integration.
- Authentication/role system unless time remains.
- Managed PostgreSQL/AWS infrastructure.
- Profit computation.
- Automatic medicine spelling correction.
- LLM-generated arithmetic.

## 14. Confidentiality rule

Do not commit the provided assignment PDF or supplied billing files to a public repository. Use independently created synthetic test fixtures and keep evaluation files in `.gitignore`.

## Step 1 status

**Complete and locked.** Any later change to a formula or validation decision must be recorded as an explicit design revision and reflected in tests.
