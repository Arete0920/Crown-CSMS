# CROWN Buyer-Ready Execution Directive

**Repository:** `tcmegahan/Crown2026`  
**Local checkout:** `C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr`  
**Authoritative baseline SHA:** `5a31d92f736b7d7ada58f6d03441dadf186322fd`

## Mission

Complete CROWN to the buyer-ready standard.

Completed means an authorized customer or approved demo user can log in and use every intended customer-visible surface exactly as designed:

- every page opens;
- every dashboard loads correctly;
- every link works;
- every widget displays correct data and behaves correctly;
- every form, filter, action, export, wizard, and workflow works end to end;
- role permissions and tenant isolation work;
- frontend-to-backend plumbing works;
- loading, empty, error, validation, and permission states work;
- appearance, branding, spacing, icons, responsiveness, and accessibility are finished;
- there are no unexplained console errors, network errors, broken assets, fake-live data, placeholders, or silent fallbacks.

Static registration, source-code existence, isolated tests, snapshots, sample data, fallbacks, or local-only evidence do not count as completed customer functionality.

## Operating rules

1. Work continuously through problems.
2. Find the defect, fix it, rerun the affected workflow, and repeat.
3. Do not stop at reporting.
4. Use narrow branches and focused commits.
5. Do not weaken authentication, tenant enforcement, RBAC, secret scanning, or release protections.
6. Do not blindly rerun structurally broken workflows.
7. Do not merge generated evidence noise.
8. Do not discard local changes until they are inventoried and preserved.
9. Do not claim production readiness from local-only results.
10. Keep production NO-GO until buyer-ready same-SHA deployed proof exists.

## Phase 1 — Reconcile the local checkout

```powershell
$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr'

git fetch origin --prune --tags
"CURRENT_BRANCH=$(git branch --show-current)"
"LOCAL_HEAD=$(git rev-parse HEAD)"
"REMOTE_MAIN=$(git rev-parse origin/main)"
git status --short --branch
git branch -vv
git log --oneline --decorate -20
```

Expected remote main:

```text
5a31d92f736b7d7ada58f6d03441dadf186322fd
```

If the working tree is dirty, preserve it before any reset or branch switch:

```powershell
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backup = "..\crown-local-reconciliation-$stamp"
New-Item -ItemType Directory -Force -Path $backup | Out-Null

git status --short --branch | Out-File "$backup\status.txt" -Encoding utf8
git branch -vv | Out-File "$backup\branches.txt" -Encoding utf8
git log --oneline --decorate -50 | Out-File "$backup\log.txt" -Encoding utf8
git diff | Out-File "$backup\working-tree.diff" -Encoding utf8
git diff --cached | Out-File "$backup\staged.diff" -Encoding utf8
git diff --stat | Out-File "$backup\working-tree-stat.txt" -Encoding utf8
git diff --cached --stat | Out-File "$backup\staged-stat.txt" -Encoding utf8
```

Inspect these known local paths:

```powershell
git status --short -- `
  scripts/release/verify-frontend-rc.mjs `
  backend/crown_api/dashboards/views.py `
  backend/core/tenant_header_middleware.py `
  backend/crown_api/dashboards/tests/test_dashboard_auth_fallback.py `
  audit-artifacts/frontend-ready-surface

git show --stat --oneline 1a5fb6c3
```

Keep these categories separate:

- release verifier;
- dashboard authentication and tenant behavior;
- durable evidence;
- unrelated local edits.

## Phase 2 — Synchronize or replace PR #1308

PR #1308 contains the secret-scan SARIF fallback repair. Its corrected historical head is `35bea30e53c31ee1feda788dc22f23647d674e41`.

Recreate or update it from current main with only `.github/workflows/secret-scan.yml`.

Required behavior:

- gitleaks findings still fail the scan;
- redaction remains enabled;
- a valid empty SARIF file is created only when gitleaks produced none;
- the SARIF file is validated as JSON;
- artifact upload remains required;
- no `continue-on-error` is added;
- secret scanning is not weakened.

## Phase 3 — Repair P0 issue #1309

The following workflows have completed substantive work and then failed during artifact upload:

- secret scan;
- schema governance;
- release scorecard;
- Python license audit;
- Node license audit;
- SBOM and related evidence workflows may share the defect.

Use GitHub CLI to inspect exact logs:

```powershell
gh auth status
gh run view 29167570098 --log
gh run view 29167570090 --log
gh run view 29167570522 --log
gh run view 29167570037 --log

git grep -n "actions/upload-artifact" -- .github/workflows
```

Determine the actual shared cause before editing workflows:

- artifact quota or retention;
- duplicate names;
- invalid paths;
- missing files;
- permissions;
- action version;
- oversized artifacts;
- GitHub service behavior.

Do not hide evidence failures with `continue-on-error`.

Required proof before closing #1309:

- secret-scan artifact uploads;
- schema-governance artifacts upload;
- release-scorecard artifact uploads;
- Python and Node license artifacts upload;
- SBOM artifact uploads if affected;
- artifacts are downloadable;
- substantive gate behavior remains unchanged.

## Phase 4 — Recover the release verifier fix

Create a current-main branch containing only:

```text
scripts/release/verify-frontend-rc.mjs
```

If local commit `1a5fb6c3` is clean and one-file, cherry-pick it. Otherwise restore only the verifier file.

The verifier must:

- resolve repository-relative paths correctly;
- work from the documented invocation directory;
- fail on genuinely missing required assets;
- avoid developer-specific absolute paths;
- preserve all release checks.

Run the exact package script from the correct package directory, then commit, push, and open a focused PR.

## Phase 5 — Resolve dev-open authentication and tenant changes

Limit this lane to:

```text
backend/crown_api/dashboards/views.py
backend/core/tenant_header_middleware.py
backend/crown_api/dashboards/tests/test_dashboard_auth_fallback.py
```

Production requirements:

- unauthenticated requests fail closed;
- missing or invalid tenant context fails closed;
- cross-tenant requests fail;
- missing roles fail;
- production cannot use fallback tenants;
- production cannot auto-create a tenant;
- production cannot bypass role checks;
- dev-open behavior cannot be accidentally enabled in production.

Add negative tests for production, anonymous, missing tenant, invalid tenant, cross-tenant, auto-creation, and RBAC bypass cases.

Do not push this lane unless fail-closed tests pass.

## Phase 6 — Replace or synchronize PR #1285

Intended five-file scope:

```text
backend/crown_api/management/commands/seed_all_dashboard_snapshots.py
backend/crown_api/tests/test_seed_all_dashboard_snapshots.py
frontend/dashboards/tests/certification/certification-matrix.ts
frontend/dashboards/tests/certification/evidence-writer.ts
frontend/dashboards/tests/certification/production-certification-crawler.spec.ts
```

No-pretend rules:

- snapshot is not live;
- sample is not live;
- fallback is not live;
- unknown is not live;
- seeded dashboard records default to `live_certified=False`;
- only authenticated tenant-scoped API evidence may classify as live;
- production certification must fail when provenance is absent or non-live.

Recreate the branch from current main and preserve only the intended scope.

## Phase 7 — Repair dependency vulnerabilities

```powershell
Set-Location 'C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr'
python -m pip install --upgrade pip pip-audit
pip-audit -r requirements.txt
if (Test-Path backend\requirements.txt) {
    pip-audit -r backend\requirements.txt
}

Set-Location frontend\dashboards
npm audit
npm audit --omit=dev
```

Use the smallest compatible fixed versions. Do not use `npm audit fix --force`.

## Phase 8 — Buyer-ready completion

Build a definitive customer-visible inventory from:

- dashboard registry;
- router;
- left and right navigation;
- role menus;
- module manifests;
- wizard registry;
- widget registry;
- customer action links.

For each route and persona:

1. log in normally;
2. confirm correct role and tenant;
3. navigate through the UI;
4. confirm the page renders;
5. confirm required APIs succeed;
6. exercise every link and button;
7. exercise widgets and filters;
8. submit forms with valid and invalid data;
9. verify loading, empty, error, validation, and permission states;
10. confirm no console errors or unexplained network failures;
11. confirm no broken images;
12. confirm responsive layout and accessibility basics;
13. fix every defect and rerun the route.

Required personas include school administrator, teacher, parent, and every other release-visible persona in the registry.

Required workflows include admissions, enrollment, billing, attendance, financial aid, discipline, communications, governance, parent workflows, teacher workflows, administrator workflows, and all registered wizards.

Appearance review must include CROWN branding, light royal theme, consistent palette, typography, spacing, symmetry, icons, responsive behavior, no clipping or overflow, finished loading/error states, and correct Microsoft asset handling.

## Phase 9 — Azure staging and same-SHA proof

After required fixes are merged:

1. identify the approved main SHA;
2. deploy that SHA to Azure staging or controlled sandbox;
3. prove backend and frontend build SHAs;
4. prove both equal the approved GitHub SHA;
5. run authenticated buyer-ready flows;
6. prove tenant propagation;
7. prove no-pretend live data;
8. run rollback and restore;
9. verify health, monitoring, Key Vault, secrets, and payment boundaries.

Do not approve production until the same deployed SHA passes.

## Merge order

1. current-main replacement for #1308;
2. #1309 artifact-upload repair;
3. release verifier fix;
4. secure tenant/auth fix;
5. clean replacement for #1285;
6. dependency vulnerability fixes;
7. functional customer-surface fixes;
8. visual customer-surface fixes;
9. recovery, secrets, monitoring, and deployment closure.

## Final reporting format

Report only:

- current main SHA;
- merged PRs;
- open PRs;
- files changed;
- commands run;
- pass results;
- failures fixed;
- remaining failures;
- customer-visible surfaces completed;
- customer-visible surfaces not complete;
- Azure deployed SHA;
- rollback result;
- restore result;
- production decision.

Production remains NO-GO unless every buyer-ready requirement has current same-SHA deployed proof.

Start with Phase 1. Preserve local work before changing branches or resetting anything.