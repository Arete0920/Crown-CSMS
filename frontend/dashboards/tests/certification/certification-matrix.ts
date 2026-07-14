export type CertificationSurface = {
  id: string;
  label: string;
  route: string;
  kind: "route" | "dashboard" | "wizard" | "module";
  personas: string[];
  tenants: string[];
  requireLiveProvenance?: boolean;
  provenanceRequiredApiFragments?: string[];
  expectedText?: string[];
  expectedApiFragments?: string[];
  allowFailedRequests?: boolean;
  allowConsoleErrors?: boolean;
};

const CORE_TENANTS = ["heritage"];
const AUTH_API = ["/api/v1/auth/token", "/api/v1/auth/me"];
const NAV_API = ["/api/v1/nav"];
const DASHBOARD_SUMMARY_API = (slug: string): string[] => [
  `/api/v1/dashboards/${slug}/summary`,
];
const WIZARD_DATA_API = ["/api/v1/wizards/"];

function dashboardSurface(config: {
  id: string;
  label: string;
  route: string;
  persona: string;
  slug: string;
}): CertificationSurface {
  const summaryApi = DASHBOARD_SUMMARY_API(config.slug);
  return {
    id: config.id,
    label: config.label,
    route: config.route,
    kind: "dashboard",
    personas: [config.persona],
    tenants: CORE_TENANTS,
    requireLiveProvenance: true,
    provenanceRequiredApiFragments: summaryApi,
    expectedApiFragments: [...AUTH_API, ...summaryApi],
  };
}

export const certificationMatrix: CertificationSurface[] = [
  {
    id: "sandbox-landing",
    label: "Sandbox landing",
    route: "/sandbox",
    kind: "route",
    personas: ["sandbox-admin", "sandbox-teacher", "sandbox-parent"],
    tenants: CORE_TENANTS,
    requireLiveProvenance: false,
    provenanceRequiredApiFragments: [],
    expectedText: ["CROWN"],
    expectedApiFragments: AUTH_API,
  },
  {
    id: "sandbox-command-center",
    label: "Sandbox command center",
    route: "/sandbox/command-center",
    kind: "route",
    personas: ["sandbox-admin"],
    tenants: CORE_TENANTS,
    requireLiveProvenance: false,
    provenanceRequiredApiFragments: [],
    expectedText: ["Demo Data"],
    expectedApiFragments: [],
  },
  dashboardSurface({
    id: "admin-dashboard",
    label: "Admin dashboard",
    route: "/admin",
    persona: "sandbox-admin",
    slug: "school-administrator",
  }),
  dashboardSurface({
    id: "school-admin-dashboard",
    label: "School admin dashboard",
    route: "/school-admin-dashboard",
    persona: "sandbox-admin",
    slug: "school-administrator",
  }),
  dashboardSurface({
    id: "teacher-dashboard",
    label: "Teacher dashboard",
    route: "/teacher",
    persona: "sandbox-teacher",
    slug: "teacher",
  }),
  dashboardSurface({
    id: "parent-dashboard",
    label: "Parent dashboard",
    route: "/parent",
    persona: "sandbox-parent",
    slug: "parent",
  }),
  dashboardSurface({
    id: "student-dashboard",
    label: "Student dashboard",
    route: "/student",
    persona: "sandbox-student",
    slug: "student",
  }),
  dashboardSurface({
    id: "board-dashboard",
    label: "Board dashboard",
    route: "/school-board-dashboard",
    persona: "sandbox-board",
    slug: "school-board",
  }),
  {
    id: "wizard-hub",
    label: "Wizard hub",
    route: "/wizards",
    kind: "wizard",
    personas: ["sandbox-admin"],
    tenants: CORE_TENANTS,
    requireLiveProvenance: true,
    provenanceRequiredApiFragments: WIZARD_DATA_API,
    expectedApiFragments: [...AUTH_API, ...NAV_API, ...WIZARD_DATA_API],
  },
];
