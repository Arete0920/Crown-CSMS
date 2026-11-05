// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { RouterProvider, createMemoryRouter } from "react-router";

import { router } from "../routes/router.jsx";
import { dashboardRoutes } from "../routes/dashboardRoutes.jsx";
import { PATHS } from "../routes/paths";
import RoleRouteGuard from "../components/routing/RoleRouteGuard";
import BillingDashboard from "../pages/BillingDashboard";
import { ADMISSIONS_PIPELINE_ALLOWED_ROLES } from "../pages/AdmissionsPipelineList.jsx";
import { hasAnyRole } from "../auth/roleAccess";


vi.mock("../components/brand/CrownLogo", () => ({
  default: () => <div>CROWN</div>,
}));

beforeEach(() => {
  vi.restoreAllMocks();
  sessionStorage.clear();
  localStorage.clear();
});

afterEach(() => {
  cleanup();
});

describe("sandbox routes", () => {
  it("renders the sandbox landing page at /sandbox", () => {
    const memoryRouter = createMemoryRouter(router.routes, {
      initialEntries: ["/sandbox"],
    });

    render(<RouterProvider router={memoryRouter} />);

    expect(screen.getAllByRole("heading", { name: "Guided Proof Sandbox" }).length).toBeGreaterThan(0);
  });

  it("renders the sandbox command center at /sandbox/command-center", () => {
    const memoryRouter = createMemoryRouter(router.routes, {
      initialEntries: ["/sandbox/command-center"],
    });

    render(<RouterProvider router={memoryRouter} />);

    expect(screen.getByRole("heading", { name: /Guided proof path|Self-guided sandbox/ })).toBeTruthy();
  });
});

describe("assembled application route ownership", () => {
  it("registers each top-level path exactly once across all route sources", () => {
    const paths = router.routes.map((route) => route.path).filter(Boolean);
    const duplicates = paths.filter((path, index) => paths.indexOf(path) !== index);
    expect(duplicates).toEqual([]);
  });

  it("keeps the explicit finance role guard on the billing dashboard", () => {
    const billing = router.routes.filter((route) => route.path === PATHS.BILLING_DASHBOARD);
    expect(billing).toHaveLength(1);
    expect(billing[0].element.type).toBe(RoleRouteGuard);
    expect(billing[0].element.props.allowedRoles).toContain("finance_director");
    expect(billing[0].element.props.allowedRoles).not.toContain("parent");
    expect(billing[0].element.props.children.type).toBe(BillingDashboard);
  });

  it("allows registrar through both admissions route and page-level authorization", () => {
    const canonical = router.routes.filter((route) => route.path === PATHS.ADMISSIONS_PIPELINE);
    expect(canonical).toHaveLength(1);
    // The top-level route has an authenticated-school wrapper and a nested
    // role guard. The page's independent check must not reject allowed roles.
    const schoolGuard = canonical[0].element;
    const roleGuard = schoolGuard.props.children;
    expect(roleGuard.type).toBe(RoleRouteGuard);
    expect(roleGuard.props.allowedRoles).toContain("registrar");
    for (const allowed of roleGuard.props.allowedRoles) {
      expect(hasAnyRole([allowed], ADMISSIONS_PIPELINE_ALLOWED_ROLES)).toBe(true);
    }
    expect(hasAnyRole(["registrar"], ADMISSIONS_PIPELINE_ALLOWED_ROLES)).toBe(true);
    expect(hasAnyRole(["parent"], ADMISSIONS_PIPELINE_ALLOWED_ROLES)).toBe(false);
    expect(hasAnyRole([], ADMISSIONS_PIPELINE_ALLOWED_ROLES)).toBe(false);
  });

  it("keeps the registry role and release-state element on the school admin dashboard", () => {
    const registered = dashboardRoutes.find((route) => route.path === PATHS.SCHOOL_ADMIN_DASHBOARD);
    const assembled = router.routes.filter((route) => route.path === PATHS.SCHOOL_ADMIN_DASHBOARD);
    expect(registered).toBeDefined();
    expect(assembled).toHaveLength(1);
    expect(assembled[0].element).toBe(registered.element);
  });
});
