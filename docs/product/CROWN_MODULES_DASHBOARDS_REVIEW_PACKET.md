# CROWN Modules and Dashboards Verification Packet

Status: Pending Copilot Review
Parent Canon: `docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md`
Release Authority: `docs/CURRENT_RELEASE_STATUS.md`
Created: 2026-06-09
Scope: Modules and dashboards only

## Purpose

This packet routes the CROWN modules and dashboards canon package through the active verification and review path: TC direction, ChatGPT drafting and evidence organization, VS Code repo inspection, GitHub evidence, CI/check outputs where available, and GitHub Copilot review captured as review evidence.

This packet does not approve the canon, certify any module, certify any dashboard, approve production release, approve sandbox launch, or alter release posture.

## Current Review Path

The active workflow is limited to:

- TC direction and priority-setting
- ChatGPT drafting, inspection support, and evidence organization
- VS Code repo inspection
- GitHub repo evidence
- CI/check outputs where available
- committed proof artifacts
- GitHub Copilot review through VS Code/GitHub, with review output captured as evidence

Claude and Grok are not part of this workflow.

Copilot may serve as the independent review support path only when its review output is captured in one of these reviewable forms:

- GitHub PR review
- GitHub PR comment
- GitHub issue comment
- committed VS Code/Copilot review transcript or summary
- pasted Copilot review output committed into an evidence packet

Until that evidence exists, the correct status is:

```text
PENDING COPILOT REVIEW - NOT APPROVED
```

After Copilot review evidence is captured and no blocking corrections remain, the correct status is:

```text
COPILOT-REVIEWED FOR PLANNING USE - NOT PRODUCTION GO
```

Copilot review does not certify modules, certify dashboards, approve sandbox launch, or approve production release.

## Files in Verification Scope

| Order | File | Purpose |
|---:|---|---|
| 1 | `docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md` | Controlling module/dashboard product and architecture canon. |
| 2 | `docs/product/CROWN_MODULE_COMPLETION_MATRIX.md` | Row-level module status, dependencies, and evidence requirements. |
| 3 | `docs/product/CROWN_MODULE_DATA_OWNERSHIP_MATRIX.md` | Canonical data ownership and duplicate-truth prevention. |
| 4 | `docs/product/CROWN_MODULE_PERMISSION_MATRIX.md` | Action-level permission, role, export, and sensitive-access requirements. |
| 5 | `docs/product/CROWN_DASHBOARD_FIT_MATRIX.md` | Dashboard-to-module fit, data provenance, freshness, drilldown, and certification requirements. |
| 6 | `docs/product/CROWN_MODULE_REVIEW_RACI.md` | Review and approval routing, including Copilot review evidence requirements. |

## Authority Boundaries

Verification and Copilot review must preserve these boundaries:

- `docs/CURRENT_RELEASE_STATUS.md` remains the only release-posture authority.
- This package does not claim production GO.
- This package does not claim sandbox approval.
- This package does not certify modules.
- This package does not certify dashboards.
- This package does not override current-head evidence requirements.
- TC is not assigned self-approval authority.
- ChatGPT is not assigned approval authority for work it authored.
- VS Code/GitHub checks provide mechanical verification.
- Copilot review must be captured as evidence before approval status changes.

## Required Verification and Review Lanes

| Lane | Required Focus | Available Mechanism |
|---|---|---|
| Technical Verification | Architecture, module ordering, dependency flow, backend/frontend wiring standards. | VS Code repo inspection, GitHub file evidence, targeted grep/search, current-head diff review. |
| Security Verification | Tenant isolation, action-level permissions, sensitive data, redaction, exports, dashboard access. | Static inspection, security checklist, permission matrix, backend tests where available. |
| QA / Evidence Verification | Evidence language, proof gates, test expectations, runtime artifact requirements. | GitHub checks, local/CI logs, evidence packets, matrix row proof links. |
| Product Workflow Verification | School operations workflow, persona fit, dashboard usefulness, competitor-research alignment. | Canon/matrix review against CROWN product strategy and school operations requirements. |
| Copilot Review | Independent review support for planning-control quality, consistency, gaps, and corrections. | VS Code/GitHub Copilot review output captured as evidence. |

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
- [ ] Copilot review evidence is required before any Copilot-reviewed approval status is claimed.

### 7. Copilot Review Checklist

Copilot review must check:

- [ ] internal consistency across all six files
- [ ] no release GO, sandbox approval, module certification, or dashboard certification is implied
- [ ] module order follows dependency flow
- [ ] first completion batch is coherent
- [ ] data ownership avoids duplicate truth
- [ ] permission model is action-level, not page-only
- [ ] dashboard fit requires source module, provenance, freshness, tenant proof, and role proof
- [ ] RACI prevents TC self-approval and ChatGPT self-approval
- [ ] blocking corrections, if any, are listed explicitly

## Known Non-Approval Statements

The package must retain these non-approval statements:

```text
This package does not approve production release.
This package does not approve sandbox launch.
This package does not certify any module.
This package does not certify any dashboard.
This package does not replace current-head release evidence.
This package is not Copilot-reviewed until Copilot review output is captured as evidence.
Copilot review for planning use is not production GO.
```

## Verification Outcome Values

Use one of these outcomes:

| Outcome | Meaning |
|---|---|
| PENDING COPILOT REVIEW | Package is prepared but Copilot review evidence is not yet captured. |
| COPILOT-REVIEWED FOR PLANNING USE | Copilot review evidence is captured and no blocking corrections remain. Not production GO. |
| COPILOT-REVIEWED WITH CORRECTIONS REQUIRED | Copilot found corrections that must be addressed before planning use. |
| REJECT FOR REVISION | Material gaps exist; revise before use. |

No outcome may be interpreted as production GO.

## First Planning Execution Step After Copilot Review

After the package is Copilot-reviewed for planning use, the next controlled execution step is:

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
- Copilot review output where applicable

## Verification Signoff Table

| Lane | Verifier | Outcome | Date | Notes / Required Corrections |
|---|---|---|---|---|
| Technical Verification | ChatGPT + VS Code/GitHub evidence | Pending | TBD | TBD |
| Security Verification | ChatGPT + VS Code/GitHub evidence | Pending | TBD | TBD |
| QA / Evidence Verification | ChatGPT + VS Code/GitHub evidence | Pending | TBD | TBD |
| Product Workflow Verification | TC direction + ChatGPT support | Pending | TBD | TBD |
| Copilot Review | GitHub Copilot via VS Code/GitHub, evidence captured | Pending | TBD | TBD |

## Current Status

Verification packet updated for the active workflow. Copilot is the independent review support path once its output is captured as evidence. Package is not yet Copilot-reviewed. Module/dashboard implementation certification has not started.
