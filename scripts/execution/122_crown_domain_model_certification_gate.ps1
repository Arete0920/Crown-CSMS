param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function New-Dir { param([string]$Path) New-Item -ItemType Directory -Force -Path $Path | Out-Null }
function Write-Utf8 { param([string]$Path, [string[]]$Lines) $Lines | Set-Content -Path $Path -Encoding UTF8 }
function Write-JsonFile { param([string]$Path, $Object) ($Object | ConvertTo-Json -Depth 12) | Set-Content -Path $Path -Encoding UTF8 }

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) { throw "Not inside a git repository." }
Set-Location $repoRoot
$branchName = (git branch --show-current 2>$null)
if ([string]::IsNullOrWhiteSpace($branchName)) { $branchName = $env:GITHUB_HEAD_REF }
if ([string]::IsNullOrWhiteSpace($branchName)) { $branchName = $env:GITHUB_REF_NAME }
if ([string]::IsNullOrWhiteSpace($branchName)) { $branchName = "detached-head" } else { $branchName = $branchName.Trim() }
. (Join-Path $repoRoot "scripts/execution/modules/runtime_evidence_validation.ps1")

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot ".crown-audit\domain-model\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\domain-model\latest"
New-Dir $outDir
New-Dir $latestDir

$entities = @(
    "tenant",
    "academic_year",
    "term",
    "person",
    "student",
    "applicant",
    "guardian",
    "household",
    "staff",
    "user_account",
    "course",
    "section",
    "enrollment",
    "attendance_record",
    "assignment",
    "grade",
    "grade_scale",
    "report_card",
    "transcript",
    "invoice",
    "payment",
    "financial_aid_application",
    "financial_aid_award",
    "communication",
    "document",
    "health_visit",
    "medication_allergy",
    "student_care_note",
    "behavior_incident",
    "activity_roster",
    "transportation_route_rider",
    "food_service_meal",
    "library_item_loan",
    "volunteer_record",
    "alumni_record",
    "audit_log"
)

$backendRoot = Join-Path $repoRoot "backend"
$frontendRoot = Join-Path $repoRoot "frontend"
$backendFiles = @()
$frontendFiles = @()
if (Test-Path $backendRoot) {
    $backendFiles = Get-ChildItem $backendRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(py|json|yaml|yml)$" }
}

if (Test-Path $frontendRoot) {
    $frontendFiles = Get-ChildItem $frontendRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(js|jsx|ts|tsx|json)$" }
}

$rows = @()
foreach ($entity in $entities) {
    $tokens = $entity -split "_"
    $backendHits = @()
    foreach ($file in $backendFiles) {
        $text = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
        $hitCount = 0
        foreach ($token in $tokens) {
            if ($file.Name -match $token -or $text -match $token) { $hitCount++ }
        }
        if ($hitCount -ge 1) { $backendHits += $file.FullName }
    }
    $frontendHits = @()
    foreach ($file in $frontendFiles) {
        $text = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
        $hitCount = 0
        foreach ($token in $tokens) {
            if ($file.Name -match $token -or $text -match $token) { $hitCount++ }
        }
        if ($hitCount -ge 1) { $frontendHits += $file.FullName }
    }
    $migrationHits = @($backendHits | Where-Object { $_ -match "migrations" }).Count
    $testHits = @($backendHits + $frontendHits | Where-Object { $_ -match "test|spec" }).Count
    $tenantSignal = @($backendHits | Where-Object { (Get-Content $_ -Raw -ErrorAction SilentlyContinue) -match "tenant|school" }).Count -gt 0
    $permissionSignal = @($backendHits + $frontendHits | Where-Object { (Get-Content $_ -Raw -ErrorAction SilentlyContinue) -match "permission|role|rbac|authorize|auth" }).Count -gt 0
    $status = if ($backendHits.Count -gt 0 -and $migrationHits -gt 0 -and $testHits -gt 0 -and $tenantSignal -and $permissionSignal) { "PROOF_REQUIRED_RUNTIME" } else { "BLOCKED_STATIC_PROOF_INCOMPLETE" }
    $rows += [pscustomobject]@{
        Entity = $entity
        BackendSignalCount = $backendHits.Count
        FrontendSignalCount = $frontendHits.Count
        MigrationSignalCount = $migrationHits
        TestSignalCount = $testHits
        TenantSignal = $tenantSignal
        PermissionSignal = $permissionSignal
        CompletionStatus = $status
    }
}

$runtime = Read-CrownRuntimeEvidence -Gate "domain-model" -Keys $entities -Criteria @("model", "migration", "tenant_boundary", "object_authorization", "api_surface", "workflow_usage", "lifecycle", "audit", "import_export", "retention", "runtime", "current_tests") -OutputDir $outDir
if ($runtime.pass -eq $true) {
    foreach ($row in $rows) {
        if ($row.CompletionStatus -notlike "BLOCKED_*") { $row.CompletionStatus = "PASS" }
    }
}

$missingModelOrMigration = @($rows | Where-Object { $_.BackendSignalCount -eq 0 -or $_.MigrationSignalCount -eq 0 })
$missingTenantOrPermission = @($rows | Where-Object { -not $_.TenantSignal -or -not $_.PermissionSignal })
$nonPass = @($rows | Where-Object { $_.CompletionStatus -ne "PASS" })

$rows | Export-Csv -Path (Join-Path $outDir "10_entity_certification.csv") -NoTypeInformation -Encoding UTF8
$missingModelOrMigration | Export-Csv -Path (Join-Path $outDir "20_missing_model_or_migration.csv") -NoTypeInformation -Encoding UTF8
$missingTenantOrPermission | Export-Csv -Path (Join-Path $outDir "30_missing_tenant_or_permission_proof.csv") -NoTypeInformation -Encoding UTF8

$pass = ($runtime.pass -eq $true -and $nonPass.Count -eq 0)
$summary = @(
    "# CROWN Domain Model Certification Gate",
    "",
    "- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "- Branch: $branchName",
    "- Head: $((git rev-parse HEAD).Trim())",
    "- Entities: $($entities.Count)",
    "- Non-pass rows: $($nonPass.Count)",
    "- Missing model/migration rows: $($missingModelOrMigration.Count)",
    "- Missing tenant/permission rows: $($missingTenantOrPermission.Count)",
    "",
    $(if ($pass) { "PASS" } else { "REVIEW REQUIRED" }),
    "",
    "This gate intentionally fails until each core SIS entity has current model, migration, tenant, permission, test, and runtime proof."
)
Write-Utf8 -Path (Join-Path $outDir "00_SUMMARY.md") -Lines $summary

$status = [ordered]@{
    runtime_evidence_errors = @($runtime.errors)
    generated_at = (Get-Date).ToString("s")
    branch = $branchName
    head = (git rev-parse HEAD).Trim()
    pass = $pass
    entity_count = $entities.Count
    non_pass_count = $nonPass.Count
    missing_model_or_migration_count = $missingModelOrMigration.Count
    missing_tenant_or_permission_count = $missingTenantOrPermission.Count
    entities = $rows
}
Write-JsonFile -Path (Join-Path $outDir "99_STATUS.json") -Object $status
Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host "DONE"
Write-Host "SUMMARY: $(Join-Path $outDir '00_SUMMARY.md')"
Write-Host "STATUS:  $(Join-Path $outDir '99_STATUS.json')"
if (-not $pass) { exit 1 }
