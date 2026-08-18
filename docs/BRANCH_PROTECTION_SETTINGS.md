# Branch Protection Target and Verification for `main`

**Status:** Supporting governance control  
**Last reconciled:** 2026-08-18  
**Authority:** `docs/CURRENT_RELEASE_STATUS.md`, current GitHub repository settings, and the exact current `main` identity

## Authority boundary

This file defines the required branch-protection target and the evidence needed to verify it. It does **not** prove the current live GitHub configuration.

Current live branch-protection state: **UNVERIFIED EXTERNALLY** until verified directly in GitHub repository administration.

Do not describe `main` as protected or unprotected from repository text alone. Confirm the current state in GitHub and retain dated evidence for any release or ownership-transfer decision that depends on the control.

## Required target

Apply a ruleset or branch-protection rule to `main` with the following controls:

1. Require a pull request before merge.
2. Require at least one approving independent human review for material changes when an eligible reviewer is available and governance requires it.
3. Dismiss stale approvals when new commits are pushed.
4. Require Code Owner review where the live ruleset and CODEOWNERS policy require it.
5. Require designated status checks to pass.
6. Require the branch to be current with `main` before merge, unless an approved merge-queue policy provides equivalent control.
7. Block force pushes.
8. Block branch deletion.
9. Apply the rule to administrators unless an explicitly documented emergency process provides equivalent control and auditability.
10. Preserve an auditable emergency override path; do not use undocumented bypasses.

## Required-check governance

The exact required-check list must be derived from current workflow names and current GitHub settings. Historical check names are not authority.

Before changing required checks:

- inventory live required checks in GitHub settings;
- map each check to the workflow and proof it actually provides;
- identify duplicate, renamed, retired, neutral, skipped, and path-conditional checks;
- verify that documentation-only changes have an explicit successful non-runtime path where required;
- verify that runtime changes cannot bypass required runtime evidence;
- record the exact setting change, actor, date, reason, and rollback procedure.

## Check authoring rule

A required check must reach a terminal success or failure result for every pull request to which the rule applies. Avoid job-level conditions that leave a required check skipped or neutral. Prefer step-level applicability checks with an explicit successful non-applicable path.

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

- Automated checks do not replace independent human review where governance requires it.
- The pull-request author must not represent self-review as independent review.
- Exact reviewer identities and authority must be verified before requesting approval or changing repository permissions.
- Where no eligible independent reviewer exists, use only the currently approved compensating-control process and describe it accurately; do not call it independent review.
- Documentation-only changes may follow a lighter path only when the live ruleset and approved policy explicitly allow it.

## Emergency override standard

Any emergency bypass must record:

- triggering incident;
- requestor and authorized approver;
- exact commit SHA;
- checks or controls bypassed;
- risk accepted;
- deployment or mitigation performed;
- follow-up action;
- time-bounded restoration and verification of normal controls.

Never copy predecessor repository IDs, ruleset IDs, branch-protection payloads, or bypass commands into a current change without verifying them directly against Crown-CSMS first.

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

Current governance decisions must be derived from:

- `docs/CURRENT_RELEASE_STATUS.md` for release and handoff posture;
- `docs/canonical/CANONICAL_DOCUMENT_INDEX.md` for documentation authority;
- `docs/ownership/OWNER_HANDOFF.md` for transfer controls;
- current GitHub rulesets/branch settings for live enforcement;
- current workflow definitions for check names and behavior.

Historical predecessor issue numbers, ruleset IDs, or repository settings are provenance only and are not current Crown-CSMS authority.

## Release implication

Branch protection is one control in the production-entry system. Even a fully verified ruleset does not authorize production or complete owner turnover without the remaining exact-source, runtime, recovery, account-transfer, and acceptance gates in `docs/CURRENT_RELEASE_STATUS.md` and `docs/ownership/OWNER_HANDOFF.md`.
