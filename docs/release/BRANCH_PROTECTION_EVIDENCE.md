# Branch Protection Evidence

**Status:** current main protection verified October 4, 2026; re-verify before decisions
**Last historical capture:** 2026-04-11

## October 4, 2026 live configuration

The owner authorized browser administration. GitHub displayed “Branch protection rule created.” The saved rule applies to `main`; a separate branch API read at main `e979e60421eb57f82dca275af26100eadef93504` returned `protected: true` and required-check enforcement `everyone`.

Saved UI settings require pull requests, up-to-date branches, status checks and conversation resolution. Required human approvals are zero under the solo-maintainer policy. Administrator bypass is disabled; force pushes and branch deletion are not allowed. Linear history and signed-commit requirements are not enabled. No security gate was disabled or bypassed.

The 16 required contexts are bound to GitHub Actions (app ID 15368):

- `Analyze (javascript-typescript)`
- `Analyze (python)`
- `Release authority gates`
- `contract-gate`
- `backend-gate`
- `backend-pip-audit`
- `gitleaks`
- `dashboards-build-gate`
- `dependency-review`
- `frontend-npm-audit`
- `schema-governance`
- `pytest-gate`
- `release-verify`
- `repository-policy`
- `wallet-npm-audit`
- `test`

Dependency Graph was enabled and the saved security UI displayed On. Real Dependency Review succeeded on PR #75 head `f4c48024c05ad83e552743578114704f4ad30491` (run 37210135688). Main's old skip-success workflow still needs replacement by the reviewed controls. Wallet auditing is introduced by PR #74; other branches must incorporate that workflow before its required check can be satisfied. Path-filtered supporting checks are not required independently; backend-gate includes tenant verification.

These settings do not clear retained-history exposure, establish hosted readiness or prove license/IP clearance. Secret Protection, Dependabot alerts/security updates and private vulnerability reporting were not enabled or certified by this administrative change. Historical ref remediation needs a separate coordinated procedure; this protection change does not authorize a force update.

## Earlier historical boundary

The following paragraphs preserve predecessor observations, not the live October 4 configuration.

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

For a later decision, capture fresh live evidence rather than treating this dated record as permanent proof.

Historical exports and screenshots remain useful provenance but are not current authority.
