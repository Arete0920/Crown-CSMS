# CROWN Parallel Module Start Runbook

Status: Morning Execution Runbook
Date: 2026-06-10
Scope: Modules first only
Release Authority: `docs/CURRENT_RELEASE_STATUS.md`
Parent Canon: `docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md`

## Purpose

This runbook gives TC, ChatGPT, VS Code, GitHub, and Copilot a clean parallel workflow for starting the module-first completion plan.

This runbook does not approve production release, approve sandbox launch, certify modules, certify dashboards, or change release posture.

## Operating Rule

```text
Modules first.
Dashboards second.
Certification last.
Registry coverage is not completion.
Sample/template data is not production proof.
TC cannot self-approve.
ChatGPT cannot approve work it authored.
Copilot review counts only when captured as evidence.
NO-GO remains until evidence proves otherwise.
```

## Active Parallel Lanes

| Lane | Owner | Work Type | Evidence Output |
|---|---|---|---|
| Direction lane | TC | Priority, product direction, final human steering | Chat direction and accepted priorities |
| Connector lane | ChatGPT | GitHub connector inspection, docs/evidence organization, repo file support | Commits, fetched file evidence, citations |
| Local execution lane | TC in VS Code | Local repo checks, grep/search, tests, Copilot review capture | Terminal logs and committed artifacts |
| Review lane | GitHub Copilot | Planning/control review and later code review | Captured review output in GitHub/VS Code/evidence packet |
| Release authority lane | Current release docs/checks | GO/NO-GO only | `docs/CURRENT_RELEASE_STATUS.md` and current-head evidence |

## Do Not Do

- Do not start dashboards.
- Do not start UI polish.
- Do not implement multiple modules at once.
- Do not change `docs/CURRENT_RELEASE_STATUS.md` in this lane.
- Do not treat Copilot output as release GO.
- Do not treat docs as module certification.
- Do not treat page rendering as completion.
- Do not treat sample data as proof.
- Do not merge or promote without captured evidence.

## Morning Sequence

### Phase A: Repo Restart

1. Open VS Code at:

```text
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr
```

2. Run the restart probe.
3. Classify dirty state before editing.
4. Verify canon files exist.
5. Capture output to evidence.

### Phase B: Canon Verification and Copilot Review

1. Verify seven canon/control files.
2. Run Copilot review against only the canon package.
3. Capture Copilot output.
4. Commit Copilot evidence.
5. Apply corrections if needed.
6. Update review packet status only if evidence supports it.

### Phase C: Module 1 Inventory

Only after Phase B is clean, begin Module 1:

```text
Module 1: School / Academic Year / Grade Level
```

Initial module evidence targets:

- `backend/core/models.py`
- migrations for `School`, `AcademicYear`, `GradeLevel`
- APIs/views/serializers/admin surfaces for school/year/grade setup
- tenant middleware and school context enforcement
- permissions touching school/year/grade setup
- tests touching school/year/grade setup
- frontend/admin/config surfaces if present
- dashboard dependency only as future fit, not dashboard implementation

## VS Code Paste Block

Paste the block below into a PowerShell terminal from the repo root or any location. It will move to the repo, create an evidence folder, run read-only verification checks, and write a restart evidence packet.

```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ============================================================
# CROWN MODULE-FIRST MORNING RESTART PACKET
# Scope: docs/evidence verification only; no implementation edits.
# Date: 2026-06-10
# ============================================================

$RepoRoot = 'C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$EvidenceRoot = Join-Path $RepoRoot 'audit-artifacts\module-first-start'
$EvidenceDir = Join-Path $EvidenceRoot $Stamp
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

Set-Location $RepoRoot

function Write-Section {
  param([string]$Title)
  ""
  "=== $Title ==="
}

$TranscriptPath = Join-Path $EvidenceDir '00_terminal_transcript.txt'
Start-Transcript -Path $TranscriptPath -Force | Out-Null

try {
  Write-Section 'REPO ROOT'
  Get-Location

  Write-Section 'BRANCH'
  git branch --show-current

  Write-Section 'HEAD'
  git rev-parse HEAD

  Write-Section 'STATUS SHORT'
  git status --short

  Write-Section 'RECENT COMMITS'
  git log --oneline -n 20

  Write-Section 'REMOTE'
  git remote -v

  Write-Section 'CANON FILE EXISTENCE'
  $CanonFiles = @(
    'docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md',
    'docs/product/CROWN_MODULE_COMPLETION_MATRIX.md',
    'docs/product/CROWN_MODULE_DATA_OWNERSHIP_MATRIX.md',
    'docs/product/CROWN_MODULE_PERMISSION_MATRIX.md',
    'docs/product/CROWN_DASHBOARD_FIT_MATRIX.md',
    'docs/product/CROWN_MODULE_REVIEW_RACI.md',
    'docs/product/CROWN_MODULES_DASHBOARDS_REVIEW_PACKET.md',
    'docs/product/CROWN_PARALLEL_MODULE_START_RUNBOOK.md'
  )

  $fileRows = foreach ($f in $CanonFiles) {
    $exists = Test-Path -LiteralPath $f
    [pscustomobject]@{
      Path = $f
      Exists = $exists
      Length = if ($exists) { (Get-Item -LiteralPath $f).Length } else { 0 }
      LastWriteTime = if ($exists) { (Get-Item -LiteralPath $f).LastWriteTime.ToString('s') } else { '' }
    }
  }
  $fileRows | Format-Table -AutoSize
  $fileRows | Export-Csv -NoTypeInformation -Path (Join-Path $EvidenceDir '01_canon_file_existence.csv')

  Write-Section 'CANON GUARDRAIL SEARCH'
  $GuardrailPatterns = @(
    'production GO',
    'sandbox approval',
    'certify any module',
    'certify any dashboard',
    'PENDING COPILOT REVIEW',
    'COPILOT-REVIEWED',
    'NO-GO remains',
    'Registry coverage is not completion',
    'Sample/template data is not production proof',
    'TC cannot self-approve',
    'ChatGPT cannot approve'
  )

  $guardrailOut = Join-Path $EvidenceDir '02_guardrail_search.txt'
  foreach ($pattern in $GuardrailPatterns) {
    "--- PATTERN: $pattern ---" | Tee-Object -FilePath $guardrailOut -Append
    Select-String -Path 'docs/product/*.md' -Pattern $pattern -CaseSensitive:$false | Tee-Object -FilePath $guardrailOut -Append
  }

  Write-Section 'MODULE 1 TARGET FILE SEARCH'
  $module1Out = Join-Path $EvidenceDir '03_module1_search.txt'
  $SearchPatterns = @(
    'class School',
    'class AcademicYear',
    'class GradeLevel',
    'SchoolView',
    'AcademicYearView',
    'GradeLevelView',
    'school-year-grade',
    'grade_level',
    'academic_year'
  )
  foreach ($pattern in $SearchPatterns) {
    "--- PATTERN: $pattern ---" | Tee-Object -FilePath $module1Out -Append
    Get-ChildItem -Recurse -File -Include *.py,*.js,*.jsx,*.ts,*.tsx,*.md |
      Where-Object { $_.FullName -notmatch '\\.git\\|node_modules|\.venv|venv|__pycache__|dist|build' } |
      Select-String -Pattern $pattern -CaseSensitive:$false |
      Select-Object Path, LineNumber, Line |
      Format-Table -AutoSize | Tee-Object -FilePath $module1Out -Append
  }

  Write-Section 'MODULE 1 MODEL CONTEXT'
  $modelContextOut = Join-Path $EvidenceDir '04_core_models_school_year_grade.txt'
  if (Test-Path 'backend/core/models.py') {
    Select-String -Path 'backend/core/models.py' -Pattern 'class School|class AcademicYear|class GradeLevel' -Context 0,30 |
      Tee-Object -FilePath $modelContextOut
  } else {
    'backend/core/models.py not found' | Tee-Object -FilePath $modelContextOut
  }

  Write-Section 'MIGRATION SEARCH FOR MODULE 1'
  $migrationOut = Join-Path $EvidenceDir '05_module1_migration_search.txt'
  if (Test-Path 'backend/core/migrations') {
    Get-ChildItem 'backend/core/migrations' -File -Filter '*.py' |
      Select-String -Pattern 'School|AcademicYear|GradeLevel' -CaseSensitive:$false |
      Select-Object Path, LineNumber, Line |
      Format-Table -AutoSize | Tee-Object -FilePath $migrationOut
  } else {
    'backend/core/migrations not found' | Tee-Object -FilePath $migrationOut
  }

  Write-Section 'URL API SURFACE SEARCH'
  $apiOut = Join-Path $EvidenceDir '06_module1_api_surface_search.txt'
  Get-ChildItem -Recurse -File -Include urls.py,views.py,serializers.py,api.py |
    Where-Object { $_.FullName -notmatch '\\.git\\|node_modules|\.venv|venv|__pycache__|dist|build' } |
    Select-String -Pattern 'School|AcademicYear|GradeLevel|school|academic_year|grade_level' -CaseSensitive:$false |
    Select-Object Path, LineNumber, Line |
    Format-Table -AutoSize | Tee-Object -FilePath $apiOut

  Write-Section 'TEST SURFACE SEARCH'
  $testOut = Join-Path $EvidenceDir '07_module1_test_surface_search.txt'
  Get-ChildItem -Recurse -File -Include '*test*.py','*.test.js','*.test.jsx','*.spec.js','*.spec.jsx' |
    Where-Object { $_.FullName -notmatch '\\.git\\|node_modules|\.venv|venv|__pycache__|dist|build' } |
    Select-String -Pattern 'School|AcademicYear|GradeLevel|school|academic_year|grade_level' -CaseSensitive:$false |
    Select-Object Path, LineNumber, Line |
    Format-Table -AutoSize | Tee-Object -FilePath $testOut

  Write-Section 'COPILOT REVIEW TEMPLATE'
  $copilotTemplate = @'
# CROWN Module/Dashboard Canon Copilot Review

Date: 2026-06-10
Scope: Module/dashboard planning governance files only
Reviewer path: GitHub Copilot through VS Code
Release impact: None
Production GO: No
Sandbox approval: No
Module certification: No
Dashboard certification: No

## Files Reviewed

- docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md
- docs/product/CROWN_MODULE_COMPLETION_MATRIX.md
- docs/product/CROWN_MODULE_DATA_OWNERSHIP_MATRIX.md
- docs/product/CROWN_MODULE_PERMISSION_MATRIX.md
- docs/product/CROWN_DASHBOARD_FIT_MATRIX.md
- docs/product/CROWN_MODULE_REVIEW_RACI.md
- docs/product/CROWN_MODULES_DASHBOARDS_REVIEW_PACKET.md
- docs/product/CROWN_PARALLEL_MODULE_START_RUNBOOK.md

## Copilot Prompt Used

Review these CROWN module/dashboard planning governance files only.

Do not review the whole repo.

Check for:
1. Internal contradictions.
2. Unsupported completion claims.
3. Any accidental production GO, sandbox approval, module certification, or dashboard certification language.
4. Any self-approval loophole for TC or ChatGPT.
5. Any missing evidence requirement.
6. Any module ordering problem.
7. Any data ownership conflict or duplicate-truth risk.
8. Any permission/security gap.
9. Any dashboard fit/certification gap.
10. Any wording that could let registry coverage, sample data, component rendering, or screenshots be treated as completion.

Return:
- PASS/FAIL for planning-use readiness.
- Blocking corrections.
- Non-blocking improvements.
- Files/sections needing edits.
- Final recommendation using one of:
  PENDING CORRECTIONS
  COPILOT-REVIEWED FOR PLANNING USE - NOT PRODUCTION GO

## Copilot Review Output

PASTE COPILOT OUTPUT HERE.
'@

  $copilotDir = Join-Path $RepoRoot 'audit-artifacts\module-canon-review'
  New-Item -ItemType Directory -Force -Path $copilotDir | Out-Null
  $copilotPath = Join-Path $copilotDir '20260610_copilot_review.md'
  if (-not (Test-Path $copilotPath)) {
    Set-Content -Path $copilotPath -Value $copilotTemplate -Encoding UTF8
  }
  Write-Host "Created/verified Copilot review template: $copilotPath"

  Write-Section 'SUMMARY JSON'
  $summary = [ordered]@{
    timestamp = $Stamp
    repo_root = $RepoRoot
    branch = (git branch --show-current)
    head = (git rev-parse HEAD)
    canon_files_expected = $CanonFiles.Count
    canon_files_present = @($fileRows | Where-Object { $_.Exists }).Count
    missing_files = @($fileRows | Where-Object { -not $_.Exists } | ForEach-Object { $_.Path })
    evidence_dir = $EvidenceDir
    copilot_review_template = $copilotPath
    production_go = 'NO'
    sandbox_approval = 'NO'
    module_certification = 'NO'
    dashboard_certification = 'NO'
    next_step = 'Run Copilot review, paste output into audit-artifacts/module-canon-review/20260610_copilot_review.md, then commit evidence only.'
  }
  $summary | ConvertTo-Json -Depth 6 | Tee-Object -FilePath (Join-Path $EvidenceDir '08_summary.json')

  Write-Section 'NEXT COMMANDS'
  @'
After Copilot output is pasted into audit-artifacts/module-canon-review/20260610_copilot_review.md, run:

git status --short
git add audit-artifacts/module-canon-review/20260610_copilot_review.md
git add audit-artifacts/module-first-start
git commit -m "audit(product): capture module-first start and Copilot review evidence"
git status --short
'@
}
finally {
  Stop-Transcript | Out-Null
}
```

## Copilot Review Prompt

Use this exact prompt in Copilot Chat after running the restart packet:

```text
Review these CROWN module/dashboard planning governance files only:

- docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md
- docs/product/CROWN_MODULE_COMPLETION_MATRIX.md
- docs/product/CROWN_MODULE_DATA_OWNERSHIP_MATRIX.md
- docs/product/CROWN_MODULE_PERMISSION_MATRIX.md
- docs/product/CROWN_DASHBOARD_FIT_MATRIX.md
- docs/product/CROWN_MODULE_REVIEW_RACI.md
- docs/product/CROWN_MODULES_DASHBOARDS_REVIEW_PACKET.md
- docs/product/CROWN_PARALLEL_MODULE_START_RUNBOOK.md

Do not review the whole repo.
Do not suggest production release.
Do not certify any module.
Do not certify any dashboard.

Check for:
1. Internal contradictions.
2. Unsupported completion claims.
3. Any accidental production GO, sandbox approval, module certification, or dashboard certification language.
4. Any self-approval loophole for TC or ChatGPT.
5. Any missing evidence requirement.
6. Any module ordering problem.
7. Any data ownership conflict or duplicate-truth risk.
8. Any permission/security gap.
9. Any dashboard fit/certification gap.
10. Any wording that could let registry coverage, sample data, component rendering, or screenshots be treated as completion.

Return:
- PASS/FAIL for planning-use readiness.
- Blocking corrections.
- Non-blocking improvements.
- Files/sections needing edits.
- Final recommendation using one of:
  PENDING CORRECTIONS
  COPILOT-REVIEWED FOR PLANNING USE - NOT PRODUCTION GO
```

## ChatGPT Connector Lane Tasks

While TC runs the VS Code block, ChatGPT should use the GitHub connector to:

1. Verify this runbook exists on GitHub.
2. Verify the canon package exists on GitHub.
3. Inspect the current committed text for release-authority boundaries.
4. Inspect Module 1 repo surfaces through connector where possible.
5. Prepare Module 1 evidence interpretation from committed repo evidence.
6. Avoid code changes until Copilot review evidence is captured.

## Module 1 Definition

Module 1 is:

```text
School / Academic Year / Grade Level
```

Module 1 does not include dashboards. Dashboard references are future fit only.

## Module 1 Required Questions

Before moving Module 1 beyond Schema-visible, answer with evidence:

1. Which models exist?
2. Which migrations create or modify them?
3. Which admin/API surfaces expose them?
4. Which serializers or schemas exist?
5. Which permissions protect them?
6. Which tenant boundaries protect them?
7. Which tests verify them?
8. Which rollover/year-end rules exist?
9. Which downstream modules depend on them?
10. Which gaps block promotion?

## Module 1 Evidence Packet Target

Expected evidence folder after local run:

```text
audit-artifacts/module-first-start/<timestamp>/
```

Expected files:

- `00_terminal_transcript.txt`
- `01_canon_file_existence.csv`
- `02_guardrail_search.txt`
- `03_module1_search.txt`
- `04_core_models_school_year_grade.txt`
- `05_module1_migration_search.txt`
- `06_module1_api_surface_search.txt`
- `07_module1_test_surface_search.txt`
- `08_summary.json`

Expected Copilot evidence file:

```text
audit-artifacts/module-canon-review/20260610_copilot_review.md
```

## Completion Criteria for Morning Start

Morning restart is complete only when:

- repo branch/head/status captured
- canon files verified
- guardrail search captured
- Module 1 search captured
- Copilot review template created
- Copilot review output pasted
- evidence committed
- no release-status changes made
- no implementation files changed

## Next Step After Morning Start

If Copilot returns `COPILOT-REVIEWED FOR PLANNING USE - NOT PRODUCTION GO`, begin Module 1 inspection and update only the relevant planning/evidence rows.

If Copilot returns blockers, fix planning docs first and rerun Copilot review.
