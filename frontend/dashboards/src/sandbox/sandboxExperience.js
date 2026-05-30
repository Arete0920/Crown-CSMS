const DEMO_SCHOOL_ID = import.meta.env.VITE_DEMO_SCHOOL_ID || "19801b59-8c05-4c84-9312-5d792e4e839d";
const DEMO_PASSWORD = import.meta.env.VITE_DEMO_PASS || "CrownDemo!2026";

export const SANDBOX_MODE_FLAG = Boolean(
  import.meta.env.VITE_DEMO_MODE === "sandbox" || import.meta.env.VITE_SANDBOX_MODE === "1"
);

export const SANDBOX_TRACKS = [
  {
    key: "school",
    label: "School Demo",
    headline: "Run a Christian school day from leadership to classroom to family.",
    summary:
      "Best for K-12 evaluators who want to see admissions, attendance, academics, finance, communications, and family access in one connected operating model.",
    recommendedMode: "guided",
    primarySchoolKey: "heritage-core",
  },
  {
    key: "daycare",
    label: "Daycare / Early Learning Demo",
    headline: "Show parent trust, daily care operations, attendance, billing, and communication.",
    summary:
      "Best for early learning centers, preschool programs, church daycares, and mixed PK-5 schools that need fast daily workflows and clear family communication.",
    recommendedMode: "guided",
    primarySchoolKey: "emmanuel-early-learning",
  },
  {
    key: "camp",
    label: "Camp / Summer Program Demo",
    headline: "Manage seasonal registration, rosters, payments, safety, attendance, and family updates.",
    summary:
      "Best for summer camps, enrichment weeks, VBS-style programs, athletics camps, arts camps, and school-run seasonal programs.",
    recommendedMode: "self-guided-after-intro",
    primarySchoolKey: "cedar-summer-camp",
  },
];

export const SANDBOX_SCHOOL_ARCHETYPES = [
  {
    id: DEMO_SCHOOL_ID,
    key: "heritage-core",
    track: "school",
    name: "Heritage Christian Academy",
    archetype: "Small K-8 Christian School",
    bestFor: "daily operations, family communication, attendance, and role context",
    enrollment: 420,
    tour: "core-operations",
  },
  {
    id: "sandbox-school-trinity-classical-school",
    key: "trinity-k12",
    track: "school",
    name: "Trinity Classical School",
    archetype: "Growing K-12 Academy",
    bestFor: "multi-division leadership, academics, and stakeholder visibility",
    enrollment: 520,
    tour: "head-of-school",
  },
  {
    id: "sandbox-school-bethlehem-stem-academy",
    key: "bethlehem-admissions",
    track: "school",
    name: "Bethlehem STEM Academy",
    archetype: "High-volume Admissions School",
    bestFor: "inquiry triage, admissions pipeline pressure, and conversion workflow",
    enrollment: 740,
    tour: "admissions",
  },
  {
    id: "sandbox-school-grace-covenant-school",
    key: "grace-finance",
    track: "school",
    name: "Grace Covenant School",
    archetype: "Tuition-sensitive School",
    bestFor: "family balances, tuition risk, finance review, and payment communication",
    enrollment: 390,
    tour: "finance",
  },
  {
    id: "sandbox-school-good-shepherd-online-hybrid",
    key: "good-shepherd-hybrid",
    track: "school",
    name: "Good Shepherd Online Hybrid",
    archetype: "Hybrid / Online School",
    bestFor: "remote workflows, communications, and student self-service",
    enrollment: 880,
    tour: "hybrid",
  },
  {
    id: "sandbox-school-emmanuel-early-learning",
    key: "emmanuel-early-learning",
    track: "daycare",
    name: "Emmanuel Early Learning Center",
    archetype: "Church-based Daycare and Preschool",
    bestFor: "daily check-in/out, parent updates, billing, allergy notes, and early learning communication",
    enrollment: 168,
    tour: "daycare-daily-care",
  },
  {
    id: "sandbox-school-cedar-summer-camp",
    key: "cedar-summer-camp",
    track: "camp",
    name: "Cedar Ridge Summer Camp",
    archetype: "Seasonal Camp / Summer Program",
    bestFor: "session registration, rosters, payments, attendance, safety notes, and family updates",
    enrollment: 260,
    tour: "camp-session-operations",
  },
];

export const SANDBOX_PERSONAS = [
  {
    value: "school_admin",
    label: "Head of School",
    loginLabel: "School Admin",
    trackKeys: ["school", "daycare", "camp"],
    route: "/school-admin-dashboard",
    email: "admin@heritage.example.org",
    password: DEMO_PASSWORD,
    defaultSchoolId: DEMO_SCHOOL_ID,
    promise: "See enrollment, attendance, finance, and communication health in one operating picture.",
    tourTitle: "Daily operating picture",
    steps: [
      "Review the leadership dashboard.",
      "Check attendance and enrollment signals.",
      "Open finance risk indicators.",
      "Review communications activity.",
      "Switch to a family or teacher view to validate stakeholder context.",
    ],
  },
  {
    value: "admissions_director",
    label: "Admissions Director",
    loginLabel: "Admissions Director",
    trackKeys: ["school", "daycare", "camp"],
    route: "/admissions-dashboard",
    email: "admin@heritage.example.org",
    password: DEMO_PASSWORD,
    defaultSchoolId: "sandbox-school-bethlehem-stem-academy",
    promise: "Walk an inquiry or registration from first contact through accepted and enrolled status.",
    tourTitle: "Inquiry-to-enrollment proof path",
    steps: [
      "Open the admissions dashboard.",
      "Review inquiry or registration volume by stage.",
      "Open an applicant or camper record.",
      "Advance a qualified applicant.",
      "Confirm dashboard metrics update against the seeded scenario.",
    ],
  },
  {
    value: "finance_director",
    label: "Finance Director",
    loginLabel: "Finance Director",
    trackKeys: ["school", "daycare", "camp"],
    route: "/finance",
    email: "admin@heritage.example.org",
    password: DEMO_PASSWORD,
    defaultSchoolId: "sandbox-school-grace-covenant-school",
    promise: "Review tuition, program fees, family balances, and payment-risk follow-up.",
    tourTitle: "Receivables and payment-risk review",
    steps: [
      "Open the finance dashboard.",
      "Review open balances.",
      "Inspect family account detail.",
      "Review exception or reconciliation queues.",
      "Prepare a follow-up communication path.",
    ],
  },
  {
    value: "teacher",
    label: "Teacher / Staff",
    loginLabel: "Teacher",
    trackKeys: ["school", "daycare", "camp"],
    route: "/teacher",
    email: "teacher.lower@heritage.example.org",
    password: DEMO_PASSWORD,
    defaultSchoolId: DEMO_SCHOOL_ID,
    promise: "Take attendance, view students or campers, and move through daily workflows quickly.",
    tourTitle: "Staff daily workflow",
    steps: [
      "Open the staff dashboard.",
      "Take attendance or check participants in.",
      "Review class, group, or roster context.",
      "Open student/camper support details.",
      "Validate that staff access is permission-scoped.",
    ],
  },
  {
    value: "parent",
    label: "Parent / Guardian",
    loginLabel: "Parent",
    trackKeys: ["school", "daycare", "camp"],
    route: "/parent",
    email: "parent.reed@heritage.example.org",
    password: DEMO_PASSWORD,
    defaultSchoolId: DEMO_SCHOOL_ID,
    promise: "See progress, school or program communication, and family account information.",
    tourTitle: "Family experience proof path",
    steps: [
      "Open the parent dashboard.",
      "Review child snapshot.",
      "Check attendance and communications.",
      "Review billing or statement context.",
      "Confirm the experience is clear for non-technical families.",
    ],
  },
  {
    value: "student",
    label: "Student / Camper",
    loginLabel: "Student/Learner",
    trackKeys: ["school", "camp"],
    route: "/student",
    email: "student.avery.reed11@heritage.example.org",
    password: DEMO_PASSWORD,
    defaultSchoolId: DEMO_SCHOOL_ID,
    promise: "View schedule, assignments, activities, and progress from a learner perspective.",
    tourTitle: "Learner self-service proof path",
    steps: [
      "Open the learner dashboard.",
      "Review schedule and assignments or activities.",
      "Inspect progress context.",
      "Check communications or next actions.",
      "Confirm no administrative functions are visible.",
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

export function getSandboxLoginHref(personaValue, schoolId, trackKey = "school", mode = "guided") {
  const persona = getSandboxPersona(personaValue);
  const track = getSandboxTrack(trackKey);
  const fallbackSchool = getSandboxSchool(track.primarySchoolKey);
  const targetSchoolId = schoolId || persona.defaultSchoolId || fallbackSchool.id;
  const params = new URLSearchParams({
    mode: "sandbox",
    experience: track.key,
    guidance: mode,
    role: persona.value,
    school: targetSchoolId,
    tour: persona.tourTitle,
  });
  return `/sandbox/command-center?${params.toString()}`;
}
