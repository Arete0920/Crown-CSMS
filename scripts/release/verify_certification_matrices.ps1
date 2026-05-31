param(
    [string]$ModuleMatrix = "docs/release/MODULE_CERTIFICATION_MATRIX_20260530.md",
    [string]$DashboardMatrix = "docs/release/DASHBOARD_CERTIFICATION_MATRIX_20260530.md",
    [string]$WizardMatrix = "docs/release/WIZARD_CERTIFICATION_MATRIX_20260530.md",
    [string]$PersonaMatrix = "docs/release/PERSONA_JOURNEY_CERTIFICATION_MATRIX_20260530.md",
    [string]$NotProvenRegister = "docs/release/NOT_PROVEN_REGISTER_20260530.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$requiredFiles = @($ModuleMatrix, $DashboardMatrix, $WizardMatrix, $PersonaMatrix, $NotProvenRegister)
$missingFiles = @()
foreach ($file in $requiredFiles) {
    if (-not (Test-Path -Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    $missingFiles | ForEach-Object { Write-Output "MATRIX_FILE_MISSING $_" }
    Write-Error "certification matrix check failed"
    exit 1
}

$moduleRows = ([regex]::Matches((Get-Content -Raw $ModuleMatrix), "\|\s*\d{3}\s*\|")).Count
$dashboardRows = ([regex]::Matches((Get-Content -Raw $DashboardMatrix), "\|\s*[a-z0-9-]+\s*\|\s*(MAPPED|PROVEN|PARTIAL|FLOW_CONTRACT_VALIDATED|NOT_PROVEN)")).Count
$wizardRows = ([regex]::Matches((Get-Content -Raw $WizardMatrix), "\|\s*[a-z0-9-]+\s*\|\s*(MAPPED|PROVEN|PARTIAL|FLOW_CONTRACT_VALIDATED|NOT_PROVEN)")).Count
$personaRows = ([regex]::Matches((Get-Content -Raw $PersonaMatrix), "\|\s*[a-z_]+\s*\|")).Count
$notProvenRows = ([regex]::Matches((Get-Content -Raw $NotProvenRegister), "\|\s*NP-\d{3}\s*\|")).Count

Write-Output "[certification-matrices] module_rows=$moduleRows dashboard_rows=$dashboardRows wizard_rows=$wizardRows persona_rows=$personaRows not_proven_rows=$notProvenRows"

if ($moduleRows -lt 51) { Write-Error "module matrix must contain at least 51 module rows"; exit 1 }
if ($dashboardRows -lt 30) { Write-Error "dashboard matrix must contain at least 30 rows"; exit 1 }
if ($wizardRows -lt 20) { Write-Error "wizard matrix must contain at least 20 rows"; exit 1 }
if ($personaRows -lt 6) { Write-Error "persona matrix must contain at least 6 rows"; exit 1 }
if ($notProvenRows -lt 4) { Write-Error "not-proven register must contain at least 4 rows"; exit 1 }

Write-Output "OK certification matrix check passed"
exit 0
