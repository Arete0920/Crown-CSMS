# Backend dependency refresh — October 12, 2026

Owner authorized completing the repository PR backlog. This is one independently reversible
manifest-and-lock refresh, not runtime lock adoption or production deployment.

## Reviewed updates

| Dependency | Manifest change | Effective lock change |
| --- | --- | --- |
| Django | 5.2.17 -> 5.2.18 | 5.2.17 -> 5.2.18 |
| Django REST Framework | 3.18.1 -> 3.18.3 | 3.18.1 -> 3.18.3 |
| Authlib | minimum 1.6.11 -> 1.8.0 | already locked at 1.8.0 |
| Celery | minimum 5.4.0 -> 5.6.3 | already locked at 5.6.3 |
| Sentry SDK | minimum 2.0.0 -> 2.71.0 | already locked at 2.71.0 |

PRs #228–#231 contribute these compatible changes. The Django major proposal #232 is
superseded for this repair by the official 5.2.18 security patch on the current LTS line.
Django's October 6 announcement covers the supported 5.2 branch:
https://www.djangoproject.com/weblog/2026/oct/06/security-releases/
Major framework adoption would require a separately scoped compatibility decision.

Compiler: pip-tools 7.6.2; target Linux/Python 3.12. Regeneration retains every other exact
package version and changes no package membership. Source and lock hashes are updated together.
No new direct dependencies or optional integrations are introduced. Existing tenant, authorization,
telemetry, migration and release controls remain authoritative.

Validation: lock verifier and its five rejection/acceptance tests; hash-required, binary-only
resolution dry-run. Exact-head required CI, security scans and complete backend suite must pass
before merge. Local/source checks do not prove deployed remediation or operational readiness.
Rollback: revert the coherent manifest/lock/metadata change; deployment remains separately governed.
