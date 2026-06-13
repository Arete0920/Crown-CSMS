# S4 Current CI Proof - 2026-06-12

## Decision

S4 current result: **COMPLETED AND VERIFIED / READY-FOR-INDEPENDENT-REVIEW**.

The S4-D1 historical tag supersession has been executed by updating `.github/prod-integrity-target.json` from `prod-2026-03-28-02` to `main-canonical-20260612` with expected SHA `3cf22a47ba29481adc435cb85a0f00fcd9bf0d30`.

Production deploy run `27411458958` completed successfully and verified deployment identity. That successful deploy is current proof context, not release authorization and not merge approval for this docs lane.

A fresh `prod-integrity-proof` run against the updated target completed successfully on PR head `42ccce8c4f4fef233c15ace6bc3075a55c5f1a60`.

Release remains NO-GO because independent review, S8 compliance/customer-readiness, and S9 pilot-entry/exit gates remain open.

## Branch Under Review

Branch: `closure/canonical-blocker-s0-s4-s8-s9-20260612`

Verified PR head for this proof update: `42ccce8c4f4fef233c15ace6bc3075a55c5f1a60`.

Reviewers must verify the current PR head SHA in GitHub immediately before review or merge.

## Hosted CI Summary - PR Checks

Prior hosted PR checks showed zero failures but included pending checks. The current PR head later produced successful current-head CI runs and successful prod-integrity proof.

- Current observed failures: 0 for the S4 proof run
- prod-integrity-proof run: `27436072680`
- prod-integrity-proof conclusion: `success`
- Verdict: **S4 proof completed; independent review still required**

## Hosted CI Summary - Main Branch / Deploy Integrity

### Prior failure classification

| Workflow | Run ID | Failure signal | Category |
|---|---|---|---|
| prod-integrity-proof | 27402673162 | `health build_sha != expected_sha` from `.github/prod-integrity-target.json` | Configured expected-SHA mismatch against live `/api/health` response |

### S4 Item D1 - Deploy parity blocker

- Prior target: `prod-2026-03-28-02`, expected SHA `c7ab4328...`
- Updated target: `main-canonical-20260612`, expected SHA `3cf22a47...`
- Workflow logic: compare production `/api/health` SHA fields to `expected_sha` from `.github/prod-integrity-target.json`
- Option B has been executed: historical target supersession via config update
- Confirmation run: `27436072680`
- Confirmation result: **PASS**

## Production Deploy Context

Production deploy run `27411458958` completed successfully after the earlier stale-target proof failure. The closing S4 integrity confirmation is `prod-integrity-proof` run `27436072680`, which completed successfully against the updated target.

## Local Gate Status

Local/generated evidence remains reviewer-reproducible evidence, not repository-tracked proof unless copied into a tracked artifact:

- `106_crown_full_completion_truth_gate.ps1`: generated output is local/gitignored unless separately attached or committed
- Reviewers must reproduce or inspect current evidence before relying on this gate for broader release closure

## Definition of Done

S4 can be treated as completed and ready for independent review because:

1. Current PR proof head is recorded
2. The deploy-integrity target was updated through the S4-D1 Option B supersession
3. `prod-integrity-proof` passed against `.github/prod-integrity-target.json`
4. The prior stale-target failure is superseded by the successful proof run

No release GO is authorized by this document.
