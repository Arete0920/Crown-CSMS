###############################################################################
# _patch_kpistrip_all.ps1
# Adds KpiStrip + dataSource metadata to all 43 REVIEW-status dashboard pages.
# Run from repo root or any directory — uses absolute paths.
###############################################################################
$ErrorActionPreference = 'Stop'
$pages = "C:\w\crown_main_postmerge_verify\frontend\dashboards\src\pages"
$kpiImportLine = "import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';"

$patched = 0
$skipped = 0
$errors  = @()

function Add-KpiImport($content, $importLine) {
    # Insert after the last import line (line starting with 'import ')
    $lines = $content -split "`n"
    $lastImport = -1
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^import ') { $lastImport = $i }
    }
    if ($lastImport -lt 0) { return $content }
    $lines = $lines[0..$lastImport] + @($importLine) + $lines[($lastImport+1)..($lines.Count-1)]
    return $lines -join "`n"
}

function Add-ConstBeforeExport($content, $constBlock) {
    # Insert the const block right before 'export default function'
    $marker = 'export default function'
    $idx = $content.IndexOf($marker)
    if ($idx -lt 0) { return $content }
    return $content.Substring(0, $idx) + $constBlock + "`n`n" + $content.Substring($idx)
}

# KPI definitions: key = filename (no .jsx), value = @{ Const; Items = @(label,src pairs) }
$kpis = [ordered]@{
    # ── STACK-ONLY (27 standard) ───────────────────────────────────────────
    'AdvancementOperationsDashboard'  = @{ Const = 'ADVANCEMENT_OPS_KPI'; Items = @(
        @('Donors Active','CRM'),@('Proposals Open','CRM'),@('Pledges YTD','Finance'),@('Events Scheduled','SIS')) }
    'AlumniRelationsDashboard'        = @{ Const = 'ALUMNI_RELATIONS_KPI'; Items = @(
        @('Alumni Records','CRM'),@('Events Planned','SIS'),@('Giving Participation','Finance'),@('Engaged This Year','CRM')) }
    'AthleticsDirectorDashboard'      = @{ Const = 'ATHLETICS_DIRECTOR_KPI'; Items = @(
        @('Teams Active','SIS'),@('Eligibility Holds','SIS'),@('Events This Week','SIS'),@('Head Coaches','HRIS')) }
    'ChaplainSpiritualLifeDashboard'  = @{ Const = 'CHAPLAIN_KPI'; Items = @(
        @('Chapel Attendance','SIS'),@('Prayer Requests','SIS'),@('Special Days','SIS'),@('Volunteer Servers','SIS')) }
    'ComplianceAuditDashboard'        = @{ Const = 'COMPLIANCE_AUDIT_KPI'; Items = @(
        @('Open Items','Audit'),@('Resolved MTD','Audit'),@('Overdue','Audit'),@('High Risk','Audit')) }
    'CurriculumPDDashboard'           = @{ Const = 'CURRICULUM_PD_KPI'; Items = @(
        @('PD Sessions','SIS'),@('Teachers Enrolled','HRIS'),@('Completion Rate','SIS'),@('Upcoming Sessions','SIS')) }
    'DashboardCertificationCenter'    = @{ Const = 'DASH_CERT_KPI'; Items = @(
        @('Certified','Registry'),@('In Review','Registry'),@('Pending','Registry'),@('Blocked','Registry')) }
    'DataMigrationDashboard'          = @{ Const = 'DATA_MIGRATION_KPI'; Items = @(
        @('Records Migrated','SIS'),@('Validation Errors','SIS'),@('Pending','SIS'),@('Validated','SIS')) }
    'ExtendedCareDashboard'           = @{ Const = 'EXTENDED_CARE_KPI'; Items = @(
        @('Children Enrolled','SIS'),@('Attendance Today','SIS'),@('Staff on Duty','HRIS'),@('Open Slots','SIS')) }
    'FacilitiesDashboard'             = @{ Const = 'FACILITIES_KPI'; Items = @(
        @('Open Work Orders','Facilities'),@('Completed MTD','Facilities'),@('Scheduled Maintenance','Facilities'),@('Critical Alerts','Facilities')) }
    'FineArtsDashboard'               = @{ Const = 'FINE_ARTS_KPI'; Items = @(
        @('Students Enrolled','SIS'),@('Performances Scheduled','SIS'),@('Practice Hours Logged','SIS'),@('Productions This Year','SIS')) }
    'FoodServiceDashboard'            = @{ Const = 'FOOD_SERVICE_KPI'; Items = @(
        @('Meals Served Today','FoodService'),@('Free & Reduced','Finance'),@('Allergy Alerts','Health'),@('Balance Owed','Finance')) }
    'HealthOfficeDashboard'           = @{ Const = 'HEALTH_OFFICE_KPI'; Items = @(
        @('Visits Today','Health'),@('Medications Due','Health'),@('Immunization Alerts','Health'),@('Referrals Pending','Health')) }
    'HRDashboard'                     = @{ Const = 'HR_KPI'; Items = @(
        @('Active Staff','HRIS'),@('On Leave','HRIS'),@('Open Positions','HRIS'),@('Background Checks','HRIS')) }
    'ImplementationSuccessDashboard'  = @{ Const = 'IMPL_SUCCESS_KPI'; Items = @(
        @('Schools Onboarded','SIS'),@('In Progress','SIS'),@('Support Tickets','Support'),@('At Risk','SIS')) }
    'IntegrationsAutomationDashboard' = @{ Const = 'INTEGRATIONS_KPI'; Items = @(
        @('Active Integrations','SIS'),@('Failed Syncs','SIS'),@('Pending Queued','SIS'),@('Last Run','SIS')) }
    'ITSupportDashboard'              = @{ Const = 'IT_SUPPORT_KPI'; Items = @(
        @('Open Tickets','Support'),@('Resolved Today','Support'),@('SLA Breaches','Support'),@('Pending Review','Support')) }
    'LibraryMediaDashboard'           = @{ Const = 'LIBRARY_MEDIA_KPI'; Items = @(
        @('Items Checked Out','Library'),@('Overdue','Library'),@('New Acquisitions','Library'),@('Holds Pending','Library')) }
    'MasterControlDashboard'          = @{ Const = 'MASTER_CONTROL_KPI'; Items = @(
        @('Schools Active','SIS'),@('Critical Alerts','SIS'),@('Platform Uptime','Monitor'),@('Revenue Today','Finance')) }
    'NetworkBenchmarkingDashboard'    = @{ Const = 'NETWORK_BENCHMARK_KPI'; Items = @(
        @('Uptime %','Monitor'),@('Bandwidth Used','Monitor'),@('Avg Latency','Monitor'),@('Active Devices','Monitor')) }
    'PortraitServiceHoursDashboard'   = @{ Const = 'PORTRAIT_HOURS_KPI'; Items = @(
        @('Hours Logged','SIS'),@('Students Participating','SIS'),@('Goals Met','SIS'),@('Overdue Submissions','SIS')) }
    'ReleaseReliabilityDashboard'     = @{ Const = 'RELEASE_RELIABILITY_KPI'; Items = @(
        @('Releases MTD','CI'),@('Test Pass Rate','CI'),@('Open Incidents','Monitor'),@('Deployments','CI')) }
    'RevenueOperationsDashboard'      = @{ Const = 'REVENUE_OPS_KPI'; Items = @(
        @('Revenue MTD','Finance'),@('Invoices Sent','Finance'),@('Collections Rate','Finance'),@('Pending','Finance')) }
    'SafetySecurityDashboard'         = @{ Const = 'SAFETY_SECURITY_KPI'; Items = @(
        @('Incidents Today','Safety'),@('Open Drills','Safety'),@('Badges Active','Safety'),@('Alerts','Safety')) }
    'SchoolBoardDashboard'            = @{ Const = 'SCHOOL_BOARD_KPI'; Items = @(
        @('Enrollment','SIS'),@('Revenue YTD','Finance'),@('Retention Rate','SIS'),@('Strategic Items','Board')) }
    'TransportationDashboard'         = @{ Const = 'TRANSPORTATION_KPI'; Items = @(
        @('Routes Active','Transport'),@('Riders Today','Transport'),@('Incidents','Transport'),@('Vehicles','Transport')) }
    'VolunteerManagementDashboard'    = @{ Const = 'VOLUNTEER_MGMT_KPI'; Items = @(
        @('Volunteers Active','SIS'),@('Events Covered','SIS'),@('Hours Logged','SIS'),@('Clearances Pending','SIS')) }

    # ── CROWN-LAYOUT (10) ─────────────────────────────────────────────────
    'ActivitiesAthleticsDashboard'    = @{ Const = 'ACTIVITIES_KPI'; Items = @(
        @('Active Clubs','SIS'),@('Teams Enrolled','SIS'),@('Events This Week','SIS'),@('Eligibility Holds','SIS')); Pattern = 'CrownLayout' }
    'AdminCommandCenterDashboard'     = @{ Const = 'ADMIN_CMD_KPI'; Items = @(
        @('Enrolled','SIS'),@('Faculty & Staff','HRIS'),@('Open Incidents','SIS'),@('Messages Pending','SIS')); Pattern = 'CrownLayout' }
    'CommunicationsDashboard'         = @{ Const = 'COMMUNICATIONS_KPI'; Items = @(
        @('Messages Sent','Comms'),@('Open Threads','Comms'),@('Announcements','Comms'),@('Response Rate','Comms')); Pattern = 'CrownLayout' }
    'FinanceDashboard'                = @{ Const = 'FINANCE_DASH_KPI'; Items = @(
        @('Revenue MTD','Finance'),@('Open Invoices','Finance'),@('Collection Rate','Finance'),@('Overdue','Finance')); Pattern = 'CrownLayout' }
    'GradebookDashboard'              = @{ Const = 'GRADEBOOK_KPI'; Items = @(
        @('Grade Submissions','SIS'),@('Pending Grades','SIS'),@('Avg GPA','SIS'),@('Missing Grades','SIS')); Pattern = 'CrownLayout' }
    'HomeDashboard'                   = @{ Const = 'HOME_KPI'; Items = @(
        @('Active Schools','SIS'),@('Daily Logins','Auth'),@('Open Items','SIS'),@('Platform Build','CI')); Pattern = 'CrownLayout' }
    'RoleDashboardPage'               = @{ Const = 'ROLE_DASHBOARD_KPI'; Items = @(
        @('Active Students','SIS'),@('Attendance Rate','SIS'),@('Open Incidents','SIS'),@('Messages','Comms')); Pattern = 'CrownLayout' }
    'SchedulingDashboard'             = @{ Const = 'SCHEDULING_KPI'; Items = @(
        @('Sections Scheduled','SIS'),@('Conflicts','SIS'),@('Substitutes Needed','HRIS'),@('Open Periods','SIS')); Pattern = 'CrownLayout' }
    'SpiritualLifeDashboard'          = @{ Const = 'SPIRITUAL_LIFE_KPI'; Items = @(
        @('Chapel Attendance','SIS'),@('Prayer Requests','SIS'),@('Special Days','SIS'),@('Events','SIS')); Pattern = 'CrownLayout' }
    'StudentCareDashboard'            = @{ Const = 'STUDENT_CARE_KPI'; Items = @(
        @('Students In Care','Health'),@('Open Cases','Health'),@('Referrals','Health'),@('Follow-Ups Due','Health')); Pattern = 'CrownLayout' }

    # ── CROWNTEMPLATE (4) ─────────────────────────────────────────────────
    'CrownLaunchDashboardPage'        = @{ Const = 'CROWN_LAUNCH_KPI'; Items = @(
        @('Enrolled','SIS'),@('Attendance Rate','SIS'),@('Open Incidents','SIS'),@('Pending Actions','SIS')); Pattern = 'Template' }
    'ParentDashboard'                 = @{ Const = 'PARENT_KPI'; Items = @(
        @('Child GPA','SIS'),@('Attendance Rate','SIS'),@('Upcoming Events','SIS'),@('Messages','Comms')); Pattern = 'Template' }
    'StudentDashboard'                = @{ Const = 'STUDENT_KPI'; Items = @(
        @('GPA','SIS'),@('Attendance Rate','SIS'),@('Assignments Due','SIS'),@('Upcoming Events','SIS')); Pattern = 'Template' }
    'TeacherDashboard'                = @{ Const = 'TEACHER_KPI'; Items = @(
        @('My Classes','SIS'),@('Students Rostered','SIS'),@('Assignments Due','SIS'),@('Attendance Rate','SIS')); Pattern = 'Template' }

    # ── SPECIAL CASES ─────────────────────────────────────────────────────
    'CompuwerxDisputesDashboard'      = @{ Const = 'COMPUWERX_KPI'; Items = @(
        @('Open Disputes','CompuWerx'),@('Resolved MTD','CompuWerx'),@('Pending Review','CompuWerx'),@('Escalated','CompuWerx')); Pattern = 'Special' }
    'SchoolAdministratorDashboard'    = @{ Const = 'SCHOOL_ADMIN_KPI'; Items = @(
        @('Enrolled','SIS'),@('Attendance Rate','SIS'),@('Faculty & Staff','HRIS'),@('Open Incidents','SIS')); Pattern = 'Special-SA' }
}

function Build-KpiConst([string]$constName, $items) {
    $lines = $items | ForEach-Object { "  { label: '$($_[0])', value: `u{2014}`, dataSource: '$($_[1])' }" }
    $inner = $lines -join ",`n"
    return "const $constName = [`n$inner`n];"
}

foreach ($filename in $kpis.Keys) {
    $path = "$pages\$filename.jsx"
    if (-not (Test-Path $path)) { Write-Warning "MISSING: $path"; $skipped++; continue }

    $content = Get-Content $path -Raw
    $def     = $kpis[$filename]
    $cName   = $def.Const
    $pattern = if ($def.ContainsKey('Pattern')) { $def.Pattern } else { 'Stack' }

    # Already patched?
    if ($content -match 'KpiStrip' -and $content -match 'dataSource:') {
        Write-Host "SKIP (already patched): $filename"
        $skipped++
        continue
    }

    try {
        # 1. Build KPI const block
        $constBlock = Build-KpiConst $cName $def.Items

        # 2. Add import after last import line
        $content = Add-KpiImport $content $kpiImportLine

        # 3. Add const before export default (or before function for special cases)
        $content = Add-ConstBeforeExport $content $constBlock

        # 4. Add render based on pattern
        switch ($pattern) {
            'Template' {
                # Change: const config = getDashboardTemplate('xxx');
                # To:     const config = { ...getDashboardTemplate('xxx'), kpiStrip: CONST };
                $content = $content -replace "(const config = )getDashboardTemplate\(('[^']+|`"[^`"]+)\)\s*;",
                    "`$1{ ...getDashboardTemplate(`$2), kpiStrip: $cName };"
                # For CrownLaunchDashboardPage the config is a spread with activePath
                # already handled since getDashboardTemplate is spread-assigned
            }
            'CrownLayout' {
                # Insert KpiStrip as first child of CrownLayout, after the closing >
                # Pattern: >\n      <FIRSTCHILD  (where first child is not already KpiStrip)
                $content = $content -replace '(?m)(>\r?\n)(\s{6}<(?!KpiStrip))', "`$1`$2<KpiStrip cards={$cName} />`n`$2"
            }
            'Stack' {
                # Insert after title div close, before next Grid/element
                $content = $content -replace '(?m)(      </div>\r?\n\r?\n)(      <)', "`$1      <KpiStrip cards={$cName} />`n`n`$2"
            }
            'Special' {
                # CompuwerxDisputesDashboard: <Box sx={{ p: 3 }}>  -- insert as first child
                $content = $content -replace '(?m)(<Box sx=\{\{ p: 3 \}\}>)(\r?\n)', "`$1`$2      <KpiStrip cards={$cName} />`n"
            }
            'Special-SA' {
                # SchoolAdministratorDashboard: wrap return with Fragment
                $content = $content -replace '(?m)(\s+return <AdminCommandCenterClean />;)',
                    "  return (`n    <>`n      <KpiStrip cards={$cName} />`n      <AdminCommandCenterClean />`n    </>`n  );"
            }
        }

        Set-Content $path $content -NoNewline -Encoding UTF8
        Write-Host "PATCHED [$pattern]: $filename"
        $patched++
    } catch {
        Write-Warning "ERROR $filename : $_"
        $errors += $filename
    }
}

Write-Host "`n=== SUMMARY ==="
Write-Host "Patched : $patched"
Write-Host "Skipped : $skipped"
Write-Host "Errors  : $($errors.Count)"
if ($errors) { Write-Host "Error files: $($errors -join ', ')" }
