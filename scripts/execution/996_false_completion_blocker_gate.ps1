param(
    [switch]$AllowDocumentedNonShippingFindings
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = (git rev-parse --show-toplevel 2>$null).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Not inside a git repository."
}
Set-Location $repoRoot

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$base = Join-Path $repoRoot "audit-artifacts/false-completion-blocker-$stamp"
New-Item -ItemType Directory -Force -Path $base | Out-Null

$findings = New-Object System.Collections.Generic.List[object]

function Add-Finding {
    param(
        [string]$Id,
        [string]$Severity,
        [string]$Area,
        [string]$File,
        [string]$Evidence,
        [string]$RequiredFix
    )

    $findings.Add([pscustomobject]@{
        id = $Id
        severity = $Severity
        area = $Area
        file = $File
        evidence = $Evidence
        required_fix = $RequiredFix
    })
}

function Read-TextFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return "" }
    return Get-Content -Path $Path -Raw
}

function Search-RepoText {
    param(
        [string[]]$Paths,
        [string]$Pattern,
        [string]$Area,
        [string]$FindingId,
        [string]$RequiredFix,
        [string]$Severity = "BLOCKER"
    )

    $matches = @()
    foreach ($path in $Paths) {
        if (-not (Test-Path $path)) { continue }
        $matches += Select-String -Path $path -Pattern $Pattern -AllMatches -ErrorAction SilentlyContinue
    }

    foreach ($match in $matches) {
        Add-Finding -Id $FindingId -Severity $Severity -Area $Area -File $match.Path -Evidence ("line {0}: {1}" -f $match.LineNumber, $match.Line.Trim()) -RequiredFix $RequiredFix
    }
}

$repoPath = Join-Path $base "01_repo_truth.txt"
"=== REPO TRUTH ===" | Set-Content -Path $repoPath -Encoding UTF8
git branch --show-current | Add-Content -Path $repoPath -Encoding UTF8
git rev-parse HEAD | Add-Content -Path $repoPath -Encoding UTF8
git status --short --branch | Add-Content -Path $repoPath -Encoding UTF8
git log --oneline -n 8 | Add-Content -Path $repoPath -Encoding UTF8

# 1. Canonical release authority cannot remain conditional/stale while GO language is being pursued.
$currentReleaseStatus = "docs/CURRENT_RELEASE_STATUS.md"
$currentReleaseText = Read-TextFile $currentReleaseStatus
if ($currentReleaseText) {
    if ($currentReleaseText -match "Repository-wide decision:\s*CONDITIONAL GO") {
        Add-Finding -Id "FC-001" -Severity "BLOCKER" -Area "release-authority" -File $currentReleaseStatus -Evidence "Repository-wide decision is still CONDITIONAL GO." -RequiredFix "Replace stale conditional release posture with current candidate-SHA PASS evidence or explicit blocked status; do not allow unrestricted GO claims."
    }
    if ($currentReleaseText -match "Parity verdict:\s*`?PARTIAL_OPEN`?") {
        Add-Finding -Id "FC-002" -Severity "BLOCKER" -Area "azure-parity" -File $currentReleaseStatus -Evidence "Deploy parity is still PARTIAL_OPEN." -RequiredFix "Run Azure P0 parity probe and update authority only after current expected SHA matches health and integrity runtime SHA."
    }
    if ($currentReleaseText -match "unrestricted GA-ready") {
        Add-Finding -Id "FC-003" -Severity "BLOCKER" -Area "release-language" -File $currentReleaseStatus -Evidence "Authority contains unrestricted GA language guardrail." -RequiredFix "Maintain blocker until all P0 readiness gates pass on the same candidate SHA."
    }
}
else {
    Add-Finding -Id "FC-004" -Severity "BLOCKER" -Area "release-authority" -File $currentReleaseStatus -Evidence "Missing canonical release status file." -RequiredFix "Restore canonical release status with current SHA and evidence links."
}

# 2. Dashboard templates with BASE_NOTE are preview/sandbox-backed unless explicitly hidden/non-shipping.
$templateFiles = @()
if (Test-Path "frontend/dashboards/src/config/dashboardTemplates") {
    $templateFiles = Get-ChildItem "frontend/dashboards/src/config/dashboardTemplates" -Filter "*.js" -Recurse | ForEach-Object FullName
}
foreach ($file in $templateFiles) {
    $text = Read-TextFile $file
    if ($text -match "BASE_NOTE" -or $text -match "Sandbox preview data shown" -or $text -match "Connect backend for live records") {
        Add-Finding -Id "FC-010" -Severity "BLOCKER" -Area "dashboard-live-data" -File $file -Evidence "Dashboard template references BASE_NOTE or sandbox-preview language." -RequiredFix "Either replace this dashboard with live service/API-backed metrics and provenance or keep it non-ready/non-production-visible."
    }
}

# 3. Backend dashboard stubs are not production-complete data services.
$backendDashboardFiles = @()
if (Test-Path "backend/crown_api/dashboards") {
    $backendDashboardFiles = Get-ChildItem "backend/crown_api/dashboards" -Filter "*.py" -Recurse | ForEach-Object FullName
}
Search-RepoText -Paths $backendDashboardFiles -Pattern "Phase A stub|gracefully degrades to stub|sample_payload|sample payload|fallback" -Area "backend-dashboard-data" -FindingId "FC-020" -RequiredFix "Replace stubs/sample/fallback paths with live tenant-scoped services or keep the surface explicitly unavailable/non-ready." -Severity "BLOCKER"

# 4. WizardHub placeholder routes are not completed wizard workflows.
$wizardRoutes = "frontend/dashboards/src/routes/wizards.js"
$wizardText = Read-TextFile $wizardRoutes
if ($wizardText) {
    $placeholderRouteMatches = Select-String -Path $wizardRoutes -Pattern @(
        'component:\s*WizardHub',
        'releaseState:\s*''placeholder''',
        'releaseState:\s*"placeholder"'
    ) -AllMatches -ErrorAction SilentlyContinue
    foreach ($match in $placeholderRouteMatches) {
        Add-Finding -Id "FC-030" -Severity "BLOCKER" -Area "wizard-completion" -File $wizardRoutes -Evidence ("line {0}: {1}" -f $match.LineNumber, $match.Line.Trim()) -RequiredFix "Complete the wizard save/continue/commit path with backend API proof or keep route non-production-visible and excluded from completion claims."
    }
}
else {
    Add-Finding -Id "FC-031" -Severity "BLOCKER" -Area "wizard-completion" -File $wizardRoutes -Evidence "Missing wizard route registry." -RequiredFix "Restore wizard route registry and certify every production-visible route."
}

# 5. 120-school launch authority remains blocking until every row is PASS/N/A.
$sandboxGate = "docs/release/final-95-plus-sprint/SANDBOX_120_SCHOOL_LAUNCH_GATE_20260601.md"
$sandboxText = Read-TextFile $sandboxGate
if ($sandboxText) {
    if ($sandboxText -match "SANDBOX 120-SCHOOL LAUNCH:\s*NO-GO") {
        Add-Finding -Id "FC-040" -Severity "BLOCKER" -Area "sandbox-120" -File $sandboxGate -Evidence "120-school sandbox launch gate remains NO-GO." -RequiredFix "Close all required global and cohort gates with committed evidence before any sandbox-120 GO claim."
    }
    if ($sandboxText -match "NOT VERIFIED|NOT DONE") {
        Add-Finding -Id "FC-041" -Severity "BLOCKER" -Area "sandbox-120" -File $sandboxGate -Evidence "Gate contains NOT VERIFIED or NOT DONE rows." -RequiredFix "Produce current candidate-SHA evidence for each row or mark formally N/A with rationale."
    }
}

# 6. Active completion queues with NOT DONE/NOT VERIFIED are blockers to full-completion claims.
$completionQueue = "docs/release/final-95-plus-sprint/FRONTEND_DASHBOARD_WIZARD_COMPLETION_QUEUE_20260530.md"
$completionText = Read-TextFile $completionQueue
if ($completionText) {
    if ($completionText -match "NOT VERIFIED on latest connector commits") {
        Add-Finding -Id "FC-050" -Severity "BLOCKER" -Area "frontend-gates" -File $completionQueue -Evidence "Frontend gates are marked NOT VERIFIED on latest connector commits." -RequiredFix "Run npm/frontend/API/navigation gates on current candidate SHA and update evidence."
    }
    if ($completionText -match "\| .* \| NOT DONE \|") {
        Add-Finding -Id "FC-051" -Severity "BLOCKER" -Area "role-journeys" -File $completionQueue -Evidence "Role journey rows remain NOT DONE." -RequiredFix "Prove every production-visible role journey end-to-end or remove from completion claims."
    }
}

$findingsPath = Join-Path $base "00_false_completion_findings.csv"
$findings | Export-Csv -Path $findingsPath -NoTypeInformation -Encoding UTF8

$summaryPath = Join-Path $base "00_FALSE_COMPLETION_SUMMARY.md"
$blockers = @($findings | Where-Object { $_.severity -eq "BLOCKER" })
$md = New-Object System.Collections.Generic.List[string]
$md.Add("# False Completion Blocker Gate")
$md.Add("")
$md.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$md.Add("- Evidence root: $base")
$md.Add("- Findings: $($findings.Count)")
$md.Add("- Blockers: $($blockers.Count)")
$md.Add("")
if ($blockers.Count -eq 0) {
    $md.Add("## Verdict")
    $md.Add("")
    $md.Add("PASS")
} else {
    $md.Add("## Verdict")
    $md.Add("")
    $md.Add("FAIL")
    $md.Add("")
    $md.Add("## Blocking findings")
    foreach ($finding in $blockers) {
        $md.Add("- $($finding.id) [$($finding.area)] $($finding.file) :: $($finding.evidence)")
    }
}
$md | Set-Content -Path $summaryPath -Encoding UTF8

Write-Host "FALSE_COMPLETION_EVIDENCE=$base"
Write-Host "FALSE_COMPLETION_SUMMARY=$summaryPath"
Write-Host "FALSE_COMPLETION_FINDINGS=$findingsPath"

if ($blockers.Count -gt 0 -and -not $AllowDocumentedNonShippingFindings) {
    exit 1
}
