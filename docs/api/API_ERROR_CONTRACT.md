# Canonical API Error Contract

Crown APIs should use one machine-readable error envelope when endpoints are created or materially revised.

```json
{
  "error": {
    "code": "stable_machine_code",
    "detail": "Human-readable explanation",
    "fields": {}
  }
}
```

## Rules

- HTTP status communicates protocol class; `code` communicates the stable Crown condition.
- Validation errors use `400` with field details.
- Authentication failures use `401`.
- Authorization failures use `403`; tenant object-existence protection may intentionally return `404`.
- Missing objects use `404`.
- Conflict/idempotency/state-transition failures use `409`.
- Rate limits use `429`.
- Unconfigured or degraded required integrations use `503`.
- Internal exception text, credentials, provider payloads, and stack traces are never returned.
- New endpoints must not invent alternate `message`/`error`/`detail` shapes without a compatibility reason.
- Existing legacy surfaces migrate incrementally through normal bounded PRs rather than a high-risk repository-wide response rewrite.
