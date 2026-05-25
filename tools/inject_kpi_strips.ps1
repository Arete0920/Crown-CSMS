# inject_kpi_strips.ps1
# Adds role-specific KPI flip card data and KpiStrip JSX to every major dashboard.
# Strategy: insert KPI const block before the export function declaration, and
# insert <KpiStrip.../> immediately after the <CrownLayout ...> closing bracket.

$base = "c:\Users\JMega\OneDrive\Desktop\Crown2026\frontend\dashboards\src\pages"

# ── KPI card definitions per dashboard ────────────────────────────────────────
$KPI = @{}

$KPI["AdminDashboard"] = @'
/* ── Head-of-School KPI flip cards (blue front, gold back) ─────────── */
const ADMIN_KPI = [
  { label: "Enrollment",        value: "742/760", trend: "+4.1% vs goal",   trendUp: true,
    definition: "Total active students enrolled this term vs. capacity. Click Enrollment for drill-down by grade.",
    dataSource: "Enrollment Module", dataHref: "/admissions" },
  { label: "Yield Rate",        value: "91%",     trend: "+4.9% vs last yr", trendUp: true,
    definition: "Percentage of accepted applicants who enrolled. Driven by admissions funnel conversion.",
    dataSource: "Admissions Pipeline", dataHref: "/admissions" },
  { label: "Attendance Today",  value: "96.4%",   trend: "+0.8%",            trendUp: true,
    definition: "Percentage of enrolled students marked present today across all sections.",
    dataSource: "Attendance Module", dataHref: "/attendance" },
  { label: "Tuition Collected", value: "93.1%",   trend: "+6.0% vs last yr", trendUp: true,
    definition: "Percentage of billed tuition that has been collected as of today across all active households.",
    dataSource: "Billing Module", dataHref: "/billing" },
  { label: "Financial Aid Used", value: "68%",    trend: "-2.3%",            trendUp: false,
    definition: "Portion of the annual aid budget that has been awarded to students this term.",
    dataSource: "Financial Aid Module", dataHref: "/financial-aid" },
  { label: "Attrition",         value: "8%",      trend: "-1.6% vs last yr", trendUp: true,
    definition: "Percentage of enrolled students who withdrew during this academic year.",
    dataSource: "Enrollment Module", dataHref: "/admissions" },
];
'@

$KPI["AdvancementDashboard"] = @'
/* ── Advancement KPI flip cards ─────────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Active Donors",       value: "127",     trend: "+14 vs last yr", trendUp: true,
    definition: "Unique donors who have given at least one gift in the current fiscal year.",
    dataSource: "Advancement Module", dataHref: "/advancement" },
  { label: "Campaign Progress",   value: "64%",     trend: "+18% MTD",       trendUp: true,
    definition: "Weighted average of progress across all active campaigns (raised ÷ goal).",
    dataSource: "Campaign Scoreboard", dataHref: "/advancement" },
  { label: "YTD Raised",          value: "$177,400", trend: null,             trendUp: null,
    definition: "Total gifts and pledges received year-to-date across all campaigns.",
    dataSource: "Advancement Module", dataHref: "/advancement" },
  { label: "Pledges Outstanding", value: "23",      trend: null,             trendUp: null,
    definition: "Number of pledge commitments not yet fulfilled — follow-up queue ready.",
    dataSource: "Advancement Module", dataHref: "/advancement" },
  { label: "Thank-Yous Due",      value: "9",       trend: null,             trendUp: null,
    definition: "Acknowledgement letters or calls not yet completed within the 48-hr stewardship window.",
    dataSource: "Advancement Module", dataHref: "/advancement" },
];
'@

$KPI["FinancialAidDashboard"] = @'
/* ── Financial Aid KPI flip cards ───────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Applications",      value: "—",    trend: null,          trendUp: null,
    definition: "Total financial aid applications submitted for the selected academic year.",
    dataSource: "Financial Aid API", dataHref: "/financial-aid" },
  { label: "Awards Active",     value: "—",    trend: null,          trendUp: null,
    definition: "Number of approved aid awards currently disbursed to students.",
    dataSource: "Financial Aid API", dataHref: "/financial-aid" },
  { label: "Total Awarded",     value: "—",    trend: null,          trendUp: null,
    definition: "Sum of all aid amounts granted this academic year across all buckets.",
    dataSource: "Financial Aid API", dataHref: "/financial-aid" },
  { label: "Avg Award",         value: "—",    trend: null,          trendUp: null,
    definition: "Mean aid amount per household awarded this term.",
    dataSource: "Financial Aid API", dataHref: "/financial-aid" },
  { label: "Budget Utilization", value: "73%", trend: "+5% vs plan",  trendUp: true,
    definition: "Percentage of the annual financial aid budget that has been committed to awards.",
    dataSource: "Financial Aid API", dataHref: "/financial-aid" },
];
'@

$KPI["BillingDashboard"] = @'
/* ── Billing / Accounts-Receivable KPI flip cards ───────────────────── */
const ADMIN_KPI = [
  { label: "Collection Rate",   value: "93.1%", trend: "+6.0% vs last yr", trendUp: true,
    definition: "Percentage of total billed tuition and fees collected as of today.",
    dataSource: "Billing Module", dataHref: "/billing" },
  { label: "Outstanding AR",    value: "$42,880", trend: null,             trendUp: null,
    definition: "Total unpaid balances across all households with open invoices.",
    dataSource: "Billing Module", dataHref: "/billing" },
  { label: "Invoices Overdue",  value: "23",    trend: "+3 vs last wk",   trendUp: false,
    definition: "Invoices past their due date that have not been paid or placed on a plan.",
    dataSource: "Billing Module", dataHref: "/billing" },
  { label: "Payment Plans",     value: "18",    trend: null,               trendUp: null,
    definition: "Number of households currently enrolled in an active installment payment plan.",
    dataSource: "Billing Module", dataHref: "/billing" },
];
'@

$KPI["TeacherDashboard"] = @'
/* ── Teacher KPI flip cards ─────────────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Present Today",     value: "—",    trend: null,             trendUp: null,
    definition: "Number of students marked present in your sections today vs. total enrolled.",
    dataSource: "Attendance Module", dataHref: "/attendance" },
  { label: "Avg Class Grade",   value: "—",    trend: null,             trendUp: null,
    definition: "Weighted mean grade across all assignments in your active sections this term.",
    dataSource: "Gradebook", dataHref: "/gradebook" },
  { label: "Missing Work",      value: "—",    trend: null,             trendUp: null,
    definition: "Total count of assignments past due with no submission, across all your sections.",
    dataSource: "Gradebook", dataHref: "/gradebook" },
  { label: "Assignments Due",   value: "3",    trend: null,             trendUp: null,
    definition: "Number of assignments due this week that still require grading.",
    dataSource: "Gradebook", dataHref: "/gradebook" },
];
'@

$KPI["IntegrityDashboard"] = @'
/* ── Integrity / Audit KPI flip cards ───────────────────────────────── */
const ADMIN_KPI = [
  { label: "Audit Events Today", value: "—",   trend: null,              trendUp: null,
    definition: "Total system audit log entries recorded in the last 24 hours.",
    dataSource: "Audit Log API", dataHref: "/integrity" },
  { label: "Failed Logins",      value: "—",   trend: null,              trendUp: null,
    definition: "Number of failed authentication attempts in the monitoring window.",
    dataSource: "Security Module", dataHref: "/security" },
  { label: "Data Changes",       value: "—",   trend: null,              trendUp: null,
    definition: "Number of create/update/delete operations on sensitive data records today.",
    dataSource: "Audit Log API", dataHref: "/integrity" },
  { label: "Compliance Score",   value: "96%", trend: "+1% vs last wk",  trendUp: true,
    definition: "Automated compliance check score across all monitored policies and access controls.",
    dataSource: "Integrity Module", dataHref: "/integrity" },
];
'@

$KPI["FacilitiesDashboard"] = @'
/* ── Facilities KPI flip cards ──────────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Open Work Orders",    value: "7",    trend: "-2 vs last wk",  trendUp: true,
    definition: "Total unresolved maintenance and repair work orders currently active.",
    dataSource: "Facilities Module", dataHref: "/facilities" },
  { label: "Resolved MTD",        value: "23",   trend: "+5 vs last mo",  trendUp: true,
    definition: "Work orders closed and completed this calendar month.",
    dataSource: "Facilities Module", dataHref: "/facilities" },
  { label: "Rooms Available",     value: "42/48", trend: null,            trendUp: null,
    definition: "Usable rooms cleared for occupancy vs. total campus rooms.",
    dataSource: "Facilities Module", dataHref: "/facilities" },
  { label: "Inspections Due",     value: "2",    trend: null,             trendUp: null,
    definition: "Scheduled safety or compliance inspections due within the next 7 days.",
    dataSource: "Facilities Module", dataHref: "/facilities" },
];
'@

$KPI["HealthDashboard"] = @'
/* ── Health / Nurse KPI flip cards ─────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Students Seen Today", value: "4",  trend: null,              trendUp: null,
    definition: "Students who visited the health office today for any reason.",
    dataSource: "Health Module", dataHref: "/health" },
  { label: "Medication Pending",  value: "2",  trend: null,              trendUp: null,
    definition: "Scheduled medication administrations not yet marked complete today.",
    dataSource: "Health Module", dataHref: "/health" },
  { label: "Immunization Gaps",   value: "3",  trend: "-1 vs last wk",  trendUp: true,
    definition: "Students whose immunization records have outstanding or expiring requirements.",
    dataSource: "Health Module", dataHref: "/health" },
  { label: "Incidents MTD",       value: "8",  trend: null,              trendUp: null,
    definition: "Total health-related incidents logged this month (injury, illness, referral).",
    dataSource: "Health Module", dataHref: "/health" },
];
'@

$KPI["HumanResources"] = @'
/* ── HR / Staff KPI flip cards ──────────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Staff Active",         value: "84",   trend: null,              trendUp: null,
    definition: "Total full-time and part-time staff with active employment records.",
    dataSource: "HR Module", dataHref: "/human-resources" },
  { label: "Open Positions",       value: "2",    trend: null,              trendUp: null,
    definition: "Approved positions currently posted or in search phase.",
    dataSource: "HR Module", dataHref: "/human-resources" },
  { label: "Retention Rate",       value: "94%",  trend: "+2% vs last yr",  trendUp: true,
    definition: "Percentage of employees who remained employed from the start of the school year to today.",
    dataSource: "HR Module", dataHref: "/human-resources" },
  { label: "Trainings Due",        value: "7",    trend: null,              trendUp: null,
    definition: "Required professional development trainings due within the next 30 days.",
    dataSource: "HR Module", dataHref: "/human-resources" },
];
'@

$KPI["ITDashboard"] = @'
/* ── IT KPI flip cards ───────────────────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Tickets Open",   value: "12",     trend: "-4 vs last wk",   trendUp: true,
    definition: "Open helpdesk tickets assigned to IT staff awaiting resolution.",
    dataSource: "IT Module", dataHref: "/it" },
  { label: "Resolved MTD",   value: "47",     trend: "+8 vs last mo",   trendUp: true,
    definition: "Helpdesk tickets resolved and closed this calendar month.",
    dataSource: "IT Module", dataHref: "/it" },
  { label: "Assets Tracked", value: "243",    trend: null,               trendUp: null,
    definition: "Technology assets (devices, licenses, AV equipment) in the asset registry.",
    dataSource: "IT Module", dataHref: "/it" },
  { label: "System Uptime",  value: "99.8%",  trend: null,               trendUp: null,
    definition: "Rolling 30-day uptime across all monitored Crown platform services.",
    dataSource: "IT Module", dataHref: "/it" },
];
'@

$KPI["AthleticsDashboard"] = @'
/* ── Athletics KPI flip cards ───────────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Teams Active",      value: "6",   trend: null,              trendUp: null,
    definition: "Active sports teams in season currently rostered and scheduled.",
    dataSource: "Athletics Module", dataHref: "/athletics" },
  { label: "Athletes Eligible", value: "90%", trend: null,              trendUp: null,
    definition: "Percentage of rostered athletes meeting academic eligibility requirements.",
    dataSource: "Gradebook + Athletics", dataHref: "/athletics" },
  { label: "Games This Week",   value: "2",   trend: null,              trendUp: null,
    definition: "Scheduled games and matches for all active teams this calendar week.",
    dataSource: "Athletics Module", dataHref: "/athletics" },
  { label: "Win Rate (Season)", value: "65%", trend: "+8% vs last yr",  trendUp: true,
    definition: "Aggregate win percentage across all active teams this season.",
    dataSource: "Athletics Module", dataHref: "/athletics" },
];
'@

$KPI["FoodDashboard"] = @'
/* ── Food / Lunch Program KPI flip cards ────────────────────────────── */
const ADMIN_KPI = [
  { label: "Meals Today",         value: "312",     trend: null,             trendUp: null,
    definition: "Total meals served today across all meal periods (breakfast, lunch, aftercare).",
    dataSource: "Food Module", dataHref: "/food" },
  { label: "Free/Reduced %",      value: "28%",     trend: null,             trendUp: null,
    definition: "Percentage of students participating in federal free or reduced-price meal programs.",
    dataSource: "Food Module", dataHref: "/food" },
  { label: "Low Balance Alerts",  value: "12",      trend: "+3 vs yesterday",trendUp: false,
    definition: "Student accounts with a meal balance below $5.00 — contact families.",
    dataSource: "Food Module", dataHref: "/food" },
  { label: "Revenue Today",       value: "$1,248",  trend: null,             trendUp: null,
    definition: "Total meal revenue collected today (paid accounts only, excluding free/reduced).",
    dataSource: "Food Module", dataHref: "/food" },
];
'@

$KPI["SpiritualLifeDashboard"] = @'
/* ── Spiritual Life KPI flip cards ─────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Chapel Attendance",  value: "94%",  trend: "+2% vs last wk",  trendUp: true,
    definition: "Percentage of enrolled students present at the most recent chapel service.",
    dataSource: "Attendance Module", dataHref: "/attendance" },
  { label: "Service Hours",      value: "847",  trend: "+112 MTD",         trendUp: true,
    definition: "Total community service hours logged by students this academic year.",
    dataSource: "Service Hours Module", dataHref: "/service-hours" },
  { label: "Events This Month",  value: "3",    trend: null,               trendUp: null,
    definition: "Spiritual life events (retreats, guest speakers, prayer events) scheduled this month.",
    dataSource: "Calendar Module", dataHref: "/calendar" },
  { label: "Devotions Sent",     value: "14",   trend: null,               trendUp: null,
    definition: "Daily devotions and reflections distributed to staff and families this term.",
    dataSource: "Communications Module", dataHref: "/communications" },
];
'@

$KPI["CounselingDashboard"] = @'
/* ── Counseling KPI flip cards ──────────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Students Seen MTD",  value: "18",  trend: null,              trendUp: null,
    definition: "Unique students who had a counseling session this calendar month.",
    dataSource: "Counseling Module", dataHref: "/counseling" },
  { label: "Referrals Open",     value: "4",   trend: null,              trendUp: null,
    definition: "Open referrals awaiting follow-up from the counselor or outside provider.",
    dataSource: "Counseling Module", dataHref: "/counseling" },
  { label: "Plans Active",       value: "12",  trend: null,              trendUp: null,
    definition: "Students with an active counseling, IEP, or 504 support plan.",
    dataSource: "Counseling Module", dataHref: "/counseling" },
  { label: "Academic Risk",      value: "6",   trend: "-2 vs last wk",  trendUp: true,
    definition: "Students flagged at academic risk (GPA below threshold or 3+ missing assignments).",
    dataSource: "Academics Module", dataHref: "/academics" },
];
'@

$KPI["LibraryDashboard"] = @'
/* ── Library KPI flip cards ─────────────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Checked Out",        value: "87",  trend: null,              trendUp: null,
    definition: "Total items (books, media, equipment) currently checked out to students or staff.",
    dataSource: "Library Module", dataHref: "/library" },
  { label: "Overdue Returns",    value: "14",  trend: "+2 vs last wk",  trendUp: false,
    definition: "Items past their return date that have not been checked back in.",
    dataSource: "Library Module", dataHref: "/library" },
  { label: "New Acquisitions",   value: "6",   trend: null,              trendUp: null,
    definition: "New titles or items added to the collection catalog this month.",
    dataSource: "Library Module", dataHref: "/library" },
  { label: "Active Borrowers",   value: "54",  trend: null,              trendUp: null,
    definition: "Unique students and staff who have checked out at least one item this term.",
    dataSource: "Library Module", dataHref: "/library" },
];
'@

$KPI["MarketingDashboard"] = @'
/* ── Marketing KPI flip cards ───────────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Inquiries MTD",     value: "28",    trend: "+6 vs last mo",  trendUp: true,
    definition: "Prospective families who submitted an inquiry form this month.",
    dataSource: "Admissions / CRM", dataHref: "/admissions" },
  { label: "Website Visits",    value: "1,842", trend: "+14% vs last mo",trendUp: true,
    definition: "Total unique visitors to the school website this calendar month.",
    dataSource: "Analytics", dataHref: "/marketing" },
  { label: "Email Open Rate",   value: "42%",   trend: "+3% vs last mo", trendUp: true,
    definition: "Average open rate across all marketing emails sent this month.",
    dataSource: "Communications Module", dataHref: "/communications" },
  { label: "Social Followers",  value: "2,140", trend: "+32 this mo",    trendUp: true,
    definition: "Total combined followers across all official school social media accounts.",
    dataSource: "Marketing Module", dataHref: "/marketing" },
];
'@

$KPI["SafetyDashboard"] = @'
/* ── Safety KPI flip cards ──────────────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Incidents MTD",     value: "2",    trend: "-1 vs last mo",  trendUp: true,
    definition: "Safety incidents (injury, near-miss, property damage) logged this month.",
    dataSource: "Safety Module", dataHref: "/safety" },
  { label: "Drills Completed",  value: "3/5",  trend: null,              trendUp: null,
    definition: "Emergency drills (fire, lockdown, shelter-in-place) completed vs. scheduled this year.",
    dataSource: "Safety Module", dataHref: "/safety" },
  { label: "Visitors Today",    value: "14",   trend: null,              trendUp: null,
    definition: "Visitors checked in through the front office visitor management system today.",
    dataSource: "Security Module", dataHref: "/security" },
  { label: "Open Hazards",      value: "0",    trend: null,              trendUp: null,
    definition: "Reported safety hazards not yet resolved by facilities or administration.",
    dataSource: "Safety Module", dataHref: "/safety" },
];
'@

$KPI["TransportationDashboard"] = @'
/* ── Transportation KPI flip cards ─────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Routes Active",     value: "8",    trend: null,              trendUp: null,
    definition: "Bus and carpool routes currently in operation for morning and afternoon runs.",
    dataSource: "Transportation Module", dataHref: "/transportation" },
  { label: "Students on Bus",   value: "142",  trend: null,              trendUp: null,
    definition: "Total students registered on daily bus routes (AM + PM).",
    dataSource: "Transportation Module", dataHref: "/transportation" },
  { label: "On-Time Rate",      value: "97%",  trend: "+1% vs last wk",  trendUp: true,
    definition: "Percentage of route arrivals within 5 minutes of scheduled pickup/drop-off.",
    dataSource: "Transportation Module", dataHref: "/transportation" },
  { label: "Incidents MTD",     value: "1",    trend: null,              trendUp: null,
    definition: "Transportation incidents (late, breakdown, safety issue) reported this month.",
    dataSource: "Transportation Module", dataHref: "/transportation" },
];
'@

$KPI["ParentDashboard"] = @'
/* ── Parent KPI flip cards ──────────────────────────────────────────── */
const ADMIN_KPI = [
  { label: "My Children",       value: "2",    trend: null,              trendUp: null,
    definition: "Number of enrolled students linked to your parent or guardian account.",
    dataSource: "Enrollment Module", dataHref: "/student" },
  { label: "Upcoming Events",   value: "4",    trend: null,              trendUp: null,
    definition: "School events in the next 14 days relevant to your family.",
    dataSource: "Calendar Module", dataHref: "/calendar" },
  { label: "Unread Messages",   value: "3",    trend: null,              trendUp: null,
    definition: "Unread messages from teachers, administrators, or the school office.",
    dataSource: "Communications Module", dataHref: "/communications" },
  { label: "Balance Due",       value: "$450", trend: null,              trendUp: null,
    definition: "Total outstanding tuition or fee balance on your household account.",
    dataSource: "Billing Module", dataHref: "/billing" },
];
'@

$KPI["StudentDashboard"] = @'
/* ── Student KPI flip cards ─────────────────────────────────────────── */
const ADMIN_KPI = [
  { label: "My GPA",            value: "3.4",  trend: "+0.2 this term",  trendUp: true,
    definition: "Your weighted grade point average across all current courses this term.",
    dataSource: "Gradebook", dataHref: "/gradebook" },
  { label: "Attendance Rate",   value: "97.1%",trend: null,               trendUp: null,
    definition: "Percentage of scheduled class days you have been marked present this term.",
    dataSource: "Attendance Module", dataHref: "/attendance" },
  { label: "Missing Work",      value: "1",    trend: null,               trendUp: null,
    definition: "Assignments that are past due with no submission recorded.",
    dataSource: "Gradebook", dataHref: "/gradebook" },
  { label: "Next Due Date",     value: "Tomorrow", trend: null,           trendUp: null,
    definition: "Your nearest upcoming assignment deadline across all courses.",
    dataSource: "Gradebook", dataHref: "/gradebook" },
];
'@

$KPI["ExtendedCareDashboard"] = @'
/* ── Extended Care KPI flip cards ───────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Enrolled Today",    value: "47",    trend: null,             trendUp: null,
    definition: "Students registered for extended care (before/aftercare) today.",
    dataSource: "Extended Care Module", dataHref: "/extended-care" },
  { label: "Checked In",        value: "43",    trend: null,             trendUp: null,
    definition: "Students who have been checked in by staff today.",
    dataSource: "Extended Care Module", dataHref: "/extended-care" },
  { label: "Revenue Today",     value: "$705",  trend: null,             trendUp: null,
    definition: "Fees collected today for extended care services (hourly + flat-rate).",
    dataSource: "Billing Module", dataHref: "/billing" },
  { label: "Staff On Duty",     value: "5",     trend: null,             trendUp: null,
    definition: "Extended care staff members currently clocked in and on duty.",
    dataSource: "HR Module", dataHref: "/human-resources" },
];
'@

$KPI["RegistrarDashboard"] = @'
/* ── Registrar KPI flip cards ───────────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Records Pending",    value: "8",    trend: null,             trendUp: null,
    definition: "Student records with incomplete or missing required fields awaiting review.",
    dataSource: "Registrar Module", dataHref: "/registrar" },
  { label: "Transcripts Issued", value: "14",   trend: null,             trendUp: null,
    definition: "Official transcripts issued to students, colleges, or third parties this month.",
    dataSource: "Registrar Module", dataHref: "/registrar" },
  { label: "Enrollment Count",   value: "742",  trend: null,             trendUp: null,
    definition: "Total verified active enrollment count for the current term.",
    dataSource: "Enrollment Module", dataHref: "/admissions" },
  { label: "GPA Calc Status",    value: "Current", trend: null,          trendUp: null,
    definition: "Indicates whether the cumulative GPA calculation has been run for the current term.",
    dataSource: "Gradebook", dataHref: "/gradebook" },
];
'@

$KPI["PDDashboard"] = @'
/* ── Professional Development KPI flip cards ────────────────────────── */
const ADMIN_KPI = [
  { label: "Trainings This Mo",  value: "5",   trend: null,              trendUp: null,
    definition: "Professional development sessions scheduled or completed this month.",
    dataSource: "PD Module", dataHref: "/pd" },
  { label: "Staff Completed",    value: "78%", trend: "+12% vs last mo", trendUp: true,
    definition: "Percentage of required staff who have completed mandatory PD for this term.",
    dataSource: "PD Module", dataHref: "/pd" },
  { label: "Hours Logged",       value: "184", trend: null,              trendUp: null,
    definition: "Total professional development contact hours logged by all staff this year.",
    dataSource: "PD Module", dataHref: "/pd" },
  { label: "Plans Active",       value: "12",  trend: null,              trendUp: null,
    definition: "Individualized professional growth plans with active goals this year.",
    dataSource: "PD Module", dataHref: "/pd" },
];
'@

$KPI["AcademicSupportDashboard"] = @'
/* ── Academic Support KPI flip cards ────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Students in Support", value: "24", trend: null,              trendUp: null,
    definition: "Students currently enrolled in at least one academic support or intervention program.",
    dataSource: "Academics Module", dataHref: "/academics" },
  { label: "Sessions This Week",  value: "38", trend: null,              trendUp: null,
    definition: "Total one-on-one or small group support sessions scheduled or completed this week.",
    dataSource: "Academic Support Module", dataHref: "/academic-support" },
  { label: "Avg GPA Improvement", value: "+0.4",trend: null,             trendUp: null,
    definition: "Mean GPA improvement for students who have been in the support program this term.",
    dataSource: "Gradebook", dataHref: "/gradebook" },
  { label: "Accommodation Plans", value: "15", trend: null,              trendUp: null,
    definition: "Active IEP, 504, or accommodation plans on file for supported students.",
    dataSource: "Academic Support Module", dataHref: "/academic-support" },
];
'@

$KPI["FineArtsDashboard"] = @'
/* ── Fine Arts KPI flip cards ───────────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Ensembles Active",    value: "4",  trend: null,              trendUp: null,
    definition: "Active musical, theatre, or visual arts groups with current rosters.",
    dataSource: "Fine Arts Module", dataHref: "/fine-arts" },
  { label: "Students Enrolled",   value: "62", trend: null,              trendUp: null,
    definition: "Total students enrolled in at least one fine arts course or ensemble this term.",
    dataSource: "Enrollment Module", dataHref: "/admissions" },
  { label: "Performances This Yr",value: "3",  trend: null,              trendUp: null,
    definition: "Public performances or showcases completed this academic year.",
    dataSource: "Calendar Module", dataHref: "/calendar" },
  { label: "Auditions Upcoming",  value: "1",  trend: null,              trendUp: null,
    definition: "Scheduled auditions or tryouts for upcoming ensembles or productions.",
    dataSource: "Fine Arts Module", dataHref: "/fine-arts" },
];
'@

$KPI["CommunicationsDirectorDashboard"] = @'
/* ── Communications KPI flip cards ─────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Messages Today",     value: "14",  trend: null,              trendUp: null,
    definition: "Total messages sent through the Crown platform today (email, SMS, in-app).",
    dataSource: "Communications Module", dataHref: "/communications" },
  { label: "Open Rate",          value: "68%", trend: "+4% vs last wk",  trendUp: true,
    definition: "Percentage of messages sent today that were opened by at least one recipient.",
    dataSource: "Communications Module", dataHref: "/communications" },
  { label: "Active Threads",     value: "32",  trend: null,              trendUp: null,
    definition: "Conversation threads with at least one message in the last 7 days.",
    dataSource: "Communications Module", dataHref: "/communications" },
  { label: "Alerts Pending",     value: "2",   trend: null,              trendUp: null,
    definition: "Scheduled announcements or emergency alerts waiting to be reviewed and sent.",
    dataSource: "Communications Module", dataHref: "/communications" },
];
'@

$KPI["SecurityDashboard"] = @'
/* ── Security KPI flip cards ────────────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Visitors Logged",   value: "14",        trend: null,            trendUp: null,
    definition: "Visitors signed in through the front-office visitor management system today.",
    dataSource: "Security Module", dataHref: "/security" },
  { label: "Access Events",     value: "847",       trend: null,            trendUp: null,
    definition: "Total door access log events recorded today across all controlled entry points.",
    dataSource: "Security Module", dataHref: "/security" },
  { label: "Camera Status",     value: "All Online",trend: null,            trendUp: null,
    definition: "Status of the campus security camera network — all feeds online and recording.",
    dataSource: "Security Module", dataHref: "/security" },
  { label: "Incidents MTD",     value: "1",         trend: "-1 vs last mo", trendUp: true,
    definition: "Security incidents (unauthorized access, alarm triggers) logged this month.",
    dataSource: "Security Module", dataHref: "/security" },
];
'@

$KPI["OfficeDashboard"] = @'
/* ── Office KPI flip cards ───────────────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Front Desk Visitors", value: "14", trend: null,               trendUp: null,
    definition: "Visitors who have checked in at the main office today.",
    dataSource: "Office Module", dataHref: "/office" },
  { label: "Messages Pending",    value: "7",  trend: null,               trendUp: null,
    definition: "Phone or written messages waiting to be delivered to staff or returned.",
    dataSource: "Communications Module", dataHref: "/communications" },
  { label: "Tasks Due Today",     value: "5",  trend: null,               trendUp: null,
    definition: "Administrative tasks assigned to the office team due today.",
    dataSource: "Office Module", dataHref: "/office" },
  { label: "Packages In",         value: "3",  trend: null,               trendUp: null,
    definition: "Deliveries received and logged at the front desk today.",
    dataSource: "Office Module", dataHref: "/office" },
];
'@

$KPI["BoardDashboard"] = @'
/* ── Board KPI flip cards ───────────────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Enrollment",         value: "742",    trend: "+4.1% vs goal",    trendUp: true,
    definition: "Total active student enrollment for the current academic year.",
    dataSource: "Enrollment Module", dataHref: "/admissions" },
  { label: "Net Tuition Rev",    value: "$6.8M",  trend: "+10% vs last yr",  trendUp: true,
    definition: "Gross tuition collected minus total financial aid awarded — year-to-date.",
    dataSource: "Billing Module", dataHref: "/billing" },
  { label: "Staff Retention",    value: "94%",    trend: "+2% vs last yr",   trendUp: true,
    definition: "Percentage of employees who remained from the start to current date this year.",
    dataSource: "HR Module", dataHref: "/human-resources" },
  { label: "Endowment Balance",  value: "$2.1M",  trend: "+$80K vs last yr", trendUp: true,
    definition: "Current endowment fund balance including investment returns and new gifts.",
    dataSource: "Finance Module", dataHref: "/finance" },
];
'@

$KPI["BoardExecutiveDashboard"] = @'
/* ── Board Executive / Strategic Command KPI flip cards ─────────────── */
const ADMIN_KPI = [
  { label: "Net Tuition Rev",    value: "$6.8M",  trend: "+10% vs last yr",  trendUp: true,
    definition: "Gross tuition billings minus total aid awarded, year-to-date. Key indicator of financial sustainability.",
    dataSource: "Billing Module", dataHref: "/billing" },
  { label: "Staff Retention",    value: "87.2%",  trend: "+1.2% vs last yr", trendUp: true,
    definition: "Percentage of staff retained from start of year to today. Reflects culture and compensation health.",
    dataSource: "HR Module", dataHref: "/human-resources" },
  { label: "Cash Runway",        value: "6.5 mo", trend: "+0.4 mo",          trendUp: true,
    definition: "Months of operating expenses currently covered by unrestricted cash and liquid reserves.",
    dataSource: "Finance Module", dataHref: "/finance" },
  { label: "Yield Rate",         value: "11.2%",  trend: "-2.3%",            trendUp: false,
    definition: "Percentage of prospective-student inquiries that converted to enrolled students.",
    dataSource: "Admissions Pipeline", dataHref: "/admissions" },
  { label: "Re-enrollment Rate", value: "87.2%",  trend: "+41.6%",           trendUp: true,
    definition: "Percentage of currently-enrolled families who have completed re-enrollment for the next year.",
    dataSource: "Enrollment Module", dataHref: "/admissions" },
];
'@

# ── Now inject KPI const + KpiStrip JSX into each file ────────────────────────

$results = @()
foreach ($d in $KPI.Keys) {
  $path = "$base\$d.jsx"
  if (!(Test-Path $path)) { $results += "MISSING: $d"; continue }

  $content = Get-Content $path -Raw -Encoding UTF8

  # 1. Check if already injected
  if ($content -match "const ADMIN_KPI\b") { $results += "SKIP (KPI already injected): $d"; continue }

  # 2. Add KPI const before the first 'export (default )? function' declaration
  $kpiBlock = $KPI[$d]
  $content = $content -replace '(export (?:default )?function \w+\s*\()', "$kpiBlock`n`$1"

  # 3. Add <KpiStrip cards={ADMIN_KPI} /> after the CrownLayout opening tag
  # Find the pattern: <CrownLayout ...> (possibly multi-line) followed by first child content
  # Strategy: insert after the first line that ends CrownLayout opening (ends with >)
  $lines = $content -split "`n"
  $inLayout = $false
  $inserted = $false
  for ($i = 0; $i -lt $lines.Count; $i++) {
    if (!$inLayout -and $lines[$i] -match '<CrownLayout') {
      $inLayout = $true
    }
    if ($inLayout -and $lines[$i] -match '>\s*$' -and !$inserted) {
      # Insert KpiStrip after this line
      $kpiJsx = "      <KpiStrip cards={ADMIN_KPI} />"
      $before = $lines[0..$i]
      $after  = if ($i+1 -lt $lines.Count) { $lines[($i+1)..($lines.Count-1)] } else { @() }
      $lines  = $before + $kpiJsx + $after
      $inserted = $true
      break
    }
  }

  if (!$inserted) { $results += "WARN (no CrownLayout anchor): $d"; continue }

  $newContent = $lines -join "`n"
  [System.IO.File]::WriteAllText($path, $newContent, [System.Text.Encoding]::UTF8)
  $results += "OK: $d"
}

$results | ForEach-Object { Write-Host $_ }
Write-Host "`nTotal: $($results.Count) dashboards processed"
