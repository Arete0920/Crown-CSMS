# Production Parity Probe

Generated: 2026-05-25 15:18:00

## Live Health Endpoint

- URL: https://crown-api-dev.azurewebsites.net/health/
- Payload:

```json
{"ok": true, "status": "ok", "demo_mode": false, "build_sha": "a609d03e038a42d3511c9369cfc8f6385b1dbe2b", "prod_deploy_tag": "", "env": "production", "build_time_utc": "2026-05-25T19:16:20.182848+00:00", "version": "crown-unknown", "db": "ok", "deploy_run_id": "26406470816", "deploy_workflow": "Dev Deploy (rc/**)"}
```

## Referenced Deploy Run

- Run ID: 26406470816
- Workflow: Dev Deploy (rc/**)
- Status/Conclusion: completed/success
- URL: https://github.com/tcmegahan/Crown2026/actions/runs/26406470816
- Run headSha: 7af6c4917cd820d0402b0a98442b1e4986c6cd1d

## Decision

- Decision: FAIL
- Reason: Live health build_sha (a609d03e038a42d3511c9369cfc8f6385b1dbe2b) does not match referenced run headSha (7af6c4917cd820d0402b0a98442b1e4986c6cd1d).
- Corroboration: Earlier prod-integrity-proof evidence also recorded SHA mismatch behavior (see 12_first_error_signatures.md, run 26389898494).
