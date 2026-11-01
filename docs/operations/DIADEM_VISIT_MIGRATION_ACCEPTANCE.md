# Diadem custody visit foundation — source-only migration acceptance

Scope: issue #595, aftercare migration 0012. This is **not** childcare
activation, approval for real custody records, or an operational re-entry route.

## Invariants

- Existing DaycareAttendance rows remain immutable with visit_number=1.
- Existing DaycareRelease attendance OneToOne and audit rows remain unchanged.
- A newly recorded admission to the same school/child/care date can use a
  higher visit number only when it references a matching, append-only
  DaycareReentryAuthorization for the immediately preceding released visit.
- Authorization is specific to school, site, child, prior attendance and
  local care date, has a non-empty fixed reason, a director identity and an
  expiry. The authorization record cannot itself admit a child.
- Same-day re-entry **continues to be denied** in the check-in service and
  public API. No new check-in parameters, permissions or routes are enabled.
- Existing timezone-local care date and after-midnight release denials remain
  unchanged. Room transfer is not yet enabled.
- Live custody and the release path remain fail-closed for all missing/expired
  or cross-tenant authorizations.

## PostgreSQL migration and restore acceptance (not yet certified)

1. On a **disposable synthetic PostgreSQL 16 clone**, back up the
   pre-migration schema and synthetic data. Do not migrate live child records.
2. Assert each preexisting attendance has exactly one release at most and
   original (school, child, care_date) uniqueness. Record row counts and stable
   attendance IDs, release IDs, actor IDs and audit IDs before migration.
3. Apply the reviewed migration 0012, including the visit-number backfill
   default of one. Confirm the migration graph remains linear after 0011.
4. Compare record counts and referential relationships; assert no existing
   attendance/release/audit rows changed or disappeared, and no approvals were
   created as a side effect. Verify the new visit-level unique constraint and
   one-time approval link, including direct ORM rejection of an unapproved visit.
5. Run check-in, release, tenant, RBAC, roster and PostgreSQL simultaneous
   admission, staffing and release race tests on the exact commit. Verify the
   full backend suite and repository-policy/release-authority CI gates.
6. Verify a restore **from backup** to a fresh disposable database, including
   counts, IDs and release audit, before considering the migration accepted.
   A database down-migration is not a substitute for restore certification.
7. Do not deploy or enable re-entry; a subsequent reviewed change must
   implement director authorization creation, explicit one-use consumption,
   chronological visit locking and transactional duplicate/cross-room defenses.

## Separate operational backlog

- Same-day re-entry service and guarded director UI with revocation/expiry
- Room-transfer transactions that preserve open custody and staff ratios
- Overnight/emergency custody release with jurisdiction-approved protocols
- Independent hosted synthetic acceptance and policy-owner sign-off

No default grant or implicit school role may create a director authorization.
