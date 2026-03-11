# Release Governance Protocol

## Purpose

Define one production truth path and reduce CI noise by separating required, scheduled, and manual lanes.

## Production Truth Contract

- Deploy success is true only when live runtime confirms expected release.
- Canonical endpoint is `/health`.
- Required fields for truth check:
  - `status` equals `ok`
  - `build_sha` equals expected release SHA (full SHA preferred)
  - `prod_deploy_tag` equals expected release tag when tag is provided
- GitHub workflow green/red is not a production truth signal by itself.

## CI Lane Model

- Required lane (branch protection):
  - PR quality gates only.
  - Deterministic, fast, no external mutation.
- Scheduled lane:
  - Nightly and periodic audits.
  - Reports findings but does not block merges by default.
- Manual certification lane:
  - Human-triggered evidence packs and release certification.
  - Produces auditable artifacts for release decisions.

## Workflow Ownership

- A workflow must have one owner team and one declared lane.
- Every workflow file should include:
  - owner
  - lane
  - trigger
  - required/non-required status
- Any workflow without clear lane/owner is non-compliant.

## PR and Issue Hygiene

- One active PR per layer:
  - UI proofs
  - API/runtime
  - CI/governance
- If duplicate PRs or issues exist for the same layer:
  - Select one canonical tracker.
  - Close duplicates with canonical pointer.
- Do not mix emergency runtime fixes with policy refactors in one PR.

## Release Evidence Pack

- Standard pack location: `release_proof/<timestamp>/`
- Minimum files:
  - `health.json`
  - `runtime.json`
  - `appsettings_keys.txt`
  - `summary.json`
- Recommended command:
  - `pwsh scripts/ops/collect-release-proof.ps1 -ExpectedSha <sha> -ExpectedTag <tag>`

## Break-Glass Rule

- Break-glass use is allowed only for active incident containment.
- Break-glass actions must include:
  - incident reference
  - operator
  - UTC timestamp
  - rollback or follow-up plan
- A post-incident cleanup PR is mandatory.

## Adoption Checklist

- Mark required checks to include only required lane workflows.
- Convert production deploy workflows to OIDC and canonical health verification.
- Keep artifact folders and local incident evidence ignored by git.
- Generate one release evidence pack for each production deploy candidate.
