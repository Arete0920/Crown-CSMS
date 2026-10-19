# Legacy Crown JWT: one-time refresh consumption

**Security finding:** #372. This is distinct from SimpleJWT issue #350.

The still-used `/api/auth/refresh/` endpoint previously accepted the same
signed Crown refresh token repeatedly. The source correction issues randomized
new refresh tokens, persists the SHA-256 digest of each successfully consumed
token under a unique database constraint, and returns a replacement refresh
with each access token. Old signed tokens without a JTI can be consumed once.
No bearer or token digest is logged.

## Migration-before-traffic deployment gate

This source is **not safe to activate** until
`crown_api.0014_legacy_refresh_consumption` has been applied and the
`crown_api_legacyrefreshconsumption` table, unique token_digest constraint,
user foreign key and expiration index are verified in the actual target
PostgreSQL database. Missing schema causes authentication to return 503
rather than mint unchecked access tokens.

The current DEV deployment's reviewed migration allowlist expressly
**does not authorize** 0014. Establish a separate exact-SHA reviewed
DEV/production migration-before-traffic stage under the existing
PostgreSQL migration lock, reconcile all unrelated pending migrations and
historic database schema, verify backup/restore and obtain an operating
recovery point before enabling the replacement runtime. The existence of
this migration file is not deployment approval.

## Client transition

Existing clients expecting only `access` may parse the unchanged access
field. They **must** also persist the new `refresh` value from each
successful refresh, replacing the previous one. Reusing the consumed
credential receives 401 even if its original signature and expiry are
otherwise valid. Retained old tokens without a JTI are handled by digest
identity once; no global logout is assumed. Confirm mobile, parent, teacher,
admin and Windows-demo clients before activating the behavior.

## Acceptance

- Run the existing legacy login, refresh and authentication rate-limit tests.
- On PostgreSQL, concurrently redeem one signed token from two connections.
  Exactly one 200 and one 401 must result, and only one digest row may exist.
- Prove sequential replay denial, fresh token usability, invalid/absent expiry
  denial, database-unavailable 503 and school/role continuity.
- Verify fresh exact-head CI, DEV schema and hosted flows, retention policy for
  expired digest records, and production migration/rollback authority.
- Record redacted environment/source/schema/test evidence, never credentials.
- Keep #372 open until deployed runtime evidence is complete.

### Expired-digest retention

The `purge_expired_legacy_refresh` management command defaults to a bounded,
read-only inspection. With separately authorized `--apply`, it removes only
rows whose signed token expiry has already passed, in bounded batches.
For example, `python manage.py purge_expired_legacy_refresh --apply
--batch-size 500 --max-batches 20` removes at most 10,000 records per run.
The command never prints JWTs or stored digests. Schedule and monitor it only
after the legacy schema and production operation are explicitly accepted.

The existing canonical `Tests` workflow's `survey-postgresql` job runs these
legacy refresh tests against its isolated PostgreSQL 16 service. No additional
workflow or paid service is created. CI reports are retained under the
existing PostgreSQL test artifact.

## Explicit activation state

The source rollout uses `CROWN_LEGACY_REFRESH_ONE_USE_ENABLED`, which defaults to
`false`. A protected source merge must not turn on ledger-backed consumption
or require the new table in hosted applications. Test settings enable the
feature only for migrated synthetic test databases. Until the operator
verifies `crown_api.0014_legacy_refresh_consumption`, schema constraints,
client replacement-token handling, and deployed replay behavior, keep the
hosted setting disabled. The legacy refresh route retains its existing
stateless behavior while disabled; this is not revocation certification.
After governed schema-first migration and client acceptance, activation on
the intended environment is a separate operator-controlled configuration
change. Never enable the feature on production merely because CI passed.
