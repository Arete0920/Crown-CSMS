param(
    [string]$SettingsFile = "backend/crown_api/settings.py"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -Path $SettingsFile)) {
    Write-Error "settings file not found: $SettingsFile"
    exit 1
}

$text = Get-Content -Raw -Path $SettingsFile

$expectedOrder = @(
    "core.middleware.DemoWriteBlockMiddleware",
    "crown_api.middleware.api_exceptions.ApiExceptionMiddleware",
    "crown_api.middleware.performance.PerformanceMiddleware",
    "crown_api.middleware.api_version.APIVersionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware"
)

$indices = @{}
$missing = @()
foreach ($mw in $expectedOrder) {
    $needle = "'$mw'"
    $idx = $text.IndexOf($needle)
    if ($idx -lt 0) {
        $missing += $mw
    } else {
        $indices[$mw] = $idx
    }
}

$orderingViolations = @()
for ($i = 0; $i -lt ($expectedOrder.Count - 1); $i++) {
    $curr = $expectedOrder[$i]
    $next = $expectedOrder[$i + 1]
    if ($indices.ContainsKey($curr) -and $indices.ContainsKey($next)) {
        if ($indices[$curr] -gt $indices[$next]) {
            $orderingViolations += "$curr must appear before $next"
        }
    }
}

Write-Output "[security-middleware-order] missing=$($missing.Count) ordering_violations=$($orderingViolations.Count)"

if ($missing.Count -gt 0) {
    $missing | ForEach-Object { Write-Output "MISSING $_" }
}

if ($orderingViolations.Count -gt 0) {
    $orderingViolations | ForEach-Object { Write-Output "ORDER_VIOLATION $_" }
}

if ($missing.Count -gt 0 -or $orderingViolations.Count -gt 0) {
    Write-Error "security middleware order check failed"
    exit 1
}

Write-Output "OK security middleware order check passed"
exit 0
