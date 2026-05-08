import { describe, expect, it } from "vitest";
import { requiredSharedDashboardCards, roleDashboardProfiles } from "../roleDashboardMatrix";

describe("CROWN role dashboard matrix", () => {
  it("defines every required role dashboard", () => {
    expect(roleDashboardProfiles.length).toBeGreaterThanOrEqual(16);
    const required = [
      "school-administrator",
      "head-of-school",
      "principal",
      "registrar",
      "admissions-director",
      "finance-director",
      "teacher",
      "parent",
      "student",
      "counselor-chaplain",
      "nurse-health",
      "activities-athletics",
      "development-director",
      "board-member",
      "technology-director",
      "operations-director",
    ];
    for (const key of required) {
      expect(roleDashboardProfiles.some((profile) => profile.key === key)).toBe(true);
    }
  });

  it("gives each dashboard role-specific KPIs, queues, quick actions, panels, and routes", () => {
    for (const profile of roleDashboardProfiles) {
      expect(profile.title).toBeTruthy();
      expect(profile.route).toMatch(/^\/dashboards\//);
      expect(profile.primaryResponsibilities.length).toBeGreaterThanOrEqual(4);
      expect(profile.kpis.length).toBeGreaterThanOrEqual(4);
      expect(profile.queue.length).toBeGreaterThanOrEqual(4);
      expect(profile.quickActions.length).toBeGreaterThanOrEqual(4);
      expect(profile.panels.length).toBeGreaterThanOrEqual(1);
    }
  });

  it("requires shared communication, calendar, mission, announcement, Microsoft 365, Microsoft Education, and Teams tools", () => {
    const requiredSharedKeys = [
      "communications",
      "calendar",
      "devotions",
      "prayer-requests",
      "announcements",
      "shared-information",
      "microsoft365",
      "microsoft-education",
      "teams",
    ];
    expect(requiredSharedDashboardCards.map((card) => card.key).sort()).toEqual(requiredSharedKeys.sort());
    for (const card of requiredSharedDashboardCards) {
      expect(card.required).toBe(true);
      expect(card.title).toBeTruthy();
      expect(card.href).toMatch(/^\//);
      expect(card.description.length).toBeGreaterThan(15);
    }
  });

  it("does not clone administrator dashboard KPIs into every role", () => {
    const serializedByRole = new Map(
      roleDashboardProfiles.map((profile) => [
        profile.key,
        profile.kpis.map((kpi) => kpi.label).join("|"),
      ])
    );
    const adminKpis = serializedByRole.get("school-administrator");
    expect(adminKpis).toBeTruthy();
    for (const [roleKey, kpis] of serializedByRole.entries()) {
      if (roleKey === "school-administrator") continue;
      expect(kpis).not.toEqual(adminKpis);
    }
  });
});