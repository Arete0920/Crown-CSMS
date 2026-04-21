param(
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

function Write-Section {
    param([string]$Path, [string]$Title)
    "=== $Title ===" | Set-Content -Path $Path -Encoding utf8
}

function Add-Output {
    param([string]$Path, [scriptblock]$Command)
    try {
        & $Command 2>&1 | Out-File -FilePath $Path -Append -Encoding utf8
    }
    catch {
        ($_ | Out-String) | Out-File -FilePath $Path -Append -Encoding utf8
    }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$out = Join-Path $repoRoot ("audit-artifacts\deploy-check-triage\" + $ts)
New-Item -ItemType Directory -Force -Path $out | Out-Null

$latestRuntime = Get-ChildItem ".\audit-artifacts\runtime-release-closure" -Directory -ErrorAction SilentlyContinue |
Sort-Object Name -Descending |
Where-Object { $_.Name -ne "latest" } |
Select-Object -First 1

Write-Section (Join-Path $out "01_latest_runtime_pointer.txt") "Latest runtime closure"
if ($latestRuntime) {
    $latestRuntime.FullName | Add-Content (Join-Path $out "01_latest_runtime_pointer.txt")
}
else {
    "No runtime-release-closure folder found." | Add-Content (Join-Path $out "01_latest_runtime_pointer.txt")
}

Write-Section (Join-Path $out "02_deploy_check_source.txt") "Deploy check source"
if ($latestRuntime -and (Test-Path (Join-Path $latestRuntime.FullName "05_deploy_check.txt"))) {
    Get-Content (Join-Path $latestRuntime.FullName "05_deploy_check.txt") | Add-Content (Join-Path $out "02_deploy_check_source.txt")
}
else {
    "05_deploy_check.txt not found." | Add-Content (Join-Path $out "02_deploy_check_source.txt")
}

Write-Section (Join-Path $out "03_manage_deploy_check_rerun.txt") "Deploy check rerun"
Add-Output (Join-Path $out "03_manage_deploy_check_rerun.txt") { python backend\manage.py check --deploy }

$settingsFiles = Get-ChildItem -Recurse -File "backend" -ErrorAction SilentlyContinue |
Where-Object {
    $_.Name -match "settings" -or
    $_.FullName -match "\\settings\\" -or
    $_.FullName -match "config"
}

$securityPatterns = @(
    "SECURE_SSL_REDIRECT",
    "SESSION_COOKIE_SECURE",
    "CSRF_COOKIE_SECURE",
    "SECURE_HSTS_SECONDS",
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    "SECURE_HSTS_PRELOAD",
    "SECURE_PROXY_SSL_HEADER",
    "SECURE_CONTENT_TYPE_NOSNIFF",
    "X_FRAME_OPTIONS",
    "SECURE_REFERRER_POLICY",
    "ALLOWED_HOSTS",
    "DEBUG",
    "SECRET_KEY"
)

Write-Section (Join-Path $out "04_security_settings_hits.txt") "Security settings hits"
foreach ($pattern in $securityPatterns) {
    Add-Content (Join-Path $out "04_security_settings_hits.txt") ("===== " + $pattern + " =====")
    try {
        Select-String -Path $settingsFiles.FullName -Pattern $pattern -SimpleMatch -ErrorAction SilentlyContinue |
        ForEach-Object { "{0}:{1}:{2}" -f $_.Path, $_.LineNumber, $_.Line.Trim() } |
        Add-Content (Join-Path $out "04_security_settings_hits.txt")
    }
    catch {
        "ERROR" | Add-Content (Join-Path $out "04_security_settings_hits.txt")
    }
    Add-Content (Join-Path $out "04_security_settings_hits.txt") ""
}

Write-Section (Join-Path $out "05_env_and_secret_hits.txt") "Env and secret hits"
$allFiles = Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object FullName
foreach ($pattern in @("os.environ", "getenv(", "dotenv", "SECRET_KEY", "ALLOWED_HOSTS", "SECURE_PROXY_SSL_HEADER")) {
    Add-Content (Join-Path $out "05_env_and_secret_hits.txt") ("===== " + $pattern + " =====")
    try {
        Select-String -Path $allFiles -Pattern $pattern -SimpleMatch -ErrorAction SilentlyContinue |
        ForEach-Object { "{0}:{1}:{2}" -f $_.Path, $_.LineNumber, $_.Line.Trim() } |
        Add-Content (Join-Path $out "05_env_and_secret_hits.txt")
    }
    catch {
        "ERROR" | Add-Content (Join-Path $out "05_env_and_secret_hits.txt")
    }
    Add-Content (Join-Path $out "05_env_and_secret_hits.txt") ""
}

Write-Section (Join-Path $out "06_common_deploy_fixes_checklist.md") "Common deploy fixes"
@"
# Common Django Deploy-Check Fixes

- [ ] DEBUG = False in production path
- [ ] ALLOWED_HOSTS is populated from env/config
- [ ] SECRET_KEY is loaded from env/config
- [ ] SECURE_SSL_REDIRECT set appropriately for production
- [ ] SESSION_COOKIE_SECURE = True for production
- [ ] CSRF_COOKIE_SECURE = True for production
- [ ] SECURE_HSTS_SECONDS set appropriately for production
- [ ] SECURE_HSTS_INCLUDE_SUBDOMAINS set appropriately
- [ ] SECURE_HSTS_PRELOAD set appropriately
- [ ] SECURE_CONTENT_TYPE_NOSNIFF = True
- [ ] X_FRAME_OPTIONS reviewed and set
- [ ] SECURE_REFERRER_POLICY reviewed and set
- [ ] SECURE_PROXY_SSL_HEADER set when behind proxy
"@ | Add-Content (Join-Path $out "06_common_deploy_fixes_checklist.md")

Write-Section (Join-Path $out "07_open_files.ps1") "Open files"
@"
code `"$out\02_deploy_check_source.txt`"
code `"$out\03_manage_deploy_check_rerun.txt`"
code `"$out\04_security_settings_hits.txt`"
code `"$out\05_env_and_secret_hits.txt`"
code `"$out\06_common_deploy_fixes_checklist.md`"
"@ | Add-Content (Join-Path $out "07_open_files.ps1")

Write-Section (Join-Path $out "SUMMARY.md") "Deploy check triage summary"
@"
# Deploy Check Triage

## Output root
$out

## Review first
- 02_deploy_check_source.txt
- 03_manage_deploy_check_rerun.txt
- 04_security_settings_hits.txt
- 05_env_and_secret_hits.txt
- 06_common_deploy_fixes_checklist.md

## Required exit condition
- python backend\manage.py check --deploy passes cleanly
- rerun scripts\execution\31_runtime_release_closure.ps1 -StartLocalServer
- 05_deploy_check.txt is clean in the newest runtime-release-closure folder
"@ | Add-Content (Join-Path $out "SUMMARY.md")

Write-Host "Done: $out"
