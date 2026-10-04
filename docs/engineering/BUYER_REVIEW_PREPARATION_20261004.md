# Buyer repository review preparation

Assessment date: October 4, 2026. Intended review window: October 11, 2026.
Baseline refreshed after PR #74 at `b47e5f2d1930f2790cbbf6c0df4780662d1326a2`; re-resolve current `main` before any decision.
This is a remediation register, not clearance for source distribution, production, or transfer.

## Cleanup and evidence boundaries

Remove obsolete implementation captures and unused tooling only after checking references and operational purpose. Preserve accurate authorship, ownership records, required third-party notices, license decisions, and evidence of security remediation. Ordinary current-tree deletion does not remove Git history.

History maintenance must follow the [existing security runbook](../security/ed25519-history-remediation-runbook.md). Prepare and verify an isolated rewrite before proposing exact shared-ref changes. A general cleanup instruction is not a verified inventory, proof of key retirement, or an approved maintenance window. Preserve necessary evidence under controlled custody; never include private keys or raw token findings in buyer material.

## Work and acceptance register

| Work | Observed status | Closure evidence |
|---|---|---|
| Wallet dependency remediation | **Merged in PR #74** with locked npm install, replacement signing implementation, audit coverage and signing tests | Preserve exact-head audit/test evidence; real Apple certificate/device acceptance remains environment-specific |
| Dependency Review | Main workflow prints an unavailable/skip message and returns success | Actual pinned review action passes with Dependency Graph enabled; no skip-success fallback |
| Retained-history security | Known private-key path remains in published history; three earlier documentation-token candidates unresolved | Trust-consumer inventory, retirement verification, adjudicated all-ref scan, reviewed rewrite, authoritative remote rescan and replacement of distributable copies |
| Branch enforcement | **Protected on October 4, 2026** with enforcement for everyone and 16 required GitHub Actions contexts; force pushes and branch deletion blocked | Re-read live protection before buyer access; keep `docs/release/BRANCH_PROTECTION_EVIDENCE.md` current |
| Hosted operation | Azure problem remains unresolved; no fresh production acceptance established here | Exact deployed SHA, migrations, tenant checks, worker/beat execution, monitoring, backup and restore exercise |
| Ownership and licenses | Policy and notices exist; complete assignment and shipped-dependency clearance not established | Contributor rights/assignments, dependency and asset inventory, applicable obligations and notices reviewed |
| Buyer evidence | PR closure and old green CI do not establish readiness | Final reviewed SHA, current reports, unresolved exceptions, reproducible setup and verified sanitized delivery |

## Diligence disclosure record

Prepare a concise, factual summary of material security incidents and remediation, outstanding limitations, ownership and license obligations, and the scope of testing. State resolved findings with their closure evidence; identify unresolved matters explicitly. Do not claim all-human authorship, independent human review, historical clearance, production readiness, or complete transfer without supporting evidence.

Tool-assisted implementation is compatible with the repository's [ownership and attribution policy](../governance/REPOSITORY_OWNERSHIP_AND_ATTRIBUTION.md). Describe it accurately when asked or required by diligence questions or transaction representations. Removing unnecessary tool references does not change authorship facts or IP obligations.

This record is an engineering disclosure recommendation. Transaction counsel determines contractual disclosure requirements and representations. Retention of a record does not by itself make every detail material; removal of a record does not eliminate an underlying material fact.

## Review sequence

1. Recover isolated security fixes and verify against current main.
2. Restore real dependency review and retained-history evidence controls.
3. Resolve historical token findings and identify every consumer of the exposed key; obtain retirement proof.
4. Prepare exact rewrite/ref inventories and verify an isolated copy, then coordinate owner-authorized shared-ref maintenance.
5. Verify remote history and distributable artifacts; complete ownership/license and runtime evidence.
6. Record the final review SHA and disclose remaining material exceptions before buyer access or delivery.

If any prerequisite remains open at the review date, report its actual status. The date does not waive security or evidence requirements.
