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

Prompt 5 intentionally ships polished placeholders only. Import, reconciliation, analytics, and narrative data integration are deferred to later prompts.

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
