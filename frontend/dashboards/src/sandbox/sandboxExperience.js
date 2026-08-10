const DEMO_SCHOOL_ID = import.meta.env.VITE_DEMO_SCHOOL_ID || "19801b59-8c05-4c84-9312-5d792e4e839d";

export const SANDBOX_MODE_FLAG = Boolean(
  import.meta.env.VITE_DEMO_MODE === "sandbox" || import.meta.env.VITE_SANDBOX_MODE === "1"
);

export const SANDBOX_TRACKS = [
  {
    key: "school",
    label: "School Demo",
    headline: "Run Heritage Christian Academy from leadership to classroom to family.",
    summary:
      "Explore admissions, attendance, academics, finance, communications, and family access in one connected Heritage Christian Academy operating model.",
    recommendedMode: "guided",
    primarySchoolKey: "heritage-core",
  },
];

export const SANDBOX_SCHOOL_ARCHETYPES = [
  {
    id: DEMO_SCHOOL_ID,
    key: "heritage-core",
    track: "school",
    name: "Heritage Christian Academy",
    archetype: "Christian School Demonstration Environment",
    bestFor: "full-system school operations, family communication, attendance, academics, and finance",
    enrollment: 420,
    tour: "core-operations",
    demo_data_only: true,
  },
];

export const SANDBOX_PERSONAS = [
  {
    value: "school_admin",
    label: "School Administrator",
    loginLabel: "School Admin",
    trackKeys: ["school"],
    route: "/school-admin-dashboard",
    email: "admin@heritage.example.org",
    defaultSchoolId: DEMO_SCHOOL_ID,
    promise: "Resolve representative school operations across enrollment, attendance, academics, finance, and communications.",
    tourTitle: "Daily operating picture",
    steps: [
      { label: "Review the leadership operating picture.", route: "/school-admin-dashboard" },
      { label: "Open student and enrollment records and verify roster context.", route: "/registrar-dashboard" },
      { label: "Review an attendance exception and the underlying attendance workflow.", route: "/attendance-dashboard" },
      { label: "Review academic and grading context for school leadership.", route: "/gradebook-dashboard" },
      { label: "Review finance risk without bypassing finance controls.", route: "/finance" },
      { label: "Review or initiate an operational communication.", route: "/communications-dashboard" },
    ],
  },
  {
    value: "admissions_director",
    label: "Admissions Director",
    loginLabel: "Admissions Director",
    trackKeys: ["school"],
    route: "/admissions-dashboard",
    email: "admissions@heritage.example.org",
    defaultSchoolId: DEMO_SCHOOL_ID,
    promise: "Move a real fictional inquiry through applicant review, decision, and enrollment conversion.",
    tourTitle: "Inquiry-to-enrollment proof path",
    steps: [
      { label: "Review the admissions operating picture.", route: "/admissions-dashboard" },
      { label: "Open the live applicant pipeline.", route: "/admissions/pipeline" },
      { label: "Open or create an applicant and complete the application workflow.", route: "/admissions/apply" },
      { label: "Review checklist and document status.", route: "/admissions/checklist" },
      { label: "Complete the accepted-to-enrolled conversion using the enrollment workflow.", route: "/reenrollment" },
    ],
  },
  {
    value: "finance_director",
    label: "Finance Director",
    loginLabel: "Finance Director",
    trackKeys: ["school"],
    route: "/finance",
    email: "finance@heritage.example.org",
    defaultSchoolId: DEMO_SCHOOL_ID,
    promise: "Work a family account from tuition balance through exception and reconciliation follow-up.",
    tourTitle: "Receivables and payment-risk review",
    steps: [
      { label: "Review the live finance operating picture.", route: "/finance" },
      { label: "Open family invoices and authoritative balances.", route: "/finance/invoices" },
      { label: "Inspect a family account and payment/allocation history.", route: "/finance/family-account" },
      { label: "Work an exception or payment-risk item.", route: "/finance/exceptions" },
      { label: "Review bank or payout reconciliation context.", route: "/finance/bank-reconciliation" },
    ],
  },
  {
    value: "teacher",
    label: "Teacher / Staff",
    loginLabel: "Teacher",
    trackKeys: ["school"],
    route: "/teacher",
    email: "teacher.lower@heritage.example.org",
    defaultSchoolId: DEMO_SCHOOL_ID,
    promise: "Take attendance, build instruction, connect curriculum, create class work, and grade authorized students.",
    tourTitle: "Staff daily workflow",
    steps: [
      { label: "Open assigned classes and roster context.", route: "/teacher/classes" },
      { label: "Take attendance for an assigned class.", route: "/teacher/attendance" },
      { label: "Create or edit today's lesson plan.", route: "/teacher/lesson-plans/today" },
      { label: "Open curriculum and connect an instructional resource.", route: "/teacher/curriculum" },
      { label: "Review assignments and daily instructional work.", route: "/teacher/daily-cockpit" },
      { label: "Enter or update grades for authorized students.", route: "/academics/teacher-grading" },
      { label: "Confirm the resulting grade/progress context in the gradebook.", route: "/gradebook" },
    ],
  },
  {
    value: "parent",
    label: "Parent / Guardian",
    loginLabel: "Parent",
    trackKeys: ["school"],
    route: "/parent",
    email: "parent.reed@heritage.example.org",
    defaultSchoolId: DEMO_SCHOOL_ID,
    promise: "Complete application and enrollment work, then manage the family's day-to-day school experience.",
    tourTitle: "Family experience proof path",
    steps: [
      { label: "Start or resume a family application.", route: "/parent/admissions/start" },
      { label: "Complete the applicant workflow and submit required information.", route: "/admissions/apply" },
      { label: "Review application status and next required action.", route: "/parent/admissions/status" },
      { label: "Complete the enrollment or re-enrollment workflow for an accepted student.", route: "/reenrollment" },
      { label: "Return to the family dashboard and verify the resulting student context.", route: "/parent" },
      { label: "Review attendance, learning status, and family billing context.", route: "/parent/learning-status" },
      { label: "Review the family account and billing stage.", route: "/parent/billing" },
    ],
  },
  {
    value: "student",
    label: "Student",
    loginLabel: "Student",
    trackKeys: ["school"],
    route: "/student",
    email: "student.avery.reed11@heritage.example.org",
    defaultSchoolId: DEMO_SCHOOL_ID,
    promise: "Use the learner workspace for schedule, assignments, progress, and school communication without administrative access.",
    tourTitle: "Learner self-service proof path",
    steps: [
      { label: "Open the learner dashboard.", route: "/student" },
      { label: "Review today's schedule, classes, and next actions.", route: "/student/today" },
      { label: "Open assignments and learning tasks.", route: "/student/assignments" },
      { label: "Review submitted work and progress context.", route: "/academics/student-work" },
      { label: "Review communications and school next actions.", route: "/communications-dashboard" },
      { label: "Confirm administrative, finance, admissions, and grading controls are unavailable.", route: "/student" },
    ],
  },
];

export function getSandboxTrack(key) {
  return SANDBOX_TRACKS.find((track) => track.key === key) || SANDBOX_TRACKS[0];
}

export function getSandboxPersona(value) {
  return SANDBOX_PERSONAS.find((persona) => persona.value === value) || SANDBOX_PERSONAS[0];
}

export function getSandboxSchool(idOrKey) {
  return (
    SANDBOX_SCHOOL_ARCHETYPES.find((school) => school.id === idOrKey || school.key === idOrKey) ||
    SANDBOX_SCHOOL_ARCHETYPES[0]
  );
}

export function getTrackSchools(trackKey) {
  return SANDBOX_SCHOOL_ARCHETYPES.filter((school) => school.track === trackKey);
}

export function getTrackPersonas(trackKey) {
  return SANDBOX_PERSONAS.filter((persona) => persona.trackKeys.includes(trackKey));
}

export function getSandboxLoginHref(
  personaValue,
  trackKeyOrLegacySchool = "school",
  modeOrLegacyTrack = "guided",
  legacyMode
) {
  const persona = getSandboxPersona(personaValue);
  const trackKey = legacyMode === undefined ? trackKeyOrLegacySchool : modeOrLegacyTrack;
  const mode = legacyMode === undefined ? modeOrLegacyTrack : legacyMode;
  const track = getSandboxTrack(trackKey);
  const heritage = SANDBOX_SCHOOL_ARCHETYPES[0];
  const params = new URLSearchParams({
    mode: "sandbox",
    experience: track.key,
    guidance: mode,
    role: persona.value,
    school: heritage.id,
    tour: persona.tourTitle,
  });
  return `/sandbox/command-center?${params.toString()}`;
}
