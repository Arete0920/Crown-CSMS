param(
    [string]$ResourceGroup = "crown-rg",
    [string]$WebAppName = "crown-api-prod",
    [string]$AcrName = "crownregistry",
    [string]$HealthUrl = "",
    [string]$IntegrityUrl = "",
    [string]$ExpectedSha = "",
    [switch]$SkipAzureCli
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = (git rev-parse --show-toplevel 2>$null).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Not inside a git repository."
}
Set-Location $repoRoot

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$base = Join-Path $repoRoot "audit-artifacts/azure-p0-current-parity-$stamp"
New-Item -ItemType Directory -Force -Path $base | Out-Null

if ([string]::IsNullOrWhiteSpace($HealthUrl)) {
    $HealthUrl = "https://$WebAppName.azurewebsites.net/api/health/"
}
if ([string]::IsNullOrWhiteSpace($IntegrityUrl)) {
    $IntegrityUrl = "https://$WebAppName.azurewebsites.net/api/integrity/"
}
if ([string]::IsNullOrWhiteSpace($ExpectedSha)) {
    $ExpectedSha = (git rev-parse HEAD).Trim()
}

function Save-Json {
    param([object]$Object, [string]$Path)
    $Object | ConvertTo-Json -Depth 20 | Set-Content -Path $Path -Encoding UTF8
}

function Assert-Present {
    param([string]$Name, [object]$Value)
    if ($null -eq $Value -or [string]::IsNullOrWhiteSpace("$Value")) {
        throw "Missing required value: $Name"
    }
}

function Get-ObjectPropertyValue {
    param(
        [object]$Object,
        [string]$Name,
        [object]$Default = $null
    )

    if ($null -eq $Object) {
        return $Default
    }

    $prop = $Object.PSObject.Properties[$Name]
    if ($null -eq $prop) {
        return $Default
    }

    return $prop.Value
}

$summary = [ordered]@{
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    repo_root = $repoRoot
    expected_sha = $ExpectedSha
    resource_group = $ResourceGroup
    web_app_name = $WebAppName
    acr_name = $AcrName
    health_url = $HealthUrl
    integrity_url = $IntegrityUrl
    checks = @()
    verdict = "FAIL"
}

function Add-Check {
    param([string]$Name, [bool]$Pass, [string]$Detail)
    $summary.checks += [ordered]@{
        name = $Name
        pass = $Pass
        detail = $Detail
    }
    if (-not $Pass) {
        Write-Host "FAIL: $Name - $Detail"
    } else {
        Write-Host "PASS: $Name - $Detail"
    }
}

try {
    $repoPath = Join-Path $base "01_repo_truth.txt"
    "=== REPO TRUTH ===" | Set-Content -Path $repoPath -Encoding UTF8
    git branch --show-current | Add-Content -Path $repoPath -Encoding UTF8
    git rev-parse HEAD | Add-Content -Path $repoPath -Encoding UTF8
    git status --short --branch | Add-Content -Path $repoPath -Encoding UTF8
    git log --oneline -n 8 | Add-Content -Path $repoPath -Encoding UTF8
    Add-Check -Name "repo_truth_captured" -Pass $true -Detail $repoPath

    if (-not $SkipAzureCli) {
        if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
            throw "Azure CLI not found. Install Azure CLI or rerun with -SkipAzureCli to capture endpoint-only proof."
        }

        $accountPath = Join-Path $base "02_azure_account.json"
        $accountRaw = az account show -o json
        $account = $accountRaw | ConvertFrom-Json
        Save-Json -Object ([ordered]@{
            name = $account.name
            tenantId = $account.tenantId
            subscriptionId = $account.id
            user = $account.user.name
        }) -Path $accountPath
        Add-Check -Name "azure_cli_authenticated" -Pass $true -Detail $accountPath

        $webappPath = Join-Path $base "03_webapp_summary.json"
        $webapp = az webapp show -g $ResourceGroup -n $WebAppName --query "{name:name,state:state,defaultHostName:defaultHostName,httpsOnly:httpsOnly,kind:kind,serverFarmId:serverFarmId}" -o json | ConvertFrom-Json
        Save-Json -Object $webapp -Path $webappPath
        Add-Check -Name "webapp_resolved" -Pass ($webapp.name -eq $WebAppName) -Detail $webappPath
        Add-Check -Name "webapp_running" -Pass ($webapp.state -eq "Running") -Detail "state=$($webapp.state)"

        $identityPath = Join-Path $base "04_webapp_identity.txt"
        $principalId = (az webapp identity show -g $ResourceGroup -n $WebAppName --query principalId -o tsv).Trim()
        "principalId=$principalId" | Set-Content -Path $identityPath -Encoding UTF8
        Add-Check -Name "managed_identity_present" -Pass (-not [string]::IsNullOrWhiteSpace($principalId)) -Detail $identityPath

        $acrPath = Join-Path $base "05_acr_summary.txt"
        $acrId = (az acr show -n $AcrName --query id -o tsv).Trim()
        "acrId=$acrId" | Set-Content -Path $acrPath -Encoding UTF8
        Add-Check -Name "acr_resolved" -Pass (-not [string]::IsNullOrWhiteSpace($acrId)) -Detail $acrPath

        $acrPullPath = Join-Path $base "06_acrpull_assignments.json"
        $acrPull = az role assignment list --assignee $principalId --scope $acrId --query "[?roleDefinitionName=='AcrPull'].{role:roleDefinitionName,scope:scope,principalId:principalId}" -o json | ConvertFrom-Json
        Save-Json -Object $acrPull -Path $acrPullPath
        $acrPullCount = @($acrPull).Count
        Add-Check -Name "managed_identity_has_acrpull" -Pass ($acrPullCount -gt 0) -Detail "count=$acrPullCount path=$acrPullPath"

        $containerPath = Join-Path $base "07_container_config.json"
        $containerConfig = az webapp config container show -g $ResourceGroup -n $WebAppName -o json | ConvertFrom-Json
        Save-Json -Object $containerConfig -Path $containerPath
        Add-Check -Name "container_config_captured" -Pass $true -Detail $containerPath

        $settingsPath = Join-Path $base "08_appsettings_presence.json"
        $settings = az webapp config appsettings list -g $ResourceGroup -n $WebAppName | ConvertFrom-Json
        $requiredSettings = @(
            "BUILD_SHA",
            "PROD_DEPLOY_TAG",
            "APP_VERSION",
            "RUN_MIGRATIONS",
            "DEPLOY_RUN_ID",
            "DEPLOY_WORKFLOW",
            "AZURE_CLIENT_ID",
            "AZURE_TENANT_ID",
            "AZURE_REDIRECT_URI",
            "AZURE_ROLE_GROUP_MAP",
            "AAD_TENANT_ID",
            "AAD_API_AUDIENCE"
        )
        $presence = foreach ($key in $requiredSettings) {
            $item = $settings | Where-Object { $_.name -eq $key } | Select-Object -First 1
            $hasValue = $false
            if ($null -ne $item) {
                $hasValue = -not [string]::IsNullOrWhiteSpace("$($item.value)")
            }
            [ordered]@{
                key = $key
                present = [bool]$item
                has_value = $hasValue
            }
        }
        Save-Json -Object $presence -Path $settingsPath
        $missing = @($presence | Where-Object { -not $_.present -or -not $_.has_value })
        Add-Check -Name "required_appsettings_present_nonsecret" -Pass ($missing.Count -eq 0) -Detail "missing_or_empty=$($missing.Count) path=$settingsPath"
    } else {
        Add-Check -Name "azure_cli_checks_skipped" -Pass $true -Detail "-SkipAzureCli was supplied; endpoint parity still required."
    }

    $healthPath = Join-Path $base "09_health.json"
    $healthResponse = Invoke-WebRequest -UseBasicParsing -Uri $HealthUrl -TimeoutSec 30
    $healthResponse.Content | Set-Content -Path $healthPath -Encoding UTF8
    $health = Get-Content $healthPath -Raw | ConvertFrom-Json
    $healthOk = Get-ObjectPropertyValue -Object $health -Name "ok"
    $healthStatus = Get-ObjectPropertyValue -Object $health -Name "status" -Default ""
    $healthEnv = Get-ObjectPropertyValue -Object $health -Name "env" -Default ""
    $healthDb = Get-ObjectPropertyValue -Object $health -Name "db" -Default ""
    $healthBuildSha = Get-ObjectPropertyValue -Object $health -Name "build_sha" -Default ""
    Add-Check -Name "health_endpoint_200" -Pass ($healthResponse.StatusCode -eq 200) -Detail "status=$($healthResponse.StatusCode) path=$healthPath"
    Add-Check -Name "health_ok" -Pass ($healthOk -eq $true -or "$healthStatus".ToLowerInvariant() -eq "ok") -Detail "ok=$healthOk status=$healthStatus"
    Add-Check -Name "health_env_prod" -Pass ("$healthEnv" -eq "prod") -Detail "env=$healthEnv"
    Add-Check -Name "health_db_ok" -Pass ("$healthDb" -eq "ok") -Detail "db=$healthDb"
    Assert-Present -Name "health.build_sha" -Value $healthBuildSha

    $integrityPath = Join-Path $base "10_integrity.json"
    $integrityResponse = Invoke-WebRequest -UseBasicParsing -Uri $IntegrityUrl -TimeoutSec 30
    $integrityResponse.Content | Set-Content -Path $integrityPath -Encoding UTF8
    $integrity = Get-Content $integrityPath -Raw | ConvertFrom-Json
    $integrityOk = Get-ObjectPropertyValue -Object $integrity -Name "ok"
    $integrityStatus = Get-ObjectPropertyValue -Object $integrity -Name "status" -Default ""
    $integrityEnv = Get-ObjectPropertyValue -Object $integrity -Name "env" -Default ""
    $integrityBuildSha = Get-ObjectPropertyValue -Object $integrity -Name "build_sha" -Default ""
    Add-Check -Name "integrity_endpoint_200" -Pass ($integrityResponse.StatusCode -eq 200) -Detail "status=$($integrityResponse.StatusCode) path=$integrityPath"
    Add-Check -Name "integrity_ok" -Pass ($integrityOk -eq $true -or "$integrityStatus".ToLowerInvariant() -eq "ok") -Detail "ok=$integrityOk status=$integrityStatus"
    Add-Check -Name "integrity_env_prod" -Pass ("$integrityEnv" -eq "prod") -Detail "env=$integrityEnv"
    Assert-Present -Name "integrity.build_sha" -Value $integrityBuildSha

    $sameRuntimeSha = ("$healthBuildSha" -eq "$integrityBuildSha")
    Add-Check -Name "health_integrity_sha_match" -Pass $sameRuntimeSha -Detail "health=$healthBuildSha integrity=$integrityBuildSha"

    $matchesExpected = ("$healthBuildSha" -eq $ExpectedSha -and "$integrityBuildSha" -eq $ExpectedSha)
    Add-Check -Name "runtime_matches_expected_sha" -Pass $matchesExpected -Detail "expected=$ExpectedSha health=$healthBuildSha integrity=$integrityBuildSha"

    $shaComparisonPath = Join-Path $base "11_sha_comparison.json"
    Save-Json -Object ([ordered]@{
        expected_sha = $ExpectedSha
        health_build_sha = "$healthBuildSha"
        integrity_build_sha = "$integrityBuildSha"
        health_ok = $healthOk
        health_status = $healthStatus
        health_env = $healthEnv
        health_db = $healthDb
        integrity_ok = $integrityOk
        integrity_status = $integrityStatus
        integrity_env = $integrityEnv
        health_integrity_sha_match = $sameRuntimeSha
        runtime_matches_expected_sha = $matchesExpected
    }) -Path $shaComparisonPath

    $failed = @($summary.checks | Where-Object { -not $_.pass })
    if ($failed.Count -eq 0) {
        $summary.verdict = "PASS"
    } else {
        $summary.verdict = "FAIL"
    }

    $summaryPath = Join-Path $base "00_AZURE_P0_SUMMARY.json"
    Save-Json -Object $summary -Path $summaryPath

    $mdPath = Join-Path $base "00_AZURE_P0_SUMMARY.md"
    $md = New-Object System.Collections.Generic.List[string]
    $md.Add("# Azure P0 Current Parity Probe")
    $md.Add("")
    $md.Add("- Verdict: $($summary.verdict)")
    $md.Add("- Expected SHA: $ExpectedSha")
    $md.Add("- Health URL: $HealthUrl")
    $md.Add("- Integrity URL: $IntegrityUrl")
    $md.Add("- Evidence root: $base")
    $md.Add("")
    $md.Add("## Checks")
    foreach ($check in $summary.checks) {
        $mark = if ($check.pass) { "PASS" } else { "FAIL" }
        $md.Add("- $mark - $($check.name): $($check.detail)")
    }
    $md | Set-Content -Path $mdPath -Encoding UTF8

    Write-Host "AZURE_P0_EVIDENCE=$base"
    Write-Host "AZURE_P0_SUMMARY=$mdPath"
    Write-Host "AZURE_P0_VERDICT=$($summary.verdict)"

    if ($summary.verdict -ne "PASS") {
        exit 1
    }
}
catch {
    $summary.verdict = "FAIL"
    $summary.error = $_.Exception.Message
    Save-Json -Object $summary -Path (Join-Path $base "00_AZURE_P0_SUMMARY.json")
    "# Azure P0 Current Parity Probe`n`n- Verdict: FAIL`n- Error: $($_.Exception.Message)`n- Evidence root: $base" | Set-Content -Path (Join-Path $base "00_AZURE_P0_SUMMARY.md") -Encoding UTF8
    Write-Host "AZURE_P0_EVIDENCE=$base"
    Write-Host "AZURE_P0_VERDICT=FAIL"
    throw
}
