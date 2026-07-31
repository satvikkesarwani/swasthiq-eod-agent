# Logging And Observability

## Log Levels

- `DEBUG`: local troubleshooting only.
- `INFO`: request lifecycle, import completion, narrative lifecycle.
- `WARNING`: expected recoverable failures such as validation rejection, provider fallback, rate limit.
- `ERROR`: unexpected internal failures.

Production default:

```env
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_INCLUDE_REQUEST_ID=true
```

## Request IDs

Each request receives or preserves `X-Request-ID`. The same value is returned on responses and attached to app logs through request context.

Synthetic JSON example:

```json
{"event":"request.end request_id=req_demo method=GET path=/api/v1/health status=200 elapsed_ms=4","level":"INFO","logger":"app.main","request_id":"req_demo"}
```

## Domain Events

Safe operational events include:

- `ingestion.replace start`
- `ingestion.validation complete`
- `analysis.report.done`
- `narrative.cache_hit`
- `narrative.generation_started`
- `narrative.provider_failed`
- `narrative.fallback_used`
- `narrative.generation_completed`

## Redaction Policy

Never log:

- billing request bodies or raw rows
- rejected raw rows
- narrative text
- prompts or raw model output
- provider response bodies
- API keys, cookies, tokens, passwords
- full database URLs

The backend redaction helper masks common sensitive keys. Frontend logging redacts records, summary/narrative fields, clipboard content, and secret-like keys.

For NVIDIA key rotation, store keys only in backend deployment secrets as `NVIDIA_API_KEYS=<key-1>,<key-2>`. Logs may mention provider fallback categories but must never include key values.

## Safe Debugging Workflow

1. Use request ID from the UI or response header.
2. Search Railway logs for the request ID.
3. Check route, status code, and safe domain events.
4. For narrative issues, inspect fallback reason code, trace count, and provider category.
5. For database issues, verify migrations and persistent volume writability.

## Railway Logs

Railway captures container stdout/stderr. Use JSON logs in production and never paste `.env` values into log search fields.
