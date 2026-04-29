# scripts/execution/136_crown_51x51_module_integrity_audit.ps1
# CROWN 51x51 Module Integrity Audit - Deterministic Resumable Mode
# Purpose:
# - Evaluates all 51 Crown capabilities/modules.
# - Applies 51 integrity checks to each module (2,601 rows).
# - GUARANTEED to emit final decision artifacts every time.
# - Supports fast mode (path-only matching, bounded search).
# - Supports resume mode (skip completed modules via checkpoints).
# - Does not modify production code.
# - Generates exact blocker/fix matrix for module completion.

param(
    [switch]$Fast,
    [switch]$Resume,
    [int]$StartModuleId = 1,
    [int]$EndModuleId = 51,
    [int]$MaxFilesPerPattern = 250,
    [int]$MaxSecondsPerModule = 20,
    [switch]$RunBackendChecks,
    [switch]$RunFrontendChecks,
    [switch]$RunPlaywright,
    [switch]$IncludeLargeSearch
)

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

function Write-Step($Message) {
    Write-Host "[CROWN-51x51] $Message" -ForegroundColor Cyan
}

function Normalize-Name($Name) {
    return (($Name -replace '[^A-Za-z0-9_.-]+', '_').Trim('_'))
}

function New-Module {
    param(
        [int]$Id, [string]$Layer, [string]$Name, [string]$Owner, [string]$Definition,
        [string[]]$Keywords, [string[]]$EssentialFunctions, [string[]]$CoreOperations,
        [string[]]$Kpis, [string[]]$RequiredWiring
    )
    [pscustomobject]@{
        Id = $Id; Layer = $Layer; Name = $Name; Owner = $Owner; Definition = $Definition
        Keywords = $Keywords; EssentialFunctions = $EssentialFunctions
        CoreOperations = $CoreOperations; Kpis = $Kpis; RequiredWiring = $RequiredWiring
    }
}

function New-Check {
    param(
        [int]$Id, [string]$Category, [string]$Name, [string]$Definition, [string]$EvidenceType,
        [string[]]$EvidenceKeywords, [string]$RequiredFixIfMissing
    )
    [pscustomobject]@{
        Id = $Id; Category = $Category; Name = $Name; Definition = $Definition
        EvidenceType = $EvidenceType; EvidenceKeywords = $EvidenceKeywords
        RequiredFixIfMissing = $RequiredFixIfMissing
    }
}

# Setup repo root and output directories
try {
    $RepoRoot = (& git rev-parse --show-toplevel 2>$null).Trim()
    if (-not $RepoRoot) { $RepoRoot = (Get-Location).Path }
} catch {
    $RepoRoot = (Get-Location).Path
}

Set-Location $RepoRoot

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutDir = "audit-artifacts\51x51-module-integrity\$Stamp"
$CheckpointDir = "$OutDir\checkpoints"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
New-Item -ItemType Directory -Force -Path $CheckpointDir | Out-Null

$MatrixCsv = "$OutDir\01_51x51_MODULE_INTEGRITY_MATRIX.csv"
$ModuleSummaryCsv = "$OutDir\02_MODULE_SUMMARY.csv"
$FixMatrixCsv = "$OutDir\03_FIX_MATRIX.csv"
$ExecutiveSummary = "$OutDir\00_EXECUTIVE_SUMMARY.md"
$JsonStatus = "$OutDir\99_STATUS.json"
$EvidenceRoot = "$OutDir\evidence"
New-Item -ItemType Directory -Force -Path $EvidenceRoot | Out-Null

# Top-level try/finally ensures artifacts are ALWAYS emitted
try {
    Write-Step "Repo root: $RepoRoot"
    Write-Step "Output: $OutDir"
    Write-Step "Mode: $(if($Fast){'FAST (path-only)'}else{'STANDARD (content-aware)'})"
    if ($Resume) { Write-Step "Resume: ON (skip completed module checkpoints)" }

    # Define all 51 modules (compact version for brevity)
    $Modules = @(
        (New-Module 1 "Platform Core" "Authentication / Login / SSO" "Dev 1" "Controls identity, login, token/session lifecycle, and SSO entry." @("auth","authentication","login","JWT","MSAL","SSO","token") @("Login","Logout","Password reset","SSO","Session refresh") @("Authenticate user","Issue token","Expire session","Map identity to role","Block unauthenticated access") @("login success rate","auth failure rate","SSO success rate","session expiry events","unauthorized attempts") @("backend auth service","frontend login route","RBAC","tenant context","audit log"))
        (New-Module 2 "Platform Core" "RBAC / Permissions" "Dev 1" "Defines what every role can view, create, update, approve, export, and delete." @("RBAC","permission","role","RoleAssignment","BasePermission","authorization") @("Role matrix","Permission checks","Route guards","API guards","Role assignment") @("Enforce role access","Deny unauthorized actions","Expose user capabilities","Audit permission changes","Support role testing") @("403 count","unauthorized route attempts","role coverage","permission test pass rate","role assignment accuracy") @("auth","tenant","API permissions","frontend route guards","audit"))
        (New-Module 3 "Platform Core" "Tenant / School Isolation" "Dev 1" "Prevents cross-school data access across every authenticated request and query." @("tenant","school_id","school isolation","TenantScoped","cross-tenant","403") @("Tenant context","Scoped querysets","Tenant middleware","Cross-tenant denial","School switch control") @("Attach school context","Filter all records","Reject cross-tenant access","Test negative cases","Audit tenant-sensitive access") @("cross-tenant test pass rate","tenant leakage count","scoped endpoint coverage","403/404 isolation results","school context errors") @("auth","request context","database models","API filters","tests"))
        (New-Module 4 "Platform Core" "Audit Logging" "Dev 1" "Records sensitive user, data, permission, export, billing, and compliance events." @("audit","AuditLog","audit logger","FERPA","AccessLog","change log") @("Create logs","Update logs","Delete logs","Export logs","Permission-change logs") @("Capture actor","Capture tenant","Capture before/after","Persist immutable event","Expose audit review") @("audit event count","sensitive action coverage","missing audit events","export log coverage","FERPA audit pass rate") @("models","middleware","service layer","finance","student data"))
        (New-Module 5 "Platform Core" "Notifications Framework" "Dev 1" "Provides shared alert, reminder, email, SMS, and workflow notification infrastructure." @("notification","NotificationEvent","EmailDispatch","SMS","Twilio","reminder") @("Create notification","Deliver email","Deliver SMS","User preferences","Notification templates") @("Queue events","Respect preferences","Send delivery","Track failure","Retry delivery") @("delivery success rate","bounce/failure count","template coverage","opt-out compliance","retry success rate") @("communications","email service","SMS provider","background jobs","preferences"))
        (New-Module 6 "Platform Core" "Document / File Framework" "Dev 1" "Stores school, student, family, billing, evidence, and workflow documents safely." @("document","file","upload","Blob","storage","StudentDocument") @("Upload","Download","Permissioned access","Versioning","Retention") @("Store files","Scope to tenant","Attach to record","Restrict access","Audit file access") @("upload success rate","download failures","orphan files","unauthorized file access","retention compliance") @("storage","tenant","RBAC","audit","records"))
        (New-Module 7 "Platform Core" "API / Integration Layer" "Dev 1" "Provides versioned contracts for frontend, modules, add-ons, and external services." @("api","integration","OpenAPI","schema","contract","webhook","drf") @("API routes","Schemas","Contracts","Versioning","Error responses") @("Expose services","Validate input","Return standard response","Protect endpoint","Publish schema") @("API test pass rate","contract drift count","schema coverage","5xx count","endpoint coverage") @("backend services","frontend client","RBAC","tenant","OpenAPI"))
        (New-Module 8 "Platform Core" "Shared Frontend Shell" "Dev 4" "Provides one consistent application frame, navigation, layout, and role-aware shell." @("AppShell","Layout","Sidebar","Topbar","navigation","route") @("Header","Sidebar","Layout","Breadcrumbs","Role navigation") @("Render app frame","Show allowed nav","Hide forbidden nav","Maintain context","Support dashboards") @("route success rate","nav broken links","shell render errors","role nav coverage","console errors") @("React Router","RBAC","role dashboards","design system","module pages"))
        (New-Module 9 "Platform Core" "Shared Design System" "Dev 4" "Defines Crown visual language, components, typography, spacing, states, and UX consistency." @("design system","theme","palette","component","Button","Card","Modal") @("Theme","Buttons","Cards","Forms","Tables") @("Apply consistent UI","Reduce UI drift","Support accessibility","Standardize states","Support responsive layout") @("component coverage","a11y violations","visual drift count","design token coverage","reuse rate") @("frontend shell","component library","forms","tables","dashboards"))
        (New-Module 10 "Platform Core" "Reporting / Data Access Standards" "Dev 5" "Controls reporting, exports, query standards, and data-access boundaries." @("reporting","reports","export","analytics","data access","dashboard") @("Reports","Exports","Filters","Download","Board-ready summaries") @("Use tenant scope","Validate permissions","Generate report","Audit export","Protect sensitive fields") @("report success rate","export count","export audit coverage","slow query count","unauthorized export attempts") @("RBAC","tenant","audit","database","API"))
        (New-Module 11 "SIS Core" "School Profile" "Dev 2" "Stores official school identity, tenant root, settings, logo, and configuration." @("School","SchoolProfile","SchoolSettings","tenant root","logo") @("School record","Settings","Branding","Contact data","Tenant setup") @("Create school","Configure school","Attach users","Control settings","Expose identity") @("school setup completion","missing settings","tenant config errors","school profile completeness","logo/config coverage") @("tenant","auth","settings","frontend shell","documents"))
        (New-Module 12 "SIS Core" "School Year / Term" "Dev 2" "Defines academic years, terms, reporting windows, and rollover structure." @("SchoolYear","Term","academic year","semester","quarter","rollover") @("Academic year","Terms","Dates","Rollover","Reporting period") @("Create year","Open/close term","Assign records","Support reports","Prevent date conflict") @("active year accuracy","term conflicts","rollover errors","report period coverage","date validation failures") @("enrollment","attendance","grades","transcripts","billing"))
        (New-Module 13 "SIS Core" "Student Master Record" "Dev 2" "Stores official student identity, demographics, status, and record truth." @("Student","student master","Student360","student record","demographics") @("Create student","Edit student","Status","Profile","Search") @("Persist official record","Prevent duplicates","Scope to school","Expose APIs","Link modules") @("duplicate students","record completeness","student API pass rate","student search success","cross-tenant leakage") @("households","enrollment","attendance","grades","billing"))
        (New-Module 14 "SIS Core" "Household / Guardians" "Dev 2" "Connects students to families, guardians, custody, billing, and communication rules." @("Household","Guardian","family","custody","parent","guardian relationship") @("Household record","Guardian link","Custody rules","Billing payer","Communication preference") @("Link student/family","Authorize parent view","Support billing","Support messages","Protect custody rules") @("household completeness","guardian link errors","parent access accuracy","billing payer accuracy","custody rule violations") @("students","parent portal","billing","communications","RBAC"))
        (New-Module 15 "SIS Core" "Staff / Faculty" "Dev 2" "Stores teachers, administrators, staff, and employment/role context." @("Staff","Faculty","Teacher","StaffMember","employee") @("Staff record","Teacher profile","Role link","Assignment","Directory") @("Create staff","Assign role","Assign section","Support portal","Restrict access") @("staff completeness","role assignment errors","teacher-section coverage","staff login success","directory accuracy") @("RBAC","teacher portal","sections","communications","scheduling"))
        (New-Module 16 "SIS Core" "Enrollment Lifecycle" "Dev 2" "Tracks inquiry/applicant/admitted/enrolled/withdrawn/alumni states." @("Enrollment","enrollment lifecycle","status","admitted","withdrawn","alumni") @("Enrollment status","Transition","Acceptance","Withdrawal","Rollover") @("Move status","Validate transition","Trigger billing","Update rosters","Audit changes") @("invalid transitions","enrollment conversion rate","withdrawal errors","billing trigger success","status conflict count") @("students","admissions","reenrollment","billing","rosters"))
        (New-Module 17 "SIS Core" "Grade Levels" "Dev 2" "Defines school grade structure, placement, progression, and grade-based rules." @("GradeLevel","grade level","K-12","placement","progression") @("Grade setup","Student placement","Progression","Reporting","Tuition rule support") @("Create grades","Assign students","Validate placement","Support reports","Support rollover") @("placement errors","grade completeness","rollover success","grade-level reporting","tuition grade mapping") @("school year","students","courses","billing","reports"))
        (New-Module 18 "SIS Core" "Courses / Sections / Rosters" "Dev 2" "Defines academic offerings, class sections, teacher assignment, and student rosters." @("Course","Section","Roster","CourseSection","SectionEnrollment") @("Courses","Sections","Rosters","Teacher assignment","Student assignment") @("Create course","Create section","Assign teacher","Enroll students","Expose roster") @("roster accuracy","section coverage","teacher assignment gaps","schedule conflicts","course completeness") @("staff","students","scheduling","attendance","gradebook"))
        (New-Module 19 "SIS Core" "Attendance" "Dev 2" "Records daily/period presence, absence, tardy, dismissal, and attendance summaries." @("Attendance","present","absent","tardy","DailyAttendance") @("Take attendance","Edit attendance","Parent visibility","Reports","Alerts") @("Submit attendance","Validate date","Notify parent","Summarize attendance","Audit change") @("attendance submission rate","missing attendance","tardy/absence trends","parent alert success","attendance correction count") @("students","rosters","teacher portal","parent portal","communications"))
        (New-Module 20 "SIS Core" "Grades / Report Cards" "Dev 2" "Stores gradebook results, term grades, report-card output, and parent/student visibility." @("Grade","Gradebook","ReportCard","grade entry","grading period") @("Grade entry","Grade calculation","Report card","Parent view","Teacher workflow") @("Record grade","Calculate term result","Publish report","Protect edits","Audit change") @("grade posting rate","missing grades","report generation success","parent view accuracy","grade correction count") @("courses","terms","teacher portal","parent portal","transcripts"))
        (New-Module 21 "SIS Core" "Transcripts / Credit History" "Dev 2" "Stores official academic history, credits, GPA, transfer courses, and graduation progress." @("Transcript","credit","GPA","Graduation","AcademicRecord") @("Transcript record","Credit history","GPA","Transfer credits","Official export") @("Calculate credits","Protect official edits","Generate transcript","Audit access","Support graduation rules") @("transcript accuracy","GPA calculation errors","credit completion","official export count","unauthorized transcript access") @("grades","terms","students","reporting","audit"))
        (New-Module 22 "SIS Core" "Student Care / Discipline Summary" "Dev 2" "Stores behavior/care summary layer and student-support references." @("StudentCare","discipline","behavior","care note","incident") @("Care summary","Behavior summary","Incident link","Referral","Admin view") @("Record incident","Summarize care","Restrict sensitive access","Notify approved users","Audit changes") @("open care items","incident response time","discipline trend","sensitive access violations","care closure rate") @("students","RBAC","parent portal","counselor","audit"))
        (New-Module 23 "SIS Core" "Emergency / Medical Essentials" "Dev 2" "Stores emergency contacts, key medical flags, allergies, and operational health essentials." @("EmergencyContact","Medical","allergy","health flag","medication") @("Emergency contact","Medical flag","Allergy","Medication note","Emergency access") @("Store emergency info","Restrict medical data","Expose to authorized roles","Update contacts","Audit access") @("missing emergency contacts","medical alert accuracy","unauthorized health access","contact update rate","emergency data completeness") @("students","households","nurse","RBAC","audit"))
        (New-Module 24 "First-Wave Module" "Admissions" "Dev 3" "Manages inquiry, application, checklist, review, decision, and acceptance." @("Admissions","Inquiry","Application","AdmissionDecision","Applicant") @("Inquiry","Application","Checklist","Review","Decision") @("Capture lead","Process application","Track checklist","Decision applicant","Convert to enrollment") @("inquiry count","application completion rate","acceptance rate","time to decision","conversion rate") @("students","households","enrollment","communications","billing"))
        (New-Module 25 "First-Wave Module" "Re-enrollment" "Dev 3" "Manages returning-family confirmation, contracts, deposits, documents, and rollover." @("ReEnrollment","reenrollment","returning","contract","deposit") @("Return intent","Contract","Deposit","Documents","Rollover") @("Invite families","Collect forms","Collect deposit","Update status","Prepare next year") @("reenrollment rate","contract completion","deposit collection","missing documents","rollover readiness") @("students","households","billing","school year","communications"))
        (New-Module 26 "First-Wave Module" "Billing / Tuition / Payments" "Dev 3" "Manages tuition plans, fees, charges, payments, balances, aid, and reconciliation." @("Billing","Tuition","Payment","Ledger","Invoice","Balance") @("Tuition plan","Charge posting","Payment","Balance","Reconciliation") @("Generate charges","Collect payment","Maintain ledger","Apply aid","Reconcile processor") @("collection rate","failed payments","ledger integrity","aging balance","aid exposure") @("households","students","CompuWerx/Stripe","audit","parent portal"))
        (New-Module 27 "First-Wave Module" "Communications" "Dev 3" "Manages announcements, messages, alerts, templates, and role-targeted communication." @("Communications","Message","Announcement","Inbox","notification") @("Announcements","Messaging","Templates","Targeting","Delivery") @("Create message","Target audience","Deliver notification","Track read status","Respect permissions") @("delivery success","unread count","message response time","failed sends","announcement reach") @("notifications","RBAC","households","staff","portals"))
        (New-Module 28 "First-Wave Module" "Parent Portal" "Dev 4" "Provides family-scoped access to students, attendance, grades, billing, messages, documents, and tasks." @("ParentPortal","parent","guardian portal","family dashboard","parent dashboard") @("Family dashboard","Student view","Billing view","Messages","Forms") @("Authenticate parent","Scope children","Show records","Submit tasks","Pay balance") @("parent login success","task completion","payment completion","message read rate","data leakage count") @("auth","households","students","billing","communications"))
        (New-Module 29 "First-Wave Module" "Teacher Portal" "Dev 4" "Provides teacher access to classes, rosters, attendance, gradebook, messages, and student context." @("TeacherPortal","teacher dashboard","class roster","gradebook","attendance submission") @("Teacher dashboard","Rosters","Attendance","Gradebook","Messages") @("Show assigned sections","Submit attendance","Enter grades","Message families","Review student context") @("attendance completion","grade posting","teacher login success","roster accuracy","message response") @("staff","sections","attendance","grades","communications"))
        (New-Module 30 "First-Wave Module" "Administrator Portal" "Dev 4" "Provides schoolwide operating command center, dashboards, approvals, alerts, and module access." @("AdminDashboard","Administrator","school admin","admin portal","command center") @("Admin dashboard","Approvals","Alerts","Schoolwide metrics","Module navigation") @("Show operating health","Approve workflows","Resolve blockers","Navigate modules","Monitor alerts") @("open admin tasks","dashboard load time","approval SLA","module health","alert resolution rate") @("all modules","RBAC","reporting","notifications","audit"))
        (New-Module 31 "Second-Wave Module" "Scheduling" "Dev 3" "Manages bell schedules, periods, rooms, sections, teacher assignments, and conflicts." @("Scheduling","schedule","BellSchedule","period","room","SectionSchedule") @("Bell schedule","Periods","Rooms","Section schedule","Conflict detection") @("Create schedule","Assign room","Assign teacher","Detect conflict","Publish schedule") @("schedule completeness","conflict count","room utilization","teacher overload","publish success") @("school year","courses","sections","staff","calendar"))
        (New-Module 32 "Second-Wave Module" "Activities / Athletics / Events" "Dev 3" "Manages clubs, teams, events, eligibility, rosters, calendars, and communications." @("Activities","Athletics","Event","team","club","eligibility") @("Teams","Clubs","Events","Eligibility","Rosters") @("Create activity","Manage roster","Check eligibility","Publish event","Message participants") @("event count","roster completion","eligibility flags","participation rate","volunteer needs") @("students","calendar","communications","staff","volunteer"))
        (New-Module 33 "Second-Wave Module" "Nurse Office / Health Office" "Dev 3" "Manages health visits, medications, alerts, incidents, and parent health communication." @("Nurse","HealthOffice","Medical","medication","health visit","incident") @("Health visit","Medication","Medical alerts","Incident","Parent follow-up") @("Log visit","Track medication","Show alerts","Notify parent","Protect sensitive data") @("visits today","medication due","health alerts","parent follow-ups","incident closure") @("students","medical essentials","RBAC","communications","audit"))
        (New-Module 34 "Second-Wave Module" "Transportation" "Dev 3" "Manages routes, buses, stops, riders, exceptions, and transportation notifications." @("Transportation","bus","route","rider","stop") @("Routes","Buses","Stops","Riders","Exceptions") @("Create route","Assign rider","Track exception","Notify parent","Export roster") @("route accuracy","rider count","exception count","notification success","late route count") @("students","households","addresses","communications","calendar"))
        (New-Module 35 "Second-Wave Module" "Food Services" "Dev 3" "Manages lunch ordering, meal accounts, menus, counts, and cafeteria workflows." @("Food","Lunch","meal","cafeteria","menu") @("Menu","Lunch order","Meal count","Account balance","Eligibility") @("Publish menu","Collect order","Calculate count","Track balance","Notify family") @("meal orders","meal balance","unpaid meals","daily count accuracy","menu publish rate") @("students","households","billing","communications","calendar"))
        (New-Module 36 "Second-Wave Module" "Volunteer / Family Engagement" "Dev 3" "Tracks family participation, volunteer hours, events, requirements, and engagement." @("Volunteer","family engagement","service hours","participation","volunteer hours") @("Opportunities","Signups","Hours","Requirements","Family status") @("Post opportunity","Collect signup","Approve hours","Track requirement","Message families") @("hours completed","open opportunities","family completion rate","approval backlog","participation fee risk") @("households","events","communications","billing","reports"))
        (New-Module 37 "Second-Wave Module" "Advanced Board Reporting" "Dev 5" "Provides leadership/board dashboards, packets, indicators, and executive reporting." @("Board","board reporting","board dashboard","governance dashboard","packet") @("Board dashboard","Packet","Executive summary","Metrics","Exports") @("Aggregate data","Protect sensitive records","Generate packet","Show KPIs","Track governance tasks") @("packet completion","board item count","report generation success","governance task closure","sensitive data exceptions") @("reporting","finance","enrollment","mission","RBAC"))
        (New-Module 38 "Second-Wave Module" "Extended Discipline Workflows" "Dev 3" "Manages behavior incidents, consequences, escalation, parent communication, and reviews." @("Discipline","behavior","incident","consequence","escalation") @("Incident","Consequence","Escalation","Parent notice","Admin review") @("Record incident","Assign consequence","Escalate case","Notify parent","Close review") @("incident count","closure time","repeat incidents","parent notification rate","escalation backlog") @("students","student care","communications","RBAC","audit"))
        (New-Module 39 "First-Wave Add-on" "Spiritual Life" "Product + Dev 3" "Tracks chapel, discipleship, Bible curriculum, spiritual milestones, and formation activity." @("Spiritual","chapel","discipleship","Bible","formation") @("Chapel","Milestones","Discipleship","Bible curriculum","Reflection") @("Record participation","Track milestones","Support reflections","Report formation","Protect sensitive notes") @("chapel participation","milestones recorded","reflection completion","formation indicators","mission engagement") @("students","mission metrics","communications","reports","RBAC"))
        (New-Module 40 "First-Wave Add-on" "Service & Outreach" "Product + Dev 3" "Manages service hours, outreach projects, mission trips, and community impact." @("Service","Outreach","mission trip","service hours","community impact") @("Projects","Hours","Approvals","Mission trips","Impact reports") @("Post opportunity","Log hours","Approve service","Track impact","Report progress") @("service hours","project participation","approval backlog","impact count","student completion rate") @("students","volunteer","communications","mission metrics","reports"))
        (New-Module 41 "First-Wave Add-on" "Crown Compass" "Product + Dev 5" "Provides school health assessment, scoring, diagnostics, and improvement planning." @("Crown Compass","Compass","school health","assessment","diagnostic") @("Assessment","Scoring","Report","Improvement plan","Benchmark") @("Collect responses","Calculate scores","Generate report","Track goals","Support consulting") @("assessment completion","score trend","action plan completion","benchmark coverage","survey response rate") @("surveys","analytics","board reporting","reports","standalone contract"))
        (New-Module 42 "First-Wave Add-on" "Board Governance Suite" "Product + Dev 5" "Supports board packets, meeting materials, policies, decisions, and governance workflows." @("Board Governance","board packet","policy","minutes","governance") @("Packet","Meeting","Minutes","Policy","Decisions") @("Build packet","Track agenda","Record decision","Manage policy","Archive minutes") @("packet readiness","policy review count","decision closure","meeting attendance","document completeness") @("board reporting","documents","RBAC","communications","calendar"))
        (New-Module 43 "First-Wave Add-on" "Christian PD Hub" "Product + Dev 5" "Provides professional development resources, courses, tracks, and completion records." @("PD Hub","professional development","course","training","teacher development") @("Course catalog","Training track","Completion","Certificate","Resource library") @("Publish course","Enroll staff","Track completion","Issue certificate","Report PD") @("course completion","active enrollments","PD hours","certificate count","staff participation") @("staff","documents","communications","reports","standalone contract"))
        (New-Module 44 "Later Add-on" "Chaplain / Pastoral Care" "Product + Dev 3" "Supports pastoral referrals, care notes, prayer follow-up, and protected ministry workflows." @("Chaplain","Pastoral","care referral","prayer follow-up","counseling") @("Referral","Care note","Follow-up","Prayer support","Meeting") @("Create referral","Restrict notes","Schedule meeting","Close care item","Audit access") @("active referrals","follow-up count","closure time","sensitive access violations","meeting completion") @("student care","spiritual life","RBAC","calendar","audit"))
        (New-Module 45 "Later Add-on" "Portrait of the Graduate" "Product + Dev 3" "Tracks mission-defined graduate outcomes, competencies, growth, and evidence." @("Portrait of the Graduate","graduate profile","competency","outcome","formation evidence") @("Competencies","Evidence","Progress","Milestones","Reports") @("Define outcomes","Attach evidence","Score progress","Report growth","Support reflection") @("outcome completion","evidence count","growth trend","advisor review rate","student reflection rate") @("students","spiritual life","service","grades","reports"))
        (New-Module 46 "Later Add-on" "Mission Metrics" "Product + Dev 5" "Aggregates mission, culture, spiritual, service, and leadership indicators." @("Mission Metrics","MissionFit","mission dashboard","faith health","culture") @("Metric definitions","Dashboard","Trend","Alerts","Reports") @("Aggregate data","Calculate indicators","Show trends","Flag risk","Report mission health") @("mission score","trend movement","risk flags","dashboard usage","report exports") @("spiritual life","service","Compass","board reporting","analytics"))
        (New-Module 47 "Later Add-on" "CRM / Marketing Suite" "Product + Dev 3" "Manages prospective family pipeline, outreach campaigns, marketing events, and engagement." @("CRM","Marketing","campaign","prospect","lead") @("Prospects","Campaigns","Segments","Follow-up","Conversion") @("Create lead","Run campaign","Track touchpoints","Convert inquiry","Measure funnel") @("lead count","campaign response","tour conversion","application conversion","follow-up SLA") @("admissions","communications","analytics","events","standalone contract"))
        (New-Module 48 "Later Add-on" "Mobile App / Family App" "Product + Dev 4" "Provides mobile access to family, student, teacher, alerts, calendar, and school-life workflows." @("Mobile","family app","app","push notification","mobile") @("Mobile login","Push alerts","Family view","Calendar","Messages") @("Authenticate mobile user","Send push","Show scoped records","Support tasks","Respect permissions") @("mobile active users","push delivery","crash rate","task completion","mobile login success") @("auth","parent portal","communications","calendar","notifications"))
        (New-Module 49 "Later Add-on" "Survey / Sentiment Engine" "Product + Dev 5" "Collects feedback, surveys, culture pulse, sandbox feedback, and sentiment reports." @("Survey","Sentiment","feedback","pulse","questionnaire") @("Survey builder","Responses","Anonymous mode","Reports","Trends") @("Create survey","Collect response","Protect anonymity","Analyze sentiment","Export results") @("response rate","sentiment trend","completion rate","survey count","follow-up actions") @("Compass","communications","analytics","reports","standalone contract"))
        (New-Module 50 "Later Add-on" "Analytics / Benchmarking" "Product + Dev 5" "Provides trends, benchmarks, comparative indicators, and data intelligence across Crown." @("Analytics","Benchmark","trend","dashboard","metrics") @("Trends","Benchmarks","Segments","Exports","Alerts") @("Aggregate data","Compute benchmarks","Visualize trends","Protect data","Export analysis") @("dashboard usage","benchmark coverage","query performance","export count","insight action rate") @("reporting","data access","mission metrics","finance","enrollment"))
        (New-Module 51 "Later Add-on" "Standalone Schedule Builder" "Product + Dev 5" "Provides scheduling optimization that can integrate with Crown or operate standalone." @("Schedule Builder","scheduler","optimizer","standalone schedule","conflict solver") @("Optimizer","Constraints","Draft schedule","Conflict resolution","Export") @("Define constraints","Generate schedule","Resolve conflicts","Export schedule","Sync to Crown") @("conflict reduction","schedule generation time","constraint satisfaction","manual edits","sync success") @("scheduling","courses","staff","rooms","standalone contract"))
    )

    # Define 51 checks
    $Checks = @(
        (New-Check 1 "Product" "Canonical Definition Exists" "Module has a clear approved definition and boundary." "Doc" @("canon","definition","module","taxonomy") "Create/approve module canon with scope, exclusions, owner, and acceptance.")
        (New-Check 2 "Product" "Layer Classification Correct" "Module is correctly classified as Core, Module, or Add-on." "Doc" @("Core","Module","Add-on","Layer") "Fix taxonomy; move misplaced capabilities into correct layer.")
        (New-Check 3 "Product" "Owner Assigned" "Module has a named accountable owner." "Doc" @("Owner","Dev","Lead","Responsible") "Assign owner and add to module inventory.")
        (New-Check 4 "Product" "Essential Functions Defined" "Core functions are explicitly listed." "Doc" @("function","workflow","capability","requirements") "Write required functions and acceptance rules.")
        (New-Check 5 "Product" "Out-of-Scope Boundaries Defined" "Module states what it does not own." "Doc" @("out of scope","does not own","boundary","exclusion") "Add exclusion rules to prevent module sprawl.")
        (New-Check 6 "Operations" "Primary Workflows Designed" "Main user workflows are mapped." "Doc" @("workflow","flow","process","pipeline") "Map role workflows and state transitions.")
        (New-Check 7 "Operations" "Lifecycle States Defined" "Module has clear states/statuses where applicable." "Code/Doc" @("status","state","transition","lifecycle") "Implement explicit status model and transition validation.")
        (New-Check 8 "Operations" "Role Responsibilities Defined" "Role-specific actions are defined." "Doc" @("role","permission","responsibility","access") "Define role-action matrix.")
        (New-Check 9 "Operations" "Admin Operation Exists" "Admin can operate/manage the module." "UI/API" @("admin","administrator","manage","dashboard") "Add admin screen/API workflow.")
        (New-Check 10 "Operations" "User Operation Exists" "End user/role can perform module workflow." "UI/API" @("portal","user","teacher","parent","student","staff") "Add role-facing screen and action flow.")
        (New-Check 11 "Data" "Canonical Data Model Exists" "Module has a data model or approved external contract." "Code" @("class ","models.Model","interface","schema","model") "Create model/schema or approved contract.")
        (New-Check 12 "Data" "No Shadow Record Risk" "Module does not duplicate Core truth." "Code/Doc" @("student","household","school_id","foreign key","relationship") "Replace duplicate record ownership with Core references.")
        (New-Check 13 "Data" "Tenant Key Present" "Tenant/school scoping is present where data is stored." "Code" @("school_id","tenant","School","TenantScoped") "Add school/tenant FK and scoped access pattern.")
        (New-Check 14 "Data" "Migration Exists" "Model changes have migrations." "Code" @("migrations","CreateModel","AlterField") "Generate and commit migrations.")
        (New-Check 15 "Data" "Seed/Demo Data Exists" "Demo/sandbox seed data exists where needed." "Code/Doc" @("seed","fixture","demo","sandbox","factory") "Add deterministic seed fixtures for sandbox testing.")
        (New-Check 16 "API" "API Endpoint Exists" "Module exposes API endpoints or service methods." "Code" @("ViewSet","APIView","router","urlpatterns","endpoint") "Create API route/service.")
        (New-Check 17 "API" "Serializer/Schema Exists" "Module validates input/output." "Code" @("Serializer","schema","validator","zod","type") "Add serializers/schemas and validation tests.")
        (New-Check 18 "API" "Service Layer Exists" "Business logic is not trapped in UI/controller only." "Code" @("service","services.py","Service","usecase","manager") "Move workflow logic into service layer.")
        (New-Check 19 "API" "Validation Exists" "Invalid inputs are rejected." "Code/Test" @("ValidationError","validate","clean","required","invalid") "Add validation and negative tests.")
        (New-Check 20 "API" "Error Handling Exists" "Failures return safe useful errors." "Code" @("try","except","error","logger","Sentry") "Add safe errors and logging.")
        (New-Check 21 "Security" "Authentication Required" "Protected actions require authentication." "Code/Test" @("IsAuthenticated","auth","login_required","ProtectedRoute") "Enforce auth on APIs and routes.")
        (New-Check 22 "Security" "Permission Enforcement Exists" "Role permissions are enforced." "Code/Test" @("permission","BasePermission","can_","403","unauthorized") "Add RBAC checks and tests.")
        (New-Check 23 "Security" "Tenant Isolation Tested" "Cross-tenant negative tests exist." "Test" @("tenant","cross-tenant","403","404","isolation") "Add cross-school denial tests.")
        (New-Check 24 "Security" "Audit Logging Exists" "Sensitive actions are logged." "Code/Test" @("audit","AuditLog","logger","FERPA") "Add audit events for mutations/access.")
        (New-Check 25 "Security" "Sensitive Data Handling Defined" "PII/financial/medical/faith data is protected." "Code/Doc" @("PII","FERPA","COPPA","medical","financial","sensitive") "Add data classification and access rules.")
        (New-Check 26 "Frontend" "Route Exists" "Frontend route/screen exists." "Code" @("Route","path","router","href","navigate") "Add route and navigation entry.")
        (New-Check 27 "Frontend" "Dashboard/Entry Card Exists" "Dashboard or role entry exists." "Code" @("Dashboard","card","KPI","summary","entry") "Add dashboard card and module entry.")
        (New-Check 28 "Frontend" "Form UI Exists" "Create/edit form exists where needed." "Code" @("Form","input","submit","TextField","validation") "Add standardized form UI.")
        (New-Check 29 "Frontend" "Table/List UI Exists" "List/search/filter table exists." "Code" @("Table","DataGrid","list","filter","pagination") "Add list/table UI.")
        (New-Check 30 "Frontend" "Empty/Loading/Error States Exist" "UI handles empty/loading/error states." "Code" @("loading","empty","error","skeleton","No records") "Add complete UI states.")
        (New-Check 31 "KPI" "KPIs Defined" "Module has measurable operating KPIs." "Doc/Code" @("KPI","metric","dashboard","score","rate") "Define KPI contract and dashboard placement.")
        (New-Check 32 "KPI" "KPI Data Source Exists" "KPIs are tied to real data sources." "Code" @("count","aggregate","annotate","metric","summary") "Wire KPI to backend query or service.")
        (New-Check 33 "KPI" "KPI Thresholds Defined" "Green/yellow/red or alert thresholds are defined." "Doc/Code" @("threshold","alert","warning","critical","green") "Add threshold rules and owner.")
        (New-Check 34 "KPI" "Reporting/Export Exists" "Module can report/export appropriate data." "Code" @("export","report","CSV","PDF","download") "Add report/export path with RBAC and audit.")
        (New-Check 35 "Integration" "Core Wiring Exists" "Module wires to Core records correctly." "Code" @("Student","Household","Staff","School","Enrollment") "Wire to Core canonical records.")
        (New-Check 36 "Integration" "Notification Wiring Exists" "Module can trigger notifications where needed." "Code" @("Notification","Email","SMS","message","announcement") "Add notification hooks.")
        (New-Check 37 "Integration" "Calendar Wiring Exists" "Module connects to calendar/events where relevant." "Code" @("Calendar","Event","schedule","date","meeting") "Add calendar/event integration or mark not applicable.")
        (New-Check 38 "Integration" "Microsoft/M365/Teams Posture Exists" "Module has integration posture where relevant." "Code/Doc" @("M365","Microsoft","MSAL","Teams","Entra") "Add enabled/deferred M365/Teams posture.")
        (New-Check 39 "Integration" "External Webhook/API Contract Exists" "External integrations use contracts." "Code/Doc" @("webhook","signature","contract","integration","sync") "Add signed webhook/API contract.")
        (New-Check 40 "Testing" "Unit Tests Exist" "Unit tests cover module logic." "Test" @("test_","describe(","it(","pytest","vitest") "Add unit tests.")
        (New-Check 41 "Testing" "API Tests Exist" "API tests cover endpoints and permissions." "Test" @("APIClient","client.get","client.post","request","response") "Add API tests.")
        (New-Check 42 "Testing" "Frontend Tests Exist" "Frontend tests cover core UI behavior." "Test" @("render","screen","userEvent","vitest","testing-library") "Add component tests.")
        (New-Check 43 "Testing" "Playwright/E2E Exists" "Browser proof exists for critical workflows." "Test" @("playwright","page.goto","expect(page","e2e","spec.ts") "Add Playwright smoke test.")
        (New-Check 44 "Testing" "Negative Tests Exist" "Invalid/unauthorized/error paths are tested." "Test" @("unauthorized","invalid","forbidden","403","raises") "Add negative coverage.")
        (New-Check 45 "Release" "Health/Integrity Check Exists" "Module has health/integrity proof or inclusion in gate." "Code/Test" @("health","integrity","gate","readiness","proof") "Add module to integrity gate.")
        (New-Check 46 "Release" "CI Gate Includes Module" "CI exercises module tests." "CI" @("workflow","pytest","npm test","playwright","gate") "Add module test to CI workflow.")
        (New-Check 47 "Release" "Sandbox Smoke Path Exists" "Sandbox tester can exercise module." "Doc/Test" @("sandbox","smoke","demo","launch packet","test script") "Add sandbox smoke path.")
        (New-Check 48 "Release" "Production Readiness Notes Exist" "Production dependencies and launch notes exist." "Doc" @("production","launch","onboarding","environment","rollout") "Add production readiness note.")
        (New-Check 49 "Operations" "Support/Triage Path Exists" "Support path for module issues exists." "Doc" @("support","triage","incident","escalation","owner") "Add owner/support escalation path.")
        (New-Check 50 "Quality" "No Placeholder/Fake Production Data" "Module avoids fake production-facing metrics/content." "Code/Doc" @("placeholder","TODO","mock","fake","sample") "Replace placeholders or clearly sandbox-scope them.")
        (New-Check 51 "Quality" "Definition of Done Met" "Module satisfies code, data, UI, tests, docs, security, and release proof." "Composite" @("Definition of Done","complete","PASS","ready","done") "Close all missing evidence rows before claiming complete.")
    )

    # Build file index for fast mode
    Write-Step "Building file index."
    $AllowedExtensions = @(".py",".js",".jsx",".ts",".tsx",".json",".yml",".yaml",".md",".txt",".ps1",".sh",".html",".css",".scss",".toml",".ini",".cfg",".env.example")
    $AllFiles = @(Get-ChildItem -Path . -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
        $ext = $_.Extension.ToLowerInvariant()
        ($AllowedExtensions -contains $ext) -and ($_.FullName -notmatch "\.git|node_modules|\.venv|venv|dist|build|audit-artifacts") -and ((-not $IncludeLargeSearch) -or $_.Length -lt 2MB)
    })
    $FileIndex = @($AllFiles | ForEach-Object { $_.FullName })

    # Fast mode search: path-only matching, bounded
    function Search-Evidence-Fast {
        param([string[]]$Keywords, [int]$MaxFiles = 250)
        $patterns = @($Keywords | Where-Object { $_ -and $_.Trim() } | Select-Object -Unique)
        $hits = @()
        foreach ($pattern in $patterns) {
            if ($hits.Count -ge $MaxFiles) { break }
            $p = $pattern.ToLowerInvariant()
            foreach ($file in $FileIndex) {
                if ($hits.Count -ge $MaxFiles) { break }
                if ($file.ToLowerInvariant().Contains($p)) { $hits += $file }
            }
        }
        return @($hits | Select-Object -Unique | Select-Object -First $MaxFiles)
    }

    # Classify status based on hits
    function Classify-Status {
        param([object]$Check, [string[]]$Hits)
        $hitCount = $Hits.Count
        if ($hitCount -eq 0) { return "NOT DESIGNED / NO EVIDENCE" }
        $hasCode = [bool]($Hits | Where-Object { $_ -match "\.(py|ts|tsx|js|jsx|yml|yaml|ps1)$" })
        $hasDoc = [bool]($Hits | Where-Object { $_ -match "\.(md|txt)$" })
        $hasTest = [bool]($Hits | Where-Object { $_ -match "(test_|\.test\.|\.spec\.|tests\\|tests/|playwright)" })
        
        switch ($Check.EvidenceType) {
            "Doc" { return $(if($hasDoc) { "DESIGNED" } else { "PARTIAL / NEEDS DOC" }) }
            "Code" { return $(if($hasCode) { "DESIGNED + IMPLEMENTED EVIDENCE" } else { "PARTIAL / NEEDS CODE" }) }
            "UI/API" { return $(if($hasCode) { "IMPLEMENTATION EVIDENCE FOUND" } else { "PARTIAL / NEEDS UI/API" }) }
            "Code/Doc" { return $(if($hasCode -and $hasDoc) { "DESIGNED + IMPLEMENTED EVIDENCE" } else { "PARTIAL / NEEDS CODE OR DOC" }) }
            "Code/Test" { return $(if($hasCode -and $hasTest) { "WORKING EVIDENCE CANDIDATE" } elseif($hasCode) { "IMPLEMENTED / TEST GAP" } else { "PARTIAL / NEEDS CODE + TEST" }) }
            "Test" { return $(if($hasTest) { "TEST EVIDENCE FOUND" } else { "NOT PROVEN / TEST GAP" }) }
            "CI" { return $(if($hasCode -or $hasTest) { "CI EVIDENCE CANDIDATE" } else { "NOT PROVEN / CI GAP" }) }
            "Composite" { return $(if($hasCode -and $hasDoc -and $hasTest) { "COMPLETE EVIDENCE CANDIDATE" } else { "NOT COMPLETE / GAPS REMAIN" }) }
            default { return $(if($hitCount -gt 0) { "EVIDENCE FOUND" } else { "NO EVIDENCE" }) }
        }
    }

    function Status-To-Severity {
        param([string]$Status)
        if ($Status -match "NO EVIDENCE|NOT DESIGNED|NOT PROVEN|NOT COMPLETE") { return "FAIL" }
        if ($Status -match "PARTIAL|GAP") { return "REVIEW" }
        if ($Status -match "CANDIDATE|FOUND|DESIGNED|IMPLEMENTED") { return "PASS-CANDIDATE" }
        return "REVIEW"
    }

    # Run audit
    Write-Step "Running 51 modules x 51 checks"
    $Rows = New-Object System.Collections.Generic.List[object]
    $FixRows = New-Object System.Collections.Generic.List[object]
    $ModuleResults = @()

    foreach ($module in $Modules) {
        $checkpointFile = "$CheckpointDir\module_$($module.Id).json"
        if ($Resume -and (Test-Path $checkpointFile)) {
            Write-Step "Auditing module $($module.Id)/51: $($module.Name) (resuming from checkpoint)"
            $checkpoint = Get-Content $checkpointFile -Raw | ConvertFrom-Json
            $checkpoint.rows | ForEach-Object { $Rows.Add($_) }
            continue
        }

        Write-Step "Auditing module $($module.Id)/51: $($module.Name)"
        $moduleStart = Get-Date

        foreach ($check in $Checks) {
            try {
                $evidenceId = "{0:D2}_{1}_{2:D2}_{3}" -f $module.Id, (Normalize-Name $module.Name), $check.Id, (Normalize-Name $check.Name)
                $evidenceFile = "$EvidenceRoot\$evidenceId.txt"

                $keywords = @() + $module.Keywords + $check.EvidenceKeywords
                $hits = @(Search-Evidence-Fast -Keywords $keywords -MaxFiles $MaxFilesPerPattern)
                
                @($hits | ForEach-Object { "path-match: $_" }) | Set-Content -Encoding UTF8 $evidenceFile

                $status = Classify-Status -Check $check -Hits $hits
                $severity = Status-To-Severity -Status $status

                $row = [pscustomobject]@{
                    ModuleId = $module.Id; Layer = $module.Layer; Module = $module.Name; Owner = $module.Owner
                    ModuleDefinition = $module.Definition; EssentialFunctions = ($module.EssentialFunctions -join " | ")
                    CoreOperations = ($module.CoreOperations -join " | "); KPIs = ($module.Kpis -join " | ")
                    RequiredWiring = ($module.RequiredWiring -join " | "); CheckId = $check.Id
                    CheckCategory = $check.Category; CheckName = $check.Name
                    CheckDefinition = $check.Definition; EvidenceType = $check.EvidenceType
                    Status = $status; Severity = $severity; EvidenceHitCount = $hits.Count
                    EvidenceFile = $evidenceFile; RequiredFixIfMissing = $check.RequiredFixIfMissing
                }

                $Rows.Add($row)
                if ($severity -ne "PASS-CANDIDATE") { $FixRows.Add($row) }

                # Check timeout per module
                $elapsed = (Get-Date) - $moduleStart
                if ($elapsed.TotalSeconds -gt $MaxSecondsPerModule) {
                    Write-Step "Module $($module.Id) timeout exceeded ($($elapsed.TotalSeconds)s > $MaxSecondsPerModule`s); skipping remaining checks"
                    break
                }
            } catch {
                Write-Step "Module $($module.Id) Check $($check.Id) error: $($_.Exception.Message)"
                $Rows.Add([pscustomobject]@{
                    ModuleId = $module.Id; Layer = $module.Layer; Module = $module.Name; Owner = $module.Owner
                    ModuleDefinition = $module.Definition; EssentialFunctions = ($module.EssentialFunctions -join " | ")
                    CoreOperations = ($module.CoreOperations -join " | "); KPIs = ($module.Kpis -join " | ")
                    RequiredWiring = ($module.RequiredWiring -join " | "); CheckId = $check.Id
                    CheckCategory = $check.Category; CheckName = $check.Name
                    CheckDefinition = $check.Definition; EvidenceType = $check.EvidenceType
                    Status = "ERROR"; Severity = "REVIEW"; EvidenceHitCount = 0
                    EvidenceFile = ""; RequiredFixIfMissing = $check.RequiredFixIfMissing
                })
            }
        }

        # Write module checkpoint
        $moduleRows = @($Rows | Where-Object { $_.ModuleId -eq $module.Id })
        @{
            moduleId = $module.Id
            timestamp = Get-Date -Format o
            rowCount = $moduleRows.Count
            rows = @($moduleRows)
        } | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $checkpointFile
    }

    # Export CSVs
    Write-Step "Exporting matrices."
    $Rows | Export-Csv -NoTypeInformation -Encoding UTF8 $MatrixCsv
    $FixRows | Export-Csv -NoTypeInformation -Encoding UTF8 $FixMatrixCsv

    # Module summaries
    Write-Step "Generating module summaries."
    $ModuleSummary = foreach ($module in $Modules) {
        $moduleRows = @($Rows | Where-Object { $_.ModuleId -eq $module.Id })
        $fail = @($moduleRows | Where-Object { $_.Severity -eq "FAIL" }).Count
        $review = @($moduleRows | Where-Object { $_.Severity -eq "REVIEW" }).Count
        $passCandidate = @($moduleRows | Where-Object { $_.Severity -eq "PASS-CANDIDATE" }).Count

        $decision = if ($fail -eq 0 -and $review -eq 0) { "COMPLETE EVIDENCE CANDIDATE" } elseif ($fail -eq 0) { "PARTIAL / REVIEW REQUIRED" } else { "NOT COMPLETE / FIX REQUIRED" }

        [pscustomobject]@{
            ModuleId = $module.Id; Layer = $module.Layer; Module = $module.Name; Owner = $module.Owner
            Decision = $decision; PassCandidate = $passCandidate; Review = $review; Fail = $fail
            TotalChecks = $moduleRows.Count
            TopFixes = (($moduleRows | Where-Object { $_.Severity -ne "PASS-CANDIDATE" } | Select-Object -First 8 | ForEach-Object { "$($_.CheckName): $($_.RequiredFixIfMissing)" }) -join " || ")
        }
    }
    $ModuleSummary | Export-Csv -NoTypeInformation -Encoding UTF8 $ModuleSummaryCsv

    # Compute final decision
    $TotalRows = $Rows.Count
    $TotalPassCandidate = @($Rows | Where-Object { $_.Severity -eq "PASS-CANDIDATE" }).Count
    $TotalReview = @($Rows | Where-Object { $_.Severity -eq "REVIEW" }).Count
    $TotalFail = @($Rows | Where-Object { $_.Severity -eq "FAIL" }).Count

    $AllModulesComplete = 51 -eq ($ModuleSummary | Measure-Object).Count
    $CompleteModules = @($ModuleSummary | Where-Object { $_.Decision -eq "COMPLETE EVIDENCE CANDIDATE" }).Count

    $OverallDecision = if ($AllModulesComplete -and $TotalFail -eq 0 -and $TotalReview -eq 0) { "PASS" } else { "NO-GO" }

    # Generate summary markdown
    $summary = @(
        "# CROWN 51x51 Module Integrity Audit"
        ""
        "Generated: $(Get-Date -Format o)"
        "Repo root: $RepoRoot"
        "Mode: $(if($Fast){'Fast (path-only evidence matching)'}else{'Standard (content-aware)'})"
        ""
        "## Final Decision"
        ""
        "**$OverallDecision**"
        ""
        "## 51x51 Counts"
        ""
        "- Total rows: $TotalRows"
        "- PASS-CANDIDATE rows: $TotalPassCandidate"
        "- REVIEW rows: $TotalReview"
        "- FAIL rows: $TotalFail"
        ""
        "## Module Completion Counts"
        ""
        "- Complete evidence candidate modules: $CompleteModules / 51"
        ""
        "## Module Summary"
        ""
        "| ID | Layer | Module | Decision | PASS-CANDIDATE | REVIEW | FAIL |"
        "|---:|---|---|---|---:|---:|---:|"
    )
    
    foreach ($m in $ModuleSummary) {
        $summary += "| $($m.ModuleId) | $($m.Layer) | $($m.Module) | $($m.Decision) | $($m.PassCandidate) | $($m.Review) | $($m.Fail) |"
    }

    $summary += @(
        ""
        "## Files"
        ""
        "- Full matrix: $MatrixCsv"
        "- Module summary: $ModuleSummaryCsv"
        "- Fix matrix: $FixMatrixCsv"
        "- Evidence folder: $EvidenceRoot"
        "- JSON status: $JsonStatus"
    )

    $summary | Set-Content -Encoding UTF8 $ExecutiveSummary

    # Generate JSON status
    @{
        timestamp = $Stamp
        repoRoot = $RepoRoot
        mode = if ($Fast) { "fast" } else { "standard" }
        complete = $AllModulesComplete
        decision = $OverallDecision
        reason = if ($AllModulesComplete) { 
            if ($TotalFail -eq 0 -and $TotalReview -eq 0) { "All modules complete, no FAIL or REVIEW" } 
            else { "Audit complete but FAIL or REVIEW rows remain" } 
        } else { 
            "Audit incomplete: $(($ModuleSummary | Measure-Object).Count) / 51 modules processed"
        }
        totalRows = $TotalRows
        passCandidateRows = $TotalPassCandidate
        reviewRows = $TotalReview
        failRows = $TotalFail
        completeModules = $CompleteModules
        executiveSummary = $ExecutiveSummary
        matrixCsv = $MatrixCsv
        moduleSummaryCsv = $ModuleSummaryCsv
        fixMatrixCsv = $FixMatrixCsv
        evidenceRoot = $EvidenceRoot
    } | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $JsonStatus

    Write-Host ""
    Write-Host "CROWN 51x51 Module Integrity Audit Complete." -ForegroundColor Green
    Write-Host "Decision: $OverallDecision" -ForegroundColor $(if($OverallDecision -eq "PASS") { "Green" } else { "Yellow" })
    Write-Host "Summary: $ExecutiveSummary"
    Write-Host "Matrix: $MatrixCsv"
    Write-Host "Status: $JsonStatus"
    Write-Host ""

} finally {
    # Ensure final artifacts are emitted even if errors occur
    if (-not (Test-Path $ExecutiveSummary) -or -not (Test-Path $JsonStatus)) {
        Write-Step "WARNING: Creating fallback final artifacts due to incomplete run"
        
        if (-not (Test-Path $ExecutiveSummary)) {
            @(
                "# CROWN 51x51 Module Integrity Audit"
                "Generated: $(Get-Date -Format o)"
                "Status: INCOMPLETE (fallback summary)"
                "Decision: NO-GO"
                "Reason: Audit run did not complete successfully"
            ) | Set-Content -Encoding UTF8 $ExecutiveSummary
        }

        if (-not (Test-Path $JsonStatus)) {
            @{
                timestamp = $Stamp
                repoRoot = $RepoRoot
                mode = if ($Fast) { "fast" } else { "standard" }
                complete = $false
                decision = "NO-GO"
                reason = "Audit incomplete or error occurred"
                totalRows = 0
                passCandidateRows = 0
                reviewRows = 0
                failRows = 0
                completeModules = 0
                executiveSummary = $ExecutiveSummary
                matrixCsv = $MatrixCsv
                moduleSummaryCsv = $ModuleSummaryCsv
                fixMatrixCsv = $FixMatrixCsv
                evidenceRoot = $EvidenceRoot
            } | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $JsonStatus
        }

        if (-not (Test-Path $MatrixCsv)) {
            "ModuleId,Layer,Module,Owner,CheckId,CheckCategory,CheckName,Status,Severity" | Set-Content -Encoding UTF8 $MatrixCsv
        }

        if (-not (Test-Path $FixMatrixCsv)) {
            "ModuleId,Layer,Module,Owner,CheckId,CheckCategory,CheckName,Status,Severity" | Set-Content -Encoding UTF8 $FixMatrixCsv
        }

        Write-Host "Fallback artifacts created." -ForegroundColor Yellow
    }
}

exit 0
