# CROWN Modules and Dashboards Review Packet

Status: Independent Review Packet
Parent Canon: `docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md`
Release Authority: `docs/CURRENT_RELEASE_STATUS.md`
Created: 2026-06-09
Scope: Modules and dashboards only

## Purpose

This packet routes the CROWN modules and dashboards canon package to independent review. It does not approve the canon, certify any module, certify any dashboard, or alter release posture.

The package is ready for review as a planning-control set. It is not implementation proof.

## Files in Review Scope

| Order | File | Purpose |
|---:|---|---|
| 1 | `docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md` | Controlling module/dashboard product and architecture canon. |
| 2 | `docs/product/CROWN_MODULE_COMPLETION_MATRIX.md` | Row-level module status, dependencies, and evidence requirements. |
| 3 | `docs/product/CROWN_MODULE_DATA_OWNERSHIP_MATRIX.md` | Canonical data ownership and duplicate-truth prevention. |
| 4 | `docs/product/CROWN_MODULE_PERMISSION_MATRIX.md` | Action-level permission, role, export, and sensitive-access requirements. |
| 5 | `docs/product/CROWN_DASHBOARD_FIT_MATRIX.md` | Dashboard-to-module fit, data provenance, freshness, drilldown, and certification requirements. |
| 6 | `docs/product/CROWN_MODULE_REVIEW_RACI.md` | Independent review and approval routing. |

## Authority Boundaries

Reviewers must verify that the package preserves these boundaries:

- `docs/CURRENT_RELEASE_STATUS.md` remains the only release-posture authority.
- This package does not claim production GO.
- This package does not claim sandbox approval.
- This package does not certify modules.
- This package does not certify dashboards.
- This package does not override current-head evidence requirements.
- TC is not assigned self-approval authority.

## Required Review Roles

At minimum, the package needs:

| Review Role | Required Focus |
|---|---|
| Technical Reviewer | Architecture, module ordering, dependency flow, backend/frontend wiring standards. |
| Security Reviewer | Tenant isolation, action-level permissions, sensitive data, redaction, exports, dashboard access. |
| QA / Evidence Reviewer | Evidence language, proof gates, test expectations, runtime artifact requirements. |
| Product Workflow Reviewer | School operations workflow, persona fit, dashboard usefulness, competitor-research alignment. |

The same person or agent that authored the package cannot be the sole approving reviewer.

## Review Checklist

### 1. Canon Review

- [ ] Confirms modules-first / dashboards-second / certification-last rule.
- [ ] Preserves release authority hierarchy.
- [ ] Uses accurate completion vocabulary.
- [ ] Prevents registry coverage from being treated as completion.
- [ ] Prevents sample/template data from being treated as production proof.
- [ ] Requires independent review.
- [ ] Defines Core / Modules / Add-ons boundaries correctly.
- [ ] Defines dashboard fit and certification states clearly.

### 2. Module Completion Matrix Review

- [ ] Inventory covers Core, first-wave modules, operational modules, mission/add-on modules, and platform ops.
- [ ] Module order follows dependency flow.
- [ ] First completion batch is correct.
- [ ] Current status language avoids completion claims unsupported by evidence.
- [ ] Blocking questions are visible.
- [ ] Next actions are verification-oriented, not assumption-based.
- [ ] Dashboard status remains subordinate to module proof.

### 3. Data Ownership Review

- [ ] Core canonical ownership is clear.
- [ ] Modules do not duplicate Core truth.
- [ ] Write-back paths require approved services.
- [ ] Sensitive data is identified.
- [ ] Rollover/retention gaps are visible.
- [ ] Event side effects are flagged for later mapping.
- [ ] Dashboard snapshots are not treated as canonical operational records.

### 4. Permission Matrix Review

- [ ] Action-level permissions exist beyond page-level access.
- [ ] Sensitive modules require restricted-view permissions.
- [ ] Direct URL access is explicitly tested.
- [ ] Export permissions are separate and audited.
- [ ] Frontend role groups must align with backend permissions.
- [ ] Tenant boundary proof is required.
- [ ] Small-cell suppression and redaction are required where applicable.

### 5. Dashboard Fit Review

- [ ] Every dashboard has a source module.
- [ ] Every dashboard has a data-source requirement.
- [ ] Current certification states are not overstated.
- [ ] Freshness/provenance expectations are explicit.
- [ ] Drilldown/export rules are included.
- [ ] Sensitive dashboards require redaction/suppression.
- [ ] Sample/template/fallback data blocks promotion unless explicitly sandbox-only.

### 6. RACI Review

- [ ] TC is not allowed to self-approve.
- [ ] Implementer cannot be sole reviewer.
- [ ] Sensitive modules require security review.
- [ ] Module certification is separate from release GO.
- [ ] Revocation conditions are defined.
- [ ] Evidence locations are defined.

## Known Non-Approval Statements

The package must retain these non-approval statements:

```text
This package does not approve production release.
This package does not approve sandbox launch.
This package does not certify any module.
This package does not certify any dashboard.
This package does not replace current-head release evidence.
This package requires independent review before it is treated as approved governance.
```

## Recommended Review Outcome Values

Reviewers should classify the package using one of these outcomes:

| Outcome | Meaning |
|---|---|
| ACCEPT FOR PLANNING USE | The package may control module/dashboard planning, but does not certify implementation. |
| ACCEPT WITH CORRECTIONS | The package may proceed after listed corrections are applied. |
| REJECT FOR REVISION | The package has material gaps and must be revised before use. |

No review outcome may be interpreted as production GO.

## First Planning Execution Step After Review

After independent review accepts this package for planning use, the next controlled execution step is:

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
- independent reviewer assignment

## Review Signoff Table

| Role | Reviewer | Outcome | Date | Notes / Required Corrections |
|---|---|---|---|---|
| Technical Reviewer | TBD | Pending | TBD | TBD |
| Security Reviewer | TBD | Pending | TBD | TBD |
| QA / Evidence Reviewer | TBD | Pending | TBD | TBD |
| Product Workflow Reviewer | TBD | Pending | TBD | TBD |

## Current Status

Review packet created. Independent review not yet completed. Package not approved. Module/dashboard implementation certification not started.
