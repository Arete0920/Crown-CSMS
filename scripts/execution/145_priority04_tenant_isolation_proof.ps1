$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
# ============================================================
# CROWN PRIORITY 4 -- TENANT ISOLATION PROOF PACK
# Non-Azure. Local/static/API-aware proof builder.
# ============================================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
Set-Location $Root
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Out   = Join-Path $Root "audit-artifacts\priority-04-tenant-isolation\$Stamp"
$Docs  = Join-Path $Root "docs\crown-master-binder"
$Ops   = "$Docs\operations"
$Sec   = "$Docs\security"
$Inv   = "$Docs\inventory"
New-Item -ItemType Directory -Force -Path $Out,$Ops,$Sec,$Inv | Out-Null
Start-Transcript -Path "$Out\00_RUN_LOG.txt" -Force | Out-Null
Write-Host "CROWN Priority 4 -- Tenant Isolation Proof"
Write-Host "Repo:   $Root"
Write-Host "Output: $Out"

# ------------------------------------------------------------
# 01. Repo state
# ------------------------------------------------------------
$Branch   = git branch --show-current
$Head     = git rev-parse --short HEAD
$HeadFull = git rev-parse HEAD
git status --short    | Set-Content "$Out\01_git_status_before.txt" -Encoding UTF8
git status            | Set-Content "$Out\02_git_status_full.txt"   -Encoding UTF8
git log --oneline -20 | Set-Content "$Out\03_recent_commits.txt"    -Encoding UTF8

# ------------------------------------------------------------
# 02. Collect source files (exclude artifacts/deps)
# ------------------------------------------------------------
$Excluded = @('\.git','node_modules','\\dist\\','\\build\\','coverage','\.venv','\\venv\\','__pycache__','audit-artifacts')
$Files = Get-ChildItem -Recurse -File | Where-Object {
    $p = $_.FullName
    $ok = $true
    foreach ($e in $Excluded) { if ($p -match $e) { $ok = $false } }
    $ok -and ($_.Extension.ToLowerInvariant() -in @('.py','.ts','.tsx','.js','.jsx','.json','.yml','.yaml','.md'))
}

# ------------------------------------------------------------
# 03. Search function
# ------------------------------------------------------------
function Search-Code {
    param([array]$Patterns, [string]$Type, [string]$Output)
    $rows = @()
    foreach ($f in $Files) {
        try {
            $hits = Select-String -Path $f.FullName -Pattern $Patterns -AllMatches -ErrorAction SilentlyContinue
            foreach ($h in $hits) {
                $rows += [pscustomobject]@{
                    Type = $Type
                    File = $f.FullName.Replace($Root,'').TrimStart('\')
                    Line = $h.LineNumber
                    Text = $h.Line.Trim()
                }
            }
        } catch {}
    }
    $rows | Export-Csv $Output -NoTypeInformation
    return $rows
}

$TenantPatterns = @('tenant','Tenant','school_id','schoolId','schoolContext','SchoolContext',
    'X-School-Id','x-school-id','request\.school','request\.tenant','current_school',
    'currentSchool','organization_id','org_id','campus_id')

$RiskPatterns = @('\.objects\.all\(\)','\.all\(\)','get_queryset','queryset\s*=','ModelViewSet',
    'APIView','ListAPIView','RetrieveAPIView','filter_backends','permission_classes',
    'AllowAny','IsAuthenticated','school_id=None','tenant_id=None',
    'bypass','skip_tenant','ignore_tenant','withoutTenant','without_tenant')

$ApiPatterns = @('urlpatterns','path\(','router\.register','ViewSet','APIView',
    'ListAPIView','RetrieveAPIView','CreateAPIView','UpdateAPIView','DestroyAPIView',
    'api_view','fetch\(','axios\.','api/')

$PermPatterns = @('permission_classes','IsAuthenticated','IsAdmin','role','Role',
    'RBAC','has_perm','can_view','can_edit','require_role','allowed_roles')

$TenantSignals = Search-Code -Type 'Tenant isolation signal'  -Output "$Out\10_tenant_isolation_signals.csv"     -Patterns $TenantPatterns
$RiskSignals   = Search-Code -Type 'Possible tenant bypass'   -Output "$Out\11_possible_tenant_bypass_risks.csv" -Patterns $RiskPatterns
$ApiSignals    = Search-Code -Type 'API endpoint signal'      -Output "$Out\12_api_view_signals.csv"             -Patterns $ApiPatterns
$PermSignals   = Search-Code -Type 'Permission / RBAC signal' -Output "$Out\13_permission_signals.csv"           -Patterns $PermPatterns

Write-Host "Tenant signals: $($TenantSignals.Count)"
Write-Host "Risk signals:   $($RiskSignals.Count)"
Write-Host "API signals:    $($ApiSignals.Count)"
Write-Host "Perm signals:   $($PermSignals.Count)"

# ------------------------------------------------------------
# 04. Entity map
# ------------------------------------------------------------
$Entities = @('Student','Household','Guardian','Parent','Enrollment','Applicant',
    'Attendance','Grade','Transcript','Invoice','Payment','Charge','Balance',
    'Message','Announcement','Document','Staff','Teacher','Section','Course','Roster')

$EntityRows = foreach ($ent in $Entities) {
    $tHits = @($TenantSignals | Where-Object { $_.Text -match $ent -or $_.File -match $ent }).Count
    $rHits = @($RiskSignals   | Where-Object { $_.Text -match $ent -or $_.File -match $ent }).Count
    $owner = if ($ent -match 'Invoice|Payment|Charge|Balance') { 'Dev 3 / Dev 1' }
             elseif ($ent -match 'Student|Household|Guardian|Enrollment|Attendance|Grade|Transcript|Section|Course|Roster') { 'Dev 2 / Dev 1' }
             else { 'Dev 1 / Dev 5' }
    [pscustomobject]@{
        Entity            = $ent
        TenantSignalCount = $tHits
        RiskSignalCount   = $rHits
        RequiredRule      = 'Must always be scoped to school/tenant context.'
        Owner             = $owner
        Status            = 'Review'
    }
}
$EntityRows | Export-Csv "$Out\14_tenant_sensitive_entity_map.csv" -NoTypeInformation
Copy-Item "$Out\14_tenant_sensitive_entity_map.csv" "$Inv\TENANT_SENSITIVE_ENTITY_MAP.csv" -Force

# ------------------------------------------------------------
# 05. Manual proof matrix
# ------------------------------------------------------------
$ProofMatrix = @(
    [pscustomobject]@{ ProofId='TI-001'; Area='Student Records'; Test='School A admin cannot access School B student by URL/API id.'; Expected='403/404 or tenant-safe redirect'; Owner='Dev 1/Dev 2/Dev 5'; Status='Open'; Evidence='' }
    [pscustomobject]@{ ProofId='TI-002'; Area='Households'; Test='School A parent cannot access School B household record.'; Expected='403/404 or tenant-safe redirect'; Owner='Dev 1/Dev 2/Dev 5'; Status='Open'; Evidence='' }
    [pscustomobject]@{ ProofId='TI-003'; Area='Enrollment'; Test='School A admissions user cannot view School B enrollment data.'; Expected='403/404 or tenant-safe redirect'; Owner='Dev 1/Dev 2/Dev 3'; Status='Open'; Evidence='' }
    [pscustomobject]@{ ProofId='TI-004'; Area='Billing'; Test='School A finance user cannot view School B invoices/payments/balances.'; Expected='403/404 or tenant-safe redirect'; Owner='Dev 1/Dev 3/Dev 5'; Status='Open'; Evidence='' }
    [pscustomobject]@{ ProofId='TI-005'; Area='Attendance'; Test='Teacher in School A cannot view/post attendance for School B section.'; Expected='403/404 or tenant-safe redirect'; Owner='Dev 1/Dev 2/Dev 5'; Status='Open'; Evidence='' }
    [pscustomobject]@{ ProofId='TI-006'; Area='Grades'; Test='Teacher in School A cannot view/post grades for School B roster.'; Expected='403/404 or tenant-safe redirect'; Owner='Dev 1/Dev 2/Dev 5'; Status='Open'; Evidence='' }
    [pscustomobject]@{ ProofId='TI-007'; Area='Communications'; Test='School A user cannot view School B messages/announcements.'; Expected='403/404 or tenant-safe redirect'; Owner='Dev 1/Dev 3/Dev 5'; Status='Open'; Evidence='' }
    [pscustomobject]@{ ProofId='TI-008'; Area='Dashboard KPIs'; Test='School A dashboard cannot aggregate School B data.'; Expected='Counts only reflect active school context'; Owner='Dev 1/Dev 4/Dev 5'; Status='Open'; Evidence='' }
    [pscustomobject]@{ ProofId='TI-009'; Area='Files/Documents'; Test='School A user cannot download School B document/file.'; Expected='403/404 or tenant-safe redirect'; Owner='Dev 1/Dev 5'; Status='Open'; Evidence='' }
    [pscustomobject]@{ ProofId='TI-010'; Area='School Switcher'; Test='Context switch only works for explicitly authorized multi-school user.'; Expected='Unauthorized switch denied'; Owner='Dev 1/Dev 5'; Status='Open'; Evidence='' }
)
$ProofMatrix | Export-Csv "$Out\15_tenant_isolation_manual_proof_matrix.csv" -NoTypeInformation
Copy-Item "$Out\15_tenant_isolation_manual_proof_matrix.csv" "$Ops\TENANT_ISOLATION_PROOF_MATRIX.csv" -Force

# ------------------------------------------------------------
# 06. Static risk scoring
# ------------------------------------------------------------
$Blockers = [System.Collections.Generic.List[pscustomobject]]::new()
function Add-Blocker([string]$Pri,[string]$Area,[string]$Issue,[string]$Owner,[string]$Ev,[string]$Fix) {
    $script:Blockers.Add([pscustomobject]@{Priority=$Pri;Area=$Area;Issue=$Issue;Owner=$Owner;Evidence=$Ev;RequiredFix=$Fix;Status='Open'})
}

function Test-CommentLikeRiskRow([string]$Text) {
    $trimmed = ($Text | ForEach-Object { $_.Trim() })
    return (
        $trimmed.StartsWith('#') -or
        $trimmed.StartsWith('//') -or
        $trimmed.StartsWith('/*') -or
        $trimmed.StartsWith('*') -or
        $trimmed.StartsWith('"""') -or
        $trimmed.StartsWith("'''")
    )
}

$HighRiskRows = @($RiskSignals | Where-Object {
    ($_.File -notmatch '(^|\\)(tests?|docs|audit-artifacts)(\\|$)') -and
    ($_.File -match 'views|api|serializers|routers|urls|viewsets|client|service') -and
    (-not (Test-CommentLikeRiskRow $_.Text)) -and
    ($_.Text -match '\.objects\.all\(\)|skip_tenant|ignore_tenant|without_tenant|withoutTenant')
})
$HighRiskRows | Export-Csv "$Out\16_high_risk_tenant_review_rows.csv" -NoTypeInformation
Write-Host "High-risk rows: $($HighRiskRows.Count)"

if ($HighRiskRows.Count -gt 0) {
    Add-Blocker 'P0' 'Tenant isolation' "$($HighRiskRows.Count) executable high-risk rows in API/view/service paths." 'Dev 1/Dev 5' "$Out\16_high_risk_tenant_review_rows.csv" 'Verify tenant scoping or fix query/permission logic.'
}
if ($TenantSignals.Count -eq 0) {
    Add-Blocker 'P0' 'Tenant isolation' 'No tenant/school context signals found.' 'Dev 1' "$Out\10_tenant_isolation_signals.csv" 'Implement tenant isolation layer before release.'
}
if ($ApiSignals.Count -eq 0) {
    Add-Blocker 'P1' 'API inventory' 'No API/view route signals found.' 'Dev 1/Dev 5' "$Out\12_api_view_signals.csv" 'Confirm route structure and rerun.'
}
if ($PermSignals.Count -eq 0) {
    Add-Blocker 'P0' 'RBAC/permissions' 'No permission/RBAC signals found.' 'Dev 1' "$Out\13_permission_signals.csv" 'Implement permission enforcement before release.'
}
foreach ($e in $EntityRows) {
    if ([int]$e.RiskSignalCount -gt 0 -and [int]$e.TenantSignalCount -eq 0) {
        Add-Blocker 'P1' 'Tenant-sensitive entity' ("$($e.Entity): risk signals present but no tenant signal.") $e.Owner "$Out\14_tenant_sensitive_entity_map.csv" 'Verify scoping for this entity.'
    }
}

$Blockers | Sort-Object Priority,Area | Export-Csv "$Out\17_TENANT_ISOLATION_BLOCKER_BOARD.csv" -NoTypeInformation
Copy-Item "$Out\17_TENANT_ISOLATION_BLOCKER_BOARD.csv" "$Ops\TENANT_ISOLATION_BLOCKER_BOARD.csv" -Force

# ------------------------------------------------------------
# 07. Write tenant isolation standard (array of strings, no here-string)
# ------------------------------------------------------------
$StdLines = @(
    "# CROWN Tenant Isolation Standard",
    "",
    ("Generated: " + (Get-Date -Format s)),
    "",
    "## Rule",
    "",
    "Every school-owned record must be scoped to the active school or tenant context on both",
    "backend and frontend. Frontend filtering alone is not sufficient; backend enforcement is mandatory.",
    "",
    "## Tenant-Sensitive Domains",
    "",
    "Students, Households, Guardians/Parents, Staff/Faculty, Applicants, Enrollment,",
    "Attendance, Grades, Transcripts, Billing (invoices/charges/payments/balances),",
    "Communications (messages/announcements), Files/Documents, Courses/Sections/Rosters,",
    "Dashboards and KPI aggregations.",
    "",
    "## Required Enforcement",
    "",
    "1. Backend querysets must filter by active tenant/school context.",
    "2. Detail endpoints must reject cross-tenant ids.",
    "3. List endpoints must return only active school data.",
    "4. Create/update endpoints must assign or validate school context.",
    "5. Delete/archive endpoints must verify school ownership.",
    "6. Dashboard aggregations must be tenant-scoped.",
    "7. File/document download endpoints must verify tenant ownership.",
    "8. School switcher must reject unauthorized context switching.",
    "9. RBAC and tenant isolation must both pass; one does not replace the other.",
    "",
    "## Release Gate",
    "",
    "No production GO until all TI-001 through TI-010 proof rows are PASS with evidence.",
    "",
    "## Generated Evidence",
    "",
    ("Tenant signals:  " + "$Out\10_tenant_isolation_signals.csv"),
    ("Bypass risks:    " + "$Out\11_possible_tenant_bypass_risks.csv"),
    ("API signals:     " + "$Out\12_api_view_signals.csv"),
    ("Perm signals:    " + "$Out\13_permission_signals.csv"),
    ("Entity map:      " + "$Out\14_tenant_sensitive_entity_map.csv"),
    ("Proof matrix:    " + "$Out\15_tenant_isolation_manual_proof_matrix.csv"),
    ("High-risk rows:  " + "$Out\16_high_risk_tenant_review_rows.csv"),
    ("Blocker board:   " + "$Out\17_TENANT_ISOLATION_BLOCKER_BOARD.csv")
)
$StdLines | Set-Content "$Sec\TENANT_ISOLATION_STANDARD.md" -Encoding UTF8
Copy-Item "$Sec\TENANT_ISOLATION_STANDARD.md" "$Out\18_TENANT_ISOLATION_STANDARD.md" -Force

# ------------------------------------------------------------
# 08. Summary (array of strings, no here-string)
# ------------------------------------------------------------
$P0 = @($Blockers | Where-Object { $_.Priority -eq 'P0' }).Count
$P1 = @($Blockers | Where-Object { $_.Priority -eq 'P1' }).Count
$P2 = @($Blockers | Where-Object { $_.Priority -eq 'P2' }).Count
$Decision = if ($P0 -eq 0) { 'TENANT_STATIC_REVIEW_PASS_MANUAL_PROOF_REQUIRED' } else { 'TENANT_STATIC_REVIEW_P0_REMEDIATION_REQUIRED' }

$BlockerTable = if ($Blockers.Count -gt 0) {
    ($Blockers | Sort-Object Priority,Area | Format-Table Priority,Area,Issue -AutoSize | Out-String).Trim()
} else { "(none)" }

$SumLines = @(
    "# CROWN Priority 4 -- Tenant Isolation Proof Summary",
    "",
    ("Generated: " + (Get-Date -Format s)),
    ("Repo:      $Root"),
    ("Branch:    $Branch"),
    ("HEAD:      $Head"),
    ("HEAD_FULL: $HeadFull"),
    "",
    "## Decision",
    "",
    $Decision,
    "",
    "## Counts",
    "",
    ("Tenant isolation signals:  " + $TenantSignals.Count),
    ("Possible bypass/risk:      " + $RiskSignals.Count),
    ("API/view signals:          " + $ApiSignals.Count),
    ("Permission/RBAC signals:   " + $PermSignals.Count),
    ("High-risk tenant rows:     " + $HighRiskRows.Count),
    ("P0 blockers:               $P0"),
    ("P1 blockers:               $P1"),
    ("P2 blockers:               $P2"),
    "",
    "## Important",
    "",
    "This is STATIC/LOCAL proof only. It does not replace browser/API runtime proof.",
    "Production readiness requires TI-001 through TI-010 executed in a running environment.",
    "",
    "## Open First",
    "",
    ("1. $Out\17_TENANT_ISOLATION_BLOCKER_BOARD.csv"),
    ("2. $Out\16_high_risk_tenant_review_rows.csv"),
    ("3. $Out\15_tenant_isolation_manual_proof_matrix.csv"),
    ("4. $Sec\TENANT_ISOLATION_STANDARD.md"),
    "",
    "## Blockers",
    "",
    $BlockerTable
)
$SumLines | Set-Content "$Out\99_SUMMARY.md" -Encoding UTF8
Copy-Item "$Out\99_SUMMARY.md" "$Ops\TENANT_ISOLATION_CURRENT_SUMMARY.md" -Force

git status --short | Set-Content "$Out\90_git_status_after.txt" -Encoding UTF8

# ------------------------------------------------------------
# 09. Open outputs
# ------------------------------------------------------------
code "$Out\99_SUMMARY.md"
code "$Out\17_TENANT_ISOLATION_BLOCKER_BOARD.csv"
code "$Out\16_high_risk_tenant_review_rows.csv"
code "$Out\15_tenant_isolation_manual_proof_matrix.csv"
code "$Sec\TENANT_ISOLATION_STANDARD.md"

Write-Host ""
Write-Host "CROWN Priority 4 Tenant Isolation Proof Pack complete."
Write-Host "Decision: $Decision"
Write-Host "Output:   $Out"
Write-Host ""
Stop-Transcript | Out-Null
