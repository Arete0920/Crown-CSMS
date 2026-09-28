param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("Start", "Close")]
    [string]$Mode,

    [string]$WorkItem = "50 Wizard Deep Dive",

    [string[]]$AllowedPrefixes = @(
        "docs/operations/",
        "scripts/execution/120_wizard_inventory_audit.ps1",
        "scripts/execution/121_50_wizard_deep_dive_assessment.ps1",
        "scripts/execution/122_crown_guarded_work_session.ps1",
        "audit-artifacts/wizard-inventory/",
        "audit-artifacts/50-wizard-deep-dive/",
        "audit-artifacts/guarded-work-sessions/"
    )
)

$ErrorActionPreference = "Stop"

function To-RepoPath {
    param([string]$Path)
    ($Path -replace "\\", "/").TrimStart("./")
}

function Is-Allowed {
    param([string]$Path, [string[]]$Prefixes)
    $p = To-RepoPath $Path
    foreach ($prefix in $Prefixes) {
        $x = To-RepoPath $prefix
        if ($p -eq $x -or $p.StartsWith($x)) {
            return $true
        }
    }
    $false
}

function Get-Stamp {
    Get-Date -Format "yyyyMMdd_HHmmss"
}

$RepoRoot = git rev-parse --show-toplevel
Set-Location $RepoRoot

$GuardRoot = "audit-artifacts\guarded-work-sessions"
New-Item -ItemType Directory -Force -Path $GuardRoot | Out-Null
$LatestFile = Join-Path $GuardRoot "LATEST.txt"

if ($Mode -eq "Start") {
    $Stamp = Get-Stamp
    $SessionDir = Join-Path $GuardRoot $Stamp
    New-Item -ItemType Directory -Force -Path $SessionDir | Out-Null

    $Status = git status --porcelain
    if ($Status) {
        $Status | Set-Content (Join-Path $SessionDir "DIRTY_STATUS_AT_START.txt")
        throw "Working tree is not clean. Stop. Commit/stash/revert unrelated work before guarded session."
    }

    $Branch = git branch --show-current
    $Head = git rev-parse HEAD
    $BackupBranch = "backup/pre-guarded-wizard-$Stamp"
    git branch $BackupBranch $Head | Out-Null

    @{
        GeneratedAt = (Get-Date).ToString("s")
        WorkItem = $WorkItem
        RepoRoot = $RepoRoot
        Branch = $Branch
        Head = $Head
        BackupBranch = $BackupBranch
    }.GetEnumerator() | ForEach-Object {
        "{0}: {1}" -f $_.Key, $_.Value
    } | Set-Content (Join-Path $SessionDir "00_SESSION_START.txt")

    $AllowedPrefixes | Set-Content (Join-Path $SessionDir "01_ALLOWED_PREFIXES.txt")

    git ls-files |
        ForEach-Object {
            $file = $_
            if (Test-Path $file) {
                $hash = (Get-FileHash -Algorithm SHA256 $file).Hash
                [pscustomobject]@{
                    Path = $file
                    Sha256 = $hash
                }
            }
        } |
        Export-Csv (Join-Path $SessionDir "02_FILE_HASHES_BEFORE.csv") -NoTypeInformation

    $SessionDir | Set-Content $LatestFile

    Write-Host ""
    Write-Host "GUARDED WORK SESSION STARTED"
    Write-Host "Session: $SessionDir"
    Write-Host "Backup branch: $BackupBranch"
    Write-Host ""
    Write-Host "Keep the work bounded to the approved work item and allowed paths. Do not allow broad edits."
    exit 0
}

if ($Mode -eq "Close") {
    if (!(Test-Path $LatestFile)) {
        throw "No guarded session found. Run Mode Start first."
    }

    $SessionDir = (Get-Content $LatestFile -Raw).Trim()
    if (!(Test-Path $SessionDir)) {
        throw "Session directory not found: $SessionDir"
    }

    $Changed = git status --porcelain
    $Changed | Set-Content (Join-Path $SessionDir "03_GIT_STATUS_AT_CLOSE.txt")
    git diff --name-status | Set-Content (Join-Path $SessionDir "04_GIT_DIFF_NAME_STATUS.txt")
    git diff --stat | Set-Content (Join-Path $SessionDir "05_GIT_DIFF_STAT.txt")
    git diff --check 2>&1 | Set-Content (Join-Path $SessionDir "06_GIT_DIFF_CHECK.txt")

    $ChangedFiles = @()
    foreach ($line in $Changed) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $path = $line.Substring(3)
        if ($path -match " -> ") {
            $path = ($path -split " -> ")[-1]
        }
        $ChangedFiles += [pscustomobject]@{
            Status = $line.Substring(0, 2).Trim()
            Path = To-RepoPath $path
            Allowed = Is-Allowed $path $AllowedPrefixes
        }
    }

    $ChangedFiles | Export-Csv (Join-Path $SessionDir "07_CHANGED_FILES_ALLOWLIST_CHECK.csv") -NoTypeInformation

    $Forbidden = @($ChangedFiles | Where-Object { $_.Allowed -eq $false })
    $Deletes = @($ChangedFiles | Where-Object { $_.Status -match "D" })

    $DangerPatterns = @(
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "requirements.txt",
        "pyproject.toml",
        "poetry.lock",
        ".github/workflows/",
        "migrations/",
        "settings.py",
        ".env",
        "azure",
        "auth",
        "rbac",
        "tenant"
    )

    $DangerHits = foreach ($f in $ChangedFiles) {
        foreach ($p in $DangerPatterns) {
            if ($f.Path.ToLowerInvariant().Contains($p.ToLowerInvariant())) {
                [pscustomobject]@{
                    Path = $f.Path
                    Pattern = $p
                }
            }
        }
    }

    $DangerHits | Export-Csv (Join-Path $SessionDir "08_DANGER_PATTERN_HITS.csv") -NoTypeInformation

    $ValidationLog = Join-Path $SessionDir "09_VALIDATION_LOG.txt"
    "=== VALIDATION START $((Get-Date).ToString('s')) ===" | Set-Content $ValidationLog
    "=== git diff --check ===" | Add-Content $ValidationLog
    git diff --check 2>&1 | Add-Content $ValidationLog

    if (Test-Path "backend\manage.py") {
        "=== Django check ===" | Add-Content $ValidationLog
        python backend\manage.py check 2>&1 | Add-Content $ValidationLog
    } elseif (Test-Path "manage.py") {
        "=== Django check ===" | Add-Content $ValidationLog
        python manage.py check 2>&1 | Add-Content $ValidationLog
    } else {
        "Django check skipped: no manage.py found." | Add-Content $ValidationLog
    }

    if (Test-Path "package.json") {
        "=== npm lint/test availability ===" | Add-Content $ValidationLog
        npm run 2>&1 | Select-String -Pattern "lint|test|typecheck|build" | Add-Content $ValidationLog
    }

    $Decision = if ($Forbidden.Count -gt 0 -or $Deletes.Count -gt 0 -or @($DangerHits).Count -gt 0) {
        "NO-GO"
    } else {
        "REVIEW"
    }

    $Summary = @"
Crown Guarded Work Session Close
Generated: $((Get-Date).ToString("s"))

Decision
$Decision

Work Item
$WorkItem

Changed Files
$($ChangedFiles.Count)

Forbidden Changed Files
$($Forbidden.Count)

Deleted Files
$($Deletes.Count)

Danger Pattern Hits
$(@($DangerHits).Count)

Rule
- NO-GO means do not commit, push, or continue until reviewed.
- REVIEW means changed files stayed inside the allowlist, but normal validation still must be inspected.
- PASS is only granted by the task-specific audit script, not by this guard script.

Files To Review
- 03_GIT_STATUS_AT_CLOSE.txt
- 04_GIT_DIFF_NAME_STATUS.txt
- 05_GIT_DIFF_STAT.txt
- 06_GIT_DIFF_CHECK.txt
- 07_CHANGED_FILES_ALLOWLIST_CHECK.csv
- 08_DANGER_PATTERN_HITS.csv
- 09_VALIDATION_LOG.txt
"@

    $Summary | Set-Content (Join-Path $SessionDir "SUMMARY.md")

    Write-Host ""
    Write-Host "GUARDED WORK SESSION CLOSED"
    Write-Host "Decision: $Decision"
    Write-Host "Session: $SessionDir"
    Write-Host ""
    Write-Host "Open summary:"
    Write-Host "code `"$SessionDir\SUMMARY.md`""
    Write-Host ""

    if ($Decision -eq "NO-GO") {
        exit 2
    }

    exit 0
}
