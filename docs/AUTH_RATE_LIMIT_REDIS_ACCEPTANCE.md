# Isolated Redis authentication counter verification

Run from a clean checkout of the exact commit being evaluated, with Python 3.12,
the existing `backend/requirements.txt` dependencies and `redis-server` installed
on Linux:

```bash
git rev-parse HEAD
python scripts/ops/verify_auth_rate_limit_redis.py
```

The existing Tests workflow runs this command before tenant fixture regressions.
Its failure blocks the existing `pytest-internal` gate through `tenant-fixtures`.
Missing dependencies are failures, not skips. Retain the Actions run URL, checkout
SHA, printed authentication module SHA-256 and terminal result as source evidence.

The harness creates a disposable Redis process with TCP disabled, persistence
disabled and a private temporary Unix socket. Two separately spawned Python
workers load the repository's actual authentication counter file directly with
minimal isolated Django settings, avoiding application package initialization
and its Celery/schema-extension imports. No deployment settings, database, credentials
or target URLs are loaded. Each case terminates its workers and owned Redis and
removes the temporary directory, including when an assertion fails.

Checks cover all four authentication counter scopes and their current identity
thresholds, visibility between workers, concurrent increments, identity cleanup
without erasing the IP bucket, independent IP/scope buckets, and fail-closed reads
and failure recording after the owned Redis process stops. Existing endpoint
regressions remain responsible for HTTP 429/503 and token/permission behavior.

This is source integration evidence using a real isolated Redis service. It does
not certify hosted Redis credentials, TLS, topology, eviction policy, deployed
SHA, cross-instance routing or application runtime acceptance. It accepts no
hosted target and grants no deployment or configuration authority. Before an
operational rollout, the authorized operator must separately satisfy the hosted
shared-cache prerequisites in `docs/AZURE_DEV_APP_SETTINGS.md`, including synthetic
cross-worker endpoint and outage checks, successful login/refresh and rollback
readiness. Never disable the shared-counter requirement to restore availability.
