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

function Require-TextPattern {
    param(
        [string]$Path,
        [string]$Pattern,
        [string]$FindingId,
        [string]$Area,
        [string]$Evidence,
        [string]$RequiredFix
    )

    $text = Read-TextFile $Path
    if (-not $text) {
        Add-Finding -Id $FindingId -Severity "BLOCKER" -Area $Area -File $Path -Evidence "Required file is missing or empty." -RequiredFix $RequiredFix
        return
    }
    if ($text -notmatch $Pattern) {
        Add-Finding -Id $FindingId -Severity "BLOCKER" -Area $Area -File $Path -Evidence $Evidence -RequiredFix $RequiredFix
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

# 2. Preview/scaffold data is blocking only when a shipping dashboard template uses it.
$templateDir = "frontend/dashboards/src/config/dashboardTemplates"
$templateFiles = @()
if (Test-Path $templateDir) {
    $templateFiles = Get-ChildItem $templateDir -Filter "*Dashboard.js" -File -Recurse | ForEach-Object FullName
}
Search-RepoText -Paths $templateFiles -Pattern "BASE_NOTE|Sandbox preview data shown|Connect backend for live records" -Area "dashboard-live-data" -FindingId "FC-010" -RequiredFix "Replace preview/scaffold usage with live service/API-backed metrics and explicit provenance, or keep the dashboard non-production-visible." -Severity "BLOCKER"

$baseDataFile = "frontend/dashboards/src/config/dashboardTemplates/_baseData.js"
$baseDataText = Read-TextFile $baseDataFile
if ($baseDataText -match "BASE_NOTE|Sandbox preview data shown|Connect backend for live records") {
    Add-Finding -Id "FC-019" -Severity "DOCUMENTED_NON_SHIPPING" -Area "dashboard-fixtures" -File $baseDataFile -Evidence "Shared scaffold fixture remains defined, but no shipping dashboard template references the generic preview note." -RequiredFix "Retain only for bounded fallback/testing contexts; production fallback controls must remain enforced."
}

$dashboardHook = "frontend/dashboards/src/hooks/useDashboardData.js"
Require-TextPattern -Path $dashboardHook -Pattern "isProduction[\s\S]*return !isProduction" -FindingId "FC-011" -Area "frontend-production-fallback" -Evidence "Frontend dashboard hook does not prove that scaffold fallback is disabled in production." -RequiredFix "Disable frontend scaffold fallback in production while retaining explicit sandbox behavior."
Require-TextPattern -Path $dashboardHook -Pattern "if \(isSandbox\) return true" -FindingId "FC-012" -Area "frontend-sandbox-boundary" -Evidence "Frontend dashboard hook does not explicitly bound fallback behavior to sandbox/non-production contexts." -RequiredFix "Keep fallback behavior explicitly bounded to sandbox or non-production runtimes."

# 3. Backend fixture definitions are not blockers by themselves. Prove that production cannot silently serve them.
$dashboardViews = "backend/crown_api/dashboards/views.py"
Require-TextPattern -Path $dashboardViews -Pattern "if\s+_is_production_runtime\(\):\s*\r?\n\s*return False" -FindingId "FC-020" -Area "backend-production-sample-guard" -Evidence "Production runtime does not have an explicit default-deny sample-payload guard." -RequiredFix "Make production live/snapshot-only by default and return unavailable when no certified source exists."
Require-TextPattern -Path $dashboardViews -Pattern "if not _sample_dashboard_payloads_allowed\(request\):" -FindingId "FC-021" -Area "backend-production-sample-guard" -Evidence "Dashboard endpoint does not invoke the sample-payload authorization guard before fixture generation." -RequiredFix "Require the sample authorization guard before any fixture builder can execute."
Require-TextPattern -Path $dashboardViews -Pattern "dashboard_live_data_required" -FindingId "FC-022" -Area "backend-production-unavailable-state" -Evidence "Dashboard endpoint lacks an explicit unavailable response when certified live/snapshot data is absent." -RequiredFix "Return an explicit unavailable response rather than silently serving fixture data."
Require-TextPattern -Path $dashboardViews -Pattern "served_from'\]\s*=\s*'snapshot'" -FindingId "FC-023" -Area "backend-snapshot-provenance" -Evidence "Snapshot responses are not explicitly labeled with snapshot provenance." -RequiredFix "Label snapshot payload provenance before returning it."

$productionGuardTest = "backend/crown_api/tests/test_dashboard_snapshot_summary_api.py"
Require-TextPattern -Path $productionGuardTest -Pattern "test_attendance_summary_rejects_sample_payload_in_production_without_snapshot" -FindingId "FC-024" -Area "backend-production-test" -Evidence "No regression test proves production rejection of sample dashboard payloads when a live/snapshot source is absent." -RequiredFix "Add a production-mode regression test for the live-data-required response."

$fixtureFiles = @(
    "backend/crown_api/dashboards/sample_payloads.py",
    "backend/crown_api/dashboards/batch5_extra_payloads.py",
    "backend/crown_api/dashboards/summary.py",
    "backend/crown_api/dashboards/management/commands/seed_dashboard_snapshots.py"
)
foreach ($fixtureFile in $fixtureFiles) {
    if (Test-Path $fixtureFile) {
        Add-Finding -Id "FC-029" -Severity "DOCUMENTED_NON_SHIPPING" -Area "backend-dashboard-fixtures" -File $fixtureFile -Evidence "Fixture, seed, or legacy scaffold code is present but is not independently eligible for production completion." -RequiredFix "Keep production access behind the verified live/snapshot and environment guards; remove obsolete fixture code when no longer needed."
    }
}

# Legacy summary builders must remain disconnected from active URL/view imports.
$backendDashboardPython = @()
if (Test-Path "backend/crown_api/dashboards") {
    $backendDashboardPython = Get-ChildItem "backend/crown_api/dashboards" -Filter "*.py" -File -Recurse |
        Where-Object { $_.FullName -notmatch "[\\/]summary\.py$" } |
        ForEach-Object FullName
}
Search-RepoText -Paths $backendDashboardPython -Pattern "from \.summary import|import crown_api\.dashboards\.summary|from crown_api\.dashboards\.summary import" -Area "legacy-dashboard-reachability" -FindingId "FC-025" -RequiredFix "Remove the shipping import or replace legacy scaffold builders with tenant-scoped live services." -Severity "BLOCKER"

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

$sandboxReadyWorkflow = ".github/workflows/sandbox-ready-evidence.yml"
$sandboxReadyText = Read-TextFile $sandboxReadyWorkflow
if ($sandboxReadyText -match "121_50_wizard_deep_dive_assessment\.ps1|all\s+50\s+wizards\s+are\s+complete\s+and\s+proof-backed") {
    Add-Finding -Id "FC-032" -Severity "BLOCKER" -Area "wizard-completion" -File $sandboxReadyWorkflow -Evidence "Sandbox readiness still relies on legacy 50-row structural scoring or an unconditional 50-wizard proof-backed claim." -RequiredFix "Use canonical registered-wizard evidence and live runtime proof instead of structural inventory."
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
$documented = @($findings | Where-Object { $_.severity -eq "DOCUMENTED_NON_SHIPPING" })
$md = New-Object System.Collections.Generic.List[string]
$md.Add("# False Completion Blocker Gate")
$md.Add("")
$md.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$md.Add("- Evidence root: $base")
$md.Add("- Findings: $($findings.Count)")
$md.Add("- Blockers: $($blockers.Count)")
$md.Add("- Documented non-shipping findings: $($documented.Count)")
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
if ($documented.Count -gt 0) {
    $md.Add("")
    $md.Add("## Documented non-shipping findings")
    foreach ($finding in $documented) {
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
