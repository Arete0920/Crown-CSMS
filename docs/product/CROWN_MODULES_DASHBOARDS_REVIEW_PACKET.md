# CROWN Modules and Dashboards Verification Packet

Status: VS Code / GitHub Verification Packet
Parent Canon: `docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md`
Release Authority: `docs/CURRENT_RELEASE_STATUS.md`
Created: 2026-06-09
Scope: Modules and dashboards only

## Purpose

This packet routes the CROWN modules and dashboards canon package through the available verification path: ChatGPT support, VS Code inspection, GitHub evidence, repository checks, and current-head proof artifacts.

This packet does not approve the canon, certify any module, certify any dashboard, approve production release, approve sandbox launch, or alter release posture.

## Current Review Constraint

External support reviewers are not available for this lane. Claude and Grok are not part of the workflow. The active workflow is limited to:

- TC direction and priority-setting
- ChatGPT drafting, inspection support, and evidence organization
- VS Code repo inspection
- GitHub repo evidence
- CI/check outputs where available
- committed proof artifacts

Because no independent human reviewer is available in this lane, this package cannot honestly be marked `independently approved` from this workflow alone. The correct status after successful verification is:

```text
MECHANICALLY VERIFIED FOR PLANNING USE — NOT INDEPENDENTLY APPROVED
```

This preserves segregation-of-duties integrity while allowing planning work to continue.

## Files in Verification Scope

| Order | File | Purpose |
|---:|---|---|
| 1 | `docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md` | Controlling module/dashboard product and architecture canon. |
| 2 | `docs/product/CROWN_MODULE_COMPLETION_MATRIX.md` | Row-level module status, dependencies, and evidence requirements. |
| 3 | `docs/product/CROWN_MODULE_DATA_OWNERSHIP_MATRIX.md` | Canonical data ownership and duplicate-truth prevention. |
| 4 | `docs/product/CROWN_MODULE_PERMISSION_MATRIX.md` | Action-level permission, role, export, and sensitive-access requirements. |
| 5 | `docs/product/CROWN_DASHBOARD_FIT_MATRIX.md` | Dashboard-to-module fit, data provenance, freshness, drilldown, and certification requirements. |
| 6 | `docs/product/CROWN_MODULE_REVIEW_RACI.md` | Review and approval routing, including the independent-review limitation. |

## Authority Boundaries

Verification must preserve these boundaries:

- `docs/CURRENT_RELEASE_STATUS.md` remains the only release-posture authority.
- This package does not claim production GO.
- This package does not claim sandbox approval.
- This package does not certify modules.
- This package does not certify dashboards.
- This package does not override current-head evidence requirements.
- TC is not assigned self-approval authority.
- ChatGPT is not assigned approval authority for work it authored.
- VS Code/GitHub checks provide mechanical verification, not independent approval.

## Required Verification Lanes

| Lane | Required Focus | Available Mechanism |
|---|---|---|
| Technical Verification | Architecture, module ordering, dependency flow, backend/frontend wiring standards. | VS Code repo inspection, GitHub file evidence, targeted grep/search, current-head diff review. |
| Security Verification | Tenant isolation, action-level permissions, sensitive data, redaction, exports, dashboard access. | Static inspection, security checklist, permission matrix, backend tests where available. |
| QA / Evidence Verification | Evidence language, proof gates, test expectations, runtime artifact requirements. | GitHub checks, local/CI logs, evidence packets, matrix row proof links. |
| Product Workflow Verification | School operations workflow, persona fit, dashboard usefulness, competitor-research alignment. | Canon/matrix review against CROWN product strategy and school operations requirements. |

## Verification Checklist

### 1. Canon Verification

- [ ] Confirms modules-first / dashboards-second / certification-last rule.
- [ ] Preserves release authority hierarchy.
- [ ] Uses accurate completion vocabulary.
- [ ] Prevents registry coverage from being treated as completion.
- [ ] Prevents sample/template data from being treated as production proof.
- [ ] Defines Core / Modules / Add-ons boundaries correctly.
- [ ] Defines dashboard fit and certification states clearly.
- [ ] Avoids unsupported completion or release claims.

### 2. Module Completion Matrix Verification

- [ ] Inventory covers Core, first-wave modules, operational modules, mission/add-on modules, and platform ops.
- [ ] Module order follows dependency flow.
- [ ] First completion batch is correct.
- [ ] Current status language avoids completion claims unsupported by evidence.
- [ ] Blocking questions are visible.
- [ ] Next actions are verification-oriented, not assumption-based.
- [ ] Dashboard status remains subordinate to module proof.

### 3. Data Ownership Verification

- [ ] Core canonical ownership is clear.
- [ ] Modules do not duplicate Core truth.
- [ ] Write-back paths require approved services.
- [ ] Sensitive data is identified.
- [ ] Rollover/retention gaps are visible.
- [ ] Event side effects are flagged for later mapping.
- [ ] Dashboard snapshots are not treated as canonical operational records.

### 4. Permission Matrix Verification

- [ ] Action-level permissions exist beyond page-level access.
- [ ] Sensitive modules require restricted-view permissions.
- [ ] Direct URL access is explicitly tested.
- [ ] Export permissions are separate and audited.
- [ ] Frontend role groups must align with backend permissions.
- [ ] Tenant boundary proof is required.
- [ ] Small-cell suppression and redaction are required where applicable.

### 5. Dashboard Fit Verification

- [ ] Every dashboard has a source module.
- [ ] Every dashboard has a data-source requirement.
- [ ] Current certification states are not overstated.
- [ ] Freshness/provenance expectations are explicit.
- [ ] Drilldown/export rules are included.
- [ ] Sensitive dashboards require redaction/suppression.
- [ ] Sample/template/fallback data blocks promotion unless explicitly sandbox-only.

### 6. RACI Verification

- [ ] TC is not allowed to self-approve.
- [ ] ChatGPT is not allowed to approve its own authored work.
- [ ] Implementer cannot be sole reviewer.
- [ ] Sensitive modules require security verification.
- [ ] Module certification is separate from release GO.
- [ ] Revocation conditions are defined.
- [ ] Evidence locations are defined.
- [ ] The unavailable independent-review condition is accurately documented.

## Known Non-Approval Statements

The package must retain these non-approval statements:

```text
This package does not approve production release.
This package does not approve sandbox launch.
This package does not certify any module.
This package does not certify any dashboard.
This package does not replace current-head release evidence.
This package is not independently approved unless a qualified independent reviewer actually reviews and signs off.
```

## Verification Outcome Values

Use one of these outcomes:

| Outcome | Meaning |
|---|---|
| MECHANICALLY VERIFIED FOR PLANNING USE | VS Code/GitHub/evidence review found no blocking planning-control defect. Not independent approval. |
| VERIFIED WITH CORRECTIONS REQUIRED | Planning can continue only after listed corrections are applied. |
| REJECT FOR REVISION | Material gaps exist; revise before use. |
| INDEPENDENTLY APPROVED | Reserved only for actual qualified independent reviewer signoff. Not available in the current lane. |

No outcome may be interpreted as production GO.

## First Planning Execution Step After Mechanical Verification

After the package is mechanically verified for planning use, the next controlled execution step is:

```text
Populate and verify the first ten module rows in CROWN_MODULE_COMPLETION_MATRIX.md:
1. School / Academic Year / Grade Level
2. Staff / User / Role
3. Family / Guardian / Household
4. Student Master Record
5. Enrollment / Registrar
6. Courses / Sections / Rosters
7. Attendance
8. Billing / Tuition / Ledger
9. Gradebook
10. Communications
```

Each first-batch module row must be expanded with:

- backend app/service evidence
- model evidence
- API evidence
- frontend route/component evidence
- persona/action permission requirements
- tenant proof requirements
- audit event requirements
- dashboard source/freshness requirements
- runtime proof requirements
- blocking questions
- verification status

## Verification Signoff Table

| Lane | Verifier | Outcome | Date | Notes / Required Corrections |
|---|---|---|---|---|
| Technical Verification | ChatGPT + VS Code/GitHub evidence | Pending | TBD | TBD |
| Security Verification | ChatGPT + VS Code/GitHub evidence | Pending | TBD | TBD |
| QA / Evidence Verification | ChatGPT + VS Code/GitHub evidence | Pending | TBD | TBD |
| Product Workflow Verification | TC direction + ChatGPT support | Pending | TBD | TBD |
| Independent Approval | Not available in current lane | Not available | TBD | Do not mark independently approved without actual independent reviewer. |

## Current Status

Verification packet updated for the current workflow. Independent review is not available in this lane. Package is not independently approved. Module/dashboard implementation certification has not started.
