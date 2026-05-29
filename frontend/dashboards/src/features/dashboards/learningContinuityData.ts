import type { DashboardRoleKey } from "./dashboardTypes";

export type LearningTone = "royal" | "sky" | "emerald" | "amber" | "rose" | "violet" | "slate";

export interface ContinuityMetric {
  label: string;
  value: string;
  helper: string;
  tone: LearningTone;
}

export interface ContinuityAction {
  label: string;
  href: string;
  helper: string;
  tone: LearningTone;
}

export interface LearningContinuitySection {
  kicker: string;
  title: string;
  description: string;
  metrics: ContinuityMetric[];
  actions: ContinuityAction[];
}

export interface LearningContinuityPayload {
  modeBanner: {
    label: string;
    title: string;
    description: string;
    status: string;
    helper: string;
  };
  sections: LearningContinuitySection[];
}

const sharedModeBanner: LearningContinuityPayload["modeBanner"] = {
  label: "Learning continuity",
  title: "Microsoft-native classroom readiness",
  description:
    "CROWN coordinates school operations, classroom expectations, family communication, and mission-life visibility around Microsoft 365, Microsoft Education, and Teams.",
  status: "Configured",
  helper:
    "Current values are configured dashboard data until live Teams, assignment, attendance, and SIS integrations are connected.",
};

const adminContinuity: LearningContinuitySection = {
  kicker: "Online learning command",
  title: "Schoolwide remote / closure readiness",
  description:
    "Activate and monitor the school day when in-person learning is interrupted by weather, emergency, illness, staffing, or facilities issues.",
  metrics: [
    {
      label: "Class readiness",
      value: "91%",
      helper: "Classes with Teams link, lesson, attendance method, and assignment plan.",
      tone: "emerald",
    },
    {
      label: "Families notified",
      value: "88%",
      helper: "Families that opened the remote-learning notice.",
      tone: "amber",
    },
    {
      label: "Live class gaps",
      value: "4",
      helper: "Classes missing launch confirmation or teacher check-in.",
      tone: "rose",
    },
    {
      label: "Teams channels",
      value: "Active",
      helper: "Class, staff, leadership, and family-resource links are surfaced.",
      tone: "royal",
    },
  ],
  actions: [
    {
      label: "Open continuity command center",
      href: "/operations/online-learning-command",
      helper: "Review class readiness, family access, attendance, and communication delivery.",
      tone: "royal",
    },
    {
      label: "Send closure announcement",
      href: "/announcements/new?template=closure-mode",
      helper: "Publish schoolwide remote-learning instructions.",
      tone: "amber",
    },
    {
      label: "Review Teams launch gaps",
      href: "/integrations/teams/class-readiness",
      helper: "Find classes missing meeting links or live confirmation.",
      tone: "rose",
    },
  ],
};

const teacherCockpit: LearningContinuitySection = {
  kicker: "Teacher cockpit",
  title: "Today's classroom execution",
  description:
    "A teacher-first view for the next class, Teams launch, lesson plan, attendance, assignments, grading, parent messages, and student support.",
  metrics: [
    {
      label: "Next class",
      value: "10:05",
      helper: "English 8B - lesson, roster, attendance, and Teams link ready.",
      tone: "royal",
    },
    {
      label: "Attendance open",
      value: "1",
      helper: "One section still needs attendance submitted.",
      tone: "amber",
    },
    {
      label: "Ungraded work",
      value: "23",
      helper: "Assignments awaiting teacher feedback.",
      tone: "rose",
    },
    {
      label: "Parent replies",
      value: "3",
      helper: "Messages need response before end of school day.",
      tone: "emerald",
    },
  ],
  actions: [
    {
      label: "Start next Teams class",
      href: "/integrations/teams/classes/next",
      helper: "Open the linked class meeting/channel.",
      tone: "royal",
    },
    {
      label: "Open today's lesson plan",
      href: "/teacher/lesson-plans/today",
      helper: "Review curriculum map, lesson objective, files, and teaching notes.",
      tone: "sky",
    },
    {
      label: "Submit attendance",
      href: "/teacher/attendance/today",
      helper: "Post attendance for open sections.",
      tone: "amber",
    },
    {
      label: "Grade pending work",
      href: "/teacher/gradebook/pending",
      helper: "Open assignments awaiting feedback.",
      tone: "rose",
    },
  ],
};

const curriculumPlanning: LearningContinuitySection = {
  kicker: "Curriculum and lesson plans",
  title: "Publisher-aligned planning",
  description:
    "Prepare support for uploaded scope-and-sequence and lesson-plan materials from BJU Press, Abeka, Purposeful Design, and other approved publishers.",
  metrics: [
    {
      label: "Publisher maps",
      value: "3",
      helper: "BJU Press, Abeka, and Purposeful Design lanes prepared.",
      tone: "royal",
    },
    {
      label: "Editable plans",
      value: "Ready",
      helper: "Teacher customization should preserve publisher baseline and local changes.",
      tone: "emerald",
    },
    {
      label: "Pacing variance",
      value: "Planned",
      helper: "Compare planned lesson, taught lesson, and missed/shifted days.",
      tone: "amber",
    },
    {
      label: "Teams assignment handoff",
      value: "Planned",
      helper: "Lesson plans should generate Teams-ready assignment shells.",
      tone: "sky",
    },
  ],
  actions: [
    {
      label: "Upload scope and sequence",
      href: "/curriculum/import",
      helper: "Import publisher pacing files and map them to courses.",
      tone: "royal",
    },
    {
      label: "Review curriculum map",
      href: "/curriculum/maps",
      helper: "Inspect course objectives, pacing, and lesson coverage.",
      tone: "emerald",
    },
    {
      label: "Create Teams assignment shell",
      href: "/teacher/assignments/new?source=lesson-plan",
      helper: "Prepare title, instructions, due date, rubric, resources, and accommodations.",
      tone: "sky",
    },
  ],
};

const parentToday: LearningContinuitySection = {
  kicker: "Family learning status",
  title: "Parent / guardian view of today",
  description:
    "Show each child's learning day clearly: schedule, Teams links, attendance, assignments, missing work, teacher messages, billing alerts, prayer, devotions, and announcements.",
  metrics: [
    {
      label: "Family tasks",
      value: "4",
      helper: "Forms, payment, messages, or acknowledgements due.",
      tone: "amber",
    },
    {
      label: "Online classes",
      value: "6",
      helper: "Classes with current Teams or assignment links.",
      tone: "royal",
    },
    {
      label: "Missing work",
      value: "2",
      helper: "Assignments requiring family awareness.",
      tone: "rose",
    },
    {
      label: "Unread messages",
      value: "3",
      helper: "Teacher or school messages awaiting review.",
      tone: "violet",
    },
  ],
  actions: [
    {
      label: "Open child learning status",
      href: "/parent/learning-status",
      helper: "See today's schedule, links, assignments, grades, and attendance.",
      tone: "royal",
    },
    {
      label: "Read school announcement",
      href: "/announcements",
      helper: "Open current schoolwide or class-level notices.",
      tone: "amber",
    },
    {
      label: "Message teacher",
      href: "/communications/new?audience=teacher",
      helper: "Start a family-to-teacher communication thread.",
      tone: "violet",
    },
  ],
};

const studentToday: LearningContinuitySection = {
  kicker: "Student daily view",
  title: "What do I do next?",
  description:
    "A student-first sequence for joining class, completing assignments, checking feedback, asking for help, and participating in mission life.",
  metrics: [
    {
      label: "Assignments due",
      value: "6",
      helper: "Work due in the next seven days.",
      tone: "amber",
    },
    {
      label: "Classes today",
      value: "7",
      helper: "Scheduled courses with class links and teacher instructions.",
      tone: "royal",
    },
    {
      label: "Unread updates",
      value: "5",
      helper: "Teacher messages or class announcements.",
      tone: "rose",
    },
    {
      label: "Service hours",
      value: "14",
      helper: "Logged service hours this year.",
      tone: "emerald",
    },
  ],
  actions: [
    {
      label: "Join next class",
      href: "/integrations/teams/classes/next",
      helper: "Open Teams class meeting or channel.",
      tone: "royal",
    },
    {
      label: "Open assignments",
      href: "/student/assignments",
      helper: "Review due dates, instructions, and submissions.",
      tone: "amber",
    },
    {
      label: "Ask for help",
      href: "/student/help-request/new",
      helper: "Request academic, technology, or care support.",
      tone: "violet",
    },
    {
      label: "Submit prayer request",
      href: "/mission/prayer-requests/new",
      helper: "Share a permission-aware prayer request.",
      tone: "emerald",
    },
  ],
};

const interventionAndCredits: LearningContinuitySection = {
  kicker: "Dual enrollment and intervention",
  title: "External, remedial, and credit-bearing online courses",
  description:
    "Track provider courses, remedial assignments, credit recovery, transcript impact, progress, access, and follow-up risk.",
  metrics: [
    {
      label: "External courses",
      value: "8",
      helper: "Dual enrollment, online electives, or provider-based courses.",
      tone: "royal",
    },
    {
      label: "Intervention plans",
      value: "12",
      helper: "Students assigned remedial or support coursework.",
      tone: "amber",
    },
    {
      label: "Transcript pending",
      value: "3",
      helper: "Courses requiring grade, credit, or transcript review.",
      tone: "rose",
    },
    {
      label: "Progress current",
      value: "84%",
      helper: "Courses with updated progress in the last seven days.",
      tone: "emerald",
    },
  ],
  actions: [
    {
      label: "Open dual enrollment tracker",
      href: "/academics/dual-enrollment",
      helper: "Review provider, course, credit, grade status, and transcript mapping.",
      tone: "royal",
    },
    {
      label: "Assign remedial course",
      href: "/academics/interventions/new",
      helper: "Create targeted support course with progress goals.",
      tone: "amber",
    },
    {
      label: "Review transcript impact",
      href: "/registrar/transcript-impact",
      helper: "Check credit-bearing online and recovery-course implications.",
      tone: "rose",
    },
  ],
};

const careAndMission: LearningContinuitySection = {
  kicker: "Mission life",
  title: "Prayer, devotions, celebrations, and care",
  description:
    "Keep Christian-school distinctives visible without mixing protected care records into inappropriate role views.",
  metrics: [
    {
      label: "Prayer follow-ups",
      value: "9",
      helper: "Requests marked for staff, chaplain, or counselor attention.",
      tone: "violet",
    },
    {
      label: "Devotion engagement",
      value: "82%",
      helper: "Students, staff, or families who opened today's devotion.",
      tone: "royal",
    },
    {
      label: "Care referrals",
      value: "12",
      helper: "Student support items needing counselor or chaplain review.",
      tone: "rose",
    },
    {
      label: "Celebrations",
      value: "6",
      helper: "Academic, service, chapel, or classroom wins ready to share.",
      tone: "emerald",
    },
  ],
  actions: [
    {
      label: "Review prayer board",
      href: "/mission/prayer-requests",
      helper: "Open permission-aware prayer requests.",
      tone: "violet",
    },
    {
      label: "Open devotions",
      href: "/mission/devotions",
      helper: "Review daily devotion and reflection prompts.",
      tone: "royal",
    },
    {
      label: "Post celebration",
      href: "/mission/celebrations/new",
      helper: "Share a student, class, service, or chapel highlight.",
      tone: "emerald",
    },
  ],
};

const defaultSectionsByRole: Partial<Record<DashboardRoleKey, LearningContinuitySection[]>> = {
  "school-administrator": [adminContinuity, interventionAndCredits, careAndMission],
  "head-of-school": [adminContinuity, interventionAndCredits, careAndMission],
  principal: [adminContinuity, curriculumPlanning, interventionAndCredits],
  registrar: [interventionAndCredits, adminContinuity],
  "admissions-director": [adminContinuity, parentToday],
  "finance-director": [adminContinuity, parentToday],
  teacher: [teacherCockpit, curriculumPlanning, interventionAndCredits],
  parent: [parentToday, adminContinuity],
  student: [studentToday, interventionAndCredits, careAndMission],
  "counselor-chaplain": [careAndMission, interventionAndCredits, adminContinuity],
  "nurse-health": [careAndMission, studentToday],
  "activities-athletics": [teacherCockpit, studentToday],
  "development-director": [adminContinuity, parentToday],
  "board-member": [adminContinuity, careAndMission],
  "technology-director": [adminContinuity, teacherCockpit],
  "operations-director": [adminContinuity, interventionAndCredits],
};

export function getLearningContinuityPayload(roleKey: DashboardRoleKey): LearningContinuityPayload {
  return {
    modeBanner: sharedModeBanner,
    sections: defaultSectionsByRole[roleKey] ?? [adminContinuity, teacherCockpit, parentToday],
  };
}
