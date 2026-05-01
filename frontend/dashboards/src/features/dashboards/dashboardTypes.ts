export type DashboardRoleKey =
  | "school-administrator"
  | "head-of-school"
  | "principal"
  | "registrar"
  | "admissions-director"
  | "finance-director"
  | "teacher"
  | "parent"
  | "student"
  | "counselor-chaplain"
  | "nurse-health"
  | "activities-athletics"
  | "development-director"
  | "board-member"
  | "technology-director"
  | "operations-director";

export type DashboardTone =
  | "royal"
  | "sky"
  | "emerald"
  | "amber"
  | "rose"
  | "violet"
  | "slate";

export interface DashboardKpi {
  label: string;
  value: string;
  helper: string;
  source: string;
  tone?: DashboardTone;
}

export interface DashboardQueueItem {
  title: string;
  count: number;
  urgency: "low" | "medium" | "high" | "critical";
  href: string;
}

export interface DashboardAction {
  label: string;
  href: string;
  description: string;
}

export interface DashboardPanel {
  title: string;
  description: string;
  items: string[];
}

export interface DashboardSharedCard {
  key:
    | "communications"
    | "calendar"
    | "devotions"
    | "prayer-requests"
    | "announcements"
    | "shared-information"
    | "microsoft365"
    | "microsoft-education"
    | "teams";
  title: string;
  description: string;
  href: string;
  required: true;
}

export interface DashboardRoleProfile {
  key: DashboardRoleKey;
  title: string;
  route: string;
  audience: string;
  purpose: string;
  primaryResponsibilities: string[];
  kpis: DashboardKpi[];
  queue: DashboardQueueItem[];
  quickActions: DashboardAction[];
  panels: DashboardPanel[];
  tone: DashboardTone;
}

export interface DashboardApiPayload {
  roleKey: DashboardRoleKey;
  generatedAt: string;
  mode: "live" | "configured-empty" | "fallback";
  kpis?: DashboardKpi[];
  queue?: DashboardQueueItem[];
  panels?: DashboardPanel[];
  shared?: DashboardSharedCard[];
  microsoft365?: {
    teamsEnabled: boolean;
    educationEnabled: boolean;
    calendarSyncEnabled: boolean;
    oneDriveEnabled: boolean;
    lastSyncLabel: string;
  };
}