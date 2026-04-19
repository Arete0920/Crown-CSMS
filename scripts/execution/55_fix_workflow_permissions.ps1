param(
    [switch]$OpenReports
)

$ErrorActionPreference = "Stop"

function Get-WorkflowFiles {
    $root = Join-Path (Get-Location) ".github\workflows"
    if (-not (Test-Path $root)) {
        throw ".github\workflows not found. Run from repo root."
    }
    return Get-ChildItem $root -File | Where-Object { $_.Extension -in ".yml", ".yaml" }
}

function Has-TopLevelPermissions {
    param([string[]]$Lines)
    foreach ($line in $Lines) {
        if ($line -match '^(permissions)\s*:\s*$') { return $true }
        if ($line -match '^\S' -and $line -notmatch '^(name|on|run-name|env|defaults|concurrency|jobs)\s*:') {
            break
        }
    }
    return $false
}

function Get-PermissionProfile {
    param(
        [string]$FileName,
        [string]$Content
    )

    $name = $FileName.ToLowerInvariant()
    $text = $Content.ToLowerInvariant()

    if ($name -match 'codeql|secret-scan|dependency-scan|dependency-audit|dependency-review') {
        if ($text -match 'security-events: write|upload-sarif|codeql-action') {
            return "security-events"
        }
        if ($name -match 'dependency-review') {
            return "pull-requests"
        }
        return "read-only"
    }

    if ($name -match 'deploy|prod-health|azure|release|rc-|promotion|ops-reset') {
        return "deploy"
    }

    if ($text -match 'azure/login@|id-token|federated|oidc') {
        return "deploy"
    }

    if ($text -match 'gh pr comment|pull-requests: write|github-script|checks: write') {
        return "checks-pr"
    }

    if ($text -match 'packages: write|npm publish|ghcr.io|docker/login-action') {
        return "packages"
    }

    return "read-only"
}

function Get-PermissionsBlock {
    param([string]$Profile)

    switch ($Profile) {
        "security-events" {
            @(
                "permissions:",
                "  contents: read",
                "  actions: read",
                "  security-events: write"
            )
        }
        "pull-requests" {
            @(
                "permissions:",
                "  contents: read",
                "  pull-requests: write"
            )
        }
        "checks-pr" {
            @(
                "permissions:",
                "  contents: read",
                "  checks: write",
                "  pull-requests: write"
            )
        }
        "deploy" {
            @(
                "permissions:",
                "  contents: read",
                "  id-token: write"
            )
        }
        "packages" {
            @(
                "permissions:",
                "  contents: read",
                "  packages: write"
            )
        }
        default {
            @(
                "permissions:",
                "  contents: read"
            )
        }
    }
}

function Get-InsertIndex {
    param([string[]]$Lines)

    for ($i = 0; $i -lt $Lines.Count; $i++) {
        if ($Lines[$i] -match '^name\s*:') {
            return ($i + 1)
        }
    }

    for ($i = 0; $i -lt $Lines.Count; $i++) {
        if ($Lines[$i] -match '^on\s*:') {
            return $i
        }
    }

    for ($i = 0; $i -lt $Lines.Count; $i++) {
        if ($Lines[$i] -match '^\s*$') { continue }
        if ($Lines[$i] -match '^\s*#') { continue }
        return $i
    }

    return 0
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$baseRoot = Join-Path $repoRoot "audit-artifacts\workflow-permissions-fix"
$base = Join-Path $baseRoot $ts
$latest = Join-Path $baseRoot "latest"
$backupDir = Join-Path $base "backup"
$reportCsv = Join-Path $base "workflow_permissions_report.csv"
$verifyTxt = Join-Path $base "workflow_permissions_verify.txt"
$summaryMd = Join-Path $base "SUMMARY.md"

New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

$results = @()

foreach ($file in Get-WorkflowFiles) {
    $relative = Resolve-Path -Relative $file.FullName
    $content = Get-Content $file.FullName -Raw
    $lines = [System.IO.File]::ReadAllLines($file.FullName)

    $backupPath = Join-Path $backupDir $file.Name
    Copy-Item $file.FullName $backupPath -Force

    if (Has-TopLevelPermissions -Lines $lines) {
        $results += [pscustomobject]@{
            File         = $file.Name
            RelativePath = $relative
            Action       = "Skipped"
            Profile      = "Existing"
            InsertIndex  = ""
        }
        continue
    }

    $profile = Get-PermissionProfile -FileName $file.Name -Content $content
    $permBlock = Get-PermissionsBlock -Profile $profile
    $insertAt = Get-InsertIndex -Lines $lines

    $newLines = @()
    if ($insertAt -gt 0) {
        $newLines += $lines[0..($insertAt - 1)]
    }
    $newLines += $permBlock
    $newLines += ""
    if ($insertAt -lt $lines.Count) {
        $newLines += $lines[$insertAt..($lines.Count - 1)]
    }

    [System.IO.File]::WriteAllLines($file.FullName, $newLines, [System.Text.UTF8Encoding]::new($false))

    $results += [pscustomobject]@{
        File         = $file.Name
        RelativePath = $relative
        Action       = "Patched"
        Profile      = $profile
        InsertIndex  = $insertAt
    }
}

$results | Sort-Object File | Export-Csv $reportCsv -NoTypeInformation -Encoding utf8

"=== WORKFLOW PERMISSIONS VERIFY ===" | Set-Content $verifyTxt -Encoding utf8
"" | Add-Content $verifyTxt -Encoding utf8

$remainingMissing = @()
foreach ($file in Get-WorkflowFiles) {
    $lines = [System.IO.File]::ReadAllLines($file.FullName)
    $hasPermissions = Has-TopLevelPermissions -Lines $lines
    ("{0} :: permissions={1}" -f $file.Name, $hasPermissions) | Add-Content $verifyTxt -Encoding utf8
    if (-not $hasPermissions) {
        $remainingMissing += $file.Name
    }
}

"" | Add-Content $verifyTxt -Encoding utf8
"=== QUICK GREP ===" | Add-Content $verifyTxt -Encoding utf8
foreach ($file in Get-WorkflowFiles) {
    $hit = Select-String -Path $file.FullName -Pattern '^permissions:|^  contents:|^  id-token:|^  security-events:|^  pull-requests:|^  checks:|^  packages:' -SimpleMatch:$false -ErrorAction SilentlyContinue
    if ($hit) {
        ("----- {0} -----" -f $file.Name) | Add-Content $verifyTxt -Encoding utf8
        $hit | ForEach-Object { "{0}:{1}:{2}" -f $_.Path, $_.LineNumber, $_.Line.TrimEnd() } | Add-Content $verifyTxt -Encoding utf8
    }
}

$patched = @($results | Where-Object { $_.Action -eq "Patched" }).Count
$skipped = @($results | Where-Object { $_.Action -eq "Skipped" }).Count
$remaining = $remainingMissing.Count

@"
# Workflow Permissions Fix Summary

## Output root
$base

## Results
- Patched: $patched
- Skipped (already had permissions): $skipped
- Remaining missing: $remaining

## Files
- $reportCsv
- $verifyTxt
- $backupDir

## Next steps
1. Review the CSV and verify report.
2. Run:
   git diff -- .github/workflows
3. Commit:
   git add .github/workflows audit-artifacts/workflow-permissions-fix/$ts
   git commit -m "security: add explicit GitHub Actions permissions blocks"
4. Push and let GitHub code scanning rescan.
"@ | Set-Content $summaryMd -Encoding utf8

if (Test-Path $latest) {
    Remove-Item $latest -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $latest | Out-Null
Copy-Item (Join-Path $base "*") $latest -Recurse -Force

Write-Host "Done: $base"
Write-Host "Patched: $patched"
Write-Host "Skipped: $skipped"
Write-Host "Remaining missing: $remaining"

if ($OpenReports) {
    code $summaryMd
    code $reportCsv
    code $verifyTxt
}
