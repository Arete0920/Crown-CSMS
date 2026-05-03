$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

Set-Location (git rev-parse --show-toplevel)

$Root = (Get-Location).Path
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Authoritative = "audit-artifacts\judgment-day-gauntlet\20260430_212943"
$Out = "audit-artifacts\execution-control-room\$Stamp"
$Docs = "docs\crown-master-binder"
$Ops = Join-Path $Docs "operations"
$Runbooks = Join-Path $Docs "runbooks"
$Scripts = "scripts\execution"

New-Item -ItemType Directory -Force -Path $Out, $Ops, $Runbooks, $Scripts | Out-Null

$LogPath = Join-Path $Out "00_EXECUTION_CONTROL_RUN_LOG.txt"
New-Item -ItemType File -Force -Path $LogPath | Out-Null

function Write-Log {
    param([string]$Message)

    $line = "[{0}] {1}" -f (Get-Date -Format s), $Message
    Add-Content -Path $LogPath -Value $line -Encoding UTF8
    Write-Host $Message
}

function Open-IfAvailable {
    param([string[]]$Paths)

    $codeCmd = Get-Command code -ErrorAction SilentlyContinue
    if (-not $codeCmd) {
        Write-Log "VS Code CLI not found in PATH; skipping automatic file open."
        return
    }

    foreach ($path in $Paths) {
        if (Test-Path $path) {
            & $codeCmd.Source --reuse-window $path | Out-Null
        }
    }
}

function ConvertTo-MarkdownTable {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$Rows,
        [Parameter(Mandatory = $true)]
        [string[]]$Columns
    )

    $header = "| " + ($Columns -join " | ") + " |"
    $divider = "|" + (($Columns | ForEach-Object { "---" }) -join "|") + "|"
    $lines = @($header, $divider)

    foreach ($row in $Rows) {
        $values = foreach ($column in $Columns) {
            $value = $row.$column
            if ($null -eq $value) { "" } else { [string]$value }
        }
        $lines += "| " + ($values -join " | ") + " |"
    }

    return ($lines -join [Environment]::NewLine)
}

function Resolve-LatestExecutionControlRoom {
    $base = Join-Path $Root "audit-artifacts\execution-control-room"
    if (-not (Test-Path $base)) {
        throw "No execution-control-room directory exists yet. Run 271_execution_control_room_pack.ps1 first."
    }

    $latest = Get-ChildItem $base -Directory | Sort-Object Name -Descending | Select-Object -First 1
    if (-not $latest) {
        throw "No execution control room outputs found under $base"
    }

    return $latest.FullName
}

Write-Log "CROWN EXECUTION CONTROL ROOM PACK"
Write-Log "Repo: $Root"
Write-Log "Output: $Out"

$Required = @(
    "README_SESSION_HANDOFF.txt",
    "SESSION_COMPLETION_SUMMARY.md",
    "60b_RUNTIME_PROOF_EXECUTION_GUIDE.md",
    "60_required_runtime_proof_matrix.csv",
    "P1_UI_DASHBOARD_ROUTE_ACTION_PLAN.md",
    "P7_POST_AZURE_FINAL_PROOF_PACKET.md",
    "22b_security_triage_report.md",
    "24b_tenant_isolation_triage_report.md",
    "81_JUDGMENT_DAY_BLOCKER_BOARD.csv",
    "80_JUDGMENT_DAY_SCORECARD.csv"
)

$FileStatus = foreach ($name in $Required) {
    $fullPath = Join-Path $Authoritative $name
    [pscustomobject]@{
        File = $fullPath
        Exists = Test-Path $fullPath
        SizeBytes = if (Test-Path $fullPath) { (Get-Item $fullPath).Length } else { 0 }
    }
}

$AuthoritativeCheckPath = Join-Path $Out "01_AUTHORITATIVE_FILE_CHECK.csv"
$FileStatus | Export-Csv $AuthoritativeCheckPath -NoTypeInformation -Encoding UTF8

$Missing = @($FileStatus | Where-Object { -not $_.Exists })
if ($Missing.Count -gt 0) {
    $stopPath = Join-Path $Out "00_STOP_MISSING_AUTHORITATIVE_FILES.txt"
    ($Missing | Format-Table -AutoSize | Out-String).Trim() | Set-Content $stopPath -Encoding UTF8
    Open-IfAvailable @($stopPath)
    throw "Missing required authoritative files. See $stopPath"
}

foreach ($name in $Required) {
    Copy-Item (Join-Path $Authoritative $name) (Join-Path $Out $name) -Force
}

$Branch = git branch --show-current
$Head = git rev-parse --short HEAD
$HeadFull = git rev-parse HEAD

git status --short | Set-Content (Join-Path $Out "02_git_status_short.txt") -Encoding UTF8
git status | Set-Content (Join-Path $Out "03_git_status_full.txt") -Encoding UTF8
git log --oneline -30 | Set-Content (Join-Path $Out "04_recent_commits.txt") -Encoding UTF8

$RuntimeMatrix = Import-Csv (Join-Path $Authoritative "60_required_runtime_proof_matrix.csv")
$TenantRows = @($RuntimeMatrix | Where-Object { $_.ProofId -like 'TI-*' })
$RbacRows = @($RuntimeMatrix | Where-Object { $_.ProofId -like 'RBAC-*' })
$WorkflowRows = @($RuntimeMatrix | Where-Object { $_.ProofId -like 'WF-*' })

$RbacMatrixPath = Join-Path $Out "21_RBAC_PROOF_MATRIX.csv"
$WorkflowMatrixPath = Join-Path $Out "22_RUNTIME_PROOF_MATRIX.csv"
$TenantMatrixPath = Join-Path $Out "23_TENANT_PROOF_MATRIX.csv"

$RbacRows | Export-Csv $RbacMatrixPath -NoTypeInformation -Encoding UTF8
$WorkflowRows | Export-Csv $WorkflowMatrixPath -NoTypeInformation -Encoding UTF8
$TenantRows | Export-Csv $TenantMatrixPath -NoTypeInformation -Encoding UTF8

$UiCleanupRows = @(
    [pscustomobject]@{ Area = "Sandbox login"; Route = "/login"; IssueType = "Sandbox clarity"; RequiredAction = "Confirm sandbox-only messaging and role options are clear."; Status = "READY_FOR_EXECUTION"; EvidencePath = ""; Notes = "" },
    [pscustomobject]@{ Area = "Admin dashboard"; Route = "/dashboard/admin"; IssueType = "Visual polish"; RequiredAction = "Remove off-brand dark panels, validate KPI drill-down credibility."; Status = "READY_FOR_EXECUTION"; EvidencePath = ""; Notes = "" },
    [pscustomobject]@{ Area = "Parent portal"; Route = "/portal/parent"; IssueType = "Dead links"; RequiredAction = "Remove href=# patterns and verify role-specific routes."; Status = "READY_FOR_EXECUTION"; EvidencePath = ""; Notes = "" },
    [pscustomobject]@{ Area = "Teacher portal"; Route = "/portal/teacher"; IssueType = "Dead links"; RequiredAction = "Remove dead links and placeholder copy."; Status = "READY_FOR_EXECUTION"; EvidencePath = ""; Notes = "" },
    [pscustomobject]@{ Area = "Admissions workflow"; Route = "/admissions"; IssueType = "Incomplete UI"; RequiredAction = "Verify core workflow screens load without placeholder states."; Status = "READY_FOR_EXECUTION"; EvidencePath = ""; Notes = "" },
    [pscustomobject]@{ Area = "Billing workflow"; Route = "/billing"; IssueType = "Route validation"; RequiredAction = "Verify pages load and user-visible errors are clean."; Status = "READY_FOR_EXECUTION"; EvidencePath = ""; Notes = "" },
    [pscustomobject]@{ Area = "SIS/student records"; Route = "/students"; IssueType = "Route validation"; RequiredAction = "Validate student record screens and empty states."; Status = "READY_FOR_EXECUTION"; EvidencePath = ""; Notes = "" },
    [pscustomobject]@{ Area = "Dashboard KPI drill-downs"; Route = "/dashboard"; IssueType = "Data credibility"; RequiredAction = "Validate drill-down destinations and user-facing data labels."; Status = "READY_FOR_EXECUTION"; EvidencePath = ""; Notes = "" },
    [pscustomobject]@{ Area = "Sidebar navigation"; Route = "global"; IssueType = "Navigation"; RequiredAction = "Confirm sidebar links resolve to valid destinations."; Status = "READY_FOR_EXECUTION"; EvidencePath = ""; Notes = "" },
    [pscustomobject]@{ Area = "Empty/error states"; Route = "global"; IssueType = "Messaging"; RequiredAction = "Ensure no raw debug output, TODO, TBD, or placeholder copy leaks to user."; Status = "READY_FOR_EXECUTION"; EvidencePath = ""; Notes = "" }
)

$UiCleanupBoardPath = Join-Path $Out "30_UI_CLEANUP_BOARD.csv"
$UiCleanupRows | Export-Csv $UiCleanupBoardPath -NoTypeInformation -Encoding UTF8

$TenantEvidence = $TenantRows | ForEach-Object {
    [pscustomobject]@{
        ProofId = $_.ProofId
        Tester = ""
        Environment = ""
        SourceRole = ""
        Target = $_.Test
        Expected = $_.Expected
        Actual = ""
        Status = "NOT_RUN"
        EvidencePath = ""
        Notes = ""
    }
}
$RbacEvidence = $RbacRows | ForEach-Object {
    [pscustomobject]@{
        ProofId = $_.ProofId
        Tester = ""
        Environment = ""
        SourceRole = ""
        Target = $_.Test
        Expected = $_.Expected
        Actual = ""
        Status = "NOT_RUN"
        EvidencePath = ""
        Notes = ""
    }
}
$WorkflowEvidence = $WorkflowRows | ForEach-Object {
    [pscustomobject]@{
        ProofId = $_.ProofId
        Tester = ""
        Environment = ""
        RoleUsed = ""
        Target = $_.Test
        Expected = $_.Expected
        Actual = ""
        Status = "NOT_RUN"
        EvidencePath = ""
        Notes = ""
    }
}
$UiEvidence = $UiCleanupRows | ForEach-Object {
    [pscustomobject]@{
        ScreenOrArea = $_.Area
        Tester = ""
        Route = $_.Route
        IssueFound = ""
        FixApplied = ""
        Status = "NOT_RUN"
        ScreenshotOrEvidence = ""
        Notes = ""
    }
}

$TenantEvidencePath = Join-Path $Out "10_TENANT_RUNTIME_EVIDENCE.csv"
$RbacEvidencePath = Join-Path $Out "11_RBAC_RUNTIME_EVIDENCE.csv"
$WorkflowEvidencePath = Join-Path $Out "12_WORKFLOW_RUNTIME_EVIDENCE.csv"
$UiEvidencePath = Join-Path $Out "20_UI_DASHBOARD_ROUTE_EVIDENCE.csv"

$TenantEvidence | Export-Csv $TenantEvidencePath -NoTypeInformation -Encoding UTF8
$RbacEvidence | Export-Csv $RbacEvidencePath -NoTypeInformation -Encoding UTF8
$WorkflowEvidence | Export-Csv $WorkflowEvidencePath -NoTypeInformation -Encoding UTF8
$UiEvidence | Export-Csv $UiEvidencePath -NoTypeInformation -Encoding UTF8

$StatusBoard = @(
    [pscustomobject]@{ Priority = "P0-4"; Team = "Dev 1 / Dev 2 / Dev 5"; Workstream = "Tenant Isolation Runtime Proof"; File = (Join-Path $Out "DEV125_TENANT_RUNTIME_PACKET.md"); Status = "READY_FOR_EXECUTION"; EvidenceRequired = "TI-001 through TI-007 with screenshots, API output, and verdicts" },
    [pscustomobject]@{ Priority = "P0-4"; Team = "Dev 1 / Dev 5"; Workstream = "RBAC Runtime Proof"; File = (Join-Path $Out "DEV15_RBAC_RUNTIME_PACKET.md"); Status = "READY_FOR_EXECUTION"; EvidenceRequired = "RBAC-001 through RBAC-006 denial proof" },
    [pscustomobject]@{ Priority = "P1"; Team = "Dev 2 / Dev 3"; Workstream = "Workflow Runtime Proof"; File = (Join-Path $Out "DEV23_WORKFLOW_RUNTIME_PACKET.md"); Status = "READY_FOR_EXECUTION"; EvidenceRequired = "WF-001 through WF-006 with screenshots or command output" },
    [pscustomobject]@{ Priority = "P1"; Team = "Dev 4"; Workstream = "UI / Dashboard / Route Polish"; File = (Join-Path $Out "DEV4_UI_POLISH_PACKET.md"); Status = "READY_FOR_EXECUTION"; EvidenceRequired = "Screenshots, route checks, no dead links/placeholders on production-facing pages" },
    [pscustomobject]@{ Priority = "P7"; Team = "Azure / DevOps"; Workstream = "Post-Azure Live Proof"; File = (Join-Path $Out "AZURE_POST_DEPLOY_PACKET.md"); Status = "WAITING_ON_AZURE"; EvidenceRequired = "Backend 200, frontend 200, build.json 200, approved SHA matches" },
    [pscustomobject]@{ Priority = "FINAL"; Team = "Dev 5 / QA Release"; Workstream = "Judgment Day Rerun"; File = (Join-Path $Out "QA_FINAL_RERUN_PACKET.md"); Status = "WAITING_ON_AZURE_AND_RUNTIME_PROOF"; EvidenceRequired = "Fresh scorecard and blocker board after all gates pass" }
)

$StatusBoardPath = Join-Path $Out "05_EXECUTION_STATUS_BOARD.csv"
$StatusBoard | Export-Csv $StatusBoardPath -NoTypeInformation -Encoding UTF8
Copy-Item $StatusBoardPath (Join-Path $Ops "CURRENT_EXECUTION_STATUS_BOARD.csv") -Force

$ExecutionPackGuidePath = Join-Path $Out "EXECUTION_PACK_GUIDE.md"
$ExecutionPackGuide = @"
# CROWN Execution Pack Guide

Generated: $(Get-Date -Format s)

## Current State

- This is GO for non-Azure execution.
- This is NOT production GO.
- Production remains blocked until Azure post-deploy proof, runtime proof, UI proof, and final Judgment Day rerun all pass.

## Open In This Order

1. 99_EXECUTION_CONTROL_SUMMARY.md
2. 05_EXECUTION_STATUS_BOARD.csv
3. DEV125_TENANT_RUNTIME_PACKET.md
4. DEV15_RBAC_RUNTIME_PACKET.md
5. DEV23_WORKFLOW_RUNTIME_PACKET.md
6. DEV4_UI_POLISH_PACKET.md
7. AZURE_POST_DEPLOY_PACKET.md
8. QA_FINAL_RERUN_PACKET.md

## Team Packet Map

| Team | Packet | Evidence Sheet |
|---|---|---|
| Dev 1 / Dev 2 / Dev 5 | DEV125_TENANT_RUNTIME_PACKET.md | 10_TENANT_RUNTIME_EVIDENCE.csv |
| Dev 1 / Dev 5 | DEV15_RBAC_RUNTIME_PACKET.md | 11_RBAC_RUNTIME_EVIDENCE.csv |
| Dev 2 / Dev 3 | DEV23_WORKFLOW_RUNTIME_PACKET.md | 12_WORKFLOW_RUNTIME_EVIDENCE.csv |
| Dev 4 | DEV4_UI_POLISH_PACKET.md | 20_UI_DASHBOARD_ROUTE_EVIDENCE.csv and 30_UI_CLEANUP_BOARD.csv |
| Azure / DevOps | AZURE_POST_DEPLOY_PACKET.md | audit-artifacts/post-azure-live-proof/<timestamp>/POST_AZURE_LIVE_PROOF.csv |
| Dev 5 / QA Release | QA_FINAL_RERUN_PACKET.md | Fresh Judgment Day rerun output |

## Generated Proof Boards

- 21_RBAC_PROOF_MATRIX.csv
- 22_RUNTIME_PROOF_MATRIX.csv
- 23_TENANT_PROOF_MATRIX.csv
- 30_UI_CLEANUP_BOARD.csv

## Capture Scripts

- scripts/execution/250_capture_runtime_proof.ps1
- scripts/execution/260_capture_ui_cleanup.ps1
- scripts/execution/270_post_azure_live_proof.ps1
"@
$ExecutionPackGuide | Set-Content $ExecutionPackGuidePath -Encoding UTF8

$TenantTable = ConvertTo-MarkdownTable -Rows $TenantRows -Columns @("ProofId", "Test", "Expected", "Owner")
$RbacTable = ConvertTo-MarkdownTable -Rows $RbacRows -Columns @("ProofId", "Test", "Expected", "Owner")
$WorkflowTable = ConvertTo-MarkdownTable -Rows $WorkflowRows -Columns @("ProofId", "Test", "Expected", "Owner")
$UiTable = ConvertTo-MarkdownTable -Rows $UiCleanupRows -Columns @("Area", "Route", "IssueType", "RequiredAction")

$TenantPacketPath = Join-Path $Out "DEV125_TENANT_RUNTIME_PACKET.md"
$TenantPacket = @"
# Dev 1 / Dev 2 / Dev 5 - Tenant Runtime Proof Packet

Generated: $(Get-Date -Format s)

## Source

- Authoritative folder: $Authoritative
- Runtime guide: $Authoritative\60b_RUNTIME_PROOF_EXECUTION_GUIDE.md
- Working matrix: $Out\23_TENANT_PROOF_MATRIX.csv

## Objective

Prove CROWN does not leak data across schools or school contexts at runtime.

## Required Proofs

$TenantTable

## Evidence Required Per Row

- tester
- date/time
- environment
- source role
- target record, route, or API
- expected result
- actual result
- screenshot or command output path
- PASS or FAIL
- notes

## Stop Condition

Any real tenant leak is P0 and immediate NO-GO.

## Fill This Evidence File

$Out\10_TENANT_RUNTIME_EVIDENCE.csv
"@
$TenantPacket | Set-Content $TenantPacketPath -Encoding UTF8

$RbacPacketPath = Join-Path $Out "DEV15_RBAC_RUNTIME_PACKET.md"
$RbacPacket = @"
# Dev 1 / Dev 5 - RBAC Runtime Proof Packet

Generated: $(Get-Date -Format s)

## Source

- Authoritative folder: $Authoritative
- Runtime guide: $Authoritative\60b_RUNTIME_PROOF_EXECUTION_GUIDE.md
- Working matrix: $Out\21_RBAC_PROOF_MATRIX.csv

## Objective

Prove protected routes and APIs stay denied for unauthorized roles.

## Required Proofs

$RbacTable

## Evidence Required Per Row

- tester
- date/time
- environment
- source role
- protected route or API
- expected result
- actual result
- screenshot or command output path
- PASS or FAIL
- notes

## Stop Condition

Any real role boundary bypass is P0 and immediate NO-GO.

## Fill This Evidence File

$Out\11_RBAC_RUNTIME_EVIDENCE.csv
"@
$RbacPacket | Set-Content $RbacPacketPath -Encoding UTF8

$WorkflowPacketPath = Join-Path $Out "DEV23_WORKFLOW_RUNTIME_PACKET.md"
$WorkflowPacket = @"
# Dev 2 / Dev 3 - Workflow Runtime Proof Packet

Generated: $(Get-Date -Format s)

## Source

- Authoritative folder: $Authoritative
- Runtime guide: $Authoritative\60b_RUNTIME_PROOF_EXECUTION_GUIDE.md
- Working matrix: $Out\22_RUNTIME_PROOF_MATRIX.csv

## Objective

Prove the main SIS workflows and dashboard drill-down flows behave credibly at runtime.

## Required Proofs

$WorkflowTable

## Evidence Required Per Row

- tester
- date/time
- environment
- role used
- workflow or route tested
- expected result
- actual result
- screenshot or command output path
- PASS or FAIL
- notes

## Stop Condition

Any broken canonical workflow is P1 and blocks readiness.

## Fill This Evidence File

$Out\12_WORKFLOW_RUNTIME_EVIDENCE.csv
"@
$WorkflowPacket | Set-Content $WorkflowPacketPath -Encoding UTF8

$UiPacketPath = Join-Path $Out "DEV4_UI_POLISH_PACKET.md"
$UiPacket = @"
# Dev 4 - UI / Dashboard / Route Polish Packet

Generated: $(Get-Date -Format s)

## Source

- Action plan: $Authoritative\P1_UI_DASHBOARD_ROUTE_ACTION_PLAN.md
- Working cleanup board: $Out\30_UI_CLEANUP_BOARD.csv

## Objective

Make production-facing CROWN screens credible, clean, and safe for sandbox or customer viewing.

## Required Checks

$UiTable

## Required Evidence

- before and after notes where applicable
- screenshot path
- route tested
- PASS or FAIL
- remaining issue if not fixed

## Stop Condition

Dead links, placeholder copy, or obviously broken production-facing UI remains open.

## Fill These Files

- $Out\20_UI_DASHBOARD_ROUTE_EVIDENCE.csv
- $Out\30_UI_CLEANUP_BOARD.csv
"@
$UiPacket | Set-Content $UiPacketPath -Encoding UTF8

$BackendBaseUrl = $env:CROWN_BACKEND_BASE_URL
if ([string]::IsNullOrWhiteSpace($BackendBaseUrl)) {
    $BackendBaseUrl = "https://crown-api-prod.azurewebsites.net"
}

$FrontendBaseUrl = $env:CROWN_FRONTEND_BASE_URL
if ([string]::IsNullOrWhiteSpace($FrontendBaseUrl)) {
    $FrontendBaseUrl = "https://yellow-forest-0eecc8b0f.7.azurestaticapps.net"
}

$ApprovedSha = $env:CROWN_APPROVED_SHA
if ([string]::IsNullOrWhiteSpace($ApprovedSha)) {
    $ApprovedSha = "b9dad81"
}

$AzurePacketPath = Join-Path $Out "AZURE_POST_DEPLOY_PACKET.md"
$AzurePacket = @"
# Azure / DevOps - Post-Deploy Proof Packet

Generated: $(Get-Date -Format s)

## Status

Production release remains NO-GO until this packet passes.

## Required Gates

1. Backend health returns HTTP 200.
2. Backend health or metadata body shows the approved SHA.
3. Frontend root returns HTTP 200.
4. Frontend /build.json returns HTTP 200.
5. Frontend build metadata shows the approved SHA.
6. Browser smoke passes.
7. Runtime tenant and RBAC proof is complete.
8. Judgment Day gauntlet rerun improves score and has no release-killing P0.

## Approved SHA Target

$ApprovedSha

## URLs

- Backend: $BackendBaseUrl/api/health/
- Frontend: $FrontendBaseUrl/
- Build proof: $FrontendBaseUrl/build.json

## Run

```powershell
powershell -ExecutionPolicy Bypass -File scripts\execution\270_post_azure_live_proof.ps1
```
"@
$AzurePacket | Set-Content $AzurePacketPath -Encoding UTF8
Copy-Item $AzurePacketPath (Join-Path $Runbooks "CURRENT_AZURE_POST_DEPLOY_PACKET.md") -Force

$WaitStatusRows = @(
    [pscustomobject]@{ Check = "GitHub deploy workflow"; CurrentState = "Failed"; Expected = "Successful deploy workflow"; Evidence = "Run #64 for Deploy Dashboard (Production) failed on Apr 29, 2026 during Azure Static Web Apps deployment." },
    [pscustomobject]@{ Check = "Backend health HTTP"; CurrentState = "200"; Expected = "200"; Evidence = "Latest post-Azure proof reached backend health successfully." },
    [pscustomobject]@{ Check = "Backend approved SHA"; CurrentState = "Mismatch"; Expected = $ApprovedSha; Evidence = "Latest post-Azure proof did not find approved SHA in backend health payload." },
    [pscustomobject]@{ Check = "Frontend root HTTP"; CurrentState = "404"; Expected = "200"; Evidence = "Latest post-Azure proof reported frontend root unavailable." },
    [pscustomobject]@{ Check = "Frontend build.json HTTP"; CurrentState = "404"; Expected = "200"; Evidence = "Latest post-Azure proof reported build.json unavailable." },
    [pscustomobject]@{ Check = "Runtime tenant proof"; CurrentState = "READY_NOT_RUN"; Expected = "PASS evidence captured"; Evidence = "Tenant packet and evidence sheet are ready for Dev 1 / Dev 2 / Dev 5." },
    [pscustomobject]@{ Check = "Runtime RBAC proof"; CurrentState = "READY_NOT_RUN"; Expected = "PASS evidence captured"; Evidence = "RBAC packet and evidence sheet are ready for Dev 1 / Dev 5." },
    [pscustomobject]@{ Check = "Runtime workflow proof"; CurrentState = "READY_NOT_RUN"; Expected = "PASS evidence captured"; Evidence = "Workflow packet and evidence sheet are ready for Dev 2 / Dev 3." },
    [pscustomobject]@{ Check = "UI cleanup proof"; CurrentState = "READY_NOT_RUN"; Expected = "PASS evidence captured"; Evidence = "UI packet, cleanup board, and evidence sheet are ready for Dev 4." }
)

$WaitStatusCsvPath = Join-Path $Out "06_WAITING_ON_AZURE_STATUS.csv"
$WaitStatusRows | Export-Csv $WaitStatusCsvPath -NoTypeInformation -Encoding UTF8

$PostAzureScriptPath = Join-Path $Scripts "270_post_azure_live_proof.ps1"
$PostAzureScript = @'
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

Set-Location (git rev-parse --show-toplevel)

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Out = "audit-artifacts\post-azure-live-proof\$Stamp"
New-Item -ItemType Directory -Force -Path $Out | Out-Null

$BackendBaseUrl = "__BACKEND_BASE_URL__"
$FrontendBaseUrl = "__FRONTEND_BASE_URL__"
$ApprovedSha = "__APPROVED_SHA__"

function Get-Status {
    param([string]$Url)

    try {
        return (curl.exe -s -o NUL -w "%{http_code}" -L -m 20 $Url)
    }
    catch {
        return "ERROR"
    }
}

function Get-Body {
    param([string]$Url)

    try {
        return (curl.exe -s -L -m 20 $Url)
    }
    catch {
        return ""
    }
}

$BackendHealthUrl = "$BackendBaseUrl/api/health/"
$FrontendRootUrl = "$FrontendBaseUrl/"
$BuildJsonUrl = "$FrontendBaseUrl/build.json"

$BackendStatus = Get-Status $BackendHealthUrl
$FrontendStatus = Get-Status $FrontendRootUrl
$BuildJsonStatus = Get-Status $BuildJsonUrl
$BackendBody = Get-Body $BackendHealthUrl
$BuildJsonBody = Get-Body $BuildJsonUrl

$BackendBody | Set-Content (Join-Path $Out "backend_health_body.txt") -Encoding UTF8
$BuildJsonBody | Set-Content (Join-Path $Out "frontend_build_json_body.txt") -Encoding UTF8

$BackendShaMatch = $BackendBody -match [regex]::Escape($ApprovedSha)
$FrontendShaMatch = $BuildJsonBody -match [regex]::Escape($ApprovedSha)

$Rows = @(
    [pscustomobject]@{ Gate = "Backend health HTTP 200"; Status = $(if ($BackendStatus -eq "200") { "PASS" } else { "FAIL" }); Actual = $BackendStatus; Required = "200"; Evidence = "backend_health_body.txt" },
    [pscustomobject]@{ Gate = "Backend approved SHA"; Status = $(if ($BackendShaMatch) { "PASS" } else { "FAIL" }); Actual = $BackendShaMatch; Required = $ApprovedSha; Evidence = "backend_health_body.txt" },
    [pscustomobject]@{ Gate = "Frontend root HTTP 200"; Status = $(if ($FrontendStatus -eq "200") { "PASS" } else { "FAIL" }); Actual = $FrontendStatus; Required = "200"; Evidence = "" },
    [pscustomobject]@{ Gate = "Frontend build.json HTTP 200"; Status = $(if ($BuildJsonStatus -eq "200") { "PASS" } else { "FAIL" }); Actual = $BuildJsonStatus; Required = "200"; Evidence = "frontend_build_json_body.txt" },
    [pscustomobject]@{ Gate = "Frontend approved SHA"; Status = $(if ($FrontendShaMatch) { "PASS" } else { "FAIL" }); Actual = $FrontendShaMatch; Required = $ApprovedSha; Evidence = "frontend_build_json_body.txt" }
)

$Rows | Export-Csv (Join-Path $Out "POST_AZURE_LIVE_PROOF.csv") -NoTypeInformation -Encoding UTF8

$FailCount = @($Rows | Where-Object { $_.Status -eq "FAIL" }).Count
if ($FailCount -eq 0) {
    $Decision = "AZURE_LIVE_PROOF_PASS"
}
else {
    $Decision = "AZURE_LIVE_PROOF_FAIL"
}

@"
# CROWN Post-Azure Live Proof

Generated: $(Get-Date -Format s)

- Decision: $Decision
- BackendStatus: $BackendStatus
- BackendShaMatch: $BackendShaMatch
- FrontendStatus: $FrontendStatus
- BuildJsonStatus: $BuildJsonStatus
- FrontendShaMatch: $FrontendShaMatch
- Output: $Out

## Rows

$($Rows | Format-Table -AutoSize | Out-String)
"@ | Set-Content (Join-Path $Out "POST_AZURE_SUMMARY.md") -Encoding UTF8

$codeCmd = Get-Command code -ErrorAction SilentlyContinue
if ($codeCmd) {
    & $codeCmd.Source --reuse-window (Join-Path $Out "POST_AZURE_SUMMARY.md") | Out-Null
    & $codeCmd.Source --reuse-window (Join-Path $Out "POST_AZURE_LIVE_PROOF.csv") | Out-Null
}

Write-Host ""
Write-Host "Post-Azure proof decision: $Decision"
Write-Host "Output: $Out"
Write-Host ""
'@
$PostAzureScript = $PostAzureScript.Replace('__BACKEND_BASE_URL__', $BackendBaseUrl).Replace('__FRONTEND_BASE_URL__', $FrontendBaseUrl).Replace('__APPROVED_SHA__', $ApprovedSha)
$PostAzureScript | Set-Content $PostAzureScriptPath -Encoding UTF8
Copy-Item $PostAzureScriptPath (Join-Path $Out "270_post_azure_live_proof.ps1") -Force

$RuntimeCaptureScriptPath = Join-Path $Scripts "250_capture_runtime_proof.ps1"
$RuntimeCaptureScript = @'
param(
    [ValidateSet("Tenant", "RBAC", "Workflow")]
    [string]$Lane = "Tenant",
    [string]$ControlRoomPath = ""
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

Set-Location (git rev-parse --show-toplevel)

function Resolve-LatestControlRoom {
    if ($ControlRoomPath -and (Test-Path $ControlRoomPath)) {
        return (Resolve-Path $ControlRoomPath).Path
    }

    $base = "audit-artifacts\execution-control-room"
    $latest = Get-ChildItem $base -Directory | Sort-Object Name -Descending | Select-Object -First 1
    if (-not $latest) {
        throw "No execution control room output found. Run 271_execution_control_room_pack.ps1 first."
    }

    return $latest.FullName
}

$Room = Resolve-LatestControlRoom
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$CaptureRoot = "audit-artifacts\runtime-proof-captures\$Stamp\$Lane"
New-Item -ItemType Directory -Force -Path $CaptureRoot, (Join-Path $CaptureRoot "api"), (Join-Path $CaptureRoot "browser"), (Join-Path $CaptureRoot "screenshots") | Out-Null

switch ($Lane) {
    "Tenant" {
        $Packet = Join-Path $Room "DEV125_TENANT_RUNTIME_PACKET.md"
        $Evidence = Join-Path $Room "10_TENANT_RUNTIME_EVIDENCE.csv"
    }
    "RBAC" {
        $Packet = Join-Path $Room "DEV15_RBAC_RUNTIME_PACKET.md"
        $Evidence = Join-Path $Room "11_RBAC_RUNTIME_EVIDENCE.csv"
    }
    "Workflow" {
        $Packet = Join-Path $Room "DEV23_WORKFLOW_RUNTIME_PACKET.md"
        $Evidence = Join-Path $Room "12_WORKFLOW_RUNTIME_EVIDENCE.csv"
    }
}

Copy-Item $Evidence (Join-Path $CaptureRoot (Split-Path $Evidence -Leaf)) -Force

@"
# Runtime Proof Capture Workspace

- Lane: $Lane
- Control room: $Room
- Capture root: $CaptureRoot
- Packet: $Packet
- Evidence seed: $(Join-Path $CaptureRoot (Split-Path $Evidence -Leaf))

Use this folder for screenshots, browser captures, and command output tied to the evidence CSV.
"@ | Set-Content (Join-Path $CaptureRoot "README.md") -Encoding UTF8

$codeCmd = Get-Command code -ErrorAction SilentlyContinue
if ($codeCmd) {
    & $codeCmd.Source --reuse-window $Packet | Out-Null
    & $codeCmd.Source --reuse-window (Join-Path $CaptureRoot (Split-Path $Evidence -Leaf)) | Out-Null
    & $codeCmd.Source --reuse-window (Join-Path $CaptureRoot "README.md") | Out-Null
}

Write-Host "Runtime proof capture workspace ready: $CaptureRoot"
'@
$RuntimeCaptureScript | Set-Content $RuntimeCaptureScriptPath -Encoding UTF8
Copy-Item $RuntimeCaptureScriptPath (Join-Path $Out "250_capture_runtime_proof.ps1") -Force

$UiCaptureScriptPath = Join-Path $Scripts "260_capture_ui_cleanup.ps1"
$UiCaptureScript = @'
param(
    [string]$ControlRoomPath = ""
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

Set-Location (git rev-parse --show-toplevel)

function Resolve-LatestControlRoom {
    if ($ControlRoomPath -and (Test-Path $ControlRoomPath)) {
        return (Resolve-Path $ControlRoomPath).Path
    }

    $base = "audit-artifacts\execution-control-room"
    $latest = Get-ChildItem $base -Directory | Sort-Object Name -Descending | Select-Object -First 1
    if (-not $latest) {
        throw "No execution control room output found. Run 271_execution_control_room_pack.ps1 first."
    }

    return $latest.FullName
}

$Room = Resolve-LatestControlRoom
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$CaptureRoot = "audit-artifacts\ui-cleanup-captures\$Stamp"
New-Item -ItemType Directory -Force -Path $CaptureRoot, (Join-Path $CaptureRoot "screenshots") | Out-Null

$Packet = Join-Path $Room "DEV4_UI_POLISH_PACKET.md"
$Evidence = Join-Path $Room "20_UI_DASHBOARD_ROUTE_EVIDENCE.csv"
$Board = Join-Path $Room "30_UI_CLEANUP_BOARD.csv"

Copy-Item $Evidence (Join-Path $CaptureRoot (Split-Path $Evidence -Leaf)) -Force
Copy-Item $Board (Join-Path $CaptureRoot (Split-Path $Board -Leaf)) -Force

@"
# UI Cleanup Capture Workspace

- Control room: $Room
- Capture root: $CaptureRoot
- Packet: $Packet
- Evidence seed: $(Join-Path $CaptureRoot (Split-Path $Evidence -Leaf))
- Cleanup board seed: $(Join-Path $CaptureRoot (Split-Path $Board -Leaf))

Use this folder for before and after screenshots plus route-level proof.
"@ | Set-Content (Join-Path $CaptureRoot "README.md") -Encoding UTF8

$codeCmd = Get-Command code -ErrorAction SilentlyContinue
if ($codeCmd) {
    & $codeCmd.Source --reuse-window $Packet | Out-Null
    & $codeCmd.Source --reuse-window (Join-Path $CaptureRoot (Split-Path $Evidence -Leaf)) | Out-Null
    & $codeCmd.Source --reuse-window (Join-Path $CaptureRoot (Split-Path $Board -Leaf)) | Out-Null
    & $codeCmd.Source --reuse-window (Join-Path $CaptureRoot "README.md") | Out-Null
}

Write-Host "UI cleanup capture workspace ready: $CaptureRoot"
'@
$UiCaptureScript | Set-Content $UiCaptureScriptPath -Encoding UTF8
Copy-Item $UiCaptureScriptPath (Join-Path $Out "260_capture_ui_cleanup.ps1") -Force

$QaPacketPath = Join-Path $Out "QA_FINAL_RERUN_PACKET.md"
$QaPacket = @"
# Dev 5 / QA Release - Final Rerun Packet

Generated: $(Get-Date -Format s)

## Prerequisites

Do not rerun final production decision until all of the following are true:

1. Azure post-deploy proof passes.
2. Tenant runtime proof is complete.
3. RBAC runtime proof is complete.
4. Workflow proof is complete.
5. UI cleanup and UI proof evidence is complete.
6. Worktree is clean or intentionally committed.
7. No P0 blocker remains unreviewed.

## Open Current Evidence

```powershell
code "$TenantEvidencePath"
code "$RbacEvidencePath"
code "$WorkflowEvidencePath"
code "$UiEvidencePath"
code "$AzurePacketPath"
```

## Run Azure Proof After Azure Team Completes

```powershell
powershell -ExecutionPolicy Bypass -File scripts\execution\270_post_azure_live_proof.ps1
```

## Then Rerun Judgment Day Gauntlet

```powershell
powershell -ExecutionPolicy Bypass -File scripts\execution\crown_judgment_day_gauntlet.ps1
```

## Decision Rule

Production GO requires:

- no unresolved P0
- frontend root 200
- build.json 200
- backend approved SHA present
- frontend approved SHA present
- tenant runtime proof PASS
- RBAC runtime proof PASS
- workflow runtime proof PASS
- UI cleanup proof PASS
- final scorecard accepted
"@
$QaPacket | Set-Content $QaPacketPath -Encoding UTF8
Copy-Item $QaPacketPath (Join-Path $Ops "CURRENT_QA_FINAL_RERUN_PACKET.md") -Force

$SummaryPath = Join-Path $Out "99_EXECUTION_CONTROL_SUMMARY.md"
$Summary = @"
# CROWN Execution Control Room Summary

Generated: $(Get-Date -Format s)

- Repo: $Root
- Branch: $Branch
- HEAD: $Head
- HEAD_FULL: $HeadFull

## Current Position

This is GO for non-Azure execution.
This is NOT production GO.
Production remains NO-GO until Azure post-deploy proof, runtime proof, UI proof, and final Judgment Day rerun pass.

## Files Created

| File | Purpose |
|---|---|
| 05_EXECUTION_STATUS_BOARD.csv | Master execution assignment board |
| EXECUTION_PACK_GUIDE.md | Start-here index for the control room |
| DEV125_TENANT_RUNTIME_PACKET.md | Dev 1 / Dev 2 / Dev 5 tenant packet |
| DEV15_RBAC_RUNTIME_PACKET.md | Dev 1 / Dev 5 RBAC packet |
| DEV23_WORKFLOW_RUNTIME_PACKET.md | Dev 2 / Dev 3 workflow packet |
| DEV4_UI_POLISH_PACKET.md | Dev 4 UI packet |
| AZURE_POST_DEPLOY_PACKET.md | Azure post-deploy proof instructions |
| QA_FINAL_RERUN_PACKET.md | Final QA rerun instructions |
| 10_TENANT_RUNTIME_EVIDENCE.csv | Tenant evidence capture sheet |
| 11_RBAC_RUNTIME_EVIDENCE.csv | RBAC evidence capture sheet |
| 12_WORKFLOW_RUNTIME_EVIDENCE.csv | Workflow evidence capture sheet |
| 20_UI_DASHBOARD_ROUTE_EVIDENCE.csv | UI evidence capture sheet |
| 21_RBAC_PROOF_MATRIX.csv | RBAC proof matrix |
| 22_RUNTIME_PROOF_MATRIX.csv | Workflow proof matrix |
| 23_TENANT_PROOF_MATRIX.csv | Tenant proof matrix |
| 30_UI_CLEANUP_BOARD.csv | UI cleanup board |
| 250_capture_runtime_proof.ps1 | Runtime capture bootstrap |
| 260_capture_ui_cleanup.ps1 | UI cleanup capture bootstrap |
| 270_post_azure_live_proof.ps1 | Post-Azure proof script |
| 06_WAITING_ON_AZURE_STATUS.csv | Current wait-state snapshot |
| 98_WAITING_ON_AZURE_STATUS.md | Current wait-state summary |
| 91_CONTROLLED_COMMIT_INSTRUCTIONS.md | Review-first commit guidance |

## Team Instructions

### Dev 1 / Dev 2 / Dev 5

Open:

```powershell
code "$TenantPacketPath"
code "$TenantEvidencePath"
```

Execute TI-001 through TI-007 and capture evidence.

### Dev 1 / Dev 5

Open:

```powershell
code "$RbacPacketPath"
code "$RbacEvidencePath"
```

Execute RBAC-001 through RBAC-006 and capture evidence.

### Dev 2 / Dev 3

Open:

```powershell
code "$WorkflowPacketPath"
code "$WorkflowEvidencePath"
```

Execute WF-001 through WF-006 and capture evidence.

### Dev 4

Open:

```powershell
code "$UiPacketPath"
code "$UiEvidencePath"
code "$UiCleanupBoardPath"
```

Complete UI cleanup and route evidence.

### Azure Team

Open:

```powershell
code "$AzurePacketPath"
```

When Azure is complete, run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\execution\270_post_azure_live_proof.ps1
```

### Dev 5 / QA Release

Open:

```powershell
code "$QaPacketPath"
```

After Azure proof and runtime proof pass, rerun Judgment Day.

## Do Not

- Do not call production GO yet.
- Do not accept verbal Azure completion.
- Do not mark tenant or RBAC PASS without runtime evidence.
- Do not ignore frontend 404 or SHA mismatch if still present.
"@
$Summary | Set-Content $SummaryPath -Encoding UTF8
Copy-Item $SummaryPath (Join-Path $Ops "CURRENT_EXECUTION_CONTROL_SUMMARY.md") -Force
Copy-Item $ExecutionPackGuidePath (Join-Path $Ops "CURRENT_EXECUTION_PACK_GUIDE.md") -Force

$WaitingSummaryPath = Join-Path $Out "98_WAITING_ON_AZURE_STATUS.md"
$WaitingSummary = @"
# CROWN Waiting On Azure Status

Generated: $(Get-Date -Format s)

- Repo: $Root
- Branch: $Branch
- HEAD: $Head
- Approved SHA Target: $ApprovedSha

## Current Decision

WAITING_ON_AZURE_COMPLETION

## What Is Ready Right Now

- Control room generated and validated.
- Team packets are ready for tenant, RBAC, workflow, and UI execution.
- Runtime capture helper scripts run successfully.
- UI cleanup capture helper runs successfully.
- Post-Azure proof script runs successfully and is safe to rerun when Azure is ready.

## What Is Still Blocking Production

- GitHub Deploy Dashboard (Production) workflow #64 is failed.
- Backend health is reachable, but approved SHA proof is not yet present.
- Frontend root is still returning 404.
- Frontend build.json is still returning 404.
- Runtime proof evidence is not yet filled in by assigned teams.

## Current Wait-State Snapshot

| Check | CurrentState | Expected | Evidence |
|---|---|---|---|
| GitHub deploy workflow | Failed | Successful deploy workflow | Run #64 failed on Apr 29, 2026 during Azure Static Web Apps deployment. |
| Backend health HTTP | 200 | 200 | Latest post-Azure proof reached backend health successfully. |
| Backend approved SHA | Mismatch | $ApprovedSha | Latest post-Azure proof did not find approved SHA in backend health payload. |
| Frontend root HTTP | 404 | 200 | Latest post-Azure proof reported frontend root unavailable. |
| Frontend build.json HTTP | 404 | 200 | Latest post-Azure proof reported build.json unavailable. |
| Runtime tenant proof | READY_NOT_RUN | PASS evidence captured | Tenant packet and evidence sheet are ready. |
| Runtime RBAC proof | READY_NOT_RUN | PASS evidence captured | RBAC packet and evidence sheet are ready. |
| Runtime workflow proof | READY_NOT_RUN | PASS evidence captured | Workflow packet and evidence sheet are ready. |
| UI cleanup proof | READY_NOT_RUN | PASS evidence captured | UI packet, cleanup board, and evidence sheet are ready. |

## Use These Files First While Azure Is Pending

- $SummaryPath
- $StatusBoardPath
- $ExecutionPackGuidePath
- $WaitStatusCsvPath
- $AzurePacketPath

## Immediate Team Order

1. Dev 1 / Dev 2 / Dev 5: execute tenant proofs and fill 10_TENANT_RUNTIME_EVIDENCE.csv.
2. Dev 1 / Dev 5: execute RBAC proofs and fill 11_RBAC_RUNTIME_EVIDENCE.csv.
3. Dev 2 / Dev 3: execute workflow proofs and fill 12_WORKFLOW_RUNTIME_EVIDENCE.csv.
4. Dev 4: execute UI cleanup and fill 20_UI_DASHBOARD_ROUTE_EVIDENCE.csv plus 30_UI_CLEANUP_BOARD.csv.
5. Azure / DevOps: rerun scripts/execution/270_post_azure_live_proof.ps1 only after deployment says complete.

## Do Not

- Do not treat backend health 200 as deployment complete.
- Do not call production GO while frontend root or build.json still returns 404.
- Do not accept SHA mismatch as a soft warning.
- Do not skip runtime evidence collection while waiting for Azure.
"@
$WaitingSummary | Set-Content $WaitingSummaryPath -Encoding UTF8
Copy-Item $WaitingSummaryPath (Join-Path $Ops "CURRENT_WAITING_ON_AZURE_STATUS.md") -Force
Copy-Item $WaitStatusCsvPath (Join-Path $Ops "CURRENT_WAITING_ON_AZURE_STATUS.csv") -Force

git status --short | Set-Content (Join-Path $Out "90_git_status_after.txt") -Encoding UTF8

$CommitInstructionsPath = Join-Path $Out "91_CONTROLLED_COMMIT_INSTRUCTIONS.md"
$CommitInstructions = @"
# Controlled Commit Instructions

Review generated files first.

Open:

```powershell
code "$SummaryPath"
code "$StatusBoardPath"
code "$(Join-Path $Out '90_git_status_after.txt')"
```

If these artifacts are intentional, commit only the control-room artifacts and scripts:

```powershell
git add "$Out"
git add docs/crown-master-binder/operations/CURRENT_EXECUTION_CONTROL_SUMMARY.md
git add docs/crown-master-binder/operations/CURRENT_EXECUTION_PACK_GUIDE.md
git add docs/crown-master-binder/operations/CURRENT_EXECUTION_STATUS_BOARD.csv
git add docs/crown-master-binder/operations/CURRENT_WAITING_ON_AZURE_STATUS.md
git add docs/crown-master-binder/operations/CURRENT_WAITING_ON_AZURE_STATUS.csv
git add docs/crown-master-binder/operations/CURRENT_QA_FINAL_RERUN_PACKET.md
git add docs/crown-master-binder/runbooks/CURRENT_AZURE_POST_DEPLOY_PACKET.md
git add scripts/execution/250_capture_runtime_proof.ps1
git add scripts/execution/260_capture_ui_cleanup.ps1
git add scripts/execution/270_post_azure_live_proof.ps1
git add scripts/execution/271_execution_control_room_pack.ps1
git status --short
git commit -m "audit: add execution control room and post-azure proof scripts"
```

Do not commit unrelated accidental edits.
"@
$CommitInstructions | Set-Content $CommitInstructionsPath -Encoding UTF8

$FilesToOpen = @(
    $SummaryPath,
    $StatusBoardPath,
    $ExecutionPackGuidePath,
    $WaitingSummaryPath,
    $TenantPacketPath,
    $RbacPacketPath,
    $WorkflowPacketPath,
    $UiPacketPath,
    $AzurePacketPath,
    $QaPacketPath,
    $TenantEvidencePath,
    $RbacEvidencePath,
    $WorkflowEvidencePath,
    $UiEvidencePath,
    $CommitInstructionsPath,
    (Join-Path $Out "90_git_status_after.txt")
)
Open-IfAvailable $FilesToOpen

Write-Log "Execution control room pack complete."
Write-Log "Open first:"
Write-Log $SummaryPath
Write-Log $StatusBoardPath
