$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
Set-Location $Root

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Out = Join-Path $Root "audit-artifacts\priority-10-release-packet\$Stamp"
$Docs = Join-Path $Root "docs\crown-master-binder"
$Ops = Join-Path $Docs "operations"
$Checklist = Join-Path $Ops "10_FINAL_RELEASE_ACCEPTANCE_CHECKLIST.csv"

New-Item -ItemType Directory -Force -Path $Out,$Ops | Out-Null
Start-Transcript -Path (Join-Path $Out "00_RUN_LOG.txt") -Force | Out-Null

Write-Host "CROWN Priority 10 release packet"
Write-Host "Repo:   $Root"
Write-Host "Output: $Out"

$Branch = git branch --show-current
$Head = git rev-parse --short HEAD
$HeadFull = git rev-parse HEAD

if (-not (Test-Path $Checklist)) {
    throw "Checklist not found: $Checklist"
}

$rows = Import-Csv $Checklist

$nonAzureFail = @($rows | Where-Object {
    $_.Gate -notmatch '^Azure|GitHub workflows' -and $_.Gate -ne 'Release packet' -and $_.Status -ne 'PASS'
})

$waitingAzure = @($rows | Where-Object { $_.Status -eq 'Waiting on Azure' })
$passed = @($rows | Where-Object { $_.Status -eq 'PASS' })

$decision = if ($nonAzureFail.Count -eq 0) {
    'LOCAL_RELEASE_PACKET_COMPLETE_AZURE_PENDING'
} else {
    'LOCAL_RELEASE_PACKET_REMEDIATION_REQUIRED'
}

$artifactIndex = foreach ($r in $rows) {
    [pscustomobject]@{
        Gate = $r.Gate
        Status = $r.Status
        Evidence = $r.Evidence
    }
}
$artifactIndex | Export-Csv (Join-Path $Out '10_release_artifact_index.csv') -NoTypeInformation

$summary = @(
    '# CROWN Priority 10 - Release Packet Summary',
    ('Generated: ' + (Get-Date -Format s)),
    ('Repo:      ' + $Root),
    ('Branch:    ' + $Branch),
    ('HEAD:      ' + $Head),
    ('HEAD_FULL: ' + $HeadFull),
    '',
    '## Decision',
    $decision,
    '',
    '## Gate Counts',
    ('PASS: ' + $passed.Count),
    ('Waiting on Azure: ' + $waitingAzure.Count),
    ('Non-Azure open/fail: ' + $nonAzureFail.Count),
    '',
    '## Key References',
    ('1. ' + $Checklist),
    ('2. ' + (Join-Path $Out '10_release_artifact_index.csv')),
    ('3. ' + (Join-Path $Ops 'HYGIENE_CURRENT_SUMMARY.md')),
    ('4. ' + (Join-Path $Ops 'TENANT_ISOLATION_CURRENT_SUMMARY.md')),
    ('5. ' + (Join-Path $Ops 'RBAC_CURRENT_SUMMARY.md')),
    ('6. ' + (Join-Path $Ops 'SANDBOX_LOGIN_CURRENT_SUMMARY.md'))
)

$summaryPath = Join-Path $Out '99_SUMMARY.md'
$summary | Set-Content $summaryPath -Encoding UTF8
Copy-Item $summaryPath (Join-Path $Ops 'RELEASE_PACKET_CURRENT_SUMMARY.md') -Force

if ($decision -eq 'LOCAL_RELEASE_PACKET_COMPLETE_AZURE_PENDING') {
    foreach ($row in $rows) {
        if ($row.Gate -eq 'Release packet') {
            $row.Status = 'PASS'
            $row.Evidence = $summaryPath
        }
    }
    $rows | Export-Csv $Checklist -NoTypeInformation
}

Write-Host ''
Write-Host 'CROWN Priority 10 release packet complete.'
Write-Host "Decision: $decision"
Write-Host "Output:   $Out"
Write-Host ''
Stop-Transcript | Out-Null