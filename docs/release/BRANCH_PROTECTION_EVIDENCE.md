# Branch Protection Evidence

**Status:** historical evidence only; live configuration must be re-verified  
**Last historical capture:** 2026-04-11

This document preserves predecessor branch-protection evidence. It is **not** current proof of the live `Arete0920/Crown-CSMS` administrative configuration.

The current repository is public, the operating model is solo-maintainer, and no current repository ruleset was visible through the connected GitHub read surface on September 27, 2026. The connector does not have administration permission to verify or modify classic branch-protection settings.

## Current intended configuration

See:

- `docs/release/BRANCH_PROTECTION_REQUIRED_CHECKS.md`
- `docs/governance/SOLO_MAINTAINER_BRANCH_PROTECTION_POLICY.md`
- `docs/CURRENT_RELEASE_STATUS.md`

## Evidence required for current status

A current branch/ruleset evidence capture should verify:

- pull request required before merge;
- zero required human approvals while solo-maintained;
- required automated gate contexts;
- conversation resolution;
- no force pushes;
- no branch deletion;
- direct-push restriction;
- administrator/emergency bypass posture;
- secret scanning and push protection;
- dependency/security features;
- private vulnerability reporting.

Until that evidence is captured, do not describe branch protection as independently verified current configuration.

Historical exports and screenshots remain useful provenance but are not current authority.
