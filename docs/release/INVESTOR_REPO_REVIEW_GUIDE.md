# Investor Repo Review Guide

Authority Scope Notice (2026-05-29)

This document is an investor review runbook and not a controlling repository-level release authority source.

Current controlling release-authority sources:

> - docs/CURRENT_RELEASE_STATUS.md
> - docs/release/CURRENT_RELEASE_SCORECARD_20260528.md

Estimated review time: 5 minutes

This guide gives an outside reviewer a fast, structured walkthrough of Crown's product scope, controls, and readiness evidence.

## 1. Start at README

Read `README.md` first for:

- product positioning,
- platform scope,
- architecture summary,
- security posture,
- governance and release links.

## 2. Review Security and Compliance

Then open:

- `SECURITY.md`
- `docs/COMPLIANCE.md`
- `docs/release/SECURITY_GATES_EVIDENCE.md`
- `docs/release/BRANCH_PROTECTION_EVIDENCE.md`

These documents show policy posture, current control evidence, and what still requires manual capture.

## 3. Review Module Scope and Workflow Governance

Open:

- `docs/release/MODULE_INVENTORY.md`
- `docs/release/WORKFLOW_CONSOLIDATION_PLAN.md`
- `docs/repo-cleanup/WORKFLOW_CLASSIFICATION_PHASE2.md`

These define what the product includes today and how CI/CD governance is being normalized.

## 4. Review Final Release Gate

Open:

- `docs/release/FINAL_RELEASE_GATE.md`
- `docs/release/FINAL_SIGNOFF_CHECKLIST.md`

These provide condition-by-condition release status with explicit PASS/PARTIAL/FAIL/manual flags.

## 5. Review Evidence Index

Open:

- `docs/release/FINAL_INVESTOR_EVIDENCE_INDEX.md`

This is the evidence map with statuses (`PRESENT`, `MISSING`, `MANUAL_CAPTURE_REQUIRED`, `PENDING_GREEN_RUN`) and owners.

## 6. Review Known Gaps and Deferred Items

Open:

- `docs/release/KNOWN_GAPS_AND_DEFERRED_ITEMS.md`

This is the candid gap list and distinguishes what is complete now versus what requires additional runs/access.

## Strongest Maturity Signals

1. Canonical documentation package is assembled and cross-linked.
2. Multi-tenant/security/compliance posture is documented.
3. Workflow governance has been inventoried and rationalized (Phases 1 and 2).
4. Final release gate and signoff process are explicit and evidence-based.

## What Still Remains Before Full Launch Readiness

1. Capture branch protection and security-gate blocking screenshots from live GitHub settings/checks.
2. Commit fresh golden-path and tenant-isolation run outputs.
3. Commit final load-test reports.
4. Capture production health/integrity responses with required fields.

## Where Proof Is Strongest vs Documentary

- Strongest executable/documentary mix:
  - workflow files under `.github/workflows/`,
  - module/compliance/security docs,
  - prior proof logs under `docs/proof/` and `docs/demo-proof/`.

- Still mainly documentary (needs fresh executable captures):
  - branch-protection UI proof,
  - blocking-check screenshots,
  - latest green-run test/load artifacts.
