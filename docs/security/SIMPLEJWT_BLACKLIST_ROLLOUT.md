# SimpleJWT refresh-token blacklist: controlled rollout

**Scope:** security issue #350; accepted runtime and database evidence must be recorded separately from a source merge. This document does not approve production deployment, credential disclosure, database rewrites or emergency privilege changes.

## Why the change matters

CROWN sets `ROTATE_REFRESH_TOKENS=True` and `BLACKLIST_AFTER_ROTATION=True`. Upstream SimpleJWT only blacklists a consumed refresh token when `rest_framework_simplejwt.token_blacklist` is installed and its database tables exist. Without that app, old refresh tokens remain usable until expiry. Once the app is enabled, token issuance itself may write to `token_blacklist_outstandingtoken`. Deploying code before migrating tables may break logins.

References:
- https://django-rest-framework-simplejwt.readthedocs.io/en/stable/settings.html
- https://django-rest-framework-simplejwt.readthedocs.io/en/stable/blacklist_app.html
- https://github.com/jazzband/djangorestframework-simplejwt/releases/tag/v5.5.1

## Required preflight in each actual deployment environment

1. Identify the exact deployed CROWN source SHA and currently installed SimpleJWT version. Check which Django settings module, database alias, and tenant/auth routes are active. No credentials or token values in evidence.
2. Make an approved, tested recovery point. Verify database restore can be completed; record the custodian, environment, UTC time, and restricted evidence location.
3. **Read** the `django_migrations` rows for `app='token_blacklist'` and inspect SimpleJWT 5.5.1's migration graph, especially `0013_blacklist`. Confirm whether a locally generated `0013` predates the vendor release and whether downstream migrations depend on it. Stop and obtain a reviewed specific remediation if the graph conflicts: never blindly fake, delete, or roll back rows.
4. On a disposable database copy matching the actual starting schema, run Django's migration plan and migrations with the **candidate code**. Confirm both token tables and token indexes, then rehearse rollback and recovery. No school data or credentials in public CI.
5. Require the controlled deployment sequence to apply approved database migrations **before serving traffic with the new code**. Ensure only the intended environment is targeted and maintenance/runbook authority is recorded. Avoid adding manual production shell commands in public issue comments.
6. Run an isolated, synthetic token proof: issue a refresh, rotate once, verify old token rejected (401), and replacement token usable. Test invalid/expired tokens and rate limit behavior, exercise tenant context, inspect logs for token absence. Preserve only redacted status/case counts. Distinguish staging from production.
   On PostgreSQL, concurrently submit the same refresh token from two connections and require exactly one 200 and one 401. Row locking is database-specific: SQLite-only tests do not certify this guarantee. Inspect transactions and lock behavior under multi-worker load; no token data in output.
7. Establish retention/maintenance for `flushexpiredtokens` on an approved recurring schedule and measure outstanding-token growth. Audit DB writes and failure behavior for the new token persistence.
8. Record exact deployed build/version, schema/migration state, 401/200 contract evidence, rollout owner and rollback decision. Close #350 only after the target runtime meets all gates.

## Source acceptance

The source PR must pass exact-head Django and PostgreSQL migration/test suites, static/security CI, and protected main governance. This checklist does **not** authorize making CI fail open, deploying without migrations, or asserting CROWN is SOC 2 compliant. Keep unrelated authentication rollout #330–#333 independently governed.
