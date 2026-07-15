# Branch Protection Target and Verification for `main`

## Authority boundary

This file defines the required branch-protection target and the evidence needed to verify it. It does not prove the current live GitHub configuration.

Current live branch-protection state: **UNVERIFIED EXTERNALLY**.

Do not describe `main` as protected or unprotected from repository text alone. Confirm the current state in GitHub repository administration and attach a dated evidence record.

## Required target

Apply a ruleset or branch-protection rule to `main` with the following controls:

1. Require a pull request before merge.
2. Require at least one approving human review for material changes.
3. Dismiss stale approvals when new commits are pushed.
4. Require Code Owner review where CODEOWNERS applies.
5. Require designated status checks to pass.
6. Require the branch to be current with `main` before merge, unless an approved merge-queue policy provides equivalent control.
7. Block force pushes.
8. Block branch deletion.
9. Apply the rule to administrators unless an explicitly documented emergency process provides equivalent control and auditability.
10. Preserve an auditable emergency override path; do not use undocumented bypasses.

## Required-check governance

The exact required-check list must be derived from current workflow names and reviewed after workflow consolidation. Historical names in this document are not automatically current authority.

Before changing required checks:

- inventory live required checks in GitHub settings;
- map each check to the workflow and proof it actually provides;
- identify duplicate, renamed, retired, neutral, skipped, and path-conditional checks;
- verify that documentation-only changes have a successful non-runtime path;
- verify that runtime changes cannot bypass required runtime evidence;
- record the change and rollback procedure.

## Check authoring rule

A required check must always reach a terminal success or failure result for every pull request to which the rule applies. Avoid job-level conditions that leave a required check skipped or neutral. Prefer step-level applicability checks with an explicit successful non-applicable path.

Example:

```yaml
jobs:
  required-gate:
    runs-on: ubuntu-latest
    steps:
      - name: Pass when not applicable
        if: ${{ !steps.scope.outputs.applies }}
        run: echo "Gate not applicable to this change; classified and passed."

      - name: Execute required proof
        if: ${{ steps.scope.outputs.applies }}
        run: python tools/verify_required_proof.py
```

## Human-review standard

- Automated checks do not replace human review for governance, security-boundary, data-model, release-authority, or production-operation changes.
- The pull-request author must not represent self-review as independent review.
- Exact reviewer identities must be verified before requesting review or changing repository permissions.
- Documentation-only changes may follow a lighter path only when the live ruleset and approved policy explicitly allow it.

## Emergency override standard

Any emergency bypass must record:

- triggering incident;
- requestor and approver;
- exact commit SHA;
- checks bypassed;
- risk accepted;
- deployment or mitigation performed;
- follow-up issue;
- time-bounded restoration of normal controls.

## Verification procedure

Capture a dated record from live GitHub settings showing:

- active ruleset or branch rule name;
- target branch pattern;
- pull-request requirement;
- approval count;
- stale-review dismissal;
- Code Owner requirement;
- administrator enforcement or bypass policy;
- force-push and deletion settings;
- exact required checks;
- merge queue status, if used;
- authorized bypass actors;
- verification date and reviewer.

Redact security-sensitive details where necessary, but do not omit the control result.

## Current repository dependencies

- #1337 — consolidate and map CI/certification workflows before finalizing the durable required-check set.
- #1343 — reconcile repository authority and buyer-defensible governance evidence.
- #1354 — ownership, attribution, and human-review governance; remains unapproved until human review is documented.
- #1357 — collaboration framework; does not itself change live repository settings.

## Release implication

Branch protection is one control in the production-entry system. Even a fully verified ruleset does not authorize production without the remaining release gates in `docs/CURRENT_RELEASE_STATUS.md`.
