# Production rollback identity evidence

Scope: retained production identity proof and automated last-known-good target selection.
Source workflow commit and deployed release commit are distinct, particularly for manual dispatch.
A successful workflow and an image tag do not independently prove the deployed build or immutable image.

## Evidence contract

After the existing production identity gate, both production workflows record a compact proof artifact
bound to repository, run ID, attempt, source commit, production app, deployed commit and configured image digest.
Schema 2 proof requires healthy runtime and database, exact reported and image-baked SHA, and consistent release tag/version/run metadata.
Only these allowlisted health fields are retained; credentials and arbitrary health payload fields are excluded.
Artifacts use attempt-specific names, fail if absent, and retain for 30 days.

Recovery searches the two trusted workflow identities, with bounded pagination and at most 40 prior eligible runs.
A newer production attempt supersedes an older failure and blocks its automated target selection.
It accepts only terminal-success runs completed before the failed run began, with one unexpired matching artifact.
It validates archive shape and manifest origin/identity; missing evidence remains blocked.
GitHub API credentials are removed when artifact downloads redirect to external storage.

Production deployment, automatic recovery and the manual rollback drill share one serialization group.
The workflow policy mandates this shared group for exactly those four known image writers; unrelated duplicate groups remain rejected.
Automatic recovery retains the production environment approval boundary.
Before mutation, recovery verifies the recorded digest still exists in the configured registry.
It restores by digest and applies the proven release metadata. Verification requires both the configured digest
and a healthy database with matching reported and image-baked restored build SHA.
The artifact identity comes from build_info.py written into the container build; overriding a runtime BUILD_SHA cannot satisfy it.
Older artifacts or endpoints without that independent field remain ineligible; no historical identity is inferred.
Image creation also records BUILD_TIME_UTC. Health separates that build timestamp (unknown for unbaked source) from observed_at_utc; a current probe time is not a deployment/build time. No source-SHA fallback or mutable-tag substitution is allowed.

## Operational limits and acceptance

This contract does not manufacture proof for earlier deployments. Missing or expired historical proof requires
manual incident control and separately verified operational evidence. Do not create synthetic historical artifacts.
Provider authentication, production approvals, concurrent operations, migration compatibility, data restore,
retention duration and actual recovery rehearsal remain environment-specific acceptance requirements.
Source tests and merging this control do not authorize a production deployment or a rollback drill.
A prior manually dispatched build must be selected using its proven deployed commit even when its workflow source differs.
Negative acceptance cases include foreign target/repository, wrong attempt, expired/duplicate artifacts,
mismatched digest or live SHA, incomplete source run and inconsistent release metadata.

Rollback of this source change: revert its isolated PR. Do not move or republish production tags.

## Source dependency prerequisites

The compact dependency review from PR228 is preserved here as part of the source proof prerequisites. Its original standalone record remains in that PR and commit history.

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
