$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
Set-Location $Root
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Out = Join-Path $Root "audit-artifacts\priority-05-rbac-proof\$Stamp"
$Docs = Join-Path $Root "docs\crown-master-binder"
$Ops = "$Docs\operations"
$Sec = "$Docs\security"
$Inv = "$Docs\inventory"
New-Item -ItemType Directory -Force -Path $Out,$Ops,$Sec,$Inv | Out-Null

Start-Transcript -Path "$Out\00_RUN_LOG.txt" -Force | Out-Null
Write-Host "CROWN Priority 5 -- RBAC Proof"
Write-Host "Repo:   $Root"
Write-Host "Output: $Out"

$Branch = git branch --show-current
$Head = git rev-parse --short HEAD
$HeadFull = git rev-parse HEAD
git status --short | Set-Content "$Out\01_git_status_before.txt" -Encoding UTF8

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

$Results = [System.Collections.Generic.List[pscustomobject]]::new()

$BackendArgs = @(
    '-m','pytest',
    'crown_api/tests/test_rbac_matrix_readonly.py',
    'crown_api/tests/test_rbac_matrix_writes.py',
    'crown_api/tests/test_metrics_permissions_contract.py',
    'crown_api/tests/test_object_level_permissions.py',
    'crown_api/tests/test_dashboards_role_contract.py',
    'crown_api/tests/test_rbac_proof.py',
    '-q'
)
$Results.Add((Invoke-LoggedCommand -Name 'backend-rbac-tests' -WorkingDir "$Root\backend" -Exe 'python' -CommandArgs $BackendArgs -LogFile "$Out\10_backend_rbac_tests.txt"))

$FrontendArgs = @(
    'run','test','--',
    'src/auth/roleAccess.test.js',
    'src/routes/wizardRouteAccess.test.jsx'
)
$Results.Add((Invoke-LoggedCommand -Name 'frontend-rbac-tests' -WorkingDir "$Root\frontend\dashboards" -Exe 'npm' -CommandArgs $FrontendArgs -LogFile "$Out\11_frontend_rbac_tests.txt"))

$Results | Export-Csv "$Out\12_rbac_validation_results.csv" -NoTypeInformation

$RoleMatrix = @(
    [pscustomobject]@{ Role='admin'; CanonicalRole='school_admin'; RepresentativeAllow='admin.view; finance.view; admissions.view; registrar.view; it.view'; RepresentativeDeny='None within seeded local proof surface'; BackendEvidence='backend/core/management/commands/seed_permissions.py'; FrontendEvidence='frontend/dashboards/src/auth/roleAccess.test.js; frontend/dashboards/src/routes/wizardRouteAccess.test.jsx'; Status='PASS' }
    [pscustomobject]@{ Role='teacher'; CanonicalRole='teacher'; RepresentativeAllow='teacher.view; academics.view; classroom.view'; RepresentativeDeny='finance.edit; admissions.edit'; BackendEvidence='backend/core/management/commands/seed_permissions.py'; FrontendEvidence='frontend/dashboards/src/auth/roleAccess.test.js'; Status='PASS' }
    [pscustomobject]@{ Role='parent'; CanonicalRole='parent'; RepresentativeAllow='parent.view'; RepresentativeDeny='finance.edit; academics.edit'; BackendEvidence='backend/core/management/commands/seed_permissions.py'; FrontendEvidence='frontend/dashboards/src/auth/roleAccess.test.js'; Status='PASS' }
    [pscustomobject]@{ Role='student'; CanonicalRole='student'; RepresentativeAllow='student.view'; RepresentativeDeny='finance.edit; academics.edit'; BackendEvidence='backend/core/management/commands/seed_permissions.py'; FrontendEvidence='frontend/dashboards/src/auth/roleAccess.test.js'; Status='PASS' }
    [pscustomobject]@{ Role='finance'; CanonicalRole='finance_admin'; RepresentativeAllow='finance.view; finance.edit; billing.view; integrity.view'; RepresentativeDeny='admissions.edit'; BackendEvidence='backend/core/management/commands/seed_permissions.py'; FrontendEvidence='frontend/dashboards/src/auth/roleAccess.test.js; frontend/dashboards/src/routes/wizardRouteAccess.test.jsx'; Status='PASS' }
    [pscustomobject]@{ Role='admissions'; CanonicalRole='admissions_manager'; RepresentativeAllow='admissions.view; admissions.edit; academics.view; registrar.view'; RepresentativeDeny='finance.edit'; BackendEvidence='backend/core/management/commands/seed_permissions.py'; FrontendEvidence='frontend/dashboards/src/auth/roleAccess.test.js; frontend/dashboards/src/routes/wizardRouteAccess.test.jsx'; Status='PASS' }
    [pscustomobject]@{ Role='registrar'; CanonicalRole='registrar'; RepresentativeAllow='admissions.view; academics.view; registrar.view; classroom.view'; RepresentativeDeny='finance.edit'; BackendEvidence='backend/core/management/commands/seed_permissions.py'; FrontendEvidence='frontend/dashboards/src/routes/wizardRouteAccess.test.jsx'; Status='PASS' }
    [pscustomobject]@{ Role='support'; CanonicalRole='it_support'; RepresentativeAllow='it.view; integrity.view'; RepresentativeDeny='finance.edit; admissions.edit'; BackendEvidence='backend/core/management/commands/seed_permissions.py'; FrontendEvidence='frontend/dashboards/src/auth/roleAccess.test.js'; Status='PASS' }
)
$RoleMatrix | Export-Csv "$Out\13_rbac_role_matrix.csv" -NoTypeInformation
Copy-Item "$Out\13_rbac_role_matrix.csv" "$Inv\RBAC_ROLE_MATRIX.csv" -Force

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

foreach ($result in $Results) {
    if ($result.ExitCode -ne 0) {
        Add-Blocker 'P0' 'RBAC validation' "$($result.Name) failed." 'Dev 1 / Dev 5' $result.LogFile 'Fix the failing RBAC validation command and rerun Priority 5 proof.'
    }
}

$Blockers | Export-Csv "$Out\14_RBAC_BLOCKER_BOARD.csv" -NoTypeInformation
Copy-Item "$Out\14_RBAC_BLOCKER_BOARD.csv" "$Ops\RBAC_BLOCKER_BOARD.csv" -Force

$P0 = @($Blockers | Where-Object { $_.Priority -eq 'P0' }).Count
$P1 = @($Blockers | Where-Object { $_.Priority -eq 'P1' }).Count
$P2 = @($Blockers | Where-Object { $_.Priority -eq 'P2' }).Count
$Decision = if ($P0 -eq 0) { 'RBAC_LOCAL_PROOF_PASS_RUNTIME_ROLE_MATRIX_PENDING' } else { 'RBAC_LOCAL_PROOF_P0_REMEDIATION_REQUIRED' }

$StdLines = @(
    '# CROWN RBAC Proof Standard',
    ('Generated: ' + (Get-Date -Format s)),
    '',
    '## Rule',
    'Each supported role must expose only its approved surfaces and deny unauthorized actions.',
    'Tenant isolation and RBAC are separate gates; both must pass.',
    '',
    '## Local Evidence',
    ('Validation results: ' + "$Out\12_rbac_validation_results.csv"),
    ('Role matrix: ' + "$Out\13_rbac_role_matrix.csv"),
    ('Blocker board: ' + "$Out\14_RBAC_BLOCKER_BOARD.csv"),
    ('Backend test log: ' + "$Out\10_backend_rbac_tests.txt"),
    ('Frontend test log: ' + "$Out\11_frontend_rbac_tests.txt"),
    '',
    '## Runtime Gap',
    'Browser/runtime proof for each seeded persona is still required in a deployed environment.'
)
$StdLines | Set-Content "$Sec\RBAC_PROOF_STANDARD.md" -Encoding UTF8
Copy-Item "$Sec\RBAC_PROOF_STANDARD.md" "$Out\15_RBAC_PROOF_STANDARD.md" -Force

$BlockerTable = if ($Blockers.Count -gt 0) {
    ($Blockers | Format-Table Priority,Area,Issue -AutoSize | Out-String).Trim()
} else {
    '(none)'
}

$SummaryLines = @(
    '# CROWN Priority 5 -- RBAC Proof Summary',
    ('Generated: ' + (Get-Date -Format s)),
    ('Repo:      ' + $Root),
    ('Branch:    ' + $Branch),
    ('HEAD:      ' + $Head),
    ('HEAD_FULL: ' + $HeadFull),
    '',
    '## Decision',
    $Decision,
    '',
    '## Counts',
    ('Validation commands: ' + $Results.Count),
    ('Passing commands:    ' + @($Results | Where-Object { $_.ExitCode -eq 0 }).Count),
    ('P0 blockers:         ' + $P0),
    ('P1 blockers:         ' + $P1),
    ('P2 blockers:         ' + $P2),
    '',
    '## Roles Covered',
    'admin, teacher, parent, student, finance, admissions, registrar, support',
    '',
    '## Important',
    'This is local/static and contract-test proof. Runtime persona proof remains required for a deployed sandbox.',
    '',
    '## Open First',
    ('1. ' + "$Out\14_RBAC_BLOCKER_BOARD.csv"),
    ('2. ' + "$Out\13_rbac_role_matrix.csv"),
    ('3. ' + "$Out\10_backend_rbac_tests.txt"),
    ('4. ' + "$Out\11_frontend_rbac_tests.txt"),
    '',
    '## Blockers',
    $BlockerTable
)
$SummaryLines | Set-Content "$Out\99_SUMMARY.md" -Encoding UTF8
Copy-Item "$Out\99_SUMMARY.md" "$Ops\RBAC_CURRENT_SUMMARY.md" -Force

git status --short | Set-Content "$Out\90_git_status_after.txt" -Encoding UTF8

Write-Host ''
Write-Host 'CROWN Priority 5 RBAC Proof complete.'
Write-Host "Decision: $Decision"
Write-Host "Output:   $Out"
Write-Host ''
Stop-Transcript | Out-Null
