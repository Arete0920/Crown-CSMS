# CI hardening implementation ledger

Owner: CROWN product owner. Authorization: owner instruction to proceed on October 9, 2026.
Base: `88ddd37ad278615903e2fdabd4fad29f2a6c134b`.
Each outcome uses a separate reversible PR and requires current exact-head CI before merge.
This ledger records source controls, not deployed operational assurance.

## Complete workflow policy enforcement

Scope: complete policy checks, existing workflow-policy violations, and immutable action-reference parsing.
Forbidden scope: application behavior, production activation, credential changes, gate weakening.
Rollback: revert the outcome PR.

- Repository Policy now checks the complete workflow inventory on every invocation.
- Failed workflow change discovery no longer becomes a clean no-change result.
- CI authoring contracts run independently of whether a workflow changed.
- Action references include both `uses:` and `- uses:` YAML forms.
- Container actions require full SHA-256 digests; unregistered `.yaml` workflows are rejected.
- Recovery artifact upload is commit-pinned; secret-scan evidence upload is no longer allowed to fail silently.
- Health-watch concurrency is explicit. Schema-stage caller runs remain independent while the existing shared production migration lock is preserved.
- Local validation: complete workflow policy and seven rejection/contract tests pass; existing CI authoring checks pass.
- Hosted CI and merge: NOT VERIFIED until exact-head GitHub evidence is inspected.

## Remaining outcomes

Release validation before mutation; governed PR coverage; artifact digest and signed provenance;
dependency/tool reproducibility; release SBOM binding; dependency admission; workflow consolidation;
effective job permissions; evidence retention; CI efficiency; live governance settings verification.
These remain open work, not completed controls.
