# SwasthiQ EOD Frontend

React + TypeScript frontend foundation for the SwasthiQ EOD Billing & Analytics Agent.

## Requirements

- Node `25.6.x`
- npm `11.8.x`

## Setup

```bash
npm install
npm run generate:api
npm run dev
```

By default, frontend requests use same-origin `/api/v1`. During local development, Vite proxies `/api` to `VITE_DEV_PROXY_TARGET`, defaulting to `http://localhost:8000`.

Set `VITE_API_BASE_URL` only when the backend is hosted on a separate origin. Do not include `/api/v1` in that value.

## Quality Commands

```bash
npm run typecheck
npm run lint
npm run test:run
npm run test:coverage
npm run build
```

## Routes

- `/reports`
- `/reports/:clinicId/:businessDate/reconciliation`
- `/reports/:clinicId/:businessDate/analytics`
- `/reports/:clinicId/:businessDate/narrative`

Prompt 7 ships the production reconciliation route. Prompt 8 ships the production analytics route. The narrative page remains a placeholder until its dedicated prompt.

## Import Workflow

`/reports` now supports the Prompt 6 billing-log workflow:

- enter clinic ID, optional clinic name/location, and business date;
- choose or drag one `.json` file;
- browser checks file size, readability, JSON syntax, and array root only;
- submit the complete parsed array to `PUT /api/v1/clinic-days/{clinic_id}/{business_date}`;
- show created/replaced/unchanged and partial-import outcomes;
- review safe validation issues from the backend;
- filter, page, and open recent reports.

The frontend accepts files up to `4.75 MiB` while documenting the backend `5 MiB` request limit. It does not persist raw billing records, preview raw rows, calculate money, or validate business row rules.

## Reconciliation Dashboard

`/reports/:clinicId/:businessDate/reconciliation` uses a React Router loader to read the canonical clinic-day detail endpoint on deep link, refresh, and explicit "Refresh report" actions.

The page includes:

- clinic/date/status context and safe report metadata;
- four prominent cards for Total Billed, Total Collected, Outstanding, and Refunds;
- accessible payment-mode table for Cash, Card, and UPI backend rows;
- collection-rate and pending/refund visit counts when supplied by the backend;
- partial-import banner with Prompt 6 validation-issues drawer access;
- empty-day, refund-only, sales-and-refunds, warning, not-found, and retryable failure states.

The frontend does not derive business metrics. It only formats backend-supplied paise, dates, counts, and percentages.

## Analytics Dashboard

`/reports/:clinicId/:businessDate/analytics` uses a React Router loader to read the canonical clinic-day detail endpoint on deep link, refresh, and explicit "Refresh analytics" actions.

The page includes:

- clinic/date/status context and safe report metadata;
- backend peak billing hour card;
- Recharts revenue-by-hour bar chart plus semantic fallback table;
- medicine rankings by backend quantity rank and backend revenue rank;
- partial-import context and validation-issues drawer access;
- empty-day, refund-only, sales-and-refunds, warning, not-found, malformed-response, and retryable failure states.

The frontend does not calculate analytics. It only formats backend-supplied paise, dates, counts, UTC hour labels, ranks, and warning text.
