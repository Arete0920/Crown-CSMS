import type { DashboardApiPayload, DashboardRoleKey } from "./dashboardTypes";

async function safeFetchJson<T>(url: string): Promise<T | null> {
  try {
    const response = await fetch(url, {
      credentials: "include",
      headers: {
        Accept: "application/json",
      },
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export async function loadRoleDashboardPayload(roleKey: DashboardRoleKey): Promise<DashboardApiPayload | null> {
  return safeFetchJson<DashboardApiPayload>(`/api/v1/dashboards/roles/${roleKey}/`);
}

export async function loadSharedDashboardPayload(): Promise<DashboardApiPayload | null> {
  return safeFetchJson<DashboardApiPayload>("/api/v1/dashboards/shared/");
}

export async function loadMicrosoft365DashboardPayload(): Promise<DashboardApiPayload | null> {
  return safeFetchJson<DashboardApiPayload>("/api/v1/dashboards/microsoft365/");
}