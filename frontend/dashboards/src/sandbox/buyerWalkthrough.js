export const BUYER_WALKTHROUGH = {
  entryRoute: "/sandbox",
  passwordless: true,
  school: "Heritage Christian Academy",
  designAuthority: [
    "styles/crown-theme.css",
    "styles/launch-shell.css",
    "styles/client-experience.css",
    "components/crown-dashboard/CrownDashboardTemplate.jsx",
  ],
  journeys: [
    {
      persona: "school_admin",
      label: "School Administrator",
      purpose: "Run the school from leadership overview through student, academic, financial, and communication workflows.",
      proofPoints: ["Leadership KPIs", "Operational queues", "Student records", "Attendance", "Academics", "Finance", "Communications"],
      routes: [
        "/school-admin-dashboard",
        "/registrar-dashboard",
        "/attendance",
        "/gradebook",
        "/finance",
        "/communications-dashboard",
      ],
    },
    {
      persona: "admissions_director",
      label: "Admissions Director",
      purpose: "Move a fictional family through inquiry, application, checklist, decision, and enrollment conversion.",
      proofPoints: ["Pipeline KPIs", "Applicant workflow", "Checklist status", "Enrollment conversion"],
      routes: [
        "/admissions-dashboard",
        "/admissions/pipeline",
        "/admissions/apply",
        "/admissions/checklist",
        "/enrollment-conversion",
      ],
    },
    {
      persona: "finance_director",
      label: "Finance Director",
      purpose: "Trace a family account through invoices, exceptions, reconciliation, and accounting controls.",
      proofPoints: ["Finance KPIs", "Family balances", "Exceptions", "Reconciliation", "Audit trail"],
      routes: [
        "/finance",
        "/finance/invoices",
        "/finance/family-account",
        "/finance/exceptions",
        "/finance/bank-reconciliation",
      ],
    },
    {
      persona: "teacher",
      label: "Teacher / Staff",
      purpose: "Demonstrate the daily instructional workflow instead of stopping at the teacher dashboard.",
      proofPoints: ["Assigned classes", "Attendance", "Lesson plans", "Curriculum", "Assignments", "Grading"],
      routes: [
        "/teacher",
        "/teacher/classes",
        "/teacher/attendance",
        "/teacher/lesson-plans/today",
        "/teacher/daily-cockpit",
        "/academics/teacher-grading",
        "/gradebook",
      ],
    },
    {
      persona: "parent",
      label: "Parent / Guardian",
      purpose: "Show the complete family lifecycle from application through everyday school participation.",
      proofPoints: ["Application", "Admissions status", "Enrollment handoff", "Learning status", "Attendance", "Billing"],
      routes: [
        "/parent/admissions/start",
        "/admissions/apply",
        "/parent/admissions/status",
        "/parent",
        "/parent/learning-status",
        "/parent/attendance",
        "/parent/billing",
      ],
    },
    {
      persona: "student",
      label: "Student",
      purpose: "Show learner self-service while preserving administrative and financial boundaries.",
      proofPoints: ["Daily schedule", "Assignments", "Student work", "Progress", "Role boundaries"],
      routes: [
        "/student",
        "/student/today",
        "/student/assignments",
        "/academics/student-work",
      ],
    },
  ],
};

export function getBuyerJourney(persona) {
  return BUYER_WALKTHROUGH.journeys.find((journey) => journey.persona === persona) || null;
}
