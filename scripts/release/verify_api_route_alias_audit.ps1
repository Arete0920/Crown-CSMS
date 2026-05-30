param(
    [string]$AuditFile = "docs/release/API_ROUTE_ALIAS_AUDIT_20260530.md",
    [string]$UrlFile = "backend/crown_api/urls.py"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -Path $AuditFile)) {
    Write-Error "alias audit file not found: $AuditFile"
    exit 1
}

if (-not (Test-Path -Path $UrlFile)) {
    Write-Error "url file not found: $UrlFile"
    exit 1
}

$audit = Get-Content -Raw -Path $AuditFile
$urls = Get-Content -Raw -Path $UrlFile

$requiredAuditTokens = @(
    "/api/v1/*",
    "/api/*",
    "/api/v1/dashboards/*",
    "/api/dashboards/*",
    "NON_ESSENTIAL_ALIAS",
    "DEPRECATE"
)

$missingAudit = @()
foreach ($token in $requiredAuditTokens) {
    if ($audit -notmatch [regex]::Escape($token)) {
        $missingAudit += $token
    }
}

$requiredUrlTokens = @(
    'path("api/v1/", include("crown_api.api_v1_urls"))',
    'path("api/", include("crown_api.api_v1_urls"))',
    'path("api/v1/dashboards/", include("crown_api.dashboards.urls"))',
    'path("api/dashboards/", include("crown_api.dashboards.urls"))'
)

$missingUrl = @()
foreach ($token in $requiredUrlTokens) {
    if ($urls -notmatch [regex]::Escape($token)) {
        $missingUrl += $token
    }
}

Write-Output "[api-alias-audit] audit_missing=$($missingAudit.Count) url_missing=$($missingUrl.Count)"

if ($missingAudit.Count -gt 0) {
    $missingAudit | ForEach-Object { Write-Output "AUDIT_MISSING $_" }
}

if ($missingUrl.Count -gt 0) {
    $missingUrl | ForEach-Object { Write-Output "URL_MISSING $_" }
}

if ($missingAudit.Count -gt 0 -or $missingUrl.Count -gt 0) {
    Write-Error "api route alias audit check failed"
    exit 1
}

Write-Output "OK api route alias audit check passed"
exit 0
