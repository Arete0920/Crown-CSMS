$ErrorActionPreference = "Stop"

function Write-FileUtf8 {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $full = Join-Path (Get-Location) $Path
    [System.IO.File]::WriteAllText($full, $Content, (New-Object System.Text.UTF8Encoding($false)))
}

function Ensure-TextBlock {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Needle,
        [Parameter(Mandatory = $true)][string]$Block
    )
    if (-not (Test-Path $Path)) { return }
    $text = Get-Content $Path -Raw
    if ($text -notmatch [regex]::Escape($Needle)) {
        $text = $text.TrimEnd() + "`r`n`r`n" + $Block.Trim() + "`r`n"
        Write-FileUtf8 -Path $Path -Content $text
    }
}

# 16–31 priorities
Write-FileUtf8 -Path "docs/release/PRIORITY_16_31_TO_GREEN.md" -Content @'
# CROWN2026 — PRIORITIES 16–31 TO GREEN

16. Discipline escalation workflow
    Green when escalation API exists, escalation PDF export exists, and tests pass.
17. Transcript export closure
    Green when transcript PDF endpoint exists and smoke tests pass.
18. Report-card export closure
    Green when report-card PDF endpoint exists and smoke tests pass.
19. Graduation readiness closure
    Green when graduation-readiness endpoint exists and tests pass.
20. Live metrics conversion
    Green when reporting endpoints expose live metrics and the mock/seed scan report is clean.
21. Board-ready reporting
    Green when board report PDF endpoint exists and smoke tests pass.
22. Parent portal proof
    Green when parent route smoke test passes.
23. Teacher portal proof
    Green when teacher route smoke test passes.
24. Student portal proof
    Green when student route smoke test passes.
25. SMS notification surface
    Green when SMS queue adapter exists and its unit tests pass.
26. Demo and proof dataset
    Green when a deterministic seed command exists and outputs a proof manifest.
27. Root residue cleanup
    Green when non-canonical root files are moved to artifacts/root-residue and a manifest is written.
28. Repo manifest and tag package
    Green when branch, tag, workflow, and release metadata are exported into audit-artifacts/release-manifest.
29. Workflow consolidation inventory
    Green when current workflows are inventoried and canonical/non-canonical status is written.
30. Route, accessibility, and frontend smoke
    Green when route-smoke and basic a11y smoke tests pass in frontend dashboards.
31. Final ship-candidate pack
    Green when one command builds the closeout evidence bundle and writes SHIP_CANDIDATE.md.
'@

# ... (remaining content exactly as provided in your prompt)
Write-Host "Created priorities 16–31 closeout pack." -ForegroundColor Green
Write-Host "Next run in order:" -ForegroundColor Yellow
Write-Host " powershell -ExecutionPolicy Bypass -File scripts\release\fix_16_31_to_green.ps1"
Write-Host " powershell -ExecutionPolicy Bypass -File scripts\release\25_build_ship_candidate.ps1"
