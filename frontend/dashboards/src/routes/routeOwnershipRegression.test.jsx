import { describe, expect, it } from "vitest";
import { DASHBOARD_REGISTRY } from "../config/dashboardRegistry";
import { PATHS } from "./paths";
import routerSource from "./router.jsx?raw";

describe("canonical billing and platform route ownership", () => {
  it("retains exactly one billing registry entry", () => {
    expect(DASHBOARD_REGISTRY.filter((dashboard) => dashboard.path === PATHS.BILLING_DASHBOARD)).toHaveLength(1);
  });

  it("registers billing via the explicit finance-guarded route, not twice through dashboardRoutes", () => {
    expect(routerSource).toContain("path: PATHS.BILLING_DASHBOARD");
    expect(routerSource).toMatch(/path:\s*PATHS\.BILLING_DASHBOARD,[\s\S]*?<RoleRouteGuard allowedRoles=\{FINANCE_ALLOWED_ROLES\}>/);
    // Billing and platform-owner routes each have their own explicit guards.
    // Neither may be registered again via generic dashboardRoutes.
    expect(routerSource).toMatch(
      /\.\.\.dashboardRoutes\.filter\(\(route\) => !\[[\s\S]*?PATHS\.BILLING_DASHBOARD,[\s\S]*?PATHS\.MASTER_CONTROL_DASHBOARD,[\s\S]*?\]\.includes\(route\.path\)\)/,
    );
  });

  it("keeps the school administrator dashboard under a single registry owner", () => {
    expect(DASHBOARD_REGISTRY.filter((dashboard) => dashboard.path === PATHS.SCHOOL_ADMIN_DASHBOARD)).toHaveLength(1);
    expect(routerSource).not.toMatch(/path:\s*PATHS\.SCHOOL_ADMIN_DASHBOARD\b/);
  });
});
