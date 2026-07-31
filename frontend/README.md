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
