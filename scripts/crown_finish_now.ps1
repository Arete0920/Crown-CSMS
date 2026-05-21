param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [switch]$EnableCleanup
)

$ErrorActionPreference = "Stop"

function New-UniqueDirectoryPath {
    param([string]$BasePath)

    $Candidate = $BasePath
    $Suffix = 1
    while (Test-Path $Candidate) {
        $Candidate = "{0}_{1:00}" -f $BasePath, $Suffix
        $Suffix++
    }

    return $Candidate
}

function New-UniqueFilePath {
    param([string]$Directory, [string]$Name)

    $Stem = [System.IO.Path]::GetFileNameWithoutExtension($Name)
    $Extension = [System.IO.Path]::GetExtension($Name)
    $Candidate = Join-Path $Directory $Name
    $Suffix = 1
    while (Test-Path $Candidate) {
        $Candidate = Join-Path $Directory ("{0}_{1:00}{2}" -f $Stem, $Suffix, $Extension)
        $Suffix++
    }

    return $Candidate
}

$RepoRoot = (Resolve-Path $RepoRoot).Path
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Out = New-UniqueDirectoryPath (Join-Path $RepoRoot "audit-artifacts/finish-now/$Stamp")
$Quarantine = Join-Path $Out "quarantine"

New-Item -ItemType Directory -Force $Out | Out-Null
New-Item -ItemType Directory -Force $Quarantine | Out-Null

Set-Location $RepoRoot

function Add-Line {
    param([string]$Text)
    Add-Content -Path (Join-Path $Out "CROWN_FINISH_REPORT.md") -Value $Text -Encoding utf8
}

function Run-Capture {
    param(
        [string]$Name,
        [scriptblock]$Command
    )

    $Safe = $Name.ToLowerInvariant() -replace '[^a-z0-9]+','-'
    $File = Join-Path $Out "$Safe.txt"

    Add-Line ""
    Add-Line "## $Name"
    Add-Line ""

    $prevEap = $ErrorActionPreference
    try {
        # Native tools (npm/node/pytest) may write warnings to stderr even on success.
        # For command capture, classify result by exit code, not stderr stream presence.
        $ErrorActionPreference = "Continue"
        & $Command *>&1 | Tee-Object -FilePath $File
        $ErrorActionPreference = $prevEap
        $Code = $LASTEXITCODE
        if ($null -eq $Code) { $Code = 0 }

        if ($Code -eq 0) {
            Add-Line "**RESULT:** PASS"
        } else {
            Add-Line "**RESULT:** FAIL exit=$Code"
        }

        Add-Line ""
        Add-Line "Artifact: $File"
        return $Code
    }
    catch {
        $ErrorActionPreference = $prevEap
        $_ | Out-File $File -Encoding utf8
        Add-Line "**RESULT:** FAIL"
        Add-Line ""
        Add-Line "Artifact: $File"
        return 1
    }
}

"# CROWN Finish-Now Report" | Set-Content (Join-Path $Out "CROWN_FINISH_REPORT.md") -Encoding utf8
Add-Line ""
Add-Line "- Timestamp: $Stamp"
Add-Line "- Repo: $RepoRoot"

# =========================================================
# 1. SAFE CLEANUP OF KNOWN ACCIDENTAL PROOF SCRIPTS
# =========================================================

Add-Line ""
Add-Line "## Safe cleanup"
Add-Line ""
if ($EnableCleanup) {
    Add-Line "- Cleanup mode: ENABLED (destructive actions allowed)"
} else {
    Add-Line "- Cleanup mode: AUDIT-ONLY DRY-RUN (no files will be moved or deleted)"
}

$KnownDebris = @(
    "release_proof.ps1",
    "scripts/release_canonical_local_proof.ps1"
)

foreach ($Rel in $KnownDebris) {
    $Path = Join-Path $RepoRoot $Rel
    if (Test-Path $Path) {
        $tracked = git ls-files --error-unmatch $Rel 2>$null
        if (-not $tracked) {
            if ($EnableCleanup) {
                Remove-Item $Path -Force
                Add-Line "- Removed untracked debris: $Rel"
            } else {
                Add-Line "- Would remove untracked debris: $Rel"
            }
        } else {
            Add-Line "- Kept tracked file: $Rel"
        }
    }
}

# Quarantine untracked backend/billing files.
$UntrackedBilling = @(git ls-files --others --exclude-standard backend/billing)
if ($UntrackedBilling.Count -gt 0) {
    if ($EnableCleanup) {
        Add-Line "- Quarantining untracked backend/billing files."
    } else {
        Add-Line "- Would quarantine untracked backend/billing files."
    }

    foreach ($Rel in $UntrackedBilling) {
        $Src = Join-Path $RepoRoot $Rel
        $Dst = New-UniqueFilePath -Directory $Quarantine -Name (($Rel -replace '[\\/:*?"<>| ]','_'))
        if ($EnableCleanup) {
            Move-Item $Src $Dst -Force
            Add-Line "  - $Rel -> $Dst"
        } else {
            Add-Line "  - $Rel -> $Dst (dry-run)"
        }
    }
} else {
    Add-Line "- No untracked backend/billing files."
}

# =========================================================
# 2. REQUIRED LIVE REPO STATE
# =========================================================

Run-Capture "git branch" { git branch --show-current } | Out-Null
Run-Capture "git status short" { git status --short } | Out-Null
Run-Capture "open pull requests" { gh pr list --state open } | Out-Null
Run-Capture "open issues" { gh issue list --state open } | Out-Null
Run-Capture "backend billing diff guard" { git diff -- backend/billing } | Out-Null
Run-Capture "backend billing untracked guard" { git ls-files --others --exclude-standard backend/billing } | Out-Null

# =========================================================
# 3. GOVERNANCE FILE CHECKS
# =========================================================

Add-Line ""
Add-Line "## Governance blockers"

$Authority = "docs/release/INTEGRITY_HOLD_RELEASE_AUTHORITY_20260506.md"
$Founder = "docs/release/FOUNDER_ACCEPTANCE.md"

if (Test-Path $Authority) {
    $AuthorityText = Get-Content $Authority -Raw
    if ($AuthorityText -match "State:\s*INTEGRITY HOLD") {
        Add-Line "- FAIL: Integrity hold is still active."
    } else {
        Add-Line "- PASS: Integrity hold marker not active."
    }
} else {
    Add-Line "- FAIL: Missing $Authority"
}

if (Test-Path $Founder) {
    $FounderText = Get-Content $Founder -Raw
    if ($FounderText -match "<!--\s*PENDING_FOUNDER_SIGNATURE\s*-->") {
        Add-Line "- FAIL: Founder acceptance is unsigned."
    } elseif ($FounderText -match "(?m)^\s*SIGNED\s*$") {
        Add-Line "- PASS: Founder acceptance signed."
    } else {
        Add-Line "- FAIL: Founder acceptance has no valid signature token."
    }
} else {
    Add-Line "- FAIL: Missing $Founder"
}

# =========================================================
# 4. BACKEND CHECKS
# =========================================================

Push-Location backend

Run-Capture "django check" { python manage.py check } | Out-Null
Run-Capture "django migration dry run" { python manage.py makemigrations --check --dry-run } | Out-Null

# Module test inventory. These are expected product areas.
$Modules = @(
    "core",
    "households",
    "applications",
    "admissions",
    "billing",
    "payments",
    "parent360",
    "student_records",
    "classroom",
    "gradebook",
    "financial_aid",
    "analytics",
    "audit",
    "tenants"
)

Add-Line ""
Add-Line "## Backend module test inventory"
Add-Line ""

foreach ($Module in $Modules) {
    if (Test-Path $Module) {
        $Safe = "pytest-$Module.txt"
        $File = Join-Path $Out $Safe

        $PytestTarget = $Module
        if (Test-Path (Join-Path $Module "tests.py")) {
            # Ensure legacy module-level tests.py files are discovered.
            $PytestTarget = (Join-Path $Module "tests.py")
        }

        python -m pytest $PytestTarget -q --tb=short *>&1 | Tee-Object -FilePath $File
        $Text = Get-Content $File -Raw

        if ($Text -match "no tests ran") {
            Add-Line "- FAIL: $Module - no tests ran. Artifact: $File"
        } elseif ($LASTEXITCODE -eq 0) {
            Add-Line "- PASS: $Module tests passed. Artifact: $File"
        } else {
            Add-Line "- FAIL: $Module tests failed. Artifact: $File"
        }
    } else {
        Add-Line "- MISSING: $Module directory not found."
    }
}

Add-Line "- INFO: billing_hardened excluded from active release proof scoring (proof-only path)."

Pop-Location

# =========================================================
# 5. FRONTEND CHECKS
# =========================================================

if (Test-Path "frontend\dashboards\package.json") {
    Run-Capture "frontend build" { npm --prefix frontend/dashboards run build } | Out-Null

    $Pkg = Get-Content "frontend\dashboards\package.json" -Raw
    if ($Pkg -match '"verify:full"') {
        Run-Capture "frontend verify full" { npm --prefix frontend/dashboards run verify:full } | Out-Null
    } else {
        Add-Line ""
        Add-Line "## frontend verify full"
        Add-Line ""
        Add-Line "**RESULT:** FAIL - package.json missing verify:full script"
    }
} else {
    Add-Line ""
    Add-Line "## frontend"
    Add-Line ""
    Add-Line "**RESULT:** FAIL - frontend/dashboards/package.json missing"
}

# =========================================================
# 6. RELEASE CLOSEOUT GATE
# =========================================================

if (Test-Path "scripts\release_closeout_proof_gate.ps1") {
    Run-Capture "release closeout proof gate" {
        $GateScript = Join-Path $RepoRoot "scripts/release_closeout_proof_gate.ps1"
        $Pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
        if (-not $Pwsh) {
            throw "pwsh executable not found; cannot run release closeout proof gate out-of-process."
        }

        $GateOutput = & $Pwsh.Source -NoProfile -File $GateScript 2>&1
        if ($null -ne $GateOutput) {
            $GateOutput | ForEach-Object { $_ }
        }

        if ($LASTEXITCODE -ne 0) {
            throw "release_closeout_proof_gate.ps1 exited with code $LASTEXITCODE"
        }
    } | Out-Null
} else {
    Add-Line ""
    Add-Line "## release closeout proof gate"
    Add-Line ""
    Add-Line "**RESULT:** FAIL - scripts/release_closeout_proof_gate.ps1 missing"
}

# =========================================================
# 7. FINAL STATUS
# =========================================================

Run-Capture "final git status short" { git status --short } | Out-Null

Add-Line ""
Add-Line "# Final Required Fix List"
Add-Line ""
Add-Line "Fix every line marked FAIL above. Do not work on unrelated items."
Add-Line ""
Add-Line "Report path:"
Add-Line ""
Add-Line '```text'
Add-Line "$Out\CROWN_FINISH_REPORT.md"
Add-Line '```'

Write-Host ""
Write-Host "CROWN finish report created:"
Write-Host "$Out\CROWN_FINISH_REPORT.md"
Write-Host ""

Get-Content (Join-Path $Out "CROWN_FINISH_REPORT.md")
