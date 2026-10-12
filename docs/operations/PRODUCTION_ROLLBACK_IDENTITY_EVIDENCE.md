# Production rollback identity evidence

Scope: retained production identity proof and automated last-known-good target selection.
Source workflow commit and deployed release commit are distinct, particularly for manual dispatch.
A successful workflow and an image tag do not independently prove the deployed build or immutable image.

## Evidence contract

After the existing production identity gate, both production workflows record a compact proof artifact
bound to repository, run ID, attempt, source commit, production app, deployed commit and configured image digest.
The proof requires healthy runtime and database, exact live SHA, and consistent release tag/version/run metadata.
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
and a healthy database with the exact restored build SHA. No source-SHA fallback or mutable-tag substitution is allowed.

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
