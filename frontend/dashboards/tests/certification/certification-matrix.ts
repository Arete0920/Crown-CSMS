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
const DASHBOARD_DATA_API = ["/api/dashboards/"];
const WIZARD_DATA_API = ["/api/v1/wizards"];

export const certificationMatrix: CertificationSurface[] = [
  {
    id: "sandbox-landing",
    label: "Sandbox landing",
    route: "/sandbox",
    kind: "route",
    personas: ["sandbox-admin", "sandbox-teacher", "sandbox-parent"],
    tenants: CORE_TENANTS,
    requireLiveProvenance: true,
    provenanceRequiredApiFragments: [],
    expectedText: ["CROWN"],
    expectedApiFragments: AUTH_API,
  },
  {
    id: "sandbox-command-center",
    label: "Sandbox command center",
    route: "/sandbox/command-center",
    kind: "dashboard",
    personas: ["sandbox-admin"],
    tenants: CORE_TENANTS,
    requireLiveProvenance: true,
    provenanceRequiredApiFragments: DASHBOARD_DATA_API,
    expectedApiFragments: AUTH_API,
  },
  {
    id: "admin-dashboard",
    label: "Admin dashboard",
    route: "/admin",
    kind: "dashboard",
    personas: ["sandbox-admin"],
    tenants: CORE_TENANTS,
    requireLiveProvenance: true,
    provenanceRequiredApiFragments: DASHBOARD_DATA_API,
    expectedApiFragments: AUTH_API,
  },
  {
    id: "school-admin-dashboard",
    label: "School admin dashboard",
    route: "/school-admin-dashboard",
    kind: "dashboard",
    personas: ["sandbox-admin"],
    tenants: CORE_TENANTS,
    requireLiveProvenance: true,
    provenanceRequiredApiFragments: DASHBOARD_DATA_API,
    expectedApiFragments: AUTH_API,
  },
  {
    id: "teacher-dashboard",
    label: "Teacher dashboard",
    route: "/teacher",
    kind: "dashboard",
    personas: ["sandbox-teacher"],
    tenants: CORE_TENANTS,
    requireLiveProvenance: true,
    provenanceRequiredApiFragments: DASHBOARD_DATA_API,
    expectedApiFragments: AUTH_API,
  },
  {
    id: "parent-dashboard",
    label: "Parent dashboard",
    route: "/parent",
    kind: "dashboard",
    personas: ["sandbox-parent"],
    tenants: CORE_TENANTS,
    requireLiveProvenance: true,
    provenanceRequiredApiFragments: DASHBOARD_DATA_API,
    expectedApiFragments: AUTH_API,
  },
  {
    id: "student-dashboard",
    label: "Student dashboard",
    route: "/student",
    kind: "dashboard",
    personas: ["sandbox-student"],
    tenants: CORE_TENANTS,
    requireLiveProvenance: true,
    provenanceRequiredApiFragments: DASHBOARD_DATA_API,
    expectedApiFragments: AUTH_API,
  },
  {
    id: "board-dashboard",
    label: "Board dashboard",
    route: "/board",
    kind: "dashboard",
    personas: ["sandbox-board"],
    tenants: CORE_TENANTS,
    requireLiveProvenance: true,
    provenanceRequiredApiFragments: DASHBOARD_DATA_API,
    expectedApiFragments: AUTH_API,
  },
  {
    id: "wizard-hub",
    label: "Wizard hub",
    route: "/wizards",
    kind: "wizard",
    personas: ["sandbox-admin"],
    tenants: CORE_TENANTS,
    requireLiveProvenance: true,
    provenanceRequiredApiFragments: WIZARD_DATA_API,
    expectedApiFragments: [...AUTH_API, ...NAV_API, "/api/v1/wizards"],
  },
];
