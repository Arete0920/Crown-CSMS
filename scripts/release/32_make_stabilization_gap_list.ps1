$ErrorActionPreference = "Stop"

function Write-Utf8File {
    param([string]$Path,[string]$Content)
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    [System.IO.File]::WriteAllText((Join-Path (Get-Location) $Path), $Content, (New-Object System.Text.UTF8Encoding($false)))
}

$latestPack = Get-ChildItem -Directory AUDIT_PACK_* -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1
if (-not $latestPack) { throw "No AUDIT_PACK_* directory found." }

$pack = $latestPack.FullName
$packName = $latestPack.Name

function Read-Text([string]$name) {
    $p = Join-Path $pack $name
    if (Test-Path $p) { return Get-Content $p -Raw }
    return ""
}

$bp   = Read-Text "05_BRANCH_PROTECTION_MAIN.json"
$urls = Read-Text "06_BACKEND_URLS.txt"
$migs = Read-Text "07_MIGRATIONS.txt"
$py   = Read-Text "08_PY_DEPS.txt"
$hp   = Read-Text "13_HEALTH_PROBE.txt"
$dep  = Read-Text "14_DEPLOY_PROD_RECENT.txt"

$bpState   = if ($bp   -match '403|Resource not accessible|not ready|error') { "OPEN" } else { "GREEN" }
$urlState  = if ($urls -match 'unavailable|not found|ERROR|Traceback|Exception|failed') { "OPEN" } else { "GREEN" }
$migState  = if ($migs -match 'not found|ERROR|Traceback|Exception|failed') { "OPEN" } else { "GREEN" }
$pyState   = if ($py   -match 'unavailable|not found|ERROR|Traceback|Exception|failed') { "OPEN" } else { "GREEN" }
$hpState   = if ($hp   -match 'ERROR:') { "OPEN" } else { "GREEN" }
$depState  = if ($dep  -match 'cannot fetch|No run data|ERROR|failed|not authenticated') { "OPEN" } else { "GREEN" }

$md = @"
# STABILIZATION GAP LIST

Pack: $packName

## Gaps

| Area | State | Exact fix path |
|---|---|---|
| Branch protection access | $bpState | Use authenticated GitHub CLI with permission to read branch protection. This is not a repo-code fix. |
| Backend URL extraction | $urlState | Ensure `django-extensions` is installed and in `INSTALLED_APPS`, then rerun the pack. |
| Migration extraction | $migState | Ensure Python env is healthy and `manage.py showmigrations` runs locally, then rerun the pack. |
| Python dependency extraction | $pyState | Ensure the audit runner can execute `python -m pip freeze`, then rerun the pack. |
| Health/integrity probe | $hpState | Set a valid health base URL or run local server on 127.0.0.1:8000 before rerun. |
| Deploy recency evidence | $depState | Use authenticated GitHub CLI and corrected `gh run list` invocation, then rerun the pack. |

## Non-fixable in repo code
- Branch protection `403` is a permissions/integration issue.
- GitHub run history fetch requires valid GitHub CLI auth.

## Next commands
1. `pwsh -File scripts/release/33_apply_stabilization_fixes.ps1`
2. `pwsh -File scripts/release/34_rerun_stabilization_audit.ps1`
"@

Write-Utf8File -Path "docs/release/STABILIZATION_GAP_LIST.md" -Content $md
Write-Host "Wrote docs/release/STABILIZATION_GAP_LIST.md"
