# Legacy Crown refresh-token rotation contract

This contract applies only to `/api/auth/login/` and `/api/auth/refresh/` in
`crown_api.auth_views`. It does not apply to SimpleJWT's `/api/v1/auth/` routes.

## Client behavior

- Store the `refresh` value returned by login.
- On refresh, submit that value and, only after a successful response, replace it
  with the response's new `refresh` value. Do not retry or reuse the consumed
  value after an ambiguous result; authenticate again if the replacement was
  not received.
- A refresh value can be consumed exactly once. Reuse returns `401`; persistence
  failures return `503` without issuing access or replacement tokens.
- Existing correctly signed refresh tokens without `jti` remain eligible for
  one refresh until their original expiry. Their retirement key is a
  server-keyed fingerprint; token contents and fingerprints must not be logged.

## Deployment sequence and rollback

1. Inventory all legacy clients and deploy the replacement-token handling before
   enabling the rotating server code. Clients that ignore the replacement will
   need to authenticate again after their first successful refresh.
2. Review the dedicated `crown_api.0014_consumedcrownrefreshtoken` schema change.
   Verify the actual DEV and production migration ledgers, database capacity,
   and a current restorable backup/restore point with the release owner.
3. Apply and verify the additive schema migration using
   `python manage.py migrate_with_lock` before directing traffic to code that
   writes the consumption table. Do not start the new application against a
   schema where this migration is unapplied.
4. Deploy the exact reviewed application head only after schema verification,
   then verify refresh, replay rejection, and database availability against the
   deployed revision.

The new table is intentionally retained if the application is rolled back.
Do not roll back to stateless refresh handling after the rotating code has
accepted traffic: that would make consumed tokens usable again. If safe
roll-forward is unavailable, disable the legacy refresh endpoint and require
clients to authenticate again. A schema downgrade is not part of application
rollback.

Repository implementation and tests do not establish the live DEV/production
migration state, a restorable production restore point, client readiness,
human release approval, or deployed behavior. Those remain release gates and
must be evidenced on the exact candidate revision before this issue is
considered operationally accepted.
