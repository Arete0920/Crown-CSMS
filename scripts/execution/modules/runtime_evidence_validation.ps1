function Read-CrownRuntimeEvidence {
    param([string]$Gate, [string[]]$Keys, [string[]]$Criteria, [string]$OutputDir)
    if ($PSVersionTable.PSVersion.Major -ge 7) { $PSNativeCommandUseErrorActionPreference = $false }
    $manifest = $env:CROWN_RELEASE_RUNTIME_EVIDENCE
    $environment = $env:CROWN_RELEASE_EVIDENCE_ENVIRONMENT
    if ([string]::IsNullOrWhiteSpace($manifest) -or [string]::IsNullOrWhiteSpace($environment)) {
        return [pscustomobject]@{ pass = $false; errors = @("Runtime evidence manifest and explicit environment are required."); records = @() }
    }
    $output = Join-Path $OutputDir "05_runtime_validation.json"
    $validator = Join-Path $repoRoot "tools/validate_release_runtime_evidence.py"
    $head = (git rev-parse HEAD).Trim()
    & python $validator --manifest $manifest --sha $head --environment $environment --gate $Gate --keys ($Keys -join ',') --criteria ($Criteria -join ',') --output $output
    $validatorExit = $LASTEXITCODE
    if ($null -eq $validatorExit -or -not (Test-Path $output)) {
        return [pscustomobject]@{ pass = $false; errors = @("Runtime validator did not produce verifiable evidence."); records = @() }
    }
    try {
        $result = Get-Content $output -Raw | ConvertFrom-Json
        if ($validatorExit -ne 0 -or $result.pass -isnot [bool] -or $result.pass -ne $true -or $result.source_sha -ne $head -or $result.environment -ne $environment -or $result.gate -ne $Gate) {
            $result.pass = $false
        }
        return $result
    } catch {
        return [pscustomobject]@{ pass = $false; errors = @("Runtime validator result is invalid."); records = @() }
    }
}
