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
    trackKeys: ["school"],
    route: "/admissions-dashboard",
    email: "admissions@heritage.example.org",
    defaultSchoolId: DEMO_SCHOOL_ID,
    promise: "Walk an inquiry from first contact through accepted and enrolled status.",
    tourTitle: "Inquiry-to-enrollment proof path",
    steps: [
      "Open the admissions dashboard.",
      "Review inquiry volume by stage.",
      "Open an applicant record.",
      "Advance a qualified applicant.",
      "Confirm dashboard metrics update against the seeded Heritage scenario.",
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
    promise: "Review tuition, family balances, and payment-risk follow-up.",
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
    trackKeys: ["school"],
    route: "/teacher",
    email: "teacher.lower@heritage.example.org",
    defaultSchoolId: DEMO_SCHOOL_ID,
    promise: "Take attendance, view students, and move through daily workflows quickly.",
    tourTitle: "Staff daily workflow",
    steps: [
      "Open the staff dashboard.",
      "Take attendance.",
      "Review class or roster context.",
      "Open student support details.",
      "Validate that staff access is permission-scoped.",
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
    promise: "See progress, school communication, and family account information.",
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
    label: "Student",
    loginLabel: "Student",
    trackKeys: ["school"],
    route: "/student",
    email: "student.avery.reed11@heritage.example.org",
    defaultSchoolId: DEMO_SCHOOL_ID,
    promise: "View schedule, assignments, activities, and progress from a learner perspective.",
    tourTitle: "Learner self-service proof path",
    steps: [
      "Open the learner dashboard.",
      "Review schedule and assignments.",
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
