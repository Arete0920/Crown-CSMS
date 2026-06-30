export type CertificationSurface = {
  id: string;
  label: string;
  route: string;
  kind: "route" | "dashboard" | "wizard" | "module";
  personas: string[];
  tenants: string[];
  expectedText?: string[];
  expectedApiFragments?: string[];
  allowFailedRequests?: boolean;
  allowConsoleErrors?: boolean;
};

export const certificationMatrix: CertificationSurface[] = [
  {
    id: "sandbox-landing",
    label: "Sandbox landing",
    route: "/sandbox",
    kind: "route",
    personas: ["sandbox-admin", "sandbox-teacher", "sandbox-parent"],
    tenants: ["heritage"],
    expectedText: ["CROWN"],
    expectedApiFragments: [],
  },
  {
    id: "sandbox-command-center",
    label: "Sandbox command center",
    route: "/sandbox/command-center",
    kind: "dashboard",
    personas: ["sandbox-admin"],
    tenants: ["heritage"],
    expectedApiFragments: [],
  },
  {
    id: "admin-dashboard",
    label: "Admin dashboard",
    route: "/admin",
    kind: "dashboard",
    personas: ["sandbox-admin"],
    tenants: ["heritage"],
    expectedApiFragments: ["/api/v1/nav"],
  },
  {
    id: "teacher-dashboard",
    label: "Teacher dashboard",
    route: "/teacher",
    kind: "dashboard",
    personas: ["sandbox-teacher"],
    tenants: ["heritage"],
    expectedApiFragments: [],
  },
  {
    id: "parent-dashboard",
    label: "Parent dashboard",
    route: "/parent",
    kind: "dashboard",
    personas: ["sandbox-parent"],
    tenants: ["heritage"],
    expectedApiFragments: [],
  },
  {
    id: "student-dashboard",
    label: "Student dashboard",
    route: "/student",
    kind: "dashboard",
    personas: ["sandbox-student"],
    tenants: ["heritage"],
    expectedApiFragments: [],
  },
  {
    id: "board-dashboard",
    label: "Board dashboard",
    route: "/board",
    kind: "dashboard",
    personas: ["sandbox-board"],
    tenants: ["heritage"],
    expectedApiFragments: [],
  },
  {
    id: "wizard-hub",
    label: "Wizard hub",
    route: "/wizards",
    kind: "wizard",
    personas: ["sandbox-admin"],
    tenants: ["heritage"],
    expectedApiFragments: ["/api/v1/nav"],
  },
];
