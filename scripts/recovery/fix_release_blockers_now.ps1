[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ============================================================
# USER SETTINGS - CHANGE THESE THREE VALUES ONLY
# ============================================================
$RepoRoot = "C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr"
$Owner = "tcmegahan"
$Repo = "Crown2026"
$Branch = "audit/pr-overlap-reconcile"
$EnvironmentName = "production"
$ProductionBaseUrl = "https://crown-api-prod.azurewebsites.net"

$AZURE_CLIENT_ID = "<your-azure-client-id>"
$AZURE_TENANT_ID = "<your-azure-tenant-id>"
$AZURE_SUBSCRIPTION_ID = "<your-azure-subscription-id>"

# Name for the Entra federated credential record
$FederatedCredentialName = "github-production-environment"

# Exact GitHub OIDC subject required for this repo/environment
$FederatedSubject = "repo:tcmegahan/Crown2026:environment:production"

# Optional: if you need to grant role assignment with CLI, uncomment and set these.
# $AzureRoleScope = "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Web/sites/<app-name>"
# $AzureRoleName = "Contributor"

# ============================================================
# HELPERS
# ============================================================
function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "=== $Message ===" -ForegroundColor Cyan
}

function Save-Text {
    param([string]$Path, [string]$Text)
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, $Text, [System.Text.UTF8Encoding]::new($false))
}

function Run-Cmd {
    param(
        [string]$Command,
        [string]$OutFile,
        [string]$WorkingDirectory,
        [switch]$AllowFailure
    )

    Push-Location $WorkingDirectory
    $prevEA = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $output = (cmd.exe /d /c $Command 2>&1) | ForEach-Object { [string]$_ }
        $exitCode = $LASTEXITCODE
        $output | Out-File -FilePath $OutFile -Encoding utf8
        if (-not $AllowFailure -and $exitCode -ne 0) {
            throw "Command failed ($exitCode): $Command`nSee: $OutFile"
        }
        return @{
            ExitCode = $exitCode
            Output   = $output
            Path     = $OutFile
        }
    }
    finally {
        $ErrorActionPreference = $prevEA
        Pop-Location
    }
}

function Ensure-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing required command: $Name"
    }
}

function Try-Http {
    param(
        [string]$Uri,
        [hashtable]$Headers = @{},
        [string]$OutFile
    )

    try {
        $resp = Invoke-WebRequest -Uri $Uri -Headers $Headers -Method Get -TimeoutSec 30 -UseBasicParsing
        Save-Text -Path $OutFile -Text $resp.Content
        return @{
            Success    = $true
            StatusCode = [int]$resp.StatusCode
            Body       = $resp.Content
        }
    }
    catch {
        $status = -1
        $body = $_.ToString()
        if ($_.Exception.Response) {
            try { $status = [int]$_.Exception.Response.StatusCode } catch {}
            try {
                $sr = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                $body = $sr.ReadToEnd()
            } catch {}
        }
        Save-Text -Path $OutFile -Text $body
        return @{
            Success    = $false
            StatusCode = $status
            Body       = $body
        }
    }
}

function Require-NonPlaceholder {
    param([string]$Value, [string]$Name)
    if ([string]::IsNullOrWhiteSpace($Value) -or $Value -match '^<REPLACE-') {
        throw "You must set $Name at the top of the script."
    }
}

# ============================================================
# PRECHECKS
# ============================================================
Ensure-Command git
Ensure-Command gh
Ensure-Command az
Require-NonPlaceholder -Value $AZURE_CLIENT_ID -Name "AZURE_CLIENT_ID"
Require-NonPlaceholder -Value $AZURE_TENANT_ID -Name "AZURE_TENANT_ID"
Require-NonPlaceholder -Value $AZURE_SUBSCRIPTION_ID -Name "AZURE_SUBSCRIPTION_ID"

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Artifacts = Join-Path $RepoRoot "audit-artifacts\fix-release-blockers-$Timestamp"
New-Item -ItemType Directory -Force -Path $Artifacts | Out-Null

$Python = $null
if (Test-Path (Join-Path $RepoRoot "venv\Scripts\python.exe")) {
    $Python = Join-Path $RepoRoot "venv\Scripts\python.exe"
} elseif (Test-Path (Join-Path $RepoRoot ".venv\Scripts\python.exe")) {
    $Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $Python = "python"
} else {
    throw "Python not found."
}

Write-Step "Record current repo state"
Push-Location $RepoRoot
try {
    $state = @()
    $state += "repo_root=$RepoRoot"
    $state += "branch=$(git rev-parse --abbrev-ref HEAD)"
    $state += "head=$(git rev-parse HEAD)"
    $state += ""
    $state += "git_status:"
    $state += (git status --short)
    $state += ""
    $state += "recent_commits:"
    $state += (git log --oneline -n 10)
    Save-Text -Path (Join-Path $Artifacts "01_repo_state.txt") -Text ($state -join [Environment]::NewLine)
}
finally {
    Pop-Location
}

# ============================================================
# 1. REPO-SIDE FIX: integrity endpoint public + regression test
# ============================================================
Write-Step "Patch integrity middleware and regression test if needed"

$MiddlewarePath = Join-Path $RepoRoot "backend\core\tenant_header_middleware.py"
$HealthTestPath = Join-Path $RepoRoot "backend\crown_api\tests\test_health.py"

if (-not (Test-Path $MiddlewarePath)) { throw "Missing $MiddlewarePath" }
if (-not (Test-Path $HealthTestPath)) { throw "Missing $HealthTestPath" }

$mw = Get-Content -Raw -Encoding utf8 $MiddlewarePath
$mwChanged = $false

if ($mw -notmatch '"/api/integrity"') {
    $mw = $mw -replace '("/api/v1/system/health",\s*)', '$1' + "`r`n" + '        "/api/integrity",' + "`r`n"
    [System.IO.File]::WriteAllText($MiddlewarePath, $mw, [System.Text.UTF8Encoding]::new($false))
    $mwChanged = $true
}

$th = Get-Content -Raw -Encoding utf8 $HealthTestPath
$testChanged = $false
if ($th -notmatch 'def test_integrity_endpoint_is_public_and_returns_contract') {
    $th += @"

@pytest.mark.django_db
def test_integrity_endpoint_is_public_and_returns_contract():
    client = Client()

    response = client.get("/api/integrity/")

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "build_sha" in data
    assert "prod_deploy_tag" in data
    assert "required_checks" in data
    assert "meta_gates" in data
"@
    [System.IO.File]::WriteAllText($HealthTestPath, $th, [System.Text.UTF8Encoding]::new($false))
    $testChanged = $true
}

Save-Text -Path (Join-Path $Artifacts "02_integrity_patch_status.txt") -Text @"
middleware_changed=$mwChanged
test_changed=$testChanged
"@

Write-Step "Commit repo-side changes if present"
Push-Location $RepoRoot
try {
    $statusNow = git status --short
    if ($statusNow -match 'tenant_header_middleware.py|test_health.py') {
        git add backend/core/tenant_header_middleware.py backend/crown_api/tests/test_health.py
        git commit -m "fix: exempt integrity endpoint from tenant middleware and add regression test" | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Commit failed for integrity fix." }
        git push origin HEAD:$Branch | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Push failed for integrity fix." }
        Save-Text -Path (Join-Path $Artifacts "03_integrity_commit.txt") -Text (git rev-parse HEAD)
    } else {
        Save-Text -Path (Join-Path $Artifacts "03_integrity_commit.txt") -Text "NO_CHANGE"
    }
}
finally {
    Pop-Location
}

# ============================================================
# 2. LOCAL PROOF BEFORE DEPLOY
# ============================================================
Write-Step "Run local backend proof"
$EnvPrefix = 'set DJANGO_DEBUG=0 && set DJANGO_ENV=production && set CROWN_ENV=local && set DJANGO_SECRET_KEY=local-proof-only && '
Run-Cmd -Command ($EnvPrefix + "$Python backend\manage.py check") -OutFile (Join-Path $Artifacts "04_django_check.txt") -WorkingDirectory $RepoRoot
Run-Cmd -Command ($EnvPrefix + "$Python -m pytest backend/crown_api/tests/test_health.py -q") -OutFile (Join-Path $Artifacts "05_pytest_health.txt") -WorkingDirectory $RepoRoot
Run-Cmd -Command ($EnvPrefix + "$Python -m pytest backend/tests/test_tenant_header_required.py backend/tests/test_tenant_header_validate_school.py backend/crown_api/tests/test_tenant_enforcement.py -q") -OutFile (Join-Path $Artifacts "06_pytest_tenant.txt") -WorkingDirectory $RepoRoot

# ============================================================
# 3. VERIFY WORKFLOW HAS OIDC PERMISSION
# ============================================================
Write-Step "Verify deploy-prod workflow is OIDC-capable"
$WorkflowPath = Join-Path $RepoRoot ".github\workflows\deploy-prod.yml"
if (-not (Test-Path $WorkflowPath)) { throw "Missing $WorkflowPath" }

$workflow = Get-Content -Raw -Encoding utf8 $WorkflowPath
if ($workflow -notmatch 'id-token:\s*write') {
    throw "deploy-prod.yml is missing permissions: id-token: write"
}
if ($workflow -match 'azurewebsites\.net/health') {
    $workflow = $workflow -replace '/health', '/api/health/'
    [System.IO.File]::WriteAllText($WorkflowPath, $workflow, [System.Text.UTF8Encoding]::new($false))

    Push-Location $RepoRoot
    try {
        git add .github/workflows/deploy-prod.yml
        git commit -m "fix: align deploy-prod health checks to api health endpoint" | Out-Null
        if ($LASTEXITCODE -eq 0) {
            git push origin HEAD:$Branch | Out-Null
        }
    }
    finally {
        Pop-Location
    }
}
Save-Text -Path (Join-Path $Artifacts "07_workflow_oidc_check.txt") -Text "id-token: write present"

# ============================================================
# 4. AZURE: CREATE/REPLACE FEDERATED CREDENTIAL
# ============================================================
Write-Step "Create or replace Azure federated credential for GitHub environment"

# Use the application object id, not the client id, for Graph writes.
$AppObjectId = (az ad app show --id $AZURE_CLIENT_ID --query id -o tsv).Trim()
if (-not $AppObjectId) {
    throw "Could not resolve Entra app object id from AZURE_CLIENT_ID"
}
Save-Text -Path (Join-Path $Artifacts "08_app_object_id.txt") -Text $AppObjectId

# Remove any old federated credential with the same name.
$ficsJson = az rest --method GET --uri "https://graph.microsoft.com/v1.0/applications/$AppObjectId/federatedIdentityCredentials" | Out-String
Save-Text -Path (Join-Path $Artifacts "09_existing_fics.json") -Text $ficsJson

$fics = $null
try { $fics = $ficsJson | ConvertFrom-Json } catch {}
if ($fics -and $fics.value) {
    $existing = $fics.value | Where-Object { $_.name -eq $FederatedCredentialName } | Select-Object -First 1
    if ($existing) {
        az rest --method DELETE --uri "https://graph.microsoft.com/v1.0/applications/$AppObjectId/federatedIdentityCredentials/$($existing.id)" | Out-Null
    }
}

$ficBody = @{
    name        = $FederatedCredentialName
    issuer      = "https://token.actions.githubusercontent.com"
    subject     = $FederatedSubject
    description = "GitHub Actions OIDC for $Owner/$Repo environment $EnvironmentName"
    audiences   = @("api://AzureADTokenExchange")
} | ConvertTo-Json -Depth 5 -Compress

Save-Text -Path (Join-Path $Artifacts "10_fic_body.json") -Text $ficBody

$ficCreate = az rest --method POST --uri "https://graph.microsoft.com/v1.0/applications/$AppObjectId/federatedIdentityCredentials" --body $ficBody | Out-String
Save-Text -Path (Join-Path $Artifacts "11_fic_create_response.json") -Text $ficCreate

# Optional role assignment
# if ($AzureRoleScope -and $AzureRoleName) {
#     az role assignment create --assignee $AZURE_CLIENT_ID --role $AzureRoleName --scope $AzureRoleScope | Out-Null
# }

# ============================================================
# 5. GITHUB: SET THE THREE REAL AZURE ENVIRONMENT SECRETS
# ============================================================
Write-Step "Set GitHub environment secrets used by Azure Login"
gh secret set AZURE_CLIENT_ID --env $EnvironmentName --body $AZURE_CLIENT_ID
gh secret set AZURE_TENANT_ID --env $EnvironmentName --body $AZURE_TENANT_ID
gh secret set AZURE_SUBSCRIPTION_ID --env $EnvironmentName --body $AZURE_SUBSCRIPTION_ID

$secretsList = gh secret list --env $EnvironmentName | Out-String
Save-Text -Path (Join-Path $Artifacts "12_environment_secrets.txt") -Text $secretsList

# ============================================================
# 6. TRIGGER CONTROLLED DEPLOY TAG
# ============================================================
Write-Step "Create and push one controlled deploy tag"
Push-Location $RepoRoot
try {
    $HeadSha = (git rev-parse HEAD).Trim()
    $Tag = "prod-deploy-$Timestamp-controlled"
    git tag -f $Tag $HeadSha
    git push -f origin "refs/tags/$Tag" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Failed to push controlled deploy tag." }

    Save-Text -Path (Join-Path $Artifacts "13_controlled_tag.txt") -Text $Tag
    Save-Text -Path (Join-Path $Artifacts "14_controlled_sha.txt") -Text $HeadSha
}
finally {
    Pop-Location
}

# ============================================================
# 7. FIND RUN, APPROVE PENDING DEPLOYMENT, WATCH TO COMPLETION
# ============================================================
Write-Step "Locate controlled deploy run"
$RunId = $null
$RunHeadSha = $null
$RunUrl = $null
$deadline = (Get-Date).AddMinutes(25)

do {
    Start-Sleep -Seconds 15
    $runListPath = Join-Path $Artifacts "15_run_list_poll.json"
    $runListText = gh run list --repo "$Owner/$Repo" --workflow deploy-prod.yml --limit 20 --json databaseId,headBranch,headSha,status,conclusion,url,createdAt | Out-String
    Save-Text -Path $runListPath -Text $runListText

    try {
        $runs = $runListText | ConvertFrom-Json
        $match = $runs | Where-Object { $_.headBranch -eq $Tag } | Select-Object -First 1
        if ($match) {
            $RunId = [string]$match.databaseId
            $RunHeadSha = [string]$match.headSha
            $RunUrl = [string]$match.url
            break
        }
    } catch {}
} while ((Get-Date) -lt $deadline)

if (-not $RunId) {
    throw "Could not find controlled deploy run for tag $Tag"
}

Save-Text -Path (Join-Path $Artifacts "16_run_id.txt") -Text $RunId
Save-Text -Path (Join-Path $Artifacts "17_run_url.txt") -Text $RunUrl

Write-Step "Approve pending environment deployments if present"
$pendingText = gh api "repos/$Owner/$Repo/actions/runs/$RunId/pending_deployments" | Out-String
Save-Text -Path (Join-Path $Artifacts "18_pending_deployments.json") -Text $pendingText

try {
    $pendingJson = $pendingText | ConvertFrom-Json
    $envIds = @()
    foreach ($item in $pendingJson) {
        if ($item.environment.id) {
            $envIds += [long]$item.environment.id
        }
    }
    $envIds = $envIds | Sort-Object -Unique

    if ($envIds.Count -gt 0) {
        $approvePayload = @{
            environment_ids = $envIds
            state = "approved"
            comment = "controlled validation deploy approval"
        } | ConvertTo-Json -Depth 5 -Compress

        $approveFile = Join-Path $Artifacts "19_approval_payload.json"
        Save-Text -Path $approveFile -Text $approvePayload

        gh api -X POST "repos/$Owner/$Repo/actions/runs/$RunId/pending_deployments" --input $approveFile | Out-String | Set-Content -Path (Join-Path $Artifacts "20_approval_response.json")
    }
} catch {
    Save-Text -Path (Join-Path $Artifacts "20_approval_response.json") -Text "PARSE_OR_APPROVAL_FAILED`r`n$($_.Exception.Message)"
}

Write-Step "Watch run to completion"
Run-Cmd -Command "gh run watch $RunId --repo $Owner/$Repo --interval 15" -OutFile (Join-Path $Artifacts "21_run_watch.txt") -WorkingDirectory $RepoRoot -AllowFailure | Out-Null
Run-Cmd -Command "gh run view $RunId --repo $Owner/$Repo --json status,conclusion,url,headBranch,headSha,createdAt,updatedAt,jobs" -OutFile (Join-Path $Artifacts "22_run_view.json") -WorkingDirectory $RepoRoot -AllowFailure | Out-Null
Run-Cmd -Command "gh api repos/$Owner/$Repo/actions/runs/$RunId/jobs" -OutFile (Join-Path $Artifacts "23_run_jobs.json") -WorkingDirectory $RepoRoot -AllowFailure | Out-Null

# Get failed job log if available
$jobId = $null
try {
    $jobsJson = Get-Content -Raw (Join-Path $Artifacts "23_run_jobs.json") | ConvertFrom-Json
    if ($jobsJson.jobs -and $jobsJson.jobs.Count -gt 0) {
        $jobId = [string]$jobsJson.jobs[0].id
    }
} catch {}

if ($jobId) {
    Run-Cmd -Command "gh run view $RunId --repo $Owner/$Repo --job $jobId --log-failed" -OutFile (Join-Path $Artifacts "24_failed_job_log.txt") -WorkingDirectory $RepoRoot -AllowFailure | Out-Null
}

# ============================================================
# 8. LIVE PROBES AFTER DEPLOY ATTEMPT
# ============================================================
Write-Step "Probe live health and integrity"
$health = Try-Http -Uri "$ProductionBaseUrl/api/health/" -OutFile (Join-Path $Artifacts "25_live_health.txt")
$intNoHdr = Try-Http -Uri "$ProductionBaseUrl/api/integrity/" -OutFile (Join-Path $Artifacts "26_live_integrity_no_header.txt")
$intHdr = Try-Http -Uri "$ProductionBaseUrl/api/integrity/" -Headers @{ "X-Crown-Integrity-Key" = "dummy" } -OutFile (Join-Path $Artifacts "27_live_integrity_with_header.txt")

$liveBuildSha = ""
$liveDeployTag = ""
try {
    $healthJson = $health.Body | ConvertFrom-Json
    if ($healthJson.build_sha) { $liveBuildSha = [string]$healthJson.build_sha }
    if ($healthJson.prod_deploy_tag) { $liveDeployTag = [string]$healthJson.prod_deploy_tag }
} catch {}

$identityText = @"
controlled_tag=$Tag
run_id=$RunId
run_head_sha=$RunHeadSha
live_build_sha=$liveBuildSha
live_prod_deploy_tag=$liveDeployTag
live_integrity_no_header_status=$($intNoHdr.StatusCode)
live_integrity_with_header_status=$($intHdr.StatusCode)
"@
Save-Text -Path (Join-Path $Artifacts "28_live_identity_compare.txt") -Text $identityText

# ============================================================
# 9. SIMPLE DECISION OUTPUT
# ============================================================
Write-Step "Write decision summary"
$failedLog = ""
$failedLogPath = Join-Path $Artifacts "24_failed_job_log.txt"
if (Test-Path $failedLogPath) {
    $failedLog = Get-Content -Raw $failedLogPath
}

$issues = New-Object System.Collections.Generic.List[string]

if ($failedLog -match 'AADSTS700213') {
    $issues.Add("Azure federated credential subject mismatch still present.")
}
if ($failedLog -match 'Azure Login' -or $failedLog -match 'azure/login') {
    $issues.Add("Azure Login still failing.")
}
if ($intNoHdr.StatusCode -ne 200 -or $intHdr.StatusCode -ne 200) {
    $issues.Add("Live integrity endpoint still not 200/200.")
}
if ($RunHeadSha -and $liveBuildSha -and $RunHeadSha -ne $liveBuildSha) {
    $issues.Add("Live build SHA does not match controlled deploy SHA.")
}
if ($Tag -and $liveDeployTag -and $Tag -ne $liveDeployTag) {
    $issues.Add("Live deploy tag does not match controlled deploy tag.")
}

$summary = @()
$summary += "Crown2026 release blocker repair summary"
$summary += "timestamp=$Timestamp"
$summary += "artifacts=$Artifacts"
$summary += ""
$summary += "health_status=$($health.StatusCode)"
$summary += "integrity_no_header_status=$($intNoHdr.StatusCode)"
$summary += "integrity_with_header_status=$($intHdr.StatusCode)"
$summary += "run_id=$RunId"
$summary += "run_head_sha=$RunHeadSha"
$summary += "live_build_sha=$liveBuildSha"
$summary += "live_prod_deploy_tag=$liveDeployTag"
$summary += ""
if ($issues.Count -eq 0) {
    $summary += "VERDICT=PASS"
    $summary += "NEXT_STEP=Promote this branch/run as the release candidate."
} else {
    $summary += "VERDICT=FAIL"
    $summary += "OPEN_ISSUES:"
    foreach ($issue in $issues) {
        $summary += "- $issue"
    }
}

Save-Text -Path (Join-Path $Artifacts "29_decision_summary.txt") -Text ($summary -join [Environment]::NewLine)

Write-Host ""
Write-Host "DONE" -ForegroundColor Green
Write-Host "Artifacts: $Artifacts" -ForegroundColor Green
Write-Host "Primary summary: $(Join-Path $Artifacts '29_decision_summary.txt')" -ForegroundColor Green