$ErrorActionPreference = "Stop"

$OutputDir = "_warroom"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$ghRuns = gh run list --limit 200 --json databaseId,workflowName,headSha,status,conclusion,url,headBranch,displayTitle,createdAt | ConvertFrom-Json
$deployRuns = $ghRuns | Where-Object { $_.workflowName -match 'Production Deploy|deploy-prod' } | Sort-Object createdAt -Descending
$latest = $deployRuns | Select-Object -First 1

$githubSha = [string]$latest.headSha
$runId = [string]$latest.databaseId

$azureImage = az webapp config container show --resource-group crown-rg --name crown-api-prod --query "[?name=='DOCKER_CUSTOM_IMAGE_NAME'].value | [0]" -o tsv
if (-not $azureImage) {
    $azureImage = az webapp config container show --resource-group crown-rg --name crown-api-prod --query linuxFxVersion -o tsv
}
$containerSha = ""
if ($azureImage -match ':(?<sha>[0-9a-f]{40})$') {
    $containerSha = $Matches['sha']
}

$healthRaw = ""
try {
    $healthRaw = curl.exe -fsSL https://crown-api-prod.azurewebsites.net/health
}
catch {
    $healthRaw = curl.exe -fsSL https://crown-api-prod.azurewebsites.net/health/
}
$healthObj = $healthRaw | ConvertFrom-Json
$healthSha = [string]$healthObj.build_sha
$healthStatus = [string]$healthObj.status
if (-not $healthStatus) {
    $healthStatus = if ($healthObj.ok -eq $true) { "ok" } else { "unknown" }
}

$result = "MISMATCH"
if ($githubSha -and $containerSha -and $healthSha -and $githubSha -eq $containerSha -and $containerSha -eq $healthSha) {
    $result = "MATCH"
}
elseif ($containerSha -and $healthSha -and $containerSha -eq $healthSha) {
    $result = "PARTIAL_MATCH_GH_DIFF"
}

@(
    "GitHub run ID: $runId"
    "GitHub build SHA: $githubSha"
    "Azure container image: $azureImage"
    "Azure container SHA: $containerSha"
    "API health status: $healthStatus"
    "API health SHA: $healthSha"
    "Result: $result"
) | Set-Content -Path "$OutputDir/deploy_truth_check.txt" -Encoding UTF8

Write-Host "Deploy truth written to $OutputDir/deploy_truth_check.txt"
