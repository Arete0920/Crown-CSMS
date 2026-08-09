export type CertificationPersona =
  | "sandbox-admin"
  | "sandbox-teacher"
  | "sandbox-parent"
  | "sandbox-student"
  | "sandbox-board";

export type CertificationSurface = {
  id: string;
  label: string;
  route: string;
  kind: "route" | "dashboard" | "wizard";
  personas: CertificationPersona[];
  tenants: string[];
  expectedApiFragments: string[];
  requireLiveProvenance: boolean;
  provenanceRequiredApiFragments?: string[];
  expectedText?: string[];
  allowFailedRequests?: boolean;
  allowConsoleErrors?: boolean;
};

const AUTH_API = ["/api/v1/auth/token", "/api/v1/auth/me"];
const UNIFIED_DASHBOARD_API = "/api/dashboards/summary/";
const ADMISSIONS_SUMMARY_API = "/api/v1/admissions/summary/";

const dashboardSurface = (config: {
  id: string;
  label: string;
  route: string;
  persona: CertificationPersona;
  slug?: string;
  summaryApi?: string;
}): CertificationSurface => {
  const summaryApi = config.summaryApi
    || (config.slug ? `/api/v1/dashboards/${config.slug}/summary` : "");
  if (!summaryApi) {
    throw new Error(`Certification surface ${config.id} requires an active summary API.`);
  }

  return {
    id: config.id,
    label: config.label,
    route: config.route,
    kind: "dashboard",
    personas: [config.persona],
    tenants: ["heritage"],
    expectedApiFragments: [...AUTH_API, summaryApi],
    requireLiveProvenance: true,
    provenanceRequiredApiFragments: [summaryApi],
  };
};

export const certificationMatrix: CertificationSurface[] = [
  {
    id: "home-route",
    label: "Home route",
    route: "/",
    kind: "route",
    personas: ["sandbox-admin"],
    tenants: ["heritage"],
    expectedApiFragments: AUTH_API,
    requireLiveProvenance: false,
  },
  {
    id: "sandbox-landing",
    label: "Sandbox landing",
    route: "/sandbox",
    kind: "route",
    personas: ["sandbox-admin", "sandbox-teacher", "sandbox-parent"],
    tenants: ["heritage"],
    expectedApiFragments: AUTH_API,
    requireLiveProvenance: false,
  },
  {
    id: "sandbox-command-center",
    label: "Sandbox command center",
    route: "/sandbox/command-center",
    kind: "route",
    personas: ["sandbox-admin"],
    tenants: ["heritage"],
    expectedApiFragments: AUTH_API,
    requireLiveProvenance: false,
  },
  dashboardSurface({
    id: "admin-dashboard",
    label: "Admin dashboard",
    route: "/admin",
    persona: "sandbox-admin",
    summaryApi: UNIFIED_DASHBOARD_API,
  }),
  dashboardSurface({
    id: "school-admin-dashboard",
    label: "School admin dashboard",
    route: "/school-admin-dashboard",
    persona: "sandbox-admin",
    summaryApi: UNIFIED_DASHBOARD_API,
  }),
  dashboardSurface({
    id: "admin-role-dashboard",
    label: "Admin role dashboard",
    route: "/dash/admin",
    persona: "sandbox-admin",
    summaryApi: UNIFIED_DASHBOARD_API,
  }),
  dashboardSurface({
    id: "teacher-dashboard",
    label: "Teacher dashboard",
    route: "/teacher",
    persona: "sandbox-teacher",
    slug: "teacher",
  }),
  dashboardSurface({
    id: "teacher-role-dashboard",
    label: "Teacher role dashboard",
    route: "/dash/teacher",
    persona: "sandbox-teacher",
    summaryApi: UNIFIED_DASHBOARD_API,
  }),
  dashboardSurface({
    id: "parent-dashboard",
    label: "Parent dashboard",
    route: "/parent",
    persona: "sandbox-parent",
    slug: "parent",
  }),
  dashboardSurface({
    id: "parent-role-dashboard",
    label: "Parent role dashboard",
    route: "/dash/parent",
    persona: "sandbox-parent",
    summaryApi: UNIFIED_DASHBOARD_API,
  }),
  dashboardSurface({
    id: "student-dashboard",
    label: "Student dashboard",
    route: "/student",
    persona: "sandbox-student",
    slug: "student",
  }),
  {
    id: "board-route",
    label: "Board route",
    route: "/board",
    kind: "route",
    personas: ["sandbox-board"],
    tenants: ["heritage"],
    expectedApiFragments: AUTH_API,
    requireLiveProvenance: false,
  },
  dashboardSurface({
    id: "board-dashboard",
    label: "Board dashboard",
    route: "/school-board-dashboard",
    persona: "sandbox-board",
    slug: "school-board",
  }),
  dashboardSurface({
    id: "finance-route",
    label: "Finance route",
    route: "/finance",
    persona: "sandbox-admin",
    slug: "billing",
  }),
  dashboardSurface({
    id: "admissions-dashboard",
    label: "Admissions dashboard",
    route: "/admissions-dashboard",
    persona: "sandbox-admin",
    summaryApi: ADMISSIONS_SUMMARY_API,
  }),
  {
    id: "wizard-hub",
    label: "Wizard hub",
    route: "/wizards",
    kind: "wizard",
    personas: ["sandbox-admin"],
    tenants: ["heritage"],
    expectedApiFragments: [...AUTH_API, "/api/v1/wizards/"],
    requireLiveProvenance: true,
    provenanceRequiredApiFragments: ["/api/v1/wizards/"],
    expectedText: ["Wizard Hub"],
  },
];
