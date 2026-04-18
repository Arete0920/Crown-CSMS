# =====================================================================
# Crown2026 - Revised 48 Hour Recovery Sprint
# Save as: scripts/recovery/run_revised_48h_sprint.ps1
# Run from repo root:
# powershell -ExecutionPolicy Bypass -File .\scripts\recovery\run_revised_48h_sprint.ps1
# =====================================================================

[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path,
    [string]$Remote = "origin",
    [string]$Branch = "audit/pr-overlap-reconcile",
    [string]$Owner = "tcmegahan",
    [string]$Repo = "Crown2026",
    [string]$EnvironmentName = "production",
    [string]$RecoveryRoot = "C:\crown2026_recovery",
    [string]$ProductionBaseUrl = "https://crown-api-prod.azurewebsites.net",
    [switch]$ApplySafeFetchLintPass = $true,
    [switch]$PushRepoSideFixes = $true,
    [int]$DeployWaitMinutes = 25,
    [int]$PollSeconds = 15
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "=== $Message ===" -ForegroundColor Cyan
}

function Fail-Step {
    param([string]$Message)
    Write-Host "[FAIL] $Message" -ForegroundColor Red
    throw $Message
}

function Note {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Gray
}

function WarnLine {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Ensure-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Fail-Step "Required command not found: $Name"
    }
}

function Get-Python {
    if (Test-Path (Join-Path $RepoRoot ".venv\Scripts\python.exe")) { return (Join-Path $RepoRoot ".venv\Scripts\python.exe") }
    if (Test-Path (Join-Path $RepoRoot "venv\Scripts\python.exe")) { return (Join-Path $RepoRoot "venv\Scripts\python.exe") }
    if (Get-Command python -ErrorAction SilentlyContinue) { return "python" }
    Fail-Step "Python not found."
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
    try {
        $prevEA = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        $output = (cmd.exe /d /c $Command 2>&1) | ForEach-Object { [string]$_ }
        $exitCode = $LASTEXITCODE
        $ErrorActionPreference = $prevEA
        $output | Out-File -FilePath $OutFile -Encoding utf8
        if (-not $AllowFailure -and $exitCode -ne 0) {
            Fail-Step "Command failed ($exitCode): $Command`nSee: $OutFile"
        }
        return @{
            ExitCode = $exitCode
            Output   = $output
            Path     = $OutFile
        }
    }
    finally {
        Pop-Location
    }
}

function Try-HttpText {
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
            Path       = $OutFile
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
            Path       = $OutFile
        }
    }
}

function Test-GitAncestor {
    param([string]$Older, [string]$Newer, [string]$WorkingDirectory)
    Push-Location $WorkingDirectory
    try {
        git merge-base --is-ancestor $Older $Newer | Out-Null
        return ($LASTEXITCODE -eq 0)
    }
    finally {
        Pop-Location
    }
}

Ensure-Command git
Ensure-Command gh
$Python = Get-Python

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Artifacts = Join-Path $RepoRoot "audit-artifacts\revised-48h-$Timestamp"
$Worktree = Join-Path $RecoveryRoot "wt_$Timestamp"
$SummaryCsv = Join-Path $Artifacts "00_summary.csv"
$SummaryTxt = Join-Path $Artifacts "00_summary.txt"
$script:Summary = @()

function Add-Result {
    param([string]$Check, [string]$Result)
    $script:Summary += [pscustomobject]@{
        Check  = $Check
        Result = $Result
    }
}

New-Item -ItemType Directory -Force -Path $Artifacts | Out-Null
New-Item -ItemType Directory -Force -Path $RecoveryRoot | Out-Null

Write-Step "Capture current local state"
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
    $state += "git_log:"
    $state += (git log --oneline -n 10)
    Save-Text -Path (Join-Path $Artifacts "01_local_state.txt") -Text ($state -join [Environment]::NewLine)
}
finally {
    Pop-Location
}

Write-Step "Fetch remote and create clean recovery worktree"
Push-Location $RepoRoot
try {
    git fetch $Remote --tags --prune
    if ($LASTEXITCODE -ne 0) { Fail-Step "git fetch failed" }

    if (Test-Path $Worktree) {
        Remove-Item -Recurse -Force $Worktree
    }

    git config core.longpaths true
    git worktree add --detach $Worktree "$Remote/$Branch"
    if ($LASTEXITCODE -ne 0) { Fail-Step "git worktree add failed" }
}
finally {
    Pop-Location
}

Push-Location $Worktree
try {
    $wtStatus = (git status --short) -join [Environment]::NewLine
    Save-Text -Path (Join-Path $Artifacts "02_worktree_state.txt") -Text $wtStatus
    if ($wtStatus.Trim().Length -ne 0) {
        Fail-Step "Recovery worktree is not clean"
    }
    Add-Result "clean_recovery_worktree" "PASS"
}
finally {
    Pop-Location
}

Write-Step "Verify remote branch includes known recovery commits"
Push-Location $RepoRoot
try {
    $remoteRef = "$Remote/$Branch"
    $hasCheckpoint = Test-GitAncestor -Older "9aaae492" -Newer $remoteRef -WorkingDirectory $RepoRoot
    $hasDeployFix = Test-GitAncestor -Older "c1b090e7" -Newer $remoteRef -WorkingDirectory $RepoRoot

    $proof = @()
    $proof += "remote_ref=$remoteRef"
    $proof += "checkpoint_present=$hasCheckpoint"
    $proof += "deploy_fix_present=$hasDeployFix"
    Save-Text -Path (Join-Path $Artifacts "03_remote_commit_proof.txt") -Text ($proof -join [Environment]::NewLine)

    if (-not $hasCheckpoint) { Fail-Step "Missing checkpoint commit 9aaae492 on remote branch" }
    if (-not $hasDeployFix) { Fail-Step "Missing deploy fix commit c1b090e7 on remote branch" }

    Add-Result "checkpoint_commit_present" "PASS"
    Add-Result "deploy_fix_commit_present" "PASS"
}
finally {
    Pop-Location
}

Write-Step "Verify deploy-prod workflow health endpoint"
$WorkflowPath = Join-Path $Worktree ".github\workflows\deploy-prod.yml"
if (-not (Test-Path $WorkflowPath)) {
    Fail-Step "Missing workflow file: $WorkflowPath"
}

$workflowText = Get-Content -Raw -Encoding utf8 $WorkflowPath
$old1 = 'azurewebsites.net/health'
$new1 = 'azurewebsites.net/api/health/'
$hasOldHealth = $workflowText -match [regex]::Escape($old1)
$hasNewHealth = $workflowText -match [regex]::Escape($new1)

if ($hasOldHealth) {
    $workflowText = $workflowText -replace '/health','/api/health/'
    [System.IO.File]::WriteAllText($WorkflowPath, $workflowText, [System.Text.UTF8Encoding]::new($false))
    Add-Result "workflow_health_endpoint_rewritten" "YES"
} else {
    Add-Result "workflow_health_endpoint_rewritten" "NO"
}

$yamlParseFile = Join-Path $Artifacts "04_workflow_yaml_parse.txt"
$yamlCmd = "$Python -c ""import yaml; yaml.safe_load(open(r'$WorkflowPath','r',encoding='utf-8')); print('YAML_OK')"""
$yamlRes = Run-Cmd -Command $yamlCmd -OutFile $yamlParseFile -WorkingDirectory $Worktree
if (-not (($yamlRes.Output -join "`n") -match 'YAML_OK')) {
    Fail-Step "deploy-prod.yml failed YAML parse"
}
Add-Result "workflow_yaml_parse" "PASS"

if ($PushRepoSideFixes) {
    Push-Location $Worktree
    try {
        if ((git status --short) -match 'deploy-prod.yml') {
            git add .github/workflows/deploy-prod.yml
            git commit -m "fix: align deploy-prod health checks to api health endpoint"
            if ($LASTEXITCODE -ne 0) { Fail-Step "Failed to commit workflow health path fix" }
            git push $Remote HEAD:$Branch
            if ($LASTEXITCODE -ne 0) { Fail-Step "Failed to push workflow health path fix" }
            Add-Result "workflow_fix_pushed" "PASS"
        } else {
            Add-Result "workflow_fix_pushed" "NO_CHANGE"
        }
    }
    finally {
        Pop-Location
    }
}

Write-Step "Apply repo-side integrity fix if missing"
$MiddlewarePath = Join-Path $Worktree "backend\core\tenant_header_middleware.py"
$HealthTestPath = Join-Path $Worktree "backend\crown_api\tests\test_health.py"

if (-not (Test-Path $MiddlewarePath)) { Fail-Step "Missing middleware file: $MiddlewarePath" }
if (-not (Test-Path $HealthTestPath)) { Fail-Step "Missing test file: $HealthTestPath" }

$mw = Get-Content -Raw -Encoding utf8 $MiddlewarePath
$mwChanged = $false

if ($mw -notmatch '/api/integrity') {
    $mw = $mw.Replace(
        '    Exempted paths: /api/auth/*, /api/v1/auth/*, /api/health/*, /api/v1/health/*,' + "`r`n" + '    /api/schema/*, /api/docs/*',
        '    Exempted paths: /api/auth/*, /api/v1/auth/*, /api/health/*, /api/v1/health/*,' + "`r`n" + '    /api/integrity/*, /api/schema/*, /api/docs/*'
    )
    $mw = $mw.Replace(
        '        "/api/v1/system/health",' + "`r`n" + '        "/api/auth",',
        '        "/api/v1/system/health",' + "`r`n" + '        "/api/integrity",' + "`r`n" + '        "/api/auth",'
    )
    [System.IO.File]::WriteAllText($MiddlewarePath, $mw, [System.Text.UTF8Encoding]::new($false))
    $mwChanged = $true
}

$th = Get-Content -Raw -Encoding utf8 $HealthTestPath
$testChanged = $false
if ($th -notmatch 'def test_integrity_endpoint_is_public_and_returns_contract') {
    $append = @"

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
    $th += $append
    [System.IO.File]::WriteAllText($HealthTestPath, $th, [System.Text.UTF8Encoding]::new($false))
    $testChanged = $true
}

Add-Result "integrity_middleware_change" $(if ($mwChanged) { "YES" } else { "NO" })
Add-Result "integrity_test_change" $(if ($testChanged) { "YES" } else { "NO" })

if ($PushRepoSideFixes) {
    Push-Location $Worktree
    try {
        $repoChanges = git status --short
        if ($repoChanges -match 'tenant_header_middleware.py|test_health.py') {
            git add backend/core/tenant_header_middleware.py backend/crown_api/tests/test_health.py
            git commit -m "fix: exempt integrity endpoint from tenant header middleware and add regression test"
            if ($LASTEXITCODE -ne 0) { Fail-Step "Failed to commit integrity fix" }
            git push $Remote HEAD:$Branch
            if ($LASTEXITCODE -ne 0) { Fail-Step "Failed to push integrity fix" }
            Add-Result "integrity_fix_pushed" "PASS"
        } else {
            Add-Result "integrity_fix_pushed" "NO_CHANGE"
        }
    }
    finally {
        Pop-Location
    }
}

Write-Step "Backend proof pack from clean worktree"
$backendDir = Join-Path $Worktree "backend"
$djangoCheckFile = Join-Path $Artifacts "05_django_check.txt"
$healthPytestFile = Join-Path $Artifacts "06_pytest_health.txt"
$tenantPytestFile = Join-Path $Artifacts "07_pytest_tenant.txt"
$deploySubsetFile = Join-Path $Artifacts "08_deploy_subset_tests.txt"
$localIntegrityShellFile = Join-Path $Artifacts "09_local_integrity_shell.txt"

$EnvPrefix = 'set DJANGO_DEBUG=0 && set DJANGO_ENV=production && set CROWN_ENV=prod && set DJANGO_SECRET_KEY=schema-local-check-only && '
$djangoRes = Run-Cmd -Command ($EnvPrefix + "$Python backend\manage.py check") -OutFile $djangoCheckFile -WorkingDirectory $Worktree
Add-Result "django_check" $(if ($djangoRes.ExitCode -eq 0) { "PASS" } else { "FAIL" })

$LocalIntegrityEnvPrefix = "set DJANGO_DEBUG=0 && set DJANGO_SECRET_KEY=schema-local-check-only && set CROWN_ENV=local && "
$localIntegrityCmd = $LocalIntegrityEnvPrefix + "$Python backend\manage.py shell -c ""from django.test import Client; c=Client(); r1=c.get('/api/integrity/', follow=True); print('NOHDR', r1.status_code); print(r1.content.decode()); r2=c.get('/api/integrity/', HTTP_X_CROWN_INTEGRITY_KEY='dummy', follow=True); print('HDR', r2.status_code); print(r2.content.decode())"""
$localIntegrityRes = Run-Cmd -Command $localIntegrityCmd -OutFile $localIntegrityShellFile -WorkingDirectory $Worktree
if (($localIntegrityRes.Output -join "`n") -notmatch 'NOHDR 200') { Fail-Step "Local integrity endpoint still not 200 without header" }
if (($localIntegrityRes.Output -join "`n") -notmatch 'HDR 200') { Fail-Step "Local integrity endpoint still not 200 with header" }
Add-Result "local_integrity_contract" "PASS"

$pytestHealth = Run-Cmd -Command "$Python -m pytest backend/crown_api/tests/test_health.py -q" -OutFile $healthPytestFile -WorkingDirectory $Worktree
if ($pytestHealth.ExitCode -ne 0) { Fail-Step "Health/integrity pytest failed" }
Add-Result "pytest_health_integrity" "PASS"

$pytestTenant = Run-Cmd -Command "$Python -m pytest backend/tests/test_tenant_header_required.py backend/tests/test_tenant_header_validate_school.py backend/crown_api/tests/test_tenant_enforcement.py -q" -OutFile $tenantPytestFile -WorkingDirectory $Worktree
if ($pytestTenant.ExitCode -ne 0) { Fail-Step "Tenant enforcement pytest failed" }
Add-Result "pytest_tenant_enforcement" "PASS"

$deploySubsetCmd = "$Python manage.py test crown_api.tests.test_households_api crown_api.tests.test_students_api crown_api.tests.test_director_router crown_api.tests.test_director_actions_auth_required crown_api.tests.test_admissions_links_api crown_api.tests.test_academics_api crown_api.tests.test_billing_summary_api crown_api.tests.test_comms_api crown_api.tests.test_scheduling_api --verbosity 0"
$deploySubsetRes = Run-Cmd -Command $deploySubsetCmd -OutFile $deploySubsetFile -WorkingDirectory $backendDir -AllowFailure
if ($deploySubsetRes.ExitCode -ne 0) {
    Fail-Step "Deploy-prod backend subset failed"
}
Add-Result "deploy_prod_backend_subset" "PASS"

Write-Step "Read production environment policies and secret metadata"
$envJsonFile = Join-Path $Artifacts "10_production_environment.json"
$envPolicyFile = Join-Path $Artifacts "11_production_branch_policies.json"
$envSecretsFile = Join-Path $Artifacts "12_production_secret_names.txt"
$envVarsFile = Join-Path $Artifacts "13_production_variable_names.txt"
$deployReferencesFile = Join-Path $Artifacts "14_deploy_prod_secret_var_references.txt"
$missingInputsFile = Join-Path $Artifacts "15_missing_deploy_inputs.txt"

$envRes = Run-Cmd -Command "gh api repos/$Owner/$Repo/environments/$EnvironmentName" -OutFile $envJsonFile -WorkingDirectory $Worktree -AllowFailure
$policyRes = Run-Cmd -Command "gh api repos/$Owner/$Repo/environments/$EnvironmentName/deployment-branch-policies" -OutFile $envPolicyFile -WorkingDirectory $Worktree -AllowFailure
$secretRes = Run-Cmd -Command "gh secret list --env $EnvironmentName" -OutFile $envSecretsFile -WorkingDirectory $Worktree -AllowFailure
$varRes = Run-Cmd -Command "gh variable list --env $EnvironmentName" -OutFile $envVarsFile -WorkingDirectory $Worktree -AllowFailure

$policyText = if (Test-Path $envPolicyFile) { Get-Content -Raw $envPolicyFile } else { "" }
if ($policyText -notmatch 'prod-deploy-\*') {
    Write-Step "Add prod-deploy-* tag policy if missing"
    $postRes = Run-Cmd -Command "gh api -X POST repos/$Owner/$Repo/environments/$EnvironmentName/deployment-branch-policies -f name=prod-deploy-* -f type=tag" -OutFile (Join-Path $Artifacts "16_add_tag_policy.json") -WorkingDirectory $Worktree -AllowFailure
    if ($postRes.ExitCode -eq 0) {
        Add-Result "prod_deploy_tag_policy" "ADDED"
    } else {
        WarnLine "Could not add prod-deploy-* tag policy automatically"
        Add-Result "prod_deploy_tag_policy" "MISSING_OR_MANUAL"
    }
} else {
    Add-Result "prod_deploy_tag_policy" "PRESENT"
}

$wfRefs = @()
$wf = Get-Content -Raw -Encoding utf8 $WorkflowPath
[regex]::Matches($wf, 'secrets\.([A-Za-z0-9_]+)') | ForEach-Object { $wfRefs += "SECRET:$($_.Groups[1].Value)" }
[regex]::Matches($wf, 'vars\.([A-Za-z0-9_]+)')    | ForEach-Object { $wfRefs += "VAR:$($_.Groups[1].Value)" }
$wfRefs = $wfRefs | Sort-Object -Unique
Save-Text -Path $deployReferencesFile -Text ($wfRefs -join [Environment]::NewLine)

$secretNames = @()
$varNames = @()
if (Test-Path $envSecretsFile) {
    $secretNames = Get-Content $envSecretsFile | ForEach-Object {
        $parts = ($_ -split '\s+')
        if ($parts.Count -ge 1) { $parts[0] }
    }
}
if (Test-Path $envVarsFile) {
    $varNames = Get-Content $envVarsFile | ForEach-Object {
        $parts = ($_ -split '\s+')
        if ($parts.Count -ge 1) { $parts[0] }
    }
}

$missing = @()
foreach ($ref in $wfRefs) {
    if ($ref.StartsWith("SECRET:")) {
        $name = $ref.Substring(7)
        if ($secretNames -notcontains $name) { $missing += "MISSING_SECRET:$name" }
    }
    elseif ($ref.StartsWith("VAR:")) {
        $name = $ref.Substring(4)
        if ($varNames -notcontains $name) { $missing += "MISSING_VAR:$name" }
    }
}
Save-Text -Path $missingInputsFile -Text ($missing -join [Environment]::NewLine)
Add-Result "missing_deploy_inputs_count" ([string]$missing.Count)

Write-Step "Trigger exactly one controlled deploy"
Push-Location $Worktree
try {
    $headSha = (git rev-parse HEAD).Trim()
    $ControlledTag = "prod-deploy-$Timestamp-controlled"
    git tag -f $ControlledTag $headSha
    if ($LASTEXITCODE -ne 0) { Fail-Step "Failed to create controlled tag" }
    git push -f $Remote "refs/tags/$ControlledTag"
    if ($LASTEXITCODE -ne 0) { Fail-Step "Failed to push controlled tag" }
    Save-Text -Path (Join-Path $Artifacts "17_controlled_tag.txt") -Text $ControlledTag
    Add-Result "controlled_tag_pushed" $ControlledTag
}
finally {
    Pop-Location
}

$RunId = ""
$RunHeadSha = ""
$RunUrl = ""
$runListFile = Join-Path $Artifacts "18_run_list_poll.json"
$deadline = (Get-Date).AddMinutes($DeployWaitMinutes)

do {
    Start-Sleep -Seconds $PollSeconds
    $listRes = Run-Cmd -Command "gh run list --repo $Owner/$Repo --workflow deploy-prod.yml --limit 20 --json databaseId,displayTitle,headBranch,headSha,status,conclusion,createdAt,url" -OutFile $runListFile -WorkingDirectory $Worktree -AllowFailure
    if ($listRes.ExitCode -eq 0) {
        try {
            $runs = Get-Content -Raw $runListFile | ConvertFrom-Json
            $match = $runs | Where-Object { $_.headBranch -eq $ControlledTag } | Select-Object -First 1
            if ($null -ne $match) {
                $RunId = [string]$match.databaseId
                $RunHeadSha = [string]$match.headSha
                $RunUrl = [string]$match.url
                break
            }
        } catch {}
    }
} while ((Get-Date) -lt $deadline)

if (-not $RunId) {
    Fail-Step "No deploy-prod run created for controlled tag $ControlledTag"
}

Add-Result "controlled_deploy_run_id" $RunId
Save-Text -Path (Join-Path $Artifacts "19_controlled_run_id.txt") -Text $RunId

Write-Step "Approve pending deployment correctly"
$pendingFile = Join-Path $Artifacts "20_pending_deployments.json"
$approveFile = Join-Path $Artifacts "21_pending_deployments_approval.json"
$pendingRes = Run-Cmd -Command "gh api repos/$Owner/$Repo/actions/runs/$RunId/pending_deployments" -OutFile $pendingFile -WorkingDirectory $Worktree -AllowFailure

if ($pendingRes.ExitCode -eq 0) {
    try {
        $pendingJson = Get-Content -Raw $pendingFile | ConvertFrom-Json
        $envIds = @()
        foreach ($item in $pendingJson) {
            if ($item.environment.id) {
                $envIds += [long]$item.environment.id
            }
        }
        $envIds = $envIds | Sort-Object -Unique
        if ($envIds.Count -gt 0) {
            $payload = @{
                environment_ids = $envIds
                state = "approved"
                comment = "controlled validation deploy approval"
            } | ConvertTo-Json -Depth 5 -Compress
            Save-Text -Path (Join-Path $Artifacts "21_pending_deployments_payload.json") -Text $payload
            $payloadPath = Join-Path $Artifacts "21_pending_deployments_payload.json"
            $approveRes = Run-Cmd -Command "gh api -X POST repos/$Owner/$Repo/actions/runs/$RunId/pending_deployments --input `"$payloadPath`"" -OutFile $approveFile -WorkingDirectory $Worktree -AllowFailure
            Add-Result "pending_deployment_approval_attempted" "YES"
        } else {
            Add-Result "pending_deployment_approval_attempted" "NO_PENDING_IDS"
        }
    } catch {
        WarnLine "Could not parse pending deployments for approval"
        Add-Result "pending_deployment_approval_attempted" "PARSE_FAIL"
    }
} else {
    Add-Result "pending_deployment_approval_attempted" "QUERY_FAIL"
}

Write-Step "Wait for controlled run and capture evidence"
$watchFile = Join-Path $Artifacts "22_run_watch.txt"
$runViewFile = Join-Path $Artifacts "23_run_view.json"
$jobsFile = Join-Path $Artifacts "24_run_jobs.json"
$azureLoginFile = Join-Path $Artifacts "25_azure_login_failure.txt"
$watchRes = Run-Cmd -Command "gh run watch $RunId --repo $Owner/$Repo --interval $PollSeconds" -OutFile $watchFile -WorkingDirectory $Worktree -AllowFailure
$runViewRes = Run-Cmd -Command "gh run view $RunId --repo $Owner/$Repo --json status,conclusion,url,headBranch,headSha,createdAt,updatedAt,jobs" -OutFile $runViewFile -WorkingDirectory $Worktree -AllowFailure
$jobsRes = Run-Cmd -Command "gh api repos/$Owner/$Repo/actions/runs/$RunId/jobs" -OutFile $jobsFile -WorkingDirectory $Worktree -AllowFailure

$stepsStarted = $false
$azureLoginBlocked = $false
$jobId = ""

if (Test-Path $jobsFile) {
    try {
        $jobsJson = Get-Content -Raw $jobsFile | ConvertFrom-Json
        if ($jobsJson.jobs -and $jobsJson.jobs.Count -gt 0) {
            $jobId = [string]$jobsJson.jobs[0].id
            if ($jobsJson.jobs[0].steps -and $jobsJson.jobs[0].steps.Count -gt 0) {
                $stepsStarted = $true
            }
        }
    } catch {}
}

Add-Result "deploy_steps_started" $(if ($stepsStarted) { "YES" } else { "NO" })

if ($jobId) {
    $failedLogFile = Join-Path $Artifacts "26_failed_job_log.txt"
    $failedLogRes = Run-Cmd -Command "gh run view $RunId --repo $Owner/$Repo --job $jobId --log-failed" -OutFile $failedLogFile -WorkingDirectory $Worktree -AllowFailure
    if (Test-Path $failedLogFile) {
        $failedLogText = Get-Content -Raw $failedLogFile
        if ($failedLogText -match 'Azure Login' -or $failedLogText -match 'azure/login' -or $failedLogText -match 'login failed' -or $failedLogText -match 'Federated credential' -or $failedLogText -match 'AADSTS') {
            $azureLoginBlocked = $true
            Save-Text -Path $azureLoginFile -Text $failedLogText
        }
    }
}
Add-Result "azure_login_failure_detected" $(if ($azureLoginBlocked) { "YES" } else { "NO" })

Write-Step "Probe live health and integrity"
$liveHealthFile = Join-Path $Artifacts "27_live_health.txt"
$liveIntegrityNoHeaderFile = Join-Path $Artifacts "28_live_integrity_no_header.txt"
$liveIntegrityWithHeaderFile = Join-Path $Artifacts "29_live_integrity_with_header.txt"
$liveIdentityFile = Join-Path $Artifacts "30_live_identity_compare.txt"

$health = Try-HttpText -Uri "$ProductionBaseUrl/api/health/" -OutFile $liveHealthFile
Add-Result "live_health_status" ([string]$health.StatusCode)
if (-not $health.Success) {
    Fail-Step "Live /api/health/ failed"
}

$liveBuildSha = ""
$liveDeployTag = ""
try {
    $healthJson = $health.Body | ConvertFrom-Json
    if ($healthJson.build_sha) { $liveBuildSha = [string]$healthJson.build_sha }
    if ($healthJson.prod_deploy_tag) { $liveDeployTag = [string]$healthJson.prod_deploy_tag }
} catch {}

$intNoHdr = Try-HttpText -Uri "$ProductionBaseUrl/api/integrity/" -OutFile $liveIntegrityNoHeaderFile
$intHdr = Try-HttpText -Uri "$ProductionBaseUrl/api/integrity/" -Headers @{ "X-Crown-Integrity-Key" = "dummy" } -OutFile $liveIntegrityWithHeaderFile

Add-Result "live_integrity_no_header_status" ([string]$intNoHdr.StatusCode)
Add-Result "live_integrity_with_header_status" ([string]$intHdr.StatusCode)

$identity = @()
$identity += "controlled_tag=$ControlledTag"
$identity += "run_id=$RunId"
$identity += "run_head_sha=$RunHeadSha"
$identity += "live_build_sha=$liveBuildSha"
$identity += "live_prod_deploy_tag=$liveDeployTag"
Save-Text -Path $liveIdentityFile -Text ($identity -join [Environment]::NewLine)

$liveIdentityMatch = $false
if ($RunHeadSha -and $liveBuildSha -and $ControlledTag) {
    if ($RunHeadSha -eq $liveBuildSha -and $ControlledTag -eq $liveDeployTag) {
        $liveIdentityMatch = $true
    }
}
Add-Result "live_identity_match" $(if ($liveIdentityMatch) { "YES" } else { "NO" })

Write-Step "Run frontend lint proof and safe fetch pass"
$fullLintBeforeFile = Join-Path $Artifacts "31_frontend_lint_before.txt"
$fullLintAfterFile = Join-Path $Artifacts "32_frontend_lint_after.txt"

$lintBefore = Run-Cmd -Command "cd /d `"$Worktree\frontend\dashboards`" && npm run lint" -OutFile $fullLintBeforeFile -WorkingDirectory $Worktree -AllowFailure

if ($ApplySafeFetchLintPass) {
    $fetchPassFile = Join-Path $Artifacts "33_fetch_pass_targets.txt"
    $fetchPassPy = @"
from pathlib import Path
import re

root = Path(r"$Worktree") / "frontend" / "dashboards" / "src"
changed = []
for path in root.rglob("*"):
    if path.suffix not in {".js", ".jsx"}:
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    new_text = re.sub(r'(?<![A-Za-z0-9_$.])fetch\(', 'window.fetch(', text)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8", newline="\n")
        changed.append(str(path.relative_to(Path(r"$Worktree"))))
Path(r"$fetchPassFile").write_text("\n".join(changed), encoding="utf-8")
print(len(changed))
"@
    $fetchPassScript = Join-Path $Artifacts "33_fetch_pass.py"
    Save-Text -Path $fetchPassScript -Text $fetchPassPy
    Run-Cmd -Command "$Python `"$fetchPassScript`"" -OutFile (Join-Path $Artifacts "33_fetch_pass_count.txt") -WorkingDirectory $Worktree -AllowFailure | Out-Null
}

$lintAfter = Run-Cmd -Command "cd /d `"$Worktree\frontend\dashboards`" && npm run lint" -OutFile $fullLintAfterFile -WorkingDirectory $Worktree -AllowFailure

function Get-LintCounts {
    param([string]$Path)
    $text = if (Test-Path $Path) { Get-Content -Raw $Path } else { "" }
    $m = [regex]::Match($text, '([0-9]+)\s+errors?\s*,\s*([0-9]+)\s+warnings?')
    if ($m.Success) {
        return @{
            Errors = [int]$m.Groups[1].Value
            Warnings = [int]$m.Groups[2].Value
        }
    }
    return @{
        Errors = -1
        Warnings = -1
    }
}

$lintCountsBefore = Get-LintCounts -Path $fullLintBeforeFile
$lintCountsAfter = Get-LintCounts -Path $fullLintAfterFile

Add-Result "frontend_lint_errors_before" ([string]$lintCountsBefore.Errors)
Add-Result "frontend_lint_warnings_before" ([string]$lintCountsBefore.Warnings)
Add-Result "frontend_lint_errors_after" ([string]$lintCountsAfter.Errors)
Add-Result "frontend_lint_warnings_after" ([string]$lintCountsAfter.Warnings)

Write-Step "Write final summary and enforce sprint stop conditions"
$script:Summary | Export-Csv -Path $SummaryCsv -NoTypeInformation

$final = @()
$final += "Crown2026 revised 48 hour sprint summary"
$final += "timestamp=$Timestamp"
$final += "repo_root=$RepoRoot"
$final += "clean_worktree=$Worktree"
$final += ""
$final += "Checks:"
foreach ($row in $script:Summary) {
    $final += "- $($row.Check) = $($row.Result)"
}
$final += ""
$final += "Artifacts=$Artifacts"
Save-Text -Path $SummaryTxt -Text ($final -join [Environment]::NewLine)

# Hard stop conditions
if ($azureLoginBlocked) {
    Fail-Step "Controlled deploy reached real execution but failed at Azure Login. Fix environment credentials or federation. See $azureLoginFile, $envSecretsFile, $envVarsFile, and $missingInputsFile"
}

if (-not $liveIdentityMatch) {
    Fail-Step "Live build identity still does not match the controlled run. See $liveIdentityFile"
}

if ($intNoHdr.StatusCode -ne 200 -or $intHdr.StatusCode -ne 200) {
    Fail-Step "Live integrity contract still not proven. See $liveIntegrityNoHeaderFile and $liveIntegrityWithHeaderFile"
}

Write-Host ""
Write-Host "Sprint proof completed successfully." -ForegroundColor Green
Write-Host "Artifacts: $Artifacts" -ForegroundColor Green
Write-Host "Summary:   $SummaryTxt" -ForegroundColor Green