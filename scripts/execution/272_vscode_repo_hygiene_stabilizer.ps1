$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$Repo = "C:\w\crown_main_postmerge_verify"
if (!(Test-Path $Repo)) {
    throw "Repo path not found: $Repo"
}

Set-Location $Repo

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Out = "audit-artifacts\vscode-hygiene\$Stamp"
New-Item -ItemType Directory -Force -Path $Out | Out-Null

function Capture-NoThrow {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Block
    )

    $Path = Join-Path $Out $Name
    "=== $Name ===" | Out-File $Path -Encoding UTF8
    "STAMP=$Stamp" | Add-Content $Path -Encoding UTF8
    "REPO=$Repo" | Add-Content $Path -Encoding UTF8
    "" | Add-Content $Path -Encoding UTF8

    try {
        $result = (& $Block 2>&1 | Out-String)
        $result | Add-Content $Path -Encoding UTF8
    }
    catch {
        "ERROR:" | Add-Content $Path -Encoding UTF8
        $_ | Out-String | Add-Content $Path -Encoding UTF8
    }
}

function Convert-ToPlainHashtable {
    param($InputObject)

    if ($null -eq $InputObject) {
        return $null
    }

    if ($InputObject -is [System.Collections.IDictionary]) {
        $hash = @{}
        foreach ($key in $InputObject.Keys) {
            $hash[$key] = Convert-ToPlainHashtable $InputObject[$key]
        }
        return $hash
    }

    if (($InputObject -is [System.Collections.IEnumerable]) -and -not ($InputObject -is [string])) {
        $arr = @()
        foreach ($item in $InputObject) {
            $arr += Convert-ToPlainHashtable $item
        }
        return $arr
    }

    if ($InputObject.PSObject -and $InputObject.PSObject.Properties -and $InputObject.GetType().Name -eq "PSCustomObject") {
        $hash = @{}
        foreach ($prop in $InputObject.PSObject.Properties) {
            $hash[$prop.Name] = Convert-ToPlainHashtable $prop.Value
        }
        return $hash
    }

    return $InputObject
}

function Ensure-HashtableSetting {
    param(
        [hashtable]$Settings,
        [string]$Key
    )

    if (!$Settings.ContainsKey($Key) -or $null -eq $Settings[$Key] -or !($Settings[$Key] -is [hashtable])) {
        $Settings[$Key] = @{}
    }

    return $Settings[$Key]
}

function Get-FirstExistingPath {
    param(
        [Parameter(Mandatory = $true)][string[]]$Candidates
    )

    foreach ($candidate in $Candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

Write-Host ""
Write-Host "=== CROWN VS CODE + REPO HYGIENE START ==="
Write-Host "Repo: $Repo"
Write-Host "Out : $Out"
Write-Host ""

Capture-NoThrow "00_repo_identity.txt" {
    "PWD:"
    Get-Location
    ""
    "Git root:"
    git rev-parse --show-toplevel
    ""
    "Branch:"
    git branch --show-current
    ""
    "HEAD:"
    git rev-parse HEAD
    ""
    "Remotes:"
    git remote -v
}

Capture-NoThrow "01_git_status_full.txt" {
    git status
}

Capture-NoThrow "02_git_status_porcelain.txt" {
    git status --porcelain=v1
}

Capture-NoThrow "03_git_diff_stat.txt" {
    git diff --stat
    ""
    "=== STAGED DIFF STAT ==="
    git diff --cached --stat
}

Capture-NoThrow "04_git_untracked_files.txt" {
    git ls-files --others --exclude-standard
}

Capture-NoThrow "05_recent_changed_files.txt" {
    git status --porcelain=v1 | ForEach-Object { $_ }
}

New-Item -ItemType Directory -Force -Path ".vscode" | Out-Null
$SettingsPath = ".vscode\settings.json"
$SettingsBackup = Join-Path $Out "settings.json.before"
if (Test-Path $SettingsPath) {
    Copy-Item $SettingsPath $SettingsBackup -Force
}
else {
    "{}" | Out-File $SettingsPath -Encoding UTF8
}

$SettingsRaw = Get-Content $SettingsPath -Raw -Encoding UTF8
try {
    $SettingsObject = $SettingsRaw | ConvertFrom-Json
    $Settings = Convert-ToPlainHashtable $SettingsObject
    if ($null -eq $Settings) {
        $Settings = @{}
    }
}
catch {
    $BadSettingsCopy = Join-Path $Out "settings.json.invalid.before"
    Copy-Item $SettingsPath $BadSettingsCopy -Force
    $Settings = @{}
}

$Settings["markdownlint.ignore"] = @(
    "**/audit-artifacts/**",
    "**/.git/**",
    "**/node_modules/**",
    "**/frontend/node_modules/**",
    "**/frontend/dist/**",
    "**/frontend/build/**",
    "**/backend/staticfiles/**",
    "**/coverage/**",
    "**/.venv/**",
    "**/venv/**",
    "**/docs/crown-master-binder/**"
)

$Settings["markdownlint.lintWorkspaceGlobs"] = @(
    ".github/**/*.md",
    "docs/**/*.md",
    "!docs/crown-master-binder/**",
    "!audit-artifacts/**"
)

$Settings["markdownlint.run"] = "onSave"
$Settings["markdownlint.configFile"] = ".markdownlint.json"

$SearchExclude = Ensure-HashtableSetting $Settings "search.exclude"
$SearchExclude["**/audit-artifacts/**"] = $true
$SearchExclude["**/node_modules/**"] = $true
$SearchExclude["**/frontend/dist/**"] = $true
$SearchExclude["**/frontend/build/**"] = $true
$SearchExclude["**/coverage/**"] = $true
$SearchExclude["**/.venv/**"] = $true
$SearchExclude["**/venv/**"] = $true

$WatcherExclude = Ensure-HashtableSetting $Settings "files.watcherExclude"
$WatcherExclude["**/audit-artifacts/**"] = $true
$WatcherExclude["**/node_modules/**"] = $true
$WatcherExclude["**/frontend/dist/**"] = $true
$WatcherExclude["**/frontend/build/**"] = $true
$WatcherExclude["**/coverage/**"] = $true
$WatcherExclude["**/.venv/**"] = $true
$WatcherExclude["**/venv/**"] = $true

$Settings["problems.sortOrder"] = "severity"
$Settings["git.autorefresh"] = $true
$Settings["git.confirmSync"] = $true

$Settings | ConvertTo-Json -Depth 20 | Out-File $SettingsPath -Encoding UTF8

$MarkdownLintIgnore = ".markdownlintignore"
$IgnoreLines = @(
    "audit-artifacts/**",
    "**/audit-artifacts/**",
    "audit-artifacts/ui-cleanup-captures/**",
    "node_modules/**",
    "**/node_modules/**",
    "frontend/dist/**",
    "frontend/build/**",
    "coverage/**",
    ".venv/**",
    "venv/**",
    "backend/staticfiles/**",
    "docs/crown-master-binder/**",
    "docs/crown-master-binder/operations/**",
    "docs/crown-master-binder/inventory/**",
    "docs/crown-master-binder/runbooks/**",
    "docs/crown-master-binder/security/**"
)

if (Test-Path $MarkdownLintIgnore) {
    Copy-Item $MarkdownLintIgnore (Join-Path $Out "markdownlintignore.before") -Force
    $ExistingIgnore = Get-Content $MarkdownLintIgnore -ErrorAction SilentlyContinue
}
else {
    $ExistingIgnore = @()
}

$MergedIgnore = @($ExistingIgnore + $IgnoreLines) |
    Where-Object { $_ -and $_.Trim().Length -gt 0 } |
    Sort-Object -Unique
$MergedIgnore | Out-File $MarkdownLintIgnore -Encoding UTF8

Capture-NoThrow "06_vscode_settings_after.txt" {
    "=== .vscode/settings.json ==="
    Get-Content ".vscode\settings.json"
    ""
    "=== .markdownlintignore ==="
    Get-Content ".markdownlintignore"
}

Capture-NoThrow "07_vscode_extensions.txt" {
    if (Get-Command code -ErrorAction SilentlyContinue) {
        code --list-extensions --show-versions
    }
    else {
        "VS Code CLI 'code' not available in PATH."
    }
}

Capture-NoThrow "08_markdownlint_after_ignore.txt" {
    if (Get-Command markdownlint-cli2 -ErrorAction SilentlyContinue) {
        markdownlint-cli2 "**/*.md"
    }
    else {
        "markdownlint-cli2 not installed in PATH. VS Code and .markdownlintignore settings were still updated."
    }
}

Capture-NoThrow "09_control_room_pack_rerun.txt" {
    if (Test-Path "scripts\execution\271_execution_control_room_pack.ps1") {
        powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\execution\271_execution_control_room_pack.ps1"
    }
    else {
        "Missing scripts\execution\271_execution_control_room_pack.ps1"
    }
}

Capture-NoThrow "10_runtime_proof_helper_tenant.txt" {
    if (Test-Path "scripts\execution\250_capture_runtime_proof.ps1") {
        powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\execution\250_capture_runtime_proof.ps1" -Lane Tenant
    }
    else {
        "Missing scripts\execution\250_capture_runtime_proof.ps1"
    }
}

Capture-NoThrow "11_ui_cleanup_helper.txt" {
    if (Test-Path "scripts\execution\260_capture_ui_cleanup.ps1") {
        powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\execution\260_capture_ui_cleanup.ps1"
    }
    else {
        "Missing scripts\execution\260_capture_ui_cleanup.ps1"
    }
}

Capture-NoThrow "12_post_azure_live_proof.txt" {
    if (Test-Path "scripts\execution\270_post_azure_live_proof.ps1") {
        powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\execution\270_post_azure_live_proof.ps1"
    }
    else {
        "Missing scripts\execution\270_post_azure_live_proof.ps1"
    }
}

Capture-NoThrow "13_backend_django_check.txt" {
    if (Test-Path "backend\manage.py") {
        python "backend\manage.py" check
        ""
        "=== DEPLOY CHECK ==="
        python "backend\manage.py" check --deploy
    }
    else {
        "No backend\manage.py found."
    }
}

Capture-NoThrow "14_frontend_package_checks.txt" {
    $FrontendPackage = Get-FirstExistingPath @(
        "frontend\package.json",
        "frontend\dashboards\package.json",
        "package.json"
    )

    if ($FrontendPackage) {
        $FrontendDir = Split-Path $FrontendPackage -Parent
        "Using frontend package: $FrontendPackage"
        Push-Location $FrontendDir
        try {
            "=== npm run lint --if-present ==="
            npm run lint --if-present
            ""
            "=== npm run build --if-present ==="
            npm run build --if-present
        }
        finally {
            Pop-Location
        }
    }
    else {
        "No frontend package.json found in expected locations."
    }
}

Capture-NoThrow "15_git_status_after.txt" {
    git status
}

Capture-NoThrow "16_git_status_porcelain_after.txt" {
    git status --porcelain=v1
}

Capture-NoThrow "17_change_focus_report.txt" {
    $rows = git status --porcelain=v1
    $interesting = @()
    foreach ($row in $rows) {
        if (-not $row -or $row.Trim().Length -eq 0) {
            continue
        }

        $path = $row.Substring(3)
        $bucket = if ($path -like ".vscode/*" -or
                         $path -eq ".markdownlintignore" -or
                         $path -like "audit-artifacts/execution-control-room/*" -or
                         $path -like "audit-artifacts/vscode-hygiene/*" -or
                         $path -like "audit-artifacts/post-azure-live-proof/*" -or
                         $path -like "docs/crown-master-binder/operations/CURRENT_*" -or
                         $path -like "docs/crown-master-binder/runbooks/CURRENT_*" -or
                         $path -like "scripts/execution/25*" -or
                         $path -like "scripts/execution/26*" -or
                         $path -like "scripts/execution/27*") {
            "HYGIENE_OR_CONTROL_ROOM"
        }
        elseif ($path -like "audit-artifacts/*" -or $path -like "docs/crown-master-binder/*") {
            "GENERATED_OR_BINDER"
        }
        else {
            "APP_OR_PIPELINE_CODE"
        }

        $interesting += [pscustomobject]@{
            Bucket = $bucket
            Status = $row.Substring(0, 2)
            Path = $path
        }
    }

    "=== COUNTS ==="
    ($interesting | Group-Object Bucket | Sort-Object Name | Format-Table Name, Count -AutoSize | Out-String).TrimEnd()
    ""
    "=== HYGIENE_OR_CONTROL_ROOM ==="
    ($interesting | Where-Object { $_.Bucket -eq "HYGIENE_OR_CONTROL_ROOM" } | Format-Table Status, Path -AutoSize | Out-String).TrimEnd()
    ""
    "=== GENERATED_OR_BINDER ==="
    ($interesting | Where-Object { $_.Bucket -eq "GENERATED_OR_BINDER" } | Format-Table Status, Path -AutoSize | Out-String).TrimEnd()
    ""
    "=== APP_OR_PIPELINE_CODE ==="
    ($interesting | Where-Object { $_.Bucket -eq "APP_OR_PIPELINE_CODE" } | Format-Table Status, Path -AutoSize | Out-String).TrimEnd()
}

$ChangeLines = @()
if (Test-Path (Join-Path $Out "16_git_status_porcelain_after.txt")) {
    $ChangeLines = Get-Content (Join-Path $Out "16_git_status_porcelain_after.txt") |
        Where-Object {
            $_ -and
            $_.Trim().Length -gt 0 -and
            $_ -notmatch "^===" -and
            $_ -notmatch "^STAMP=" -and
            $_ -notmatch "^REPO="
        }
}

$ChangeCount = @($ChangeLines).Count
$LatestExecutionControlRoom = Get-ChildItem "audit-artifacts\execution-control-room" -Directory -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
$LatestPostAzure = Get-ChildItem "audit-artifacts\post-azure-live-proof" -Directory -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

$SummaryPath = Join-Path $Out "00_SUMMARY.md"
@"
# CROWN VS Code and Repo Hygiene Summary

Generated: $Stamp
Repo: $Repo

## Immediate result

- VS Code workspace hygiene settings updated.
- Generated and audit markdown folders excluded from markdownlint noise.
- Repo state captured before and after.
- Control-room and helper scripts rerun if present.
- Backend and frontend quick checks attempted if present.
- No files were deleted.
- No changes were discarded.
- No commit was created.
- No push was performed.

## Current source-control change count

$ChangeCount changed or untracked rows reported by git status porcelain after this run.

If this is still high, it is source-control state, not merely unsaved editor buffers.

## Latest generated folders

- Latest execution control room: $($LatestExecutionControlRoom.FullName)
- Latest post-Azure proof: $($LatestPostAzure.FullName)

## Read these next

1. 15_git_status_after.txt
2. 16_git_status_porcelain_after.txt
3. 17_change_focus_report.txt
4. 12_post_azure_live_proof.txt
5. 13_backend_django_check.txt
6. 14_frontend_package_checks.txt
7. 08_markdownlint_after_ignore.txt

## Decision rule

- If git status contains only intended scripts, binder pointers, settings, and proof artifacts: commit them.
- If git status contains app-code changes you did not expect: inspect before committing.
- If live proof still shows frontend 404 or SHA mismatch: production remains NO-GO.
"@ | Out-File $SummaryPath -Encoding UTF8

Write-Host ""
Write-Host "=== CROWN VS CODE + REPO HYGIENE COMPLETE ==="
Write-Host "Summary: $SummaryPath"
Write-Host ""

if (Get-Command code -ErrorAction SilentlyContinue) {
    code $Out
    code $SummaryPath
}
else {
    Write-Host "Open manually: $SummaryPath"
}
