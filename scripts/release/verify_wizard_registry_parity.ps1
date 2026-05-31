Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$backendPath = "backend/crown_api/wizard_registry.py"
$frontendPath = "frontend/dashboards/src/routes/wizard-manifest.js"

$backendText = Get-Content -Raw -Path $backendPath
$frontendText = Get-Content -Raw -Path $frontendPath

$backendMatches = [regex]::Matches($backendText, '"url_prefix"\s*:\s*"api/v1/([^/]+)/(sessions|imports)/"')
$frontendSlugMatches = [regex]::Matches($frontendText, 'slug:\s*"([^"]+)"')
$frontendPlaceholderMatches = [regex]::Matches($frontendText, 'slug:\s*"([^"]+)"[^\r\n]*path:\s*"/wizards"')

$backendSlugs = @($backendMatches | ForEach-Object { $_.Groups[1].Value })
$frontendSlugs = @($frontendSlugMatches | ForEach-Object { $_.Groups[1].Value })
$placeholderSlugs = @($frontendPlaceholderMatches | ForEach-Object { $_.Groups[1].Value })

$backendSet = New-Object System.Collections.Generic.HashSet[string]
$frontendSet = New-Object System.Collections.Generic.HashSet[string]
$backendSlugs | ForEach-Object { [void]$backendSet.Add($_) }
$frontendSlugs | ForEach-Object { [void]$frontendSet.Add($_) }

$missingFrontend = @()
foreach ($slug in $backendSet) {
    if (-not $frontendSet.Contains($slug)) { $missingFrontend += $slug }
}

$missingBackend = @()
foreach ($slug in $frontendSet) {
    if (-not $backendSet.Contains($slug)) { $missingBackend += $slug }
}

Write-Output "[wizard-parity] backend_slugs=$($backendSet.Count) frontend_slugs=$($frontendSet.Count) placeholders=$($placeholderSlugs.Count)"
if ($missingFrontend.Count -gt 0) {
    Write-Output "MISSING_FRONTEND $($missingFrontend -join ', ')"
}
if ($missingBackend.Count -gt 0) {
    Write-Output "MISSING_BACKEND $($missingBackend -join ', ')"
}
if ($placeholderSlugs.Count -gt 0) {
    Write-Output "PLACEHOLDER_PATH /wizards for slugs: $($placeholderSlugs -join ', ')"
}

if ($missingFrontend.Count -gt 0 -or $missingBackend.Count -gt 0 -or $placeholderSlugs.Count -gt 0) {
    Write-Error "wizard parity check failed"
    exit 1
}

Write-Output "OK wizard parity check passed"
exit 0
