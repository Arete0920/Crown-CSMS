---
applyTo: "**"
---

# Crown2026: Full Workspace Audit Report Specification (NON-FIXING)

You are producing a comprehensive audit report for Crown2026.
This report must be exhaustive and evidence-based.

## Absolute constraints
- NO FIXES. No code changes. No patch suggestions.
- NO SECRETS. Never output secret values. If referenced, provide only metadata (path+line+category).
- Use the generated audit evidence pack under AUDIT_PACK/ as primary sources.

## Required input evidence (must reference each if present)
- AUDIT_PACK/00_OVERVIEW.txt
- AUDIT_PACK/01_TREE.txt
- AUDIT_PACK/02_WORKFLOWS_INDEX.txt
- AUDIT_PACK/03_WORKFLOWS_TRIGGERS.txt
- AUDIT_PACK/04_JOB_LEVEL_IF.txt
- AUDIT_PACK/05_BRANCH_PROTECTION_MAIN.json
- AUDIT_PACK/06_BACKEND_URLS.txt
- AUDIT_PACK/07_MIGRATIONS.txt
- AUDIT_PACK/08_PY_DEPS.txt
- AUDIT_PACK/09_NODE_DEPS.txt
- AUDIT_PACK/10_SECRET_SCAN_FINDINGS.txt
- AUDIT_PACK/11_TRACKED_BINARIES.txt
- AUDIT_PACK/12_UNTRACKED_ARTIFACTS.txt
- AUDIT_PACK/13_HEALTH_PROBE.txt
- AUDIT_PACK/14_DEPLOY_PROD_RECENT.txt

If any evidence file is missing, call it out explicitly in "Missing Evidence".

## Report structure (required)
1) Executive Summary (facts only)
2) Repo Map (backend/frontend/tools/docs/ci)
3) CI/CD Surface
   - Workflows list
   - Required checks mapping
   - High-risk workflow patterns (job-level if, authoring hazards)
4) Runtime/Deploy Integrity
   - Health endpoint signals
   - Build SHA/Version behavior
   - Deploy-prod recent runs
5) Security & Secrets Hygiene (metadata only)
   - Findings by category
   - Tracked sensitive files (if any)
6) Dependency & Supply Chain Surface
   - Python deps
   - Node deps
7) Data & Migration Surface
   - Migration status, lock gates, any drift signals
8) Artifact Hygiene
   - Tracked binaries
   - Untracked artifacts likely to be harmful
9) Risk Register (table)
   - Risk | Severity | Evidence | Impact | Confidence
10) Unknowns / Needs Verification
11) Appendix: Exact evidence references used

## Thoroughness requirement
- Do not ignore any workflow, any directory, or any evidence file.
- If evidence is large, summarize with pointers; do not omit.
