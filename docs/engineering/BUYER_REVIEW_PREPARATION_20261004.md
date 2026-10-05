# Buyer repository review preparation

Assessment refreshed: October 5, 2026. Intended review window: October 11, 2026.
Current authoritative repository: `Arete0920/Crown-CSMS`.
Current reviewed main SHA: `5a5b15ea01542710690433645a92a6b4f43e59c2`.

This is an engineering diligence register. It records verified repository controls, remaining exceptions, and the evidence required before source distribution, production certification, or transaction representations.

## Current repository controls

- `main` is protected.
- Required status checks are enforced for everyone. The current protection record contains 16 required contexts, including CodeQL analysis, release authority, contract, backend, dependency, secret-scan, schema, pytest, release-verification and repository-policy controls.
- Canonical repository identity is `Arete0920/Crown-CSMS`; repository-identity enforcement merged in PR #118.
- Wallet remediation merged in PR #74.
- Repository pull-request hygiene enforces bounded change sets, including a 20-file normal PR limit.
- Historical or superseded PRs are not release authority. Only current-main or refreshed exact-head evidence is authoritative.

## Current remediation boundaries

### Dependency review

The current dependency-review workflow records that GitHub's native dependency-review capability is unavailable for this repository and therefore does not currently provide substantive dependency-diff enforcement. This remains an engineering control gap. Do not describe the present skip-success workflow as an implemented dependency-review control.

Closure evidence:
- enable a supported dependency-diff control for this repository;
- require that control in branch protection only after it provides substantive pass/fail evidence;
- retain backend, frontend, Wallet and other package-manager audit gates independently.

### Retained-history security

Current-tree cleanup does not erase Git history. Any retained-history credential or key remediation must continue through the controlled security runbook. Do not remove or rewrite history merely to improve diligence appearance.

Closure evidence:
- adjudicated all-ref scan;
- consumer and trust inventory;
- verified retirement/replacement of affected credentials or keys;
- isolated rewrite evidence where required;
- authoritative remote rescan after any approved history maintenance.

### Hosted operation

Hosted production acceptance is not established by repository CI alone. Azure/deployed-runtime work remains a separate deployment-evidence requirement.

Closure evidence:
- exact deployed SHA;
- successful migrations;
- tenant-isolation checks;
- worker/scheduler execution;
- monitoring and alerting;
- backup/restore exercise;
- deployment-specific smoke and acceptance evidence.

### Ownership and licenses

Repository policy and notices exist, but transaction counsel and the owner should still confirm assignment, contributor-rights and shipped-dependency obligations before a transfer representation is made.

## Buyer evidence standard

A buyer should evaluate the current authoritative line, not stale branch state. The diligence package should provide:

1. the final reviewed `main` SHA;
2. branch-protection evidence;
3. exact-head CI and security results for that SHA;
4. the active exception register;
5. reproducible setup/build instructions;
6. current license and ownership records;
7. current deployment limitations;
8. any material historical-security remediation evidence required for the transaction.

Closed, superseded, cancelled or stale workflow runs are historical engineering records. They are not evidence of the present release state and should not be represented as such.

## Repository-cleanup discipline

Repository cleanup must preserve material history while keeping the active work surface controlled.

- Keep ordinary PRs at or below the repository hygiene limits.
- Prefer one active remediation lane at a time.
- Refresh stale feature work against the current integration line before certification.
- Close superseded PRs explicitly rather than leaving abandoned branches presented as active work.
- Merge only from current, exact-head, terminal-green evidence.
- Recheck `main` after each merge before opening the next remediation lane.

## Diligence disclosure rule

State resolved findings together with their closure evidence and identify unresolved material exceptions explicitly. Do not claim historical clearance, hosted production readiness, legal compliance, independent review, or transaction readiness without supporting evidence.

Tool-assisted implementation does not alter ownership facts by itself. Describe development provenance accurately when required by diligence questions or transaction representations.

This record is an engineering disclosure aid, not legal advice. Transaction counsel determines contractual disclosures, representations, warranties and materiality.
