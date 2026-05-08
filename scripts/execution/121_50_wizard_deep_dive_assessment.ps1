param(
    [string]$OutRoot = "audit-artifacts\50-wizard-deep-dive",
    [switch]$Open
)

$ErrorActionPreference = "Stop"

function New-Stamp {
    Get-Date -Format "yyyyMMdd_HHmmss"
}

function Normalize-Key {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return "" }
    $v = $Value.ToLowerInvariant()
    $v = $v -replace "wizard", ""
    $v = $v -replace "re-enrollment", "reenrollment"
    $v = $v -replace "communications", "communication"
    $v = $v -replace "guardian and household", "guardian household"
    $v = $v -replace "staff and roles", "staff roles"
    $v = $v -replace "crown compass", "compass"
    $v = $v -replace "[^a-z0-9]+", ""
    $v.Trim()
}

function Test-ExcludedPath {
    param([string]$Path)
    $p = $Path.ToLowerInvariant()
    $excluded = @(
        "\.git\", "\node_modules\", "\dist\", "\build\", "\.next\", "\coverage\",
        "\.venv\", "\venv\", "\__pycache__\", "\.pytest_cache\", "\audit-artifacts\"
    )
    foreach ($x in $excluded) {
        if ($p -like "*$x*") { return $true }
    }
    $false
}

function Score-Wizard {
    param($Row)
    $score = 0
    $max = 12
    if ($Row.HasRegistry) { $score++ }
    if ($Row.HasRoute) { $score++ }
    if ($Row.HasFrontend) { $score++ }
    if ($Row.HasApiOrService) { $score++ }
    if ($Row.HasModelOrSchema) { $score++ }
    if ($Row.HasPermission) { $score++ }
    if ($Row.HasTenantGuard) { $score++ }
    if ($Row.HasKpiOrMetric) { $score++ }
    if ($Row.HasSeedOrDemo) { $score++ }
    if ($Row.HasTests) { $score++ }
    if ($Row.HasDocs) { $score++ }
    if ($Row.HasAuditOrLogging) { $score++ }

    $pct = [math]::Round(($score / $max) * 100, 2)
    $status = if ($score -ge 11) {
        "PASS"
    } elseif ($score -ge 7) {
        "REVIEW"
    } elseif ($score -ge 1) {
        "FAIL_PARTIAL"
    } else {
        "FAIL_MISSING"
    }

    [pscustomobject]@{
        Score = $score
        MaxScore = $max
        ScorePct = $pct
        Status = $status
    }
}

$WizardCsv = @'
N,Name,Layer,Domain,Function,Operation,PrimaryKPI,SecondaryKPI
1,"Billing Wizard","Core / Module","Billing","Create and manage billing workflow setup","Configure billing flow, review account state, submit billing actions","Billing completion rate","Open balance accuracy"
2,"Billing Setup Wizard","Core / Module","Billing","Set initial billing configuration","Configure billing terms, cadence, rules, defaults","Setup completion rate","Billing configuration error count"
3,"Financial Aid Wizard","Module","Financial Aid","Guide aid application and review","Collect aid inputs, validate documents, route review","Aid application completion rate","Aid review cycle time"
4,"Aid Wizard","Module","Financial Aid","Support aid award processing","Review aid eligibility, package award, record decision","Aid decision completion rate","Incomplete aid file count"
5,"Scheduling Wizard","Module","Scheduling","Build or adjust master schedule","Assign sections, periods, rooms, teachers","Schedule conflict count","Schedule completion rate"
6,"Communications Wizard","Module","Communications","Create targeted school communications","Select audience, channel, message, delivery window","Message delivery success rate","Audience targeting accuracy"
7,"Section Assign Wizard","Core / Module","Sections","Assign students to sections","Select course/section, place students, validate roster","Roster completion rate","Roster conflict count"
8,"Bell Schedule Wizard","Module","Scheduling","Configure bell schedule","Create periods, times, exceptions, day patterns","Bell schedule validity","Schedule exception count"
9,"Gradebook Setup Wizard","Core / Module","Gradebook","Configure gradebook settings","Set categories, weights, grading rules","Gradebook setup completion","Invalid gradebook configuration count"
10,"Attendance Rules Wizard","Core","Attendance","Configure attendance codes and rules","Define attendance states, rules, notifications","Attendance rule validity","Attendance exception count"
11,"Enrollment Conversion Wizard","Core / Module","Enrollment","Convert applicant/admitted student to enrolled student","Validate records, confirm household, assign year/grade/status","Conversion completion rate","Conversion error count"
12,"Invoice Run Wizard","Module","Billing","Generate invoice batch","Select billing population, preview, validate, post invoices","Invoice run success rate","Invoice exception count"
13,"Staff Onboarding Wizard","Core / Module","Staff","Onboard staff user and assignments","Create staff profile, role, school access, assignment","Staff onboarding completion","Permission setup error count"
14,"Fee Schedule Wizard","Module","Billing","Configure tuition and fee schedules","Create fee tables, grades, charges, effective dates","Fee schedule validity","Fee mismatch count"
15,"Academic Year Rollover Wizard","Core","Academic Year","Roll school year forward","Create new year, terms, statuses, promotion path","Rollover completion rate","Rollover exception count"
16,"Enrollment Period Wizard","Module","Enrollment","Configure enrollment windows","Open/close period, eligibility, deadlines, forms","Enrollment period readiness","Late/incomplete enrollment count"
17,"Grade Scale Wizard","Core / Module","Gradebook","Configure grade scales","Define letter/numeric scale, thresholds, GPA mapping","Grade scale validity","Grade calculation exception count"
18,"Term Structure Wizard","Core","Academic Year","Configure terms","Create quarters/semesters, dates, reporting periods","Term setup validity","Term overlap/conflict count"
19,"Section Scheduler Wizard","Module","Scheduling","Schedule course sections","Place teachers, rooms, periods, students","Section schedule completion","Teacher/room conflict count"
20,"Staff & Roles Wizard","Core","Identity / RBAC","Configure staff roles","Assign role, permission group, school access","Role assignment accuracy","Unauthorized access finding count"
21,"Course Catalog Wizard","Core / Module","Academics","Build course catalog","Create courses, credits, grade levels, prerequisites","Course catalog completion","Invalid course metadata count"
22,"Rooms Setup Wizard","Module","Facilities","Configure rooms and spaces","Create room inventory, capacity, availability","Room setup completion","Room scheduling conflict count"
23,"Promotion Map Wizard","Core","Enrollment","Map grade promotion rules","Define grade progression and exceptions","Promotion map validity","Promotion exception count"
24,"Student Import Wizard","Core","Student Records","Import student records","Upload, map, validate, preview, import","Import success rate","Rejected row count"
25,"Guardian & Household Wizard","Core","Household","Create family and guardian relationships","Create household, guardians, contacts, custody/access flags","Household record completion","Duplicate guardian/household count"
26,"Section Staffing Wizard","Module","Scheduling","Assign staff to sections","Map teacher/staff to sections and periods","Section staffing completion","Unstaffed section count"
27,"Attendance Codes Wizard","Core","Attendance","Configure attendance codes","Create present/absent/tardy/excused codes","Attendance code validity","Unmapped attendance code count"
28,"Grade Weights Wizard","Module","Gradebook","Configure grade weights","Set assignment categories and weighting rules","Grade weight validity","Grade calculation error count"
29,"Finance Setup Wizard","Module","Finance","Configure finance defaults","Set accounts, payment rules, fee defaults","Finance setup completion","Finance configuration exception count"
30,"Discipline Escalation Wizard","Module","Discipline / Student Care","Guide discipline escalation workflow","Record incident, assign severity, notify stakeholders, route intervention","Incident resolution cycle time","Escalation compliance rate"
31,"Transcript / Graduation Wizard","Core / Module","Transcript / Graduation","Guide transcript and graduation review","Validate credits, requirements, status, transcript output","Graduation requirement completion","Transcript exception count"
32,"PDF Export / Institutional Output Wizard","Platform","Exports","Generate official institutional output","Select report/export, validate data, generate PDF/packet","Export success rate","Export failure count"
33,"Crown Compass Trigger / Response Wizard","Add-on","Crown Compass","Trigger and manage Compass response","Review signal, assign response, track follow-up","Signal response completion","Unresolved critical signal count"
34,"Live Metrics Aggregation Review Wizard","Platform / Add-on","Analytics","Review KPI aggregation health","Validate metric source, calculation, freshness, display","Metric freshness rate","Broken KPI count"
35,"Admissions Pipeline Wizard","Module","Admissions","Manage inquiry-to-decision pipeline","Advance applicant through inquiry, checklist, review, decision","Applicant conversion rate","Application completion rate"
36,"Re-enrollment Contract Wizard","Module","Re-enrollment","Guide returning family contract process","Review student, confirm terms, sign contract, collect deposit","Re-enrollment completion rate","Unsigned contract count"
37,"Activities / Events Wizard","Module","Activities / Events","Create and manage school activities/events","Create event, eligibility, registration, roster, communications","Event registration completion","Event roster accuracy"
38,"Nurse / Health Office Wizard","Module","Health Office","Guide health office records and actions","Review student health flags, log visit, action outcome","Health visit documentation rate","Unresolved health alert count"
39,"Transportation Wizard","Module","Transportation","Configure transportation assignments","Assign route, stop, student, schedule, contacts","Route assignment completion","Transportation conflict count"
40,"Food Services Wizard","Module","Food Services","Configure lunch/food service operations","Set menu/account/eligibility/order/payment flow","Meal order completion","Food account exception count"
41,"Volunteer / Family Engagement Wizard","Module","Volunteer / Engagement","Coordinate volunteer/family engagement","Create opportunity, eligibility, signup, approval, tracking","Volunteer slot fill rate","Unapproved volunteer count"
42,"Board Governance Packet Wizard","Add-on","Board Governance","Build board governance packet","Select reports, KPIs, agenda, risks, approvals","Board packet completion","Board action item closure rate"
43,"Spiritual Life Tracking Wizard","Add-on","Spiritual Life","Track spiritual life programs and indicators","Configure program, participation, observations, follow-up","Spiritual life participation rate","Follow-up completion rate"
44,"Service / Outreach Wizard","Add-on","Service / Outreach","Manage service/outreach programs","Create opportunity, student participation, hours, reflection","Service hour completion","Outreach participation rate"
45,"Portrait of the Graduate Wizard","Add-on","Portrait of the Graduate","Configure graduate outcome framework","Define outcomes, evidence, scoring, reporting","Outcome evidence completion","Graduate profile readiness"
46,"Pastoral / Chaplain Care Wizard","Add-on","Pastoral Care","Guide pastoral care workflow","Create care concern, confidentiality level, follow-up, resolution","Care follow-up completion","Open care concern age"
47,"Christian PD Hub Wizard","Add-on","PD Hub","Guide professional development setup and participation","Assign PD path, track completion, collect reflection","PD completion rate","Assigned PD overdue count"
48,"Mission-Fit Dashboard Setup Wizard","Add-on","Mission Metrics","Configure mission-fit dashboard","Select metrics, sources, targets, dashboard visibility","Mission metric coverage","Metric target attainment"
49,"School Health / Compass Assessment Wizard","Add-on","Crown Compass","Run school health assessment","Collect assessment, score results, recommend next actions","Assessment completion rate","Priority action closure rate"
50,"Solomon Guided Implementation Wizard","Platform / Add-on","Solomon","Guide implementation onboarding training support and readiness","Select school path, role training, templates, walkthroughs, support triage, readiness proof","Implementation readiness completion","Open onboarding/support blockers"
'@

$WizardScope = $WizardCsv | ConvertFrom-Csv

$Stamp = New-Stamp
$OutDir = Join-Path $OutRoot $Stamp
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$RepoRoot = (Get-Location).Path
$Branch = git branch --show-current 2>$null
$Head = git rev-parse HEAD 2>$null

@"
GeneratedAt: $((Get-Date).ToString("s"))
RepoRoot: $RepoRoot
Branch: $Branch
HEAD: $Head
Scope: 50 parent wizard rows
"@ | Set-Content (Join-Path $OutDir "00_REPO_AND_SCOPE.txt")

$WizardScope | Export-Csv (Join-Path $OutDir "01_50_WIZARD_MASTER_SCOPE.csv") -NoTypeInformation

$AllowedExtensions = @(".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".yml", ".yaml", ".html", ".css", ".scss", ".txt")

$ScanRoots = @("backend", "frontend", "scripts", "docs", ".github", "tests")
$ExistingScanRoots = @($ScanRoots | Where-Object { Test-Path $_ })

$rg = Get-Command rg -ErrorAction SilentlyContinue
if ($rg) {
    $rgFiles = & rg --files @ExistingScanRoots 2>$null
    $AllFiles = foreach ($path in $rgFiles) {
        if (!(Test-Path $path)) { continue }
        $fi = Get-Item -Force $path
        if ($fi.PSIsContainer) { continue }
        if (Test-ExcludedPath $fi.FullName) { continue }
        $ext = [string]$fi.Extension
        if ($AllowedExtensions -contains $ext.ToLowerInvariant()) {
            $fi
        }
    }
} else {
    $AllFiles = foreach ($root in $ExistingScanRoots) {
        Get-ChildItem -Path $root -Recurse -File -Force |
            Where-Object {
                -not (Test-ExcludedPath $_.FullName) -and
                $AllowedExtensions -contains $_.Extension.ToLowerInvariant()
            }
    }
}

$FileIndex = foreach ($File in $AllFiles) {
    $relative = [string](Resolve-Path -Relative $File.FullName)
    if ([string]::IsNullOrWhiteSpace($relative)) { $relative = [string]$File.FullName }
    $ext = [string]$File.Extension
    if ($null -eq $ext) { $ext = "" }
    [pscustomobject]@{
        Path = $relative
        Extension = $ext.ToLowerInvariant()
        SizeBytes = $File.Length
        Content = ""
        Lower = ""
    }
}

$EvidenceRows = foreach ($wiz in $WizardScope) {
    $key = Normalize-Key $wiz.Name
    $tokens = @($wiz.Name, ($wiz.Name -replace " Wizard", ""), $wiz.Domain, $key) |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
        Sort-Object -Unique

    $hits = New-Object System.Collections.Generic.List[object]

    foreach ($f in $FileIndex) {
        $pathLower = $f.Path.ToLowerInvariant()
        $contentLower = $f.Lower
        $matched = $false

        foreach ($t in $tokens) {
            $tl = $t.ToLowerInvariant()
            $tk = Normalize-Key $t
            if ($tl.Length -ge 4 -and ($pathLower -like "*$tl*" -or $contentLower -like "*$tl*")) { $matched = $true }
            if ($tk.Length -ge 5 -and (($pathLower -replace "[^a-z0-9]", "") -like "*$tk*")) { $matched = $true }
            if ($tk.Length -ge 5 -and (($contentLower -replace "[^a-z0-9]", "") -like "*$tk*")) { $matched = $true }
        }

        if ($matched) { $hits.Add($f) }
    }

    $paths = @($hits | ForEach-Object { $_.Path } | Sort-Object -Unique)
    $joinedContent = (($hits | ForEach-Object { $_.Lower }) -join "`n")
    $joinedPaths = ($paths -join " | ").ToLowerInvariant()
    $all = "$joinedPaths`n$joinedContent"

    $row = [pscustomobject]@{
        N = [int]$wiz.N
        Wizard = $wiz.Name
        Layer = $wiz.Layer
        Domain = $wiz.Domain
        ExpectedFunction = $wiz.Function
        ExpectedOperation = $wiz.Operation
        PrimaryKPI = $wiz.PrimaryKPI
        SecondaryKPI = $wiz.SecondaryKPI
        SourceHitCount = $paths.Count
        HasRegistry = [bool]($all -match "wizard.*registry|registry.*wizard|wizard_registry|wizardregistry|manifest")
        HasRoute = [bool]($all -match "route|router|path\(|urlpatterns|sidebar|navigation|nav")
        HasFrontend = [bool]($paths | Where-Object { $_ -match "\.(tsx|jsx|ts|js|html)$" -and $_ -notmatch "(?i)test|spec" })
        HasApiOrService = [bool]($all -match "api|endpoint|service|controller|viewset|serializer|handler|mutation|query")
        HasModelOrSchema = [bool]($all -match "model|schema|migration|entity|table|interface|type ")
        HasPermission = [bool]($all -match "permission|rbac|role|authorize|policy|can\(|allowed|access")
        HasTenantGuard = [bool]($all -match "tenant|school_id|schoolid|x-school-id|organization|org_id")
        HasKpiOrMetric = [bool]($all -match "kpi|metric|measure|dashboard|score|rate|count|aggregation|aggregate")
        HasSeedOrDemo = [bool]($all -match "seed|fixture|factory|demo|sandbox|sample")
        HasTests = [bool]($paths | Where-Object { $_ -match "(?i)test|spec|playwright|pytest|jest|vitest|e2e" })
        HasDocs = [bool]($paths | Where-Object { $_ -match "\.(md|txt)$" -or $_ -match "(?i)docs|canon|readme|matrix|inventory" })
        HasAuditOrLogging = [bool]($all -match "audit|log|event|history|trace")
        EvidencePaths = ($paths -join " | ")
    }

    $score = Score-Wizard $row

    [pscustomobject]@{
        N = $row.N
        Wizard = $row.Wizard
        Layer = $row.Layer
        Domain = $row.Domain
        ExpectedFunction = $row.ExpectedFunction
        ExpectedOperation = $row.ExpectedOperation
        PrimaryKPI = $row.PrimaryKPI
        SecondaryKPI = $row.SecondaryKPI
        Score = $score.Score
        MaxScore = $score.MaxScore
        ScorePct = $score.ScorePct
        Status = $score.Status
        SourceHitCount = $row.SourceHitCount
        HasRegistry = $row.HasRegistry
        HasRoute = $row.HasRoute
        HasFrontend = $row.HasFrontend
        HasApiOrService = $row.HasApiOrService
        HasModelOrSchema = $row.HasModelOrSchema
        HasPermission = $row.HasPermission
        HasTenantGuard = $row.HasTenantGuard
        HasKpiOrMetric = $row.HasKpiOrMetric
        HasSeedOrDemo = $row.HasSeedOrDemo
        HasTests = $row.HasTests
        HasDocs = $row.HasDocs
        HasAuditOrLogging = $row.HasAuditOrLogging
        EvidencePaths = $row.EvidencePaths
    }
}

$EvidenceRows | Sort-Object N | Export-Csv (Join-Path $OutDir "02_50_WIZARD_DEEP_DIVE_ASSESSMENT.csv") -NoTypeInformation

$FixQueue = foreach ($row in $EvidenceRows | Sort-Object N) {
    $missing = New-Object System.Collections.Generic.List[string]
    if (-not $row.HasRegistry) { $missing.Add("central registry/manifest entry") }
    if (-not $row.HasRoute) { $missing.Add("route/navigation wiring") }
    if (-not $row.HasFrontend) { $missing.Add("frontend wizard flow") }
    if (-not $row.HasApiOrService) { $missing.Add("API/service contract") }
    if (-not $row.HasModelOrSchema) { $missing.Add("model/schema/entity contract") }
    if (-not $row.HasPermission) { $missing.Add("role/permission enforcement") }
    if (-not $row.HasTenantGuard) { $missing.Add("tenant/school isolation") }
    if (-not $row.HasKpiOrMetric) { $missing.Add("KPI/metric wiring") }
    if (-not $row.HasSeedOrDemo) { $missing.Add("seed/demo/sandbox data") }
    if (-not $row.HasTests) { $missing.Add("automated tests/proof") }
    if (-not $row.HasDocs) { $missing.Add("docs/canon entry") }
    if (-not $row.HasAuditOrLogging) { $missing.Add("audit/logging/event trail") }

    $priority = if ($row.Status -in @("FAIL_MISSING", "FAIL_PARTIAL")) {
        "P0"
    } elseif ($row.Status -eq "REVIEW") {
        "P1"
    } else {
        "P3"
    }

    [pscustomobject]@{
        Priority = $priority
        Status = $row.Status
        Wizard = $row.Wizard
        Layer = $row.Layer
        Domain = $row.Domain
        CurrentScore = "$($row.Score)/$($row.MaxScore)"
        Missing = ($missing -join "; ")
        FixRequired = if ($row.Status -eq "PASS") { "None" } else { "Complete missing wiring and proof items before release/sandbox reliance." }
        Owner = if ($row.Layer -match "Core|Platform") {
            "Dev 1 Platform Lead + Dev 5 QA Lead"
        } elseif ($row.Layer -match "Add-on") {
            "Add-on Owner + Dev 4 Frontend Lead + Dev 5 QA Lead"
        } else {
            "Module Owner + Dev 4 Frontend Lead + Dev 5 QA Lead"
        }
        DoneDefinition = "Registry + route + frontend + API/service + model/schema + permissions + tenant isolation + KPI wiring + seed/demo + tests + docs + audit trail all present and proof-backed."
    }
}

$FixQueue | Sort-Object Priority, Status, Wizard | Export-Csv (Join-Path $OutDir "03_50_WIZARD_FIX_QUEUE.csv") -NoTypeInformation

$FunctionMap = New-Object System.Text.StringBuilder
[void]$FunctionMap.AppendLine("# 50 Wizard Function / Operation / KPI Map")
[void]$FunctionMap.AppendLine("")
foreach ($w in $WizardScope | Sort-Object {[int]$_.N}) {
    [void]$FunctionMap.AppendLine("## $($w.N). $($w.Name)")
    [void]$FunctionMap.AppendLine("- Layer: $($w.Layer)")
    [void]$FunctionMap.AppendLine("- Domain: $($w.Domain)")
    [void]$FunctionMap.AppendLine("- Function: $($w.Function)")
    [void]$FunctionMap.AppendLine("- Operation: $($w.Operation)")
    [void]$FunctionMap.AppendLine("- Primary KPI: $($w.PrimaryKPI)")
    [void]$FunctionMap.AppendLine("- Secondary KPI: $($w.SecondaryKPI)")
    [void]$FunctionMap.AppendLine("")
}
$FunctionMap.ToString() | Set-Content (Join-Path $OutDir "04_50_WIZARD_FUNCTION_OPERATION_KPI_MAP.md")

$Canon = @"
# Crown 50 Wizard Canon

## Scope

Crown currently tracks 50 parent wizard rows.

## Required Wiring Per Wizard

Each active wizard must have:
1. Central registry/manifest entry
2. Route/navigation wiring
3. Frontend wizard flow
4. API/service contract
5. Model/schema/entity contract when data persists
6. Role/permission enforcement
7. Tenant/school isolation
8. KPI/metric wiring
9. Seed/demo/sandbox data
10. Automated tests/proof
11. Documentation/canon entry
12. Audit/logging/event trail where records, money, student status, discipline, transcripts, implementation readiness, or compliance are affected

## Status Rules

- PASS: 11-12 evidence points
- REVIEW: 7-10 evidence points
- FAIL_PARTIAL: 1-6 evidence points
- FAIL_MISSING: 0 evidence points

## Release Rule

No wizard may be treated as sandbox-ready, demo-ready, or production-ready unless its status is PASS.
"@
$Canon | Set-Content (Join-Path $OutDir "05_50_WIZARD_CANON.md")

$Backlog = New-Object System.Text.StringBuilder
[void]$Backlog.AppendLine("# 50 Wizard Implementation Backlog")
[void]$Backlog.AppendLine("")
foreach ($f in $FixQueue | Where-Object { $_.Status -ne "PASS" } | Sort-Object Priority, Wizard) {
    [void]$Backlog.AppendLine("## [$($f.Priority)] $($f.Wizard)")
    [void]$Backlog.AppendLine("- Status: $($f.Status)")
    [void]$Backlog.AppendLine("- Layer: $($f.Layer)")
    [void]$Backlog.AppendLine("- Domain: $($f.Domain)")
    [void]$Backlog.AppendLine("- Current score: $($f.CurrentScore)")
    [void]$Backlog.AppendLine("- Missing: $($f.Missing)")
    [void]$Backlog.AppendLine("- Owner: $($f.Owner)")
    [void]$Backlog.AppendLine("- Done: $($f.DoneDefinition)")
    [void]$Backlog.AppendLine("")
}
$Backlog.ToString() | Set-Content (Join-Path $OutDir "06_50_WIZARD_IMPLEMENTATION_BACKLOG.md")

$pass = @($EvidenceRows | Where-Object { $_.Status -eq "PASS" }).Count
$review = @($EvidenceRows | Where-Object { $_.Status -eq "REVIEW" }).Count
$failPartial = @($EvidenceRows | Where-Object { $_.Status -eq "FAIL_PARTIAL" }).Count
$failMissing = @($EvidenceRows | Where-Object { $_.Status -eq "FAIL_MISSING" }).Count
$p0 = @($FixQueue | Where-Object { $_.Priority -eq "P0" }).Count

$Decision = if ($pass -eq 50) { "PASS - all 50 wizards are complete and proof-backed." } else { "NO-GO - at least one wizard is not complete and proof-backed." }

$Summary = @"
# 50 Wizard Deep Dive Assessment Summary

Generated: $((Get-Date).ToString("s"))

## Repo

- Root: $RepoRoot
- Branch: $Branch
- HEAD: $Head

## Scope

- Parent wizard rows assessed: 50
- Evidence categories per wizard: 12
- Total evidence cells: 600

## Results

- PASS: $pass
- REVIEW: $review
- FAIL_PARTIAL: $failPartial
- FAIL_MISSING: $failMissing
- P0 fix rows: $p0

## Decision

$Decision

## Required Output Review Order

1. 02_50_WIZARD_DEEP_DIVE_ASSESSMENT.csv
2. 03_50_WIZARD_FIX_QUEUE.csv
3. 06_50_WIZARD_IMPLEMENTATION_BACKLOG.md
4. 04_50_WIZARD_FUNCTION_OPERATION_KPI_MAP.md
5. 05_50_WIZARD_CANON.md
"@

$Summary | Set-Content (Join-Path $OutDir "SUMMARY.md")

Write-Host ""
Write-Host "50-wizard deep dive complete."
Write-Host "Output: $OutDir"
Write-Host ""
Write-Host "PASS: $pass"
Write-Host "REVIEW: $review"
Write-Host "FAIL_PARTIAL: $failPartial"
Write-Host "FAIL_MISSING: $failMissing"
Write-Host "P0 fix rows: $p0"
Write-Host ""

if ($Open) {
    code $OutDir
    code (Join-Path $OutDir "SUMMARY.md")
    code (Join-Path $OutDir "02_50_WIZARD_DEEP_DIVE_ASSESSMENT.csv")
    code (Join-Path $OutDir "03_50_WIZARD_FIX_QUEUE.csv")
    code (Join-Path $OutDir "06_50_WIZARD_IMPLEMENTATION_BACKLOG.md")
}
