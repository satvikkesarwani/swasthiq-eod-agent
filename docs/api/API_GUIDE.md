# API Guide

Base path: `/api/v1`.

## Health

`GET /health`

Returns application status, database connectivity, and version. It does not expose paths, secrets, or provider state.

## List Clinic Days

`GET /clinic-days?clinic_id=&date_from=&date_to=&limit=10&offset=0`

Returns recent stored clinic-day summaries and backend money totals.

## Import Or Replace Clinic Day

`PUT /clinic-days/{clinic_id}/{business_date}`

Request body:

```json
{
  "clinic_name": "Demo Clinic",
  "clinic_location": "Kanpur",
  "records": []
}
```

The backend validates rows, computes the deterministic report, and atomically creates/replaces the clinic-day. Non-empty all-invalid uploads return `422`.

## Get Report

`GET /clinic-days/{clinic_id}/{business_date}`

Returns canonical reconciliation, analytics, data-quality warnings, ingestion counts, hashes, and safe metadata.

## Get Validation Issues

`GET /clinic-days/{clinic_id}/{business_date}/errors?limit=100&offset=0`

Returns safe validation issue fields only. Raw rejected rows are not returned.

## Get Narrative

`GET /clinic-days/{clinic_id}/{business_date}/narrative`

Returns the current generated or fallback summary when it matches the current deterministic report.

## Generate Narrative

`POST /clinic-days/{clinic_id}/{business_date}/narrative`

Request body:

```json
{ "force_regenerate": false }
```

Returns a backend-validated narrative with traces and unavailable metrics. Missing NVIDIA credentials return deterministic fallback, not a failed app. When `NVIDIA_API_KEYS` contains multiple comma-separated keys, the backend rotates one key per provider call before falling back to `NVIDIA_API_KEY`.
