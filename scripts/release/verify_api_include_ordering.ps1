param(
    [string]$ApiV1File = "backend/crown_api/api_v1_urls.py"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -Path $ApiV1File)) {
    Write-Error "api_v1 url file not found: $ApiV1File"
    exit 1
}

$text = Get-Content -Raw -Path $ApiV1File

function Get-IndexOrFail {
    param(
        [string]$Needle,
        [string]$Label
    )

    $index = $text.IndexOf($Needle)
    if ($index -lt 0) {
        throw "missing required include/order token: $Label"
    }

    return $index
}

$legacyCatchAll = Get-IndexOrFail -Needle 'path("", include("crown_api.api_urls"))' -Label 'legacy catch-all include'

$mustPrecede = @(
    'path("board/", include("board_oversight.urls"))',
    'path("hr/", include("hr.urls"))',
    'path("advancement/", include("advancement.urls"))',
    'path("pd/", include("pdhub.urls"))',
    'path("safety/", include("safety.urls"))',
    'path("connectors/", include("integrations_real.urls"))',
    'path("student-records/", include("student_records.urls"))',
    'path("parent360/", include("parent360.api.urls"))',
    'path("aftercare/", include("aftercare.urls"))',
    'path("summer-camp/", include("summer_camp.urls"))',
    'path("m365/", include("governance.urls"))'
)

$orderingViolations = @()
foreach ($token in $mustPrecede) {
    $idx = Get-IndexOrFail -Needle $token -Label $token
    if ($idx -gt $legacyCatchAll) {
        $orderingViolations += $token
    }
}

Write-Output "[api-include-ordering] checked=$($mustPrecede.Count) violations=$($orderingViolations.Count)"

if ($orderingViolations.Count -gt 0) {
    $orderingViolations | ForEach-Object { Write-Output "ORDER_VIOLATION $_" }
    Write-Error "api include ordering check failed"
    exit 1
}

Write-Output "OK api include ordering check passed"
exit 0
