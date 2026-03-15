# Crown2026 Full Workspace Audit Report

Source pack: AUDIT_PACK_20260314_125613

## 1) Executive Summary

All required evidence files 00 through 14 are present in the selected audit pack. The captured workspace state shows local modifications and untracked sqlite artifacts at collection time. Branch protection for main could not be retrieved in this evidence run due authentication failure on the live API query. Runtime health and integrity probes report ok with matching build_sha and prod_deploy_tag. Recent deploy-prod workflow runs listed in the evidence are all failed conclusions.

## 2) Repo Map

- Backend surface present: 01_TREE.txt line 13367
- Frontend surface present: 01_TREE.txt line 18559
- Tools surface present: 01_TREE.txt line 19723
- Docs surface present: 01_TREE.txt line 18451
- CI workflows surface present: 01_TREE.txt line 32 and 02_WORKFLOWS_INDEX.txt lines 1-51
- Supporting operational surfaces present: .venv-1, venv, _tmp, artifacts, prod logs (01_TREE.txt lines 92, 19804, 9873, 13160, 19514)

## 3) CI/CD Surface

### Workflows list

Workflows indexed (51):

- azure-drift-watchdog.yml
- backend-gate.yml
- ci.yml
- ci-meta-gate-authoring.yml
- codeql.yml
- contract-gate.yml
- crown-magus0-gate.yml
- dashboards-build-gate.yml
- demo-contract-freeze.yml
- demo-reset.yml
- demo-reset-smoke.yml
- demo-surface-gate.yml
- dependency-review.yml
- dependency-scan.yml
- deploy-dashboard.yml
- deploy-dev.yml
- deploy-integrity-proof.yml
- deploy-prod.yml
- deploy-prod-dispatch.yml
- deploy-prod-tagpush.yml
- dev-smoke.yml
- dev-smoke-azure-dev.yml
- gradebookro-ui-gate.yml
- lockdown-golden-path-gate.yml
- migration-lock-gate.yml
- msgraph-smoke.yml
- ops-reset-dev.yml
- phase1-gate.yml
- phase3-demo-proof-pack.yml
- phase3-runtime-proof.yml
- phase4-gradebook-demo-proof.yml
- prod-health-watch.yml
- prod-integrity-proof.yml
- proof-ceremony.yml
- proof-ceremony-after-prod.yml
- proof-ceremony-prod.yml
- proof-gradebook.yml
- pytest-gate.yml
- rc-build-sha-proof.yml
- rc-gate.yml
- rc-promotion-gate.yml
- rc-runbook.yml
- rc-tier1-deployed-smoke.yml
- routes-gate.yml
- secret-scan.yml
- spine-audit.yml
- system-health.yml
- tests.yml
- ui-proof-gate.yml
- ui-proof-gates.yml
- ui-shell-gate.yml

Evidence: 02_WORKFLOWS_INDEX.txt lines 1-51

### Required checks mapping

- Branch protection required-check source for main is unavailable in this evidence due 401 auth error.
  - Evidence: 05_BRANCH_PROTECTION_MAIN.json lines 2-5
- Integrity endpoint exposes required_checks payload with 13 check names in response.
  - Evidence: 13_HEALTH_PROBE.txt line 6

### High-risk workflow patterns

- Job-level if clauses detected in six workflows.
  - Evidence: 04_JOB_LEVEL_IF.txt lines 1-6
- Production deploy workflows include job-level if: always().
  - Evidence: 04_JOB_LEVEL_IF.txt lines 2-4
- Lockdown gate includes conditional check on runtime_changed output.
  - Evidence: 04_JOB_LEVEL_IF.txt line 5

## 4) Runtime/Deploy Integrity

### Health endpoint signals

- Health response ok=true, status=ok, env=prod, db=ok.
  - Evidence: 13_HEALTH_PROBE.txt line 3
- Integrity response ok=true and includes commit/tag linkage.
  - Evidence: 13_HEALTH_PROBE.txt line 6

### Build SHA/Version behavior

- build_sha matches across health and integrity payloads.
  - Evidence: 13_HEALTH_PROBE.txt lines 3 and 6
- version is crown-0.3.0 in both payloads.
  - Evidence: 13_HEALTH_PROBE.txt lines 3 and 6
- prod_deploy_tag aligns between health and integrity payloads.
  - Evidence: 13_HEALTH_PROBE.txt lines 3 and 6

### Deploy-prod recent runs

- Live metadata query succeeded (status_code=200).
  - Evidence: 14_DEPLOY_PROD_RECENT.txt line 2
- All listed recent runs have conclusion=failure.
  - Evidence: 14_DEPLOY_PROD_RECENT.txt lines 4-23

## 5) Security & Secrets Hygiene (metadata only)

### Findings by category

- PrivateKeyHeader findings present.
  - Evidence: 10_SECRET_SCAN_FINDINGS.txt line 3
- DjangoSecretKeyLiteral findings present.
  - Evidence: 10_SECRET_SCAN_FINDINGS.txt line 7
- DatabaseUrl findings present.
  - Evidence: 10_SECRET_SCAN_FINDINGS.txt line 17
- PasswordAssignment findings present.
  - Evidence: 10_SECRET_SCAN_FINDINGS.txt line 25
- ApiKeyLike findings present.
  - Evidence: 10_SECRET_SCAN_FINDINGS.txt line 256
- TokenLike findings present.
  - Evidence: 10_SECRET_SCAN_FINDINGS.txt line 258

### Tracked sensitive files

- Tracked binaries list includes only zip archives in this evidence.
  - Evidence: 11_TRACKED_BINARIES.txt lines 1-3

### Scanner coverage note

- gitleaks not installed in this run; pattern scan only.
  - Evidence: 10_SECRET_SCAN_FINDINGS.txt lines 290-291

## 6) Dependency & Supply Chain Surface

### Python deps

- pip freeze snapshot captured.
  - Evidence: 08_PY_DEPS.txt lines 1-79
- Core framework and platform packages visible, including Django, djangorestframework, celery, psycopg, redis, sentry-sdk, stripe, twilio.
  - Evidence: 08_PY_DEPS.txt lines 12, 25, 27, 57, 65, 69, 72

### Node deps

- Frontend dependency inventory captured from frontend/dashboards package.
  - Evidence: 09_NODE_DEPS.txt lines 2 and 7-28
- lockfile present.
  - Evidence: 09_NODE_DEPS.txt line 5

## 7) Data & Migration Surface

- Migration listing shows applied migrations broadly across apps.
  - Evidence: 07_MIGRATIONS.txt lines 1-236
- No pending unchecked entries were shown in evidence output.
  - Evidence: 07_MIGRATIONS.txt full list
- App modules with explicit no migrations markers:
  - integrations_real
    - Evidence: 07_MIGRATIONS.txt lines 163-164
  - student360
    - Evidence: 07_MIGRATIONS.txt lines 222-223
- Backend URL extraction unavailable due missing django-extensions in active venv.
  - Evidence: 06_BACKEND_URLS.txt line 1

## 8) Artifact Hygiene

### Tracked binaries

- app_logs.zip
- prod_logs_now.zip
- webapp_logs.zip

Evidence: 11_TRACKED_BINARIES.txt lines 1-3

### Untracked artifacts likely harmful

- Modified workflows/audit script and untracked sqlite/branch-protection files.
  - Evidence: 12_UNTRACKED_ARTIFACTS.txt lines 1-6

## 9) Risk Register

| Risk | Severity | Evidence | Impact | Confidence |
|---|---|---|---|---|
| Branch protection live details unavailable due 401 | High | 05_BRANCH_PROTECTION_MAIN.json lines 3-5 | Required-check enforcement on main cannot be validated from this pack | High |
| Recent deploy-prod runs all failing | High | 14_DEPLOY_PROD_RECENT.txt lines 4-23 | Production deployment reliability risk | High |
| Backend URL inventory unavailable | Medium | 06_BACKEND_URLS.txt line 1 | Route integrity/coverage cannot be fully audited in this run | High |
| Secret scan reports multiple rule categories | Medium | 10_SECRET_SCAN_FINDINGS.txt lines 3, 7, 17, 25, 256, 258 | Requires triage to distinguish expected test/docs literals from exposure risk | Medium |
| gitleaks absent in evidence run | Medium | 10_SECRET_SCAN_FINDINGS.txt lines 290-291 | Reduced scanner diversity/coverage in this snapshot | High |
| Local sqlite and ad hoc artifacts present in working state | Low | 00_OVERVIEW.txt lines 16-19 and 12_UNTRACKED_ARTIFACTS.txt lines 3-6 | Hygiene noise and accidental commit risk | High |

## 10) Unknowns / Needs Verification

- None of the required evidence files are missing in this pack.
- Live branch protection payload could not be retrieved due authentication failure in pack generation context.
  - Evidence: 05_BRANCH_PROTECTION_MAIN.json line 3
- URL inventory could not be generated in active venv due missing django-extensions.
  - Evidence: 06_BACKEND_URLS.txt line 1

## 11) Appendix: Exact evidence references used

- AUDIT_PACK_20260314_125613/00_OVERVIEW.txt
- AUDIT_PACK_20260314_125613/01_TREE.txt
- AUDIT_PACK_20260314_125613/02_WORKFLOWS_INDEX.txt
- AUDIT_PACK_20260314_125613/03_WORKFLOWS_TRIGGERS.txt
- AUDIT_PACK_20260314_125613/04_JOB_LEVEL_IF.txt
- AUDIT_PACK_20260314_125613/05_BRANCH_PROTECTION_MAIN.json
- AUDIT_PACK_20260314_125613/06_BACKEND_URLS.txt
- AUDIT_PACK_20260314_125613/07_MIGRATIONS.txt
- AUDIT_PACK_20260314_125613/08_PY_DEPS.txt
- AUDIT_PACK_20260314_125613/09_NODE_DEPS.txt
- AUDIT_PACK_20260314_125613/10_SECRET_SCAN_FINDINGS.txt
- AUDIT_PACK_20260314_125613/11_TRACKED_BINARIES.txt
- AUDIT_PACK_20260314_125613/12_UNTRACKED_ARTIFACTS.txt
- AUDIT_PACK_20260314_125613/13_HEALTH_PROBE.txt
- AUDIT_PACK_20260314_125613/14_DEPLOY_PROD_RECENT.txt
