# Aftercare permission scope repair

Base: b0a537fc6ce3bcb26eb6b007b43088bd3da1e2e1
Branch: fix/aftercare-canonical-permission-scope
Decision owner: TC Megahan; remediation authorized.

Outcome: bind wizard read/write permission checks to the validated canonical school used for config access. Allowed scope: aftercare wizard, authorization regression tests, this record. No global RBAC, migrations, accounting, workflow, dependency, or deployment changes.

Verification: six isolated actual-view control-flow cases passed locally, covering GET/POST, allowed/denied requests, and absent/conflicting request.school. Added a direct DRF regression for permissions granted only in another school. Full Django tests and exact-head CI remain required; local isolated checks are not integration certification.

Rollback: revert this commit; no schema changes. Independent review and deployed-runtime behavior are NOT VERIFIED.
