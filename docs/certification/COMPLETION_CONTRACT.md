# Crown2026 Completion Contract (Single Definition of Done)

> **Superseded authority notice (2026-10-05):** This document belongs to a predecessor certification cycle and is retained for historical evidence only. Current authority is `docs/CURRENT_RELEASE_STATUS.md`, `docs/canonical/CANONICAL_DOCUMENT_INDEX.md`, and exact-head GitHub evidence.


Status date: 2026-03-15
Contract version: 1.0 (locked)

## Scope labels (mandatory)

Every update, report, PR note, and status claim must be labeled as exactly one:
- Branch stabilization
- Module completion
- Production certification
- Investor-demo certification

## Allowed status terms (canonical)

### Local verified
Definition:
- Required local checks for the target blocker class pass on contributor machine.
- No claim is made about CI, merge, deploy, or production state.

Minimum evidence:
- command list
- exit codes
- timestamp

### CI verified
Definition:
- Required checks for the workstream are green in GitHub checks for the target SHA.
- No claim is made about merge, deploy, or production state.

Minimum evidence:
- check name(s)
- run URL(s)
- conclusion
- commit SHA

### Merged
Definition:
- Changes are merged into main.
- No claim is made about deploy or runtime truth.

Minimum evidence:
- merge commit SHA
- PR number

### Deployed
Definition:
- Deployment workflow completed and target environment accepted artifact.
- No claim is made about post-deploy runtime integrity until verified.

Minimum evidence:
- deploy workflow run URL
- deployed commit SHA
- environment name

### Production certified
Definition:
- Deployed SHA, runtime SHA, release artifact SHA/tag, and required production checklist all match and pass.

Minimum evidence:
- deployed SHA
- runtime health response fields (build_sha, status, prod_deploy_tag)
- release artifact metadata
- completed PRODUCTION_CERTIFICATION_CHECKLIST.md

### Investor ready
Definition:
- Production certified release plus complete investor evidence packet with module matrix, known limitations, and scripted demo proof.

Minimum evidence:
- completed INVESTOR_EVIDENCE_PACKET.md
- current module matrix signoff
- current blocker ledger with no open Bucket 1 or blocker-level Bucket 4 items

## Forbidden language

Do not use:
- almost there
- nearly finished
- mostly complete
- high percentage complete without evidence

Use only evidence-backed statements tied to:
- branch
- head sha
- check run URL
- artifact sha/tag
- deployed truth

## Enforcement rule

A completion claim is invalid if any required evidence field is missing.
