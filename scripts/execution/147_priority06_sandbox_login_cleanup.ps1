$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
Set-Location $Root
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Out = Join-Path $Root "audit-artifacts\priority-06-sandbox-login\$Stamp"
$Docs = Join-Path $Root "docs\crown-master-binder"
$Ops = "$Docs\operations"
New-Item -ItemType Directory -Force -Path $Out,$Ops | Out-Null

Start-Transcript -Path "$Out\00_RUN_LOG.txt" -Force | Out-Null
Write-Host "CROWN Priority 6 -- Sandbox Login Cleanup"
Write-Host "Repo:   $Root"
Write-Host "Output: $Out"

$Branch = git branch --show-current
$Head = git rev-parse --short HEAD
$HeadFull = git rev-parse HEAD

function Invoke-LoggedCommand {
    param(
        [string]$Name,
        [string]$WorkingDir,
        [string]$Exe,
        [string[]]$CommandArgs,
        [string]$LogFile
    )

    Write-Host "Running: $Name"
    Write-Host "  Dir: $WorkingDir"
    Write-Host "  Cmd: $Exe $($CommandArgs -join ' ')"

    $exitCode = 0
    Push-Location $WorkingDir
    try {
        & $Exe @CommandArgs 2>&1 | Tee-Object -FilePath $LogFile | Out-Host
        $exitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }

    return [pscustomobject]@{
        Name = $Name
        WorkingDir = $WorkingDir
        Command = "$Exe $($CommandArgs -join ' ')"
        LogFile = $LogFile
        ExitCode = $exitCode
        Status = if ($exitCode -eq 0) { 'PASS' } else { 'FAIL' }
    }
}

$LoginPagePath = Join-Path $Root 'frontend\dashboards\src\pages\LoginPage.jsx'
$LoginSource = Get-Content $LoginPagePath -Raw
$StaticChecks = @(
    [pscustomobject]@{ Check='Sandbox heading present'; Requirement='Sandbox Environment'; Status= if ($LoginSource -match 'Sandbox Environment') { 'PASS' } else { 'FAIL' } }
    [pscustomobject]@{ Check='Sandbox credential fill control present'; Requirement='Use Sandbox Credentials'; Status= if ($LoginSource -match 'Use Sandbox Credentials') { 'PASS' } else { 'FAIL' } }
    [pscustomobject]@{ Check='Real-school warning present'; Requirement='Use demo data only. Do not enter real school records.'; Status= if ($LoginSource -match 'Use demo data only\. Do not enter real school records\.') { 'PASS' } else { 'FAIL' } }
    [pscustomobject]@{ Check='Dev JWT fallback hidden'; Requirement='No Dev JWT Login surface'; Status= if ($LoginSource -match 'Dev JWT Login') { 'FAIL' } else { 'PASS' } }
    [pscustomobject]@{ Check='Offline fallback hidden'; Requirement='No Offline / Fallback surface'; Status= if ($LoginSource -match 'Offline / Fallback') { 'FAIL' } else { 'PASS' } }
)
$StaticChecks | Export-Csv "$Out\10_static_login_checks.csv" -NoTypeInformation

$TestArgs = @('run','test','--','src/tests/loginPagePolish.test.jsx')
$TestResult = Invoke-LoggedCommand -Name 'frontend-login-polish-test' -WorkingDir "$Root\frontend\dashboards" -Exe 'npm' -CommandArgs $TestArgs -LogFile "$Out\11_login_polish_test.txt"
$TestResult | Export-Csv "$Out\12_validation_results.csv" -NoTypeInformation

$Blockers = [System.Collections.Generic.List[pscustomobject]]::new()
function Add-Blocker([string]$Priority,[string]$Area,[string]$Issue,[string]$Owner,[string]$Evidence,[string]$RequiredFix) {
    $script:Blockers.Add([pscustomobject]@{
        Priority = $Priority
        Area = $Area
        Issue = $Issue
        Owner = $Owner
        Evidence = $Evidence
        RequiredFix = $RequiredFix
        Status = 'Open'
    })
}

if ($TestResult.ExitCode -ne 0) {
    Add-Blocker 'P0' 'Sandbox login' 'loginPagePolish test failed.' 'Dev 4 / Dev 5' $TestResult.LogFile 'Fix the failing sandbox login behavior and rerun Priority 6 proof.'
}

foreach ($check in $StaticChecks) {
    if ($check.Status -ne 'PASS') {
        Add-Blocker 'P0' 'Sandbox login' ("Static check failed: " + $check.Check) 'Dev 4 / Dev 5' "$Out\10_static_login_checks.csv" 'Correct the login surface so sandbox-only controls and warnings are accurate.'
    }
}

$Blockers | Export-Csv "$Out\13_SANDBOX_LOGIN_BLOCKER_BOARD.csv" -NoTypeInformation
Copy-Item "$Out\13_SANDBOX_LOGIN_BLOCKER_BOARD.csv" "$Ops\SANDBOX_LOGIN_BLOCKER_BOARD.csv" -Force

$P0 = @($Blockers | Where-Object { $_.Priority -eq 'P0' }).Count
$Decision = if ($P0 -eq 0) { 'SANDBOX_LOGIN_LOCAL_PROOF_PASS' } else { 'SANDBOX_LOGIN_P0_REMEDIATION_REQUIRED' }

$SummaryLines = @(
    '# CROWN Priority 6 -- Sandbox Login Cleanup Summary',
    ('Generated: ' + (Get-Date -Format s)),
    ('Repo:      ' + $Root),
    ('Branch:    ' + $Branch),
    ('HEAD:      ' + $Head),
    ('HEAD_FULL: ' + $HeadFull),
    '',
    '## Decision',
    $Decision,
    '',
    '## Checks',
    ('Static login checks: ' + $StaticChecks.Count),
    ('Frontend login test exit code: ' + $TestResult.ExitCode),
    ('P0 blockers: ' + $P0),
    '',
    '## Evidence',
    ('1. ' + "$Out\10_static_login_checks.csv"),
    ('2. ' + "$Out\11_login_polish_test.txt"),
    ('3. ' + "$Out\12_validation_results.csv"),
    ('4. ' + "$Out\13_SANDBOX_LOGIN_BLOCKER_BOARD.csv")
)
$SummaryLines | Set-Content "$Out\99_SUMMARY.md" -Encoding UTF8
Copy-Item "$Out\99_SUMMARY.md" "$Ops\SANDBOX_LOGIN_CURRENT_SUMMARY.md" -Force

Write-Host ''
Write-Host 'CROWN Priority 6 Sandbox Login Cleanup complete.'
Write-Host "Decision: $Decision"
Write-Host "Output:   $Out"
Write-Host ''
Stop-Transcript | Out-Null
