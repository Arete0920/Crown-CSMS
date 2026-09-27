# CROWN Versioning and Release Policy

**Status:** current engineering policy
**Repository:** `Arete0920/Crown-CSMS`

## Versioning model

CROWN uses semantic versioning for product releases:

- MAJOR: incompatible platform, API, data-model, or deployment contract changes;
- MINOR: backward-compatible product capability or module additions;
- PATCH: backward-compatible defect, security, documentation, or operational corrections.

Pre-release identifiers may be used for release candidates, for example `1.0.0-rc.1`.

## Source identity

A semantic version never replaces exact source identity. Every release decision must retain the full Git commit SHA and immutable release tag.

## Tagging

Current release tags should use:

- `crown-vX.Y.Z`
- `crown-vX.Y.Z-rc.N`
- `crown-vX.Y.Z-hotfix.N`

Environment/deployment tags may remain separate when required by deployment tooling, but must resolve to the exact approved release SHA.

Historical predecessor tags remain immutable historical evidence and are not renamed or repointed.

## Release requirements

A release version may be published only when:

1. exact-head required checks pass;
2. unresolved critical/high findings are dispositioned;
3. schema/migration state is verified;
4. tenant and authorization boundaries are verified;
5. security/dependency gates pass;
6. release notes identify material changes and known limitations;
7. the immutable tag resolves to the approved full SHA;
8. runtime/deployment evidence is captured when representing a deployed release.

## Change discipline

Do not increment versions solely for documentation churn or CI retries. Version changes should represent a releasable product state or an intentional release candidate.

## Compatibility

Legacy route, identifier, or schema compatibility may be retained when removal would break supported integrations. Such compatibility must be explicitly documented, bounded, and prevented from becoming the current product name or new implementation authority.
