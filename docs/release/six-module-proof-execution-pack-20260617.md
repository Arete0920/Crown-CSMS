# CROWN Six-Module Proof Execution Pack - 2026-06-17

## Purpose

This execution pack coordinates same-day closure for the six remaining NOT_PROVEN module lanes without overstating release, dashboard, wizard, or production readiness.

Parent issue: #1070.

## Controlling evidence reviewed

- `audit-artifacts/module-completion/current/05_completion_scorecard.md`
- `audit-artifacts/module-completion/current/01_module_matrix_expanded.csv`
- `audit-artifacts/full-completion-discovery/20260616_220702/01_remaining_module_inventory.csv`
- `audit-artifacts/module-completion/remaining-six-inventory/20260617_090619/01_file_universe.txt`
- `docs/release/WIZARD_EVIDENCE_BOUNDARY_20260614.md`
- `docs/release/crown-universal-proof/CROWN_12x12_UNIVERSAL_PROOF_MATRIX.md`
- PR #1068 changed-file inventory
- PR #1069 changed-file inventory

## Verified baseline

- Modules: 45 of 51 PROVEN; 6 NOT_PROVEN.
- Remaining modules: 026, 030, 031, 037, 039, 050.
- Dashboards: 40 mapped; 0 live-data validated.
- Wizards: 28 of 28 route/API contract validated only; not full E2E wizard completion.
- Production remains NO-GO.

## Non-negotiable rule

Do not mark a module PROVEN unless proof exists on merged main and the canonical matrix plus scorecard have been reconciled after merge. Local-only evidence, issue text, draft PRs, or unmerged PR evidence does not move the canonical score.

## Tightened execution approach

The earlier plan is directionally correct and consistent with the controlling scorecard. The required tightening is that each VS Code lane must first run a local preflight inventory against actual repository files before writing proof tests. Proof tests must target real implementation surfaces, not guessed routes/classes/functions.

## Module lanes

| Module | Status now | Blocker | Current execution source | Integrity requirement |
| --- | --- | --- | --- | --- |
| 026 After-School & Extended Care | NOT_PROVEN | Enrollment and activity scheduling tests required | Existing PR #1068 | Review changed focused test and validation artifacts before merge. |
| 030 Student Portal | NOT_PROVEN | Student account and enrollment view tests required | Issue #1071 | Build proof from actual student/account/enrollment routes and tests discovered locally. |
| 031 Administrative Portal | NOT_PROVEN | Admin workspace and oversight tests required | Issue #1072 | Build proof from actual admin/oversight/workspace surfaces discovered locally. |
| 037 Advanced Discipline Workflows | NOT_PROVEN | Appeal process and data retention tests required | Issue #1073 | Build proof from actual discipline/appeal/retention surfaces discovered locally. |
| 039 Christian Formation & Tracking | NOT_PROVEN | Faith formation rubric and portfolio tests required | Existing PR #1069 | Evidence-only PR must be reviewed against existing spiritual-life tests before PROVEN credit. |
| 050 BI/reporting suite | NOT_PROVEN | Data warehouse and reporting tests required | Issue #1074 | Build proof from actual analytics/reporting/export/warehouse surfaces discovered locally. |

## PR #1068 review focus

PR #1068 includes a focused test file and evidence packet paths for Module 026. Review should check:

- test file is not superficial/static-only;
- enrollment behavior is covered;
- activity scheduling behavior is covered;
- auth denial is covered;
- tenant scoping/isolation is covered;
- `manage.py check` output is captured;
- focused pytest output is captured;
- evidence packet is committed.

## PR #1069 review focus

PR #1069 changed-file inventory is evidence-artifact only. It should not be accepted as Module 039 proof unless its evidence packet demonstrates that existing spiritual-life tests already prove:

- formation rubric behavior;
- portfolio behavior;
- API/view/route surface;
- auth denial;
- tenant scoping/isolation;
- focused pytest output.

If that review does not prove the blocker, add or require a focused test file such as:

```text
backend/tests/test_51x51_evidence_039_christian_formation.py
```

or the correct existing app-level test path if implementation is already under `backend/spiritual_life/tests/`.

## VS Code preflight inventory - run before writing test code

Run from repository root in PowerShell.

```powershell
$ErrorActionPreference = "Stop"
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
  $PSNativeCommandUseErrorActionPreference = $false
}
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$root = "audit-artifacts/module-completion/six-module-preflight/$stamp"
New-Item -ItemType Directory -Force -Path $root | Out-Null

git status --short | Out-File "$root/00_git_status.txt" -Encoding utf8
git rev-parse HEAD | Out-File "$root/01_head_sha.txt" -Encoding utf8
python backend/manage.py check *>&1 | Out-File "$root/02_manage_check.txt" -Encoding utf8

$queries = @(
  "aftercare|extended care|activity scheduling|activity schedule|enrollment",
  "student portal|student account|student profile|student enrollment|student360|views_students",
  "administrative portal|admin portal|admin workspace|oversight|administrator",
  "discipline appeal|appeal process|retention|archive|advanced discipline",
  "christian formation|formation rubric|spiritual life|portfolio|faith formation",
  "business intelligence|analytics|warehouse|reporting|reports|metrics"
)

$idx = 1
foreach ($q in $queries) {
  $safe = $idx.ToString("00")
  rg -n -i $q backend frontend docs audit-artifacts --glob '!**/.git/**' *> "$root/${safe}_rg.txt"
  $idx++
}

Get-ChildItem backend -Recurse -File -Include "*test*.py" |
  Select-Object -ExpandProperty FullName |
  Out-File "$root/20_backend_test_inventory.txt" -Encoding utf8

Get-ChildItem backend -Recurse -File -Include "urls.py","api_urls.py","views.py","api.py","services.py","models.py","serializers.py" |
  Select-Object -ExpandProperty FullName |
  Out-File "$root/21_backend_surface_inventory.txt" -Encoding utf8

git status --short | Out-File "$root/99_git_status_after.txt" -Encoding utf8
Write-Host "Preflight inventory written to $root"
```

## Isolated proof branch workflow

Use one branch per module. Do not combine implementation proof for multiple modules unless deliberately reviewed that way.

```powershell
$ErrorActionPreference = "Stop"

git checkout main
git pull

git checkout -b feat/module-030-student-portal-proof-20260617
```

Then create the focused test only after reading the preflight inventory.

## Required validation for every module PR

```powershell
python backend/manage.py check
python -m pytest <focused-test-file> -v --nomigrations --tb=short
```

Capture both outputs under the module evidence folder:

```text
audit-artifacts/module-completion/module-<id>-<slug>/<timestamp>/02_manage_check.txt
audit-artifacts/module-completion/module-<id>-<slug>/<timestamp>/03_pytest.txt
```

## Module-specific target files

Expected focused test paths unless local preflight proves a better app-level path:

```text
backend/tests/test_51x51_evidence_030_student_portal.py
backend/tests/test_51x51_evidence_031_administrative_portal.py
backend/tests/test_51x51_evidence_037_advanced_discipline_workflows.py
backend/tests/test_51x51_evidence_050_business_intelligence_suite.py
```

For Module 039, prefer reviewing existing PR #1069 first. Add a focused test only if the existing evidence does not satisfy the rubric/portfolio blocker.

## Reconciliation after merge

Only after the proof PRs merge:

1. Update `audit-artifacts/module-completion/current/01_module_matrix_expanded.csv`.
2. Update `audit-artifacts/module-completion/current/05_completion_scorecard.md`.
3. Cite the merged PR numbers and evidence paths.
4. Preserve explicit boundaries:
   - dashboard live-data readiness remains separate;
   - full E2E wizard completion remains separate;
   - production readiness remains separate;
   - independent review remains required.

## Final expected module score if all six are proven and reconciled

If and only if all six modules are merged and reconciled from evidence, module completion may move from 45/51 to 51/51. This does not move dashboard status from 0/40 live-data validated and does not independently authorize production GO.
