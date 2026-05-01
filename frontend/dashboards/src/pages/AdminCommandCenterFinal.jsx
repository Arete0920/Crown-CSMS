import { useEffect, useState } from "react";
import "../styles/admin-command-center-final.css";

const sandboxSchoolDemoData = {
  heritage: {
    schoolName: "Heritage Christian Academy",
    established: "Est. 1998",
    schoolYear: "2025-2026",
    adminName: "David Anderson",
    adminRole: "School Administrator",
    adminInitials: "DA",
    funnelLevels: [
      ["Inquiries", "128", "cc-blue"],
      ["Applications", "96", "cc-blue-soft"],
      ["Interviews", "64", "cc-purple"],
      ["Offers", "48", "cc-gold"],
      ["Enrolled", "32", "cc-blue-deep"],
    ],
    attendance: { percent: "99.4%", present: "492", absent: "14", tardy: "6" },
    finance: { income: "$128,540", expenses: "$89,230", net: "$39,310" },
    kpis: [
      { label: "Total Students", value: "912", detail: "5 new this month", icon: "students", tone: "blue" },
      { label: "Admissions", value: "418", detail: "9 this month", icon: "admissions", tone: "microsoft" },
      { label: "Attendance Today", value: "99.4%", detail: "Above target", icon: "attendance", tone: "success" },
      { label: "Open Invoices", value: "19", detail: "$38,580 outstanding", icon: "invoice", tone: "warning" },
      { label: "Teacher Attendance", value: "91.1%", detail: "9 Approaching", icon: "teacher", tone: "mission" },
      { label: "Monthly Revenue", value: "$128,940", detail: "8.4% over last month", icon: "revenue", tone: "success" },
    ],
    todayAtGlanceMetrics: [
      { label: "Students", value: "912", sourceId: "student-demographics" },
      { label: "Attendance", value: "99.4%", sourceId: "attendance-overview" },
      { label: "Admissions", value: "418", sourceId: "admissions-overview" },
      { label: "Tuition", value: "$128,940", sourceId: "tuition-overview" },
      { label: "Messages / Alerts", value: "9 open", sourceId: "messages-alerts" },
      { label: "Mission Score", value: "94", sourceId: "mission-pulse" },
    ],
    demoSegments: [
      { label: "Elementary K-5", value: 156, color: "#3B82F6" },
      { label: "Middle 6-8", value: 128, color: "#A78BFA" },
      { label: "High 9-12", value: 168, color: "#1D4ED8" },
      { label: "Pre-K", value: 60, color: "#FBBF24" },
    ],
    gradeGroups: [
      { label: "A", value: 142, color: "#3B82F6" },
      { label: "B", value: 198, color: "#A78BFA" },
      { label: "C", value: 87, color: "#D97706" },
      { label: "D/F", value: 23, color: "#DC2626" },
    ],
    overviewCards: [
      {
        id: "academics-overview",
        title: "Academics Overview",
        rows: [["Assignments due today", "24"], ["Grades needing review", "18"], ["Missing assignments", "7"], ["Upcoming tests", "12"]],
        action: "Go to gradebook",
      },
      {
        id: "student-demographics-rows",
        title: "Student Demographics",
        rows: [["Elementary K-5", "156"], ["Middle School 6-8", "128"], ["High School 9-12", "168"], ["Pre-K", "60"]],
        action: "View demographic report",
      },
      {
        id: "grade-distribution-rows",
        title: "Grade Distribution",
        rows: [["A (90-100)", "142"], ["B (80-89)", "198"], ["C (70-79)", "87"], ["D / F (below 70)", "23"]],
        action: "View gradebook",
      },
      {
        id: "staff-overview",
        title: "Staff Overview",
        rows: [["Certified Teachers", "42"], ["Support Staff", "18"], ["Administrators", "6"], ["Substitutes active", "3"]],
        action: "View staff directory",
      },
    ],
    schoolYearProgressRows: [["Completed", "136/200"], ["Remaining", "64 days"]],
    dailyScheduleRows: [["8:00 AM", "Faculty Devotion"], ["9:00 AM", "Chapel Service"], ["1:00 PM", "3rd Grade Field Trip"]],
    topAttendanceRows: [["K", "97.8%"], ["1", "97.2%"], ["2", "96.8%"], ["9", "93.2%"]],
    rightRail: [
      {
        id: "mission-pulse",
        title: "Daily Prayer & Devotion",
        hasPhoto: true,
        photoLabel: "Morning devotion",
        items: [
          "Be strong and courageous.",
          "Do not be afraid; the Lord your God will be with you.",
          "- Joshua 1:9",
        ],
        action: "Read devotion",
        tone: "mission",
      },
      {
        id: "today-devotion",
        title: "Today's Devotion",
        hasPhoto: true,
        photoLabel: "Open Bible",
        items: ["Walking by Faith, Not by Sight", "Reflect on 2 Corinthians 5:7"],
        action: "Read more",
        tone: "mission",
      },
      {
        id: "announcements",
        title: "Announcements",
        items: ["Spring Carnival is this Saturday", "Chapel guest speaker next week", "Yearbook orders due May 1"],
        action: "View all",
        tone: "microsoft",
      },
      {
        id: "counsel-segment",
        title: "Counsel Segment",
        isGrid: true,
        gridRows: [["Student", "Proxy", "Score"], ["A. James", "Parent", "92"], ["B. Smith", "Counselor", "87"], ["C. Brown", "Teacher", "78"]],
        action: "View all",
        tone: "microsoft",
      },
      {
        id: "family-focus",
        title: "Family Focus",
        items: ["3 families awaiting follow-up", "1 new inquiry this morning", "2 re-enrollment meetings today"],
        action: "View families",
        tone: "mission",
      },
      {
        id: "messages-alerts",
        title: "Today Due",
        items: ["Submit payroll approvals", "Review 3 pending invoices", "Respond to board email", "Sign field trip forms"],
        action: "View all tasks",
        tone: "operation",
      },
      {
        id: "system-status",
        title: "System Status",
        items: ["All systems operational", "Last checked: 7:45 AM"],
        action: "View status",
        tone: "operation",
      },
    ],
  },
  covenant: {
    schoolName: "Covenant Preparatory School",
    established: "Est. 2004",
    schoolYear: "2025-2026",
    adminName: "Rachel Cole",
    adminRole: "School Administrator",
    adminInitials: "RC",
    funnelLevels: [
      ["Inquiries", "119", "cc-blue"],
      ["Applications", "88", "cc-blue-soft"],
      ["Interviews", "63", "cc-purple"],
      ["Offers", "41", "cc-gold"],
      ["Enrolled", "27", "cc-blue-deep"],
    ],
    attendance: { percent: "98.9%", present: "468", absent: "18", tardy: "7" },
    finance: { income: "$121,480", expenses: "$85,920", net: "$35,560" },
    kpis: [
      { label: "Total Students", value: "864", detail: "6 new this month", icon: "students", tone: "blue" },
      { label: "Admissions", value: "389", detail: "11 this month", icon: "admissions", tone: "microsoft" },
      { label: "Attendance Today", value: "98.9%", detail: "On target", icon: "attendance", tone: "success" },
      { label: "Open Invoices", value: "22", detail: "$34,220 outstanding", icon: "invoice", tone: "warning" },
      { label: "Teacher Attendance", value: "92.6%", detail: "7 Approaching", icon: "teacher", tone: "mission" },
      { label: "Monthly Revenue", value: "$121,480", detail: "6.1% over last month", icon: "revenue", tone: "success" },
    ],
    todayAtGlanceMetrics: [
      { label: "Students", value: "864", sourceId: "student-demographics" },
      { label: "Attendance", value: "98.9%", sourceId: "attendance-overview" },
      { label: "Admissions", value: "389", sourceId: "admissions-overview" },
      { label: "Tuition", value: "$121,480", sourceId: "tuition-overview" },
      { label: "Messages / Alerts", value: "11 open", sourceId: "messages-alerts" },
      { label: "Mission Score", value: "92", sourceId: "mission-pulse" },
    ],
    demoSegments: [
      { label: "Elementary K-5", value: 148, color: "#3B82F6" },
      { label: "Middle 6-8", value: 132, color: "#A78BFA" },
      { label: "High 9-12", value: 154, color: "#1D4ED8" },
      { label: "Pre-K", value: 54, color: "#FBBF24" },
    ],
    gradeGroups: [
      { label: "A", value: 134, color: "#3B82F6" },
      { label: "B", value: 184, color: "#A78BFA" },
      { label: "C", value: 96, color: "#D97706" },
      { label: "D/F", value: 20, color: "#DC2626" },
    ],
    overviewCards: [
      {
        id: "academics-overview",
        title: "Academics Overview",
        rows: [["Assignments due today", "20"], ["Grades needing review", "14"], ["Missing assignments", "9"], ["Upcoming tests", "10"]],
        action: "Go to gradebook",
      },
      {
        id: "student-demographics-rows",
        title: "Student Demographics",
        rows: [["Elementary K-5", "148"], ["Middle School 6-8", "132"], ["High School 9-12", "154"], ["Pre-K", "54"]],
        action: "View demographic report",
      },
      {
        id: "grade-distribution-rows",
        title: "Grade Distribution",
        rows: [["A (90-100)", "134"], ["B (80-89)", "184"], ["C (70-79)", "96"], ["D / F (below 70)", "20"]],
        action: "View gradebook",
      },
      {
        id: "staff-overview",
        title: "Staff Overview",
        rows: [["Certified Teachers", "39"], ["Support Staff", "16"], ["Administrators", "5"], ["Substitutes active", "4"]],
        action: "View staff directory",
      },
    ],
    schoolYearProgressRows: [["Completed", "134/200"], ["Remaining", "66 days"]],
    dailyScheduleRows: [["7:45 AM", "Staff Prayer Huddle"], ["9:20 AM", "MS Robotics Lab"], ["2:15 PM", "Parent Meeting"]],
    topAttendanceRows: [["K", "97.4%"], ["3", "96.9%"], ["7", "95.8%"], ["10", "94.6%"]],
    rightRail: [
      {
        id: "mission-pulse",
        title: "Daily Prayer & Devotion",
        hasPhoto: true,
        photoLabel: "Morning devotion",
        items: ["Commit your way to the Lord.", "Trust in Him and He will act.", "- Psalm 37:5"],
        action: "Read devotion",
        tone: "mission",
      },
      {
        id: "today-devotion",
        title: "Today's Devotion",
        hasPhoto: true,
        photoLabel: "Open Bible",
        items: ["Standing Firm in Hope", "Reflect on Romans 15:13"],
        action: "Read more",
        tone: "mission",
      },
      {
        id: "announcements",
        title: "Announcements",
        items: ["Parent prayer breakfast Friday", "MS robotics showcase next week", "Uniform order deadline May 3"],
        action: "View all",
        tone: "microsoft",
      },
      {
        id: "counsel-segment",
        title: "Counsel Segment",
        isGrid: true,
        gridRows: [["Student", "Proxy", "Score"], ["L. Moss", "Parent", "90"], ["J. Grant", "Counselor", "84"], ["S. Yang", "Teacher", "79"]],
        action: "View all",
        tone: "microsoft",
      },
      {
        id: "family-focus",
        title: "Family Focus",
        items: ["4 families awaiting follow-up", "2 new inquiries this morning", "1 re-enrollment meeting today"],
        action: "View families",
        tone: "mission",
      },
      {
        id: "messages-alerts",
        title: "Today Due",
        items: ["Finalize transport roster", "Review 2 pending invoices", "Reply to PTA email", "Approve grade-level memo"],
        action: "View all tasks",
        tone: "operation",
      },
      {
        id: "system-status",
        title: "System Status",
        items: ["All systems operational", "Last checked: 7:40 AM"],
        action: "View status",
        tone: "operation",
      },
    ],
  },
  grace: {
    schoolName: "Grace Fellowship Academy",
    established: "Est. 2011",
    schoolYear: "2025-2026",
    adminName: "Michael Torres",
    adminRole: "School Administrator",
    adminInitials: "MT",
    funnelLevels: [
      ["Inquiries", "106", "cc-blue"],
      ["Applications", "82", "cc-blue-soft"],
      ["Interviews", "58", "cc-purple"],
      ["Offers", "39", "cc-gold"],
      ["Enrolled", "25", "cc-blue-deep"],
    ],
    attendance: { percent: "98.6%", present: "432", absent: "16", tardy: "5" },
    finance: { income: "$115,260", expenses: "$81,420", net: "$33,840" },
    kpis: [
      { label: "Total Students", value: "798", detail: "4 new this month", icon: "students", tone: "blue" },
      { label: "Admissions", value: "344", detail: "8 this month", icon: "admissions", tone: "microsoft" },
      { label: "Attendance Today", value: "98.6%", detail: "Near target", icon: "attendance", tone: "success" },
      { label: "Open Invoices", value: "17", detail: "$29,740 outstanding", icon: "invoice", tone: "warning" },
      { label: "Teacher Attendance", value: "93.4%", detail: "5 Approaching", icon: "teacher", tone: "mission" },
      { label: "Monthly Revenue", value: "$115,260", detail: "7.2% over last month", icon: "revenue", tone: "success" },
    ],
    todayAtGlanceMetrics: [
      { label: "Students", value: "798", sourceId: "student-demographics" },
      { label: "Attendance", value: "98.6%", sourceId: "attendance-overview" },
      { label: "Admissions", value: "344", sourceId: "admissions-overview" },
      { label: "Tuition", value: "$115,260", sourceId: "tuition-overview" },
      { label: "Messages / Alerts", value: "7 open", sourceId: "messages-alerts" },
      { label: "Mission Score", value: "95", sourceId: "mission-pulse" },
    ],
    demoSegments: [
      { label: "Elementary K-5", value: 136, color: "#3B82F6" },
      { label: "Middle 6-8", value: 118, color: "#A78BFA" },
      { label: "High 9-12", value: 146, color: "#1D4ED8" },
      { label: "Pre-K", value: 48, color: "#FBBF24" },
    ],
    gradeGroups: [
      { label: "A", value: 126, color: "#3B82F6" },
      { label: "B", value: 173, color: "#A78BFA" },
      { label: "C", value: 89, color: "#D97706" },
      { label: "D/F", value: 14, color: "#DC2626" },
    ],
    overviewCards: [
      {
        id: "academics-overview",
        title: "Academics Overview",
        rows: [["Assignments due today", "18"], ["Grades needing review", "12"], ["Missing assignments", "6"], ["Upcoming tests", "11"]],
        action: "Go to gradebook",
      },
      {
        id: "student-demographics-rows",
        title: "Student Demographics",
        rows: [["Elementary K-5", "136"], ["Middle School 6-8", "118"], ["High School 9-12", "146"], ["Pre-K", "48"]],
        action: "View demographic report",
      },
      {
        id: "grade-distribution-rows",
        title: "Grade Distribution",
        rows: [["A (90-100)", "126"], ["B (80-89)", "173"], ["C (70-79)", "89"], ["D / F (below 70)", "14"]],
        action: "View gradebook",
      },
      {
        id: "staff-overview",
        title: "Staff Overview",
        rows: [["Certified Teachers", "36"], ["Support Staff", "14"], ["Administrators", "5"], ["Substitutes active", "2"]],
        action: "View staff directory",
      },
    ],
    schoolYearProgressRows: [["Completed", "132/200"], ["Remaining", "68 days"]],
    dailyScheduleRows: [["8:10 AM", "Morning Worship"], ["10:00 AM", "Student Support Review"], ["1:30 PM", "Elementary Chapel Prep"]],
    topAttendanceRows: [["1", "97.1%"], ["2", "96.7%"], ["6", "95.9%"], ["11", "94.8%"]],
    rightRail: [
      {
        id: "mission-pulse",
        title: "Daily Prayer & Devotion",
        hasPhoto: true,
        photoLabel: "Morning devotion",
        items: ["Let all that you do be done in love.", "Lead with grace and patience today.", "- 1 Corinthians 16:14"],
        action: "Read devotion",
        tone: "mission",
      },
      {
        id: "today-devotion",
        title: "Today's Devotion",
        hasPhoto: true,
        photoLabel: "Open Bible",
        items: ["Walking in Wisdom", "Reflect on James 1:5"],
        action: "Read more",
        tone: "mission",
      },
      {
        id: "announcements",
        title: "Announcements",
        items: ["Senior service day this Friday", "Teacher appreciation planning underway", "Library hours extended"],
        action: "View all",
        tone: "microsoft",
      },
      {
        id: "counsel-segment",
        title: "Counsel Segment",
        isGrid: true,
        gridRows: [["Student", "Proxy", "Score"], ["D. Cruz", "Parent", "93"], ["M. Hill", "Counselor", "88"], ["K. Patel", "Teacher", "81"]],
        action: "View all",
        tone: "microsoft",
      },
      {
        id: "family-focus",
        title: "Family Focus",
        items: ["2 families awaiting follow-up", "2 new inquiries this morning", "3 re-enrollment meetings today"],
        action: "View families",
        tone: "mission",
      },
      {
        id: "messages-alerts",
        title: "Today Due",
        items: ["Sign transport permissions", "Review 1 pending invoice", "Respond to board message", "Publish weekly bulletin"],
        action: "View all tasks",
        tone: "operation",
      },
      {
        id: "system-status",
        title: "System Status",
        items: ["All systems operational", "Last checked: 7:48 AM"],
        action: "View status",
        tone: "operation",
      },
    ],
  },
};

const sandboxSchoolIds = Object.keys(sandboxSchoolDemoData);

function getNextSchoolId(currentSchoolId) {
  const currentIndex = sandboxSchoolIds.indexOf(currentSchoolId);
  if (currentIndex < 0) return sandboxSchoolIds[0];
  return sandboxSchoolIds[(currentIndex + 1) % sandboxSchoolIds.length];
}

const navGroups = [
  { title: "Command Centre", items: ["Dashboard", "Overview"] },
  { title: "School Operations", items: ["Admissions", "Students", "Attendance", "Gradebook", "Academics"] },
  { title: "Offices & Finance", items: ["Finance", "Human Resources", "Boarding"] },
  { title: "Communications", items: ["Communications", "Database", "Administration", "Chaplain"] },
  { title: "Student Services", items: ["Family Pay", "Student Lending", "Fundraising"] },
];

const quickActions = [
  { label: "Add Inquiry", icon: "add", targetId: "admissions-overview" },
  { label: "Add Student", icon: "students", targetId: "student-demographics" },
  { label: "Take Attendance", icon: "attendance", targetId: "attendance-overview" },
  { label: "Create Invoice", icon: "invoice", targetId: "tuition-overview" },
  { label: "Send Message", icon: "message", targetId: "messages-alerts" },
  { label: "Add Event", icon: "calendar", targetId: "today-devotion" },
  { label: "Create Announcement", icon: "announcement", targetId: "announcements" },
  { label: "Run Report", icon: "report", targetId: "grade-distribution" },
  { label: "Upload Document", icon: "upload", targetId: "system-status" },
  { label: "More", icon: "more", targetId: "mission-pulse" },
];

const railItems = [
  { key: "dashboard", icon: "dashboard", targetId: "overview" },
  { key: "students", icon: "students", targetId: "student-demographics" },
  { key: "grid", icon: "grid", targetId: "grade-distribution" },
  { key: "finance", icon: "invoice", targetId: "tuition-overview" },
  { key: "reports", icon: "report", targetId: "academics-overview" },
  { key: "message", icon: "message", targetId: "messages-alerts" },
  { key: "check", icon: "attendance", targetId: "attendance-overview" },
  { key: "settings", icon: "settings", targetId: "system-status" },
];

const topbarIcons = [
  { icon: "message", badge: "3", label: "Messages", targetId: "messages-alerts" },
  { icon: "bell", badge: "6", label: "Notifications", targetId: "messages-alerts" },
  { icon: "task", label: "Tasks", targetId: "system-status" },
  { icon: "help", label: "Help", targetId: "today-devotion" },
];

const navTargetsByItem = {
  Dashboard: "overview",
  Overview: "overview",
  Admissions: "admissions-overview",
  Students: "student-demographics",
  Attendance: "attendance-overview",
  Gradebook: "grade-distribution",
  Academics: "academics-overview",
  Finance: "tuition-overview",
  "Human Resources": "staff-overview",
  Boarding: "family-focus",
  Communications: "messages-alerts",
  Database: "announcements",
  Administration: "system-status",
  Chaplain: "mission-pulse",
  "Family Pay": "tuition-overview",
  "Student Lending": "tuition-overview",
  Fundraising: "announcements",
};

function scrollToSection(sectionId) {
  const target = document.getElementById(sectionId);
  if (!target) return;

  const prefersReducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
  target.scrollIntoView({ behavior: prefersReducedMotion ? "auto" : "smooth", block: "start" });
  if (window?.history?.replaceState) {
    window.history.replaceState(null, "", `#${sectionId}`);
  }
}

function MiniIcon({ name, className = "" }) {
  const iconPaths = {
    add: "M12 5v14M5 12h14",
    dashboard: "M4 4h7v7H4zM13 4h7v4h-7zM13 10h7v10h-7zM4 13h7v7H4z",
    students: "M16 11c1.7 0 3-1.6 3-3.5S17.7 4 16 4s-3 1.6-3 3.5 1.3 3.5 3 3.5zM8 11c1.9 0 3.5-1.8 3.5-4S9.9 3 8 3 4.5 4.8 4.5 7 6.1 11 8 11zM8 13c-3 0-5.5 1.8-5.5 4v2h11v-2c0-2.2-2.5-4-5.5-4zM16 13c-.6 0-1.3.1-1.8.3 1.2.9 1.8 2.1 1.8 3.7v2h5v-2c0-2.2-2.2-4-5-4z",
    admissions: "M6 4h9l3 3v13H6zM15 4v3h3M9 12h6M9 16h6",
    attendance: "M5 12l4 4 10-10",
    invoice: "M6 4h12v16H6zM9 8h6M9 12h6M9 16h4",
    teacher: "M3 7l9-4 9 4-9 4-9-4zM6 10v5c0 1.8 2.7 3 6 3s6-1.2 6-3v-5",
    revenue: "M4 18h16M7 14v4M12 10v8M17 6v12",
    grid: "M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z",
    report: "M6 3h10l4 4v14H6zM16 3v4h4M9 12h8M9 16h8",
    message: "M4 6h16v10H8l-4 4z",
    calendar: "M7 3v3M17 3v3M4 8h16M5 6h14v14H5z",
    announcement: "M12 4L3 9l9 5 9-5-9-5zM8 12v4c0 1.2 1.8 2 4 2s4-.8 4-2v-4",
    upload: "M12 15V6M8.5 9.5 12 6l3.5 3.5M5 18h14",
    more: "M6 12h.01M12 12h.01M18 12h.01",
    settings: "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zm8 4-2 1 .1 2.2-2 1.1-1.3-1.8-2.1.5-1.1 2H9.4l-1.1-2-2.1-.5-1.3 1.8-2-1.1L3 13 1 12l2-1-.1-2.2 2-1.1 1.3 1.8 2.1-.5 1.1-2h2.2l1.1 2 2.1.5 1.3-1.8 2 1.1L18 11z",
    bell: "M12 4a5 5 0 0 1 5 5v3l1.5 2.5H5.5L7 12V9a5 5 0 0 1 5-5zm0 16a2.5 2.5 0 0 0 2.4-2h-4.8A2.5 2.5 0 0 0 12 20z",
    task: "M5 6h14M5 12h14M5 18h14M3 6h.01M3 12h.01M3 18h.01",
    help: "M12 19a1.2 1.2 0 1 0 0 .01M9.5 9a2.5 2.5 0 0 1 5 0c0 1.7-2.5 1.9-2.5 3.8",
  };

  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={iconPaths[name] || iconPaths.dashboard} />
    </svg>
  );
}


function KpiCard({ item }) {
  return (
    <article className={`cc-kpi cc-tone-${item.tone}`}>
      <div>
        <p>{item.label}</p>
        <strong>{item.value}</strong>
        <span>{item.detail}</span>
      </div>
      <div className="cc-kpi-icon" aria-hidden="true">
        <MiniIcon name={item.icon} className="cc-mini-icon" />
      </div>
    </article>
  );
}

function NavSidebar({ activeSection, isSidebarCollapsed, schoolData, onCycleSchool }) {
  return (
    <>
      <aside className="cc-icon-rail" aria-label="Quick module rail">
        <img src="/brand/crown-mark-transparent.svg" alt="" className="cc-icon-rail-mark" />
        {railItems.map((item) => (
          <button
            key={item.key}
            className={activeSection === item.targetId ? "active" : ""}
            type="button"
            aria-label={item.key}
            aria-current={activeSection === item.targetId ? "page" : undefined}
            onClick={() => scrollToSection(item.targetId)}
          >
            <MiniIcon name={item.icon} className="cc-mini-icon" />
          </button>
        ))}
      </aside>

      <aside id="primary-crown-navigation" className="cc-nav" aria-label="Primary CROWN navigation" aria-hidden={isSidebarCollapsed}>
        <img
          src="/assets/crown-logo.svg"
          alt="CROWN Christian School Management Solution"
          className="cc-logo-img"
        />

        <button className="cc-school-switcher" type="button" onClick={onCycleSchool}>
          <span>{schoolData.schoolName}</span>
          <span>⌄</span>
        </button>

        <nav>
          {navGroups.map((group) => (
            <section key={group.title}>
              <h2>{group.title}</h2>
              {group.items.map((item) => (
                <a
                  key={item}
                  href={`#${navTargetsByItem[item] || "overview"}`}
                  className={activeSection === (navTargetsByItem[item] || "overview") ? "active" : ""}
                  aria-current={activeSection === (navTargetsByItem[item] || "overview") ? "page" : undefined}
                  onClick={(event) => {
                    event.preventDefault();
                    scrollToSection(navTargetsByItem[item] || "overview");
                  }}
                >
                  <span>{item}</span>
                  <span>›</span>
                </a>
              ))}
            </section>
          ))}
        </nav>

        <div className="cc-school-card">
          <img src="/brand/crown-mark-transparent.svg" alt="" />
          <div>
            <strong>{schoolData.schoolName}</strong>
            <span>{schoolData.established}</span>
          </div>
        </div>
      </aside>
    </>
  );
}

function Topbar({ onToggleSidebar, isSidebarCollapsed, schoolData }) {
  return (
    <header className="cc-topbar">
      <button
        className="cc-sidebar-toggle"
        type="button"
        onClick={onToggleSidebar}
        aria-label="Toggle sidebar"
        aria-expanded={!isSidebarCollapsed}
        aria-controls="primary-crown-navigation"
      >
        <MiniIcon name="grid" className="cc-mini-icon" />
      </button>

      <label className="cc-search">
        <span>⌕</span>
        <input placeholder="Search students, families, staff, invoices..." />
      </label>

      <button className="cc-primary-action" type="button" onClick={() => scrollToSection("quick-actions")}>+ Quick Add</button>

      <div className="cc-year">
        <span>School Year</span>
        <strong>{schoolData.schoolYear}</strong>
      </div>

      {topbarIcons.map((item) => (
        <button
          key={item.label}
          type="button"
          className="cc-top-icon"
          aria-label={item.label}
          onClick={() => scrollToSection(item.targetId)}
        >
          <MiniIcon name={item.icon} className="cc-mini-icon" />
          {item.badge ? <b>{item.badge}</b> : null}
        </button>
      ))}

      <button className="cc-user" type="button">
        <span className="cc-avatar">{schoolData.adminInitials}</span>
        <span>
          <strong>{schoolData.adminName}</strong>
          <small>{schoolData.adminRole}</small>
        </span>
        <span>⌄</span>
      </button>
    </header>
  );
}

function FunnelCard({ levels }) {

  return (
    <article id="admissions-overview" className="cc-card cc-card-operation cc-analytics-card">
      <h3>Enrollment Funnel <span>This Year</span></h3>
      <div className="cc-funnel-layout">
        <div className="cc-funnel">
          {levels.map((level, index) => (
            <div key={level[0]} className={`cc-funnel-level ${level[2]}`} style={{ width: `${100 - index * 14}%` }} />
          ))}
        </div>

        <div className="cc-legend">
          {levels.map(([label, value, color]) => (
            <div key={label}>
              <i className={color} />
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
      </div>
      <a
        href="#admissions-overview"
        onClick={(event) => {
          event.preventDefault();
          scrollToSection("admissions-overview");
        }}
      >
        View full enrollment report →
      </a>
    </article>
  );
}

function AttendanceCard({ attendance }) {
  return (
    <article id="attendance-overview" className="cc-card cc-card-operation cc-analytics-card">
      <h3>Attendance Overview</h3>
      <div className="cc-attendance-layout">
        <div className="cc-donut">
          <span>{attendance.percent}</span>
          <small>Today</small>
        </div>
        <div className="cc-legend">
          <div><i className="cc-green" /><span>Present</span><strong>{attendance.present}</strong></div>
          <div><i className="cc-red" /><span>Absent</span><strong>{attendance.absent}</strong></div>
          <div><i className="cc-warning" /><span>Tardy</span><strong>{attendance.tardy}</strong></div>
        </div>
      </div>
      <a
        href="#attendance-overview"
        onClick={(event) => {
          event.preventDefault();
          scrollToSection("attendance-overview");
        }}
      >
        View attendance dashboard →
      </a>
    </article>
  );
}

function FinanceCard({ finance }) {
  return (
    <article id="tuition-overview" className="cc-card cc-card-operation cc-analytics-card">
      <h3>Financial Overview <span>This Month</span></h3>
      <div className="cc-finance-summary">
        <div><span>Total Income</span><strong>{finance.income}</strong></div>
        <div><span>Total Expenses</span><strong>{finance.expenses}</strong></div>
        <div><span>Net Income</span><strong className="positive">{finance.net}</strong></div>
      </div>
      <div className="cc-bars" aria-label="Income and expense chart">
        {Array.from({ length: 26 }).map((_, index) => (
          <div key={index}>
            <i style={{ height: `${35 + ((index * 17) % 95)}px` }} />
            <b style={{ height: `${25 + ((index * 23) % 80)}px` }} />
          </div>
        ))}
      </div>
      <a
        href="#tuition-overview"
        onClick={(event) => {
          event.preventDefault();
          scrollToSection("tuition-overview");
        }}
      >
        View finance dashboard →
      </a>
    </article>
  );
}

function QuickActions() {
  return (
    <section id="quick-actions" className="cc-card cc-card-operation cc-quick-actions">
      <h3>Quick Actions</h3>
      <div>
        {quickActions.map((action) => (
          <button key={action.label} type="button" aria-label={action.label} onClick={() => scrollToSection(action.targetId)}>
            <span>
              <MiniIcon name={action.icon} className="cc-mini-icon" />
            </span>
            {action.label}
          </button>
        ))}
      </div>
    </section>
  );
}

function SmallCard({ card }) {
  return (
    <article id={card.id} className="cc-card cc-small-card">
      <h3>{card.title}</h3>
      {card.rows.map(([label, value]) => (
        <div key={label}>
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
      ))}
      <a
        href={`#${card.id}`}
        onClick={(event) => {
          event.preventDefault();
          scrollToSection(card.id);
        }}
      >
        {card.action} →
      </a>
    </article>
  );
}

function StudentDemographicsCard({ demoSegments }) {
  const total = demoSegments.reduce((s, d) => s + d.value, 0);
  const r = 46;
  const circ = 2 * Math.PI * r;
  const slices = demoSegments.reduce((acc, seg) => {
    const prev = acc.length ? acc[acc.length - 1] : { offset: 0, dash: 0 };
    const dash = (seg.value / total) * circ;
    const gap  = circ - dash;
    acc.push({ ...seg, dash, gap, offset: prev.offset + prev.dash });
    return acc;
  }, []);
  return (
    <article id="student-demographics" className="cc-card cc-small-card">
      <h3>Student Demographics</h3>
      <div className="cc-demo-layout">
        <svg viewBox="0 0 120 120" className="cc-demo-donut" aria-hidden="true">
          <circle cx="60" cy="60" r={r} fill="none" stroke="#f1f5f9" strokeWidth="18" />
          {slices.map((s) => (
            <circle
              key={s.label}
              cx="60" cy="60" r={r}
              fill="none"
              stroke={s.color}
              strokeWidth="18"
              strokeDasharray={`${s.dash} ${s.gap}`}
              strokeDashoffset={-s.offset}
              transform="rotate(-90 60 60)"
            />
          ))}
          <text x="60" y="56" textAnchor="middle" fontSize="14" fontWeight="700" fill="#0B2A5B">{total}</text>
          <text x="60" y="70" textAnchor="middle" fontSize="8" fill="#64748b">Students</text>
        </svg>
        <ul className="cc-demo-legend">
          {demoSegments.map((seg) => (
            <li key={seg.label}>
              <i style={{ background: seg.color }} />
              <span>{seg.label}</span>
              <strong>{seg.value}</strong>
            </li>
          ))}
        </ul>
      </div>
      <a
        href="#student-demographics"
        onClick={(event) => {
          event.preventDefault();
          scrollToSection("student-demographics");
        }}
      >
        View demographic report →
      </a>
    </article>
  );
}

function GradeDistributionCard({ gradeGroups }) {
  const maxVal = Math.max(...gradeGroups.map((g) => g.value));
  return (
    <article id="grade-distribution" className="cc-card cc-small-card">
      <h3>Grade Distribution</h3>
      <div className="cc-grade-bars" aria-label="Grade distribution bar chart">
        {gradeGroups.map((g) => (
          <div key={g.label} className="cc-grade-bar-row">
            <span className="cc-grade-bar-label">{g.label}</span>
            <div className="cc-grade-bar-track">
              <div
                className="cc-grade-bar-fill"
                style={{ width: `${(g.value / maxVal) * 100}%`, background: g.color }}
              />
            </div>
            <strong className="cc-grade-bar-val">{g.value}</strong>
          </div>
        ))}
      </div>
      <a
        href="#grade-distribution"
        onClick={(event) => {
          event.preventDefault();
          scrollToSection("grade-distribution");
        }}
      >
        View gradebook →
      </a>
    </article>
  );
}

function RightRail({ rightRail }) {
  return (
    <aside className="cc-right-rail" aria-label="Administrator context rail">
      {rightRail.map((section) => (
        <section key={section.title} id={section.id} className={`cc-rail-card cc-rail-${section.tone || "default"}`}>
          <h3>{section.title}</h3>
          {section.hasPhoto && (
            <div className="cc-rail-photo" role="img" aria-label={section.photoLabel} />
          )}
          {section.isGrid ? (
            <table className="cc-rail-grid">
              <thead>
                <tr>{section.gridRows[0].map((h) => <th key={h}>{h}</th>)}</tr>
              </thead>
              <tbody>
                {section.gridRows.slice(1).map((row) => (
                  <tr key={row[0]}>{row.map((cell) => <td key={cell}>{cell}</td>)}</tr>
                ))}
              </tbody>
            </table>
          ) : (
            <ul>
              {section.items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          )}
          <a
            href={`#${section.id}`}
            onClick={(event) => {
              event.preventDefault();
              scrollToSection(section.id);
            }}
          >
            {section.action} →
          </a>
        </section>
      ))}
    </aside>
  );
}

export default function AdminCommandCenterFinal() {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
    try {
      return window.localStorage.getItem("crown.final.sidebarCollapsed") === "1";
    } catch {
      // Ignore storage access errors in restricted browsing contexts.
      return false;
    }
  });
  const [activeSection, setActiveSection] = useState("overview");
  const [selectedSchoolId, setSelectedSchoolId] = useState("heritage");
  const schoolData = sandboxSchoolDemoData[selectedSchoolId] || sandboxSchoolDemoData.heritage;
  const kpis = schoolData.kpis;
  const todayAtGlanceMetrics = schoolData.todayAtGlanceMetrics;
  const overviewCards = schoolData.overviewCards;

  const handleCycleSchool = () => {
    setSelectedSchoolId((previous) => getNextSchoolId(previous));
  };

  useEffect(() => {
    const trackIds = Array.from(new Set([
      "overview",
      ...railItems.map((item) => item.targetId),
      ...todayAtGlanceMetrics.map((metric) => metric.sourceId),
      ...overviewCards.map((card) => card.id),
      "quick-actions",
      "school-year-progress",
      "daily-schedule",
      "top-attendance-by-grade",
    ]));

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
        if (visible.length > 0) {
          setActiveSection(visible[0].target.id);
        }
      },
      { rootMargin: "-30% 0px -55% 0px", threshold: [0.25, 0.5, 0.75] }
    );

    trackIds.forEach((id) => {
      const node = document.getElementById(id);
      if (node) observer.observe(node);
    });

    return () => observer.disconnect();
  }, [overviewCards, todayAtGlanceMetrics]);

  const handleToggleSidebar = () => {
    setIsSidebarCollapsed((previous) => {
      const next = !previous;
      try {
        window.localStorage.setItem("crown.final.sidebarCollapsed", next ? "1" : "0");
      } catch {
        // Ignore storage access errors in restricted browsing contexts.
      }
      return next;
    });
  };

  return (
    <div className={`cc-dashboard ${isSidebarCollapsed ? "cc-dashboard-collapsed" : ""}`}>
      <NavSidebar activeSection={activeSection} isSidebarCollapsed={isSidebarCollapsed} schoolData={schoolData} onCycleSchool={handleCycleSchool} />

      <div className="cc-shell">
        <Topbar onToggleSidebar={handleToggleSidebar} isSidebarCollapsed={isSidebarCollapsed} schoolData={schoolData} />

        <main className="cc-main">
          <section className="cc-content">
            <section id="overview" className="cc-hero">
              <div>
                <span className="cc-hero-kicker">School Administrator Dashboard</span>
                <h2>Good morning, {schoolData.adminName.split(" ")[0]}! ☀</h2>
                <p>{schoolData.schoolName} daily command center for sandbox operations.</p>
              </div>

              <section className="cc-snapshot-panel" aria-label="Today at a Glance">
                <h3>
                  Today at a Glance
                  <small>Fast executive scan (sandbox sample data)</small>
                </h3>

                <div className="cc-snapshot-grid">
                  {todayAtGlanceMetrics.map((metric) => (
                    <a
                      key={metric.label}
                      href={`#${metric.sourceId}`}
                      className="cc-snapshot-item"
                      onClick={(event) => {
                        event.preventDefault();
                        scrollToSection(metric.sourceId);
                      }}
                    >
                      <strong>{metric.value}</strong>
                      <span>{metric.label}</span>
                    </a>
                  ))}
                </div>
              </section>

              <img src="/brand/crown-mark-transparent.svg" alt="" />
            </section>

            <section className="cc-kpi-grid" aria-label="Executive KPI cards">
              {kpis.map((item) => (
                <KpiCard key={item.label} item={item} />
              ))}
            </section>

            <section className="cc-analytics-grid">
              <FunnelCard levels={schoolData.funnelLevels} />
              <AttendanceCard attendance={schoolData.attendance} />
              <FinanceCard finance={schoolData.finance} />
            </section>

            <QuickActions />

            <section className="cc-small-grid">
              <SmallCard key={overviewCards[0].title} card={overviewCards[0]} />
              <StudentDemographicsCard demoSegments={schoolData.demoSegments} />
              <GradeDistributionCard gradeGroups={schoolData.gradeGroups} />
              <SmallCard key={overviewCards[3].title} card={overviewCards[3]} />
            </section>

            <section className="cc-bottom-grid">
              <SmallCard card={{
                id: "school-year-progress",
                title: "School Year Progress",
                rows: schoolData.schoolYearProgressRows,
                action: "View academic calendar",
              }} />
              <SmallCard card={{
                id: "daily-schedule",
                title: "Today&apos;s Schedule",
                rows: schoolData.dailyScheduleRows,
                action: "View full calendar",
              }} />
              <SmallCard card={{
                id: "top-attendance-by-grade",
                title: "Top Attendance by Grade",
                rows: schoolData.topAttendanceRows,
                action: "View attendance by class",
              }} />
            </section>
          </section>

          <RightRail rightRail={schoolData.rightRail} />
        </main>
      </div>
    </div>
  );
}
