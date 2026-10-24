import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

/**
 * Source-only regression: the historical Master Control dashboard must not
 * render invented operating figures. Live Azure and RBAC proof remain separate.
 */
describe("platform Master Control legacy-route truth", () => {
  it("redirects the historical dashboard component to the canonical owner console", () => {
    const component = readFileSync("src/pages/MasterControlDashboard.jsx", "utf8");
    expect(component).toContain('import { Navigate } from "react-router"');
    expect(component).toContain("to={PATHS.MASTER_CONTROL}");
    expect(component).toContain("replace");
    expect(component).not.toContain("CrownDashboardTemplate");
    expect(component).not.toContain("getDashboardTemplate");
  });

  it("uses a schoolless guard for both canonical and legacy owner paths", () => {
    const router = readFileSync("src/routes/router.jsx", "utf8");
    const legacyStart = router.indexOf("path: PATHS.MASTER_CONTROL_DASHBOARD,");
    expect(legacyStart).toBeGreaterThanOrEqual(0);
    const legacyBlock = router.slice(legacyStart, router.indexOf("\n  },", legacyStart));
    expect(legacyBlock).toContain("<AuthenticatedPlatformRouteGuard>");
    expect(legacyBlock).toContain("<Navigate to={PATHS.MASTER_CONTROL} replace />");
    expect(legacyBlock).not.toContain("<RoleRouteGuard");
    expect(legacyBlock).not.toContain("<AuthenticatedSchoolRouteGuard");
    expect(router).toContain("&& route.path !== PATHS.MASTER_CONTROL_DASHBOARD");
  });

  it("preserves an authenticated platform route and server-side authority", () => {
    const router = readFileSync("src/routes/router.jsx", "utf8");
    const operatorApi = readFileSync("../../backend/platform_ops/views.py", "utf8");
    const ownerGuard = readFileSync(
      "src/components/routing/AuthenticatedPlatformRouteGuard.jsx", "utf8",
    );
    const routeStart = router.indexOf("path: PATHS.MASTER_CONTROL,");
    expect(routeStart).toBeGreaterThanOrEqual(0);
    const routeBlock = router.slice(routeStart, router.indexOf("\n  },", routeStart));
    expect(routeBlock).toContain("<AuthenticatedPlatformRouteGuard>");
    expect(routeBlock).toContain("<PlatformOwnerConsole />");
    expect(ownerGuard).toContain("!getAccessToken()");
    expect(operatorApi).toContain("@permission_classes([IsPlatformOperator])");
  });
});
