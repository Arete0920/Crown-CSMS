import { BASE_NOTE } from "./_baseData.js";

const ENROLLMENT_TREND = [
  { month: "Jan", value: 18 },
  { month: "Feb", value: 39 },
  { month: "Mar", value: 67 },
  { month: "Apr", value: 91 },
  { month: "May", value: 122 },
  { month: "Jun", value: 138 },
];

const READINESS_TREND = [
  { month: "Jan", value: 42 },
  { month: "Feb", value: 55 },
  { month: "Mar", value: 63 },
  { month: "Apr", value: 78 },
  { month: "May", value: 86 },
  { month: "Jun", value: 92 },
];

export default {
  key: "summerCamp",
  activePath: "/summer-camp-dashboard",
  schoolName: "Heritage Christian Academy",
  updatesCount: 3,
  user: { initials: "SC", name: "Summer Camp Team", role: "Extended Programs" },
  eyebrow: "CROWN Launch Preview",
  title: "Summer Camp Operations",
  subtitle: "Heritage Christian Academy",
  note: BASE_NOTE,

  metrics: [
    { label: "Registered Campers", value: "138", detail: "Across all sessions", accent: "blue" },
    { label: "Today's Attendance", value: "126", detail: "11 pending check-ins", accent: "emerald" },
    { label: "Waitlist", value: "14", detail: "Auto-promote enabled", accent: "gold" },
    { label: "Readiness", value: "92%", detail: "Forms + payment + health", accent: "navy" },
  ],

  priorities: [
    { title: "Resolve missing forms", detail: "9 families missing required forms.", state: "Today", tone: "warn" },
    { title: "Review health queue", detail: "4 campers awaiting health review.", state: "Today", tone: "warn" },
    { title: "Finalize Week 3 staffing", detail: "1 group still below ideal ratio.", state: "This week", tone: "nominal" },
  ],
  prioritiesTitle: "Summer Camp priorities",

  alerts: [
    { title: "14 campers on waitlist", detail: "Capacity release could auto-promote campers.", tone: "warn" },
    { title: "3 incidents logged MTD", detail: "All incidents have follow-up owners.", tone: "nominal" },
  ],

  commandModules: [
    {
      key: "enrollment",
      icon: "EN",
      title: "Enrollment",
      status: "Stable",
      statusTone: "good",
      mainKpi: "138 registered, 14 waitlisted",
      summary: "Steady growth with active waitlist management.",
      kpis: [
        { label: "Registered", value: "138" },
        { label: "Waitlist", value: "14" },
        { label: "Promoted", value: "11" },
        { label: "Dropped", value: "3" },
      ],
      details: [
        "Registration open through June 30",
        "Auto-promote waitlist enabled",
        "Average response time 2.1 days",
      ],
      primaryActionLabel: "Open Enrollment",
      backActionLabel: "View Roster",
      primaryActionHref: "/summer-camp-dashboard/roster",
      backActionHref: "/summer-camp-dashboard/roster",
      lastUpdated: "8:05 AM",
    },
  ],

  trendPanels: [
    { kicker: "Registration", title: "Camper Enrollment", chip: "138 registered", trend: ENROLLMENT_TREND },
    { kicker: "Readiness", title: "Readiness Score", chip: "92% ready", trend: READINESS_TREND },
  ],

  activities: [
    "11 waitlisted campers auto-promoted this week.",
    "4 health records moved to nurse review queue.",
    "Daily attendance export shared with board packet owner.",
  ],

  quickActions: [
    { label: "Roster", href: "/summer-camp-dashboard/roster" },
    { label: "Setup Wizard", href: "/summer-camp-dashboard/setup" },
    { label: "Board Summary", href: "/summer-camp-dashboard" },
  ],

  statuses: [
    { label: "Enrollment", state: "138 registered" },
    { label: "Waitlist", state: "14 pending" },
    { label: "Readiness", state: "92%" },
    { label: "Incidents MTD", state: "3" },
  ],
};
