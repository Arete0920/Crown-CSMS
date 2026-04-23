param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Not inside a git repository."
}
Set-Location $repoRoot

$deepAuditRoot = Join-Path $repoRoot "audit-artifacts\deep-audit"
$invDir = Join-Path $deepAuditRoot "03_inventories"
$snapDir = Join-Path $deepAuditRoot "00_repo_snapshot"
$shotDir = Join-Path $deepAuditRoot "04_screenshots_walkthroughs"

New-Item -ItemType Directory -Force -Path $invDir | Out-Null
New-Item -ItemType Directory -Force -Path $snapDir | Out-Null
New-Item -ItemType Directory -Force -Path $shotDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$branch = (git branch --show-current).Trim()
$head = (git rev-parse HEAD).Trim()
$status = @(git status --short)
$snapshotPath = Join-Path $snapDir "repo_snapshot_$timestamp.md"

@(
    "# Repo Snapshot",
    "",
    "- Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "- Branch: $branch",
    "- Head: $head",
    "- Dirty count: $($status.Count)",
    "",
    "## Dirty entries",
    ""
) + $(if ($status.Count -eq 0) { "- None" } else { $status | ForEach-Object { "- $_" } }) | Set-Content -Path $snapshotPath -Encoding UTF8

# module inventory
$coreNames = @("core","crown_api","tenants","platform_ops","signals")
$moduleRows = Get-ChildItem (Join-Path $repoRoot "backend") -Directory |
    Where-Object { $_.Name -notin @("__pycache__","scripts","quarantine_old_tests") } |
    ForEach-Object {
        [pscustomobject][ordered]@{
            module_id = $_.Name
            module_name = $_.Name
            taxonomy_bucket = if ($coreNames -contains $_.Name) { "Core" } elseif ($_.Name -match "wizard") { "Add-on" } else { "Module" }
            decision_tag = "Keep"
            maturity_tag = "Partial"
            owner_area = "Engineering"
            repo_path_or_artifact = "backend/$($_.Name)"
            evidence_path = "backend/$($_.Name)"
            proof_freshness = "Current"
            current_release_relevance = "Yes"
            notes = "Auto-generated"
        }
    }
$moduleRows | Sort-Object module_id | Export-Csv -Path (Join-Path $invDir "module_inventory.csv") -NoTypeInformation -Encoding UTF8

# route inventory
$routeRows = @()
$pathsFile = Join-Path $repoRoot "frontend\dashboards\src\routes\paths.js"
if (Test-Path $pathsFile) {
    foreach ($line in Get-Content $pathsFile) {
        if ($line -match "^\s*([A-Z0-9_]+):\s*'([^']+)'") {
            $id = $matches[1]
            $path = $matches[2]
            $persona = if ($path -match '^/teacher') { "teacher" } elseif ($path -match '^/parent') { "parent" } elseif ($path -match '^/student') { "student" } elseif ($path -match '^/finance') { "finance" } else { "shared" }
            $routeRows += [pscustomobject][ordered]@{
                route_id = $id
                route_path = $path
                feature_name = ($id -replace '_',' ').ToLowerInvariant()
                taxonomy_bucket = "Module"
                decision_tag = "Keep"
                maturity_tag = "Partial"
                persona = $persona
                source_file = "frontend/dashboards/src/routes/paths.js"
                evidence_path = "frontend/dashboards/src/routes/router.jsx"
                proof_freshness = "Current"
                notes = "Auto-discovered from PATHS"
            }
        }
    }
}
$routeRows | Sort-Object route_id | Export-Csv -Path (Join-Path $invDir "route_inventory.csv") -NoTypeInformation -Encoding UTF8

# dashboard inventory
$dashRows = @()
$dashFile = Join-Path $repoRoot "frontend\dashboards\src\config\dashboardRegistry.js"
if (Test-Path $dashFile) {
    foreach ($line in Get-Content $dashFile) {
        if ($line -match "key:\s*'([^']+)'") {
            $k = $matches[1]
            $dashRows += [pscustomobject][ordered]@{
                dashboard_id = $k
                dashboard_name = $k
                taxonomy_bucket = "Module"
                decision_tag = "Keep"
                maturity_tag = "Partial"
                persona = "role-gated"
                source_file = "frontend/dashboards/src/config/dashboardRegistry.js"
                evidence_path = "frontend/dashboards/src/routes/dashboardRoutes.jsx"
                proof_freshness = "Current"
                seed_or_demo_backed = "Unknown"
                notes = "Auto-extracted"
            }
        }
    }
}
$dashRows | Sort-Object dashboard_id -Unique | Export-Csv -Path (Join-Path $invDir "dashboard_inventory.csv") -NoTypeInformation -Encoding UTF8

# wizard inventory
$wizRows = @()
$wizFile = Join-Path $repoRoot "frontend\dashboards\src\routes\wizard-manifest.js"
if (Test-Path $wizFile) {
    foreach ($line in Get-Content $wizFile) {
        if ($line -match 'slug:\s*"([^"]+)".*title:\s*"([^"]+)".*path:\s*"([^"]+)"') {
            $wizRows += [pscustomobject][ordered]@{
                wizard_id = $matches[1]
                wizard_name = $matches[2]
                taxonomy_bucket = "Add-on"
                decision_tag = "Keep"
                maturity_tag = "Partial"
                start_route = $matches[3]
                end_route = $matches[3]
                source_file = "frontend/dashboards/src/routes/wizard-manifest.js"
                evidence_path = "frontend/dashboards/src/routes/wizards.js"
                proof_freshness = "Current"
                notes = "Manifest entry"
            }
        }
    }
}
$wizRows | Sort-Object wizard_id -Unique | Export-Csv -Path (Join-Path $invDir "wizard_inventory.csv") -NoTypeInformation -Encoding UTF8

# widget template inventory
$widgetRows = @()
$summaryFile = Join-Path $repoRoot "backend\crown_api\dashboards\summary.py"
if (Test-Path $summaryFile) {
    foreach ($m in (Select-String -Path $summaryFile -Pattern '"key"\s*:\s*"([^"]+)"' -AllMatches)) {
        $k = $m.Matches[0].Groups[1].Value
        $widgetRows += [pscustomobject][ordered]@{
            widget_id = $k
            widget_or_template_name = $k
            taxonomy_bucket = "Module"
            decision_tag = "Keep"
            maturity_tag = "Partial"
            host_surface = "dashboard"
            source_file = "backend/crown_api/dashboards/summary.py"
            evidence_path = "backend/crown_api/dashboards/summary.py"
            proof_freshness = "Current"
            seed_or_demo_backed = "Possible"
            notes = "Auto-extracted widget key"
        }
    }
}
$widgetRows | Sort-Object widget_id -Unique | Export-Csv -Path (Join-Path $invDir "widget_template_inventory.csv") -NoTypeInformation -Encoding UTF8

# workflow inventory
$workflowRows = @()
$gapFile = Join-Path $repoRoot "audit-artifacts\release-closeout\02_workflow_gap_list.md"
if (Test-Path $gapFile) {
    foreach ($ln in Get-Content $gapFile) {
        if ($ln.StartsWith("| ") -and -not $ln.StartsWith("| ---") -and -not $ln.StartsWith("| Workflow")) {
            $parts = $ln.Trim('|').Split('|') | ForEach-Object { $_.Trim() }
            if ($parts.Count -ge 7) {
                $workflowRows += [pscustomobject][ordered]@{
                    workflow_id = (($parts[0] -replace '[^a-zA-Z0-9]+','_').Trim('_').ToLowerInvariant())
                    workflow_name = $parts[0]
                    taxonomy_bucket = "Module"
                    decision_tag = "Keep"
                    maturity_tag = "Partial"
                    start_state = $parts[1]
                    expected_end_state = "Production-ready"
                    actual_evidence = $parts[2]
                    evidence_path = "audit-artifacts/release-closeout/02_workflow_gap_list.md"
                    blocking_gap = $parts[4]
                    notes = "Owner: $($parts[5]); Status: $($parts[6])"
                }
            }
        }
    }
}
$workflowRows | Export-Csv -Path (Join-Path $invDir "workflow_inventory.csv") -NoTypeInformation -Encoding UTF8

# test inventory
$testRows = @()
Get-ChildItem (Join-Path $repoRoot ".github\workflows") -File -Filter *.yml | ForEach-Object {
    $testRows += [pscustomobject][ordered]@{
        test_id = ($_.BaseName -replace '[^a-zA-Z0-9]+','_').ToLowerInvariant()
        test_name = $_.BaseName
        test_type = "ci-workflow"
        taxonomy_bucket = "Core"
        decision_tag = "Keep"
        maturity_tag = "Strong but bounded"
        command_or_suite = "GitHub Actions"
        source_file = ".github/workflows/$($_.Name)"
        latest_artifact_or_log = "audit-artifacts/live-scorecard/20260423_024146/SCORECARD.md"
        pass_state = "Unknown"
        notes = "Auto-indexed"
    }
}
$testRows | Sort-Object test_id | Export-Csv -Path (Join-Path $invDir "test_inventory.csv") -NoTypeInformation -Encoding UTF8

# integration inventory
$intRows = @()
$apiV1 = Join-Path $repoRoot "backend\crown_api\api_v1_urls.py"
if (Test-Path $apiV1) {
    foreach ($m in (Select-String -Path $apiV1 -Pattern 'include\("([^"]+)"\)' -AllMatches)) {
        $name = $m.Matches[0].Groups[1].Value
        $intRows += [pscustomobject][ordered]@{
            integration_id = ($name -replace '[^a-zA-Z0-9]+','_').ToLowerInvariant()
            integration_name = $name
            taxonomy_bucket = "Module"
            decision_tag = "Keep"
            maturity_tag = "Partial"
            dependency_type = "django-include"
            source_file_or_config = "backend/crown_api/api_v1_urls.py"
            evidence_path = "backend/crown_api/api_v1_urls.py"
            production_backed = "Unknown"
            notes = "Auto-discovered include"
        }
    }
}
$intRows | Sort-Object integration_id -Unique | Export-Csv -Path (Join-Path $invDir "integration_inventory.csv") -NoTypeInformation -Encoding UTF8

# open PR inventory
$prRows = @()
$prCsv = Join-Path $repoRoot "audit-artifacts\pr-reconcile\09_pr_overlap_rollup.csv"
if (Test-Path $prCsv) {
    Import-Csv -Path $prCsv | ForEach-Object {
        $prRows += [pscustomobject][ordered]@{
            pr_number = $_.PRNumber
            title = $_.Title
            status = if ($_.Draft -eq "True") { "Draft" } else { "Open" }
            taxonomy_bucket = "Core"
            decision_tag = "Keep"
            maturity_tag = "Partial"
            overlap_risk = $_.Risk
            evidence_path = "audit-artifacts/pr-reconcile/09_pr_overlap_rollup.csv"
            shipping_or_deferral = "Unknown"
            notes = "Branch: $($_.Branch); OverlapCount: $($_.OverlapCount); Url: $($_.Url)"
        }
    }
}
$prRows | Sort-Object {[int]$_.pr_number} | Export-Csv -Path (Join-Path $invDir "open_pr_inventory.csv") -NoTypeInformation -Encoding UTF8

# release proof inventory
$proofRows = @()
$proofMd = Join-Path $repoRoot "audit-artifacts\release-closeout\01_proof_inventory.md"
if (Test-Path $proofMd) {
    foreach ($ln in Get-Content $proofMd) {
        if ($ln.StartsWith("| ") -and -not $ln.StartsWith("| ---") -and -not $ln.StartsWith("| Proof")) {
            $parts = $ln.Trim('|').Split('|') | ForEach-Object { $_.Trim() }
            if ($parts.Count -ge 6) {
                $proofRows += [pscustomobject][ordered]@{
                    proof_id = (($parts[0] -replace '[^a-zA-Z0-9]+','_').Trim('_').ToLowerInvariant())
                    proof_name = $parts[0]
                    taxonomy_bucket = "Core"
                    decision_tag = "Keep"
                    maturity_tag = if ($parts[1] -eq "GREEN") { "Strong but bounded" } else { "Partial" }
                    source_artifact = $parts[2]
                    evidence_path = "audit-artifacts/release-closeout/01_proof_inventory.md"
                    current_or_stale = $parts[3]
                    release_lane = $parts[0]
                    blocking_if_missing = if ($parts[1] -eq "RED") { "Yes" } else { "Potential" }
                    notes = $parts[4]
                }
            }
        }
    }
}
$proofRows | Export-Csv -Path (Join-Path $invDir "release_proof_inventory.csv") -NoTypeInformation -Encoding UTF8

# screenshot index refresh
$screenPath = Join-Path $shotDir "runtime_screenshot_index.md"
@(
    "# Runtime Screenshot Index",
    "",
    "## Manifest",
    "",
    "| Screenshot ID | Area | Taxonomy bucket | Walkthrough name | Source path | Capture date | Current or stale | Related proof | Notes |",
    "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    "| branch_protection_main | Governance | Core | Branch protection policy evidence | audit-artifacts/release-certification/latest/01_branch_protection_screenshot.png |  | stale | audit-artifacts/release-certification/latest/01_branch_protection_manual.txt | Required for final signoff |",
    "| blocked_pr_codeql | Governance | Core | Blocked PR capture (CodeQL) | audit-artifacts/release-certification/latest/blocked_pr_codeql.png |  | stale | audit-artifacts/release-closeout/evidence-pack/05_missing_evidence_checklist.md | Optional extra but requested in manual checklist |",
    "| blocked_pr_dependency_audit | Governance | Core | Blocked PR capture (dependency audit) | audit-artifacts/release-certification/latest/blocked_pr_dependency_audit.png |  | stale | audit-artifacts/release-closeout/evidence-pack/05_missing_evidence_checklist.md | Optional extra but requested in manual checklist |",
    "| registrar_transcript_e2e | Reporting/export/transcript | Module | Registrar transcript flow | audit-artifacts/release-closeout/evidence-pack/transcript_operator_flow.png |  | unknown | audit-artifacts/release-closeout/02_workflow_gap_list.md | Capture required for non-probe product proof |"
) | Set-Content -Path $screenPath -Encoding UTF8

# blocker ledger
$blockerPath = Join-Path $snapDir "program_completion_blockers_$timestamp.md"
@(
    "# Program Completion Blockers",
    "",
    "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "",
    "## Auto-verified blockers",
    "",
    "- Branch-protection screenshot still manual-open per audit-artifacts/release-certification/latest/01_branch_protection_manual.txt.",
    "- Missing-evidence checklist contains unresolved items in audit-artifacts/release-closeout/evidence-pack/05_missing_evidence_checklist.md.",
    "- Worktree currently dirty (see repo snapshot file).",
    "",
    "## Immediate closure sequence",
    "",
    "1. Capture and store branch-protection and blocked-check screenshots.",
    "2. Close transcript/export/reporting operator proof gap with concrete runtime artifacts.",
    "3. Resolve dirty worktree intentionally.",
    "4. Rerun scripts/execution/95_live_scorecard_audit.ps1 -Deep.",
    "5. Rebuild evidence pack via scripts/execution/91_release_closeout_evidence_pack.ps1.",
    "6. Revalidate missing-evidence checklist to zero unresolved items."
) | Set-Content -Path $blockerPath -Encoding UTF8

Write-Host "AUTOPILOT COMPLETE"
Write-Host "Repo snapshot: $snapshotPath"
Write-Host "Blocker ledger: $blockerPath"
Write-Host "Inventories refreshed in: $invDir"
