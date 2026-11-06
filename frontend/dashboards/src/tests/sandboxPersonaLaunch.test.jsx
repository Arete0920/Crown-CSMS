// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../components/brand/CrownLogo", () => ({
  default: () => <div>CROWN</div>,
}));

beforeEach(() => {
  vi.restoreAllMocks();
  sessionStorage.clear();
  localStorage.clear();
  vi.stubGlobal("fetch", vi.fn((url) => {
    if (String(url).includes("/api/v1/sandbox/session/")) {
      return Promise.resolve(new Response(JSON.stringify({
          access: "access-token",
          refresh: "refresh-token",
          school_id: "19801b59-8c05-4c84-9312-5d792e4e839d",
          school_name: "Heritage Christian Academy",
          role: "school_admin",
          route: "/school-admin-dashboard",
          guidance: "guided",
          tour: "Daily operating picture",
          command_center: {},
        }), { status: 200, headers: { "Content-Type": "application/json" } }));
    }
    return Promise.resolve(new Response(JSON.stringify({ ok: true }), { status: 200, headers: { "Content-Type": "application/json" } }));
  }));
  delete window.location;
  window.location = {
    href: "",
    origin: "http://127.0.0.1:4173",
    hostname: "127.0.0.1",
    search: "",
    assign(url) {
      this.href = url;
    },
  };
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("Sandbox persona launch", () => {
  it("starts a one-click role session without visible credential fields", async () => {
    const { default: SandboxLandingPage } = await import("../pages/SandboxLandingPage.jsx");
    render(<SandboxLandingPage />);

    expect(screen.queryByLabelText("Email")).toBeNull();
    expect(screen.queryByLabelText("Password")).toBeNull();

    fireEvent.click(screen.getAllByText("Start guided")[0]);

    await waitFor(() => {
      expect(sessionStorage.getItem("crown.jwt.access")).toBe("access-token");
    });

    expect(sessionStorage.getItem("crown.school.id")).toBe("19801b59-8c05-4c84-9312-5d792e4e839d");
    expect(window.location.href).toContain("/sandbox/command-center?");
    expect(window.location.href).toContain("role=school_admin");
    expect(window.location.href).toContain("guidance=guided");
  });

  it("carries the Django CSRF cookie when changing authenticated sandbox roles", async () => {
    document.cookie = "csrftoken=second%2Dsession%2Dtoken; path=/";
    sessionStorage.setItem("crown.jwt.access", "previous-school-admin-jwt");

    const { createSandboxSession } = await import("../sandbox/sandboxApi.js");
    const response = await createSandboxSession({
      inviteId: "",
      role: "parent",
      school: "heritage-core",
      track: "school",
      guidance: "guided",
      tour: "Family experience proof path",
    });
    expect(response).toBeTruthy();
    const [, options] = globalThis.fetch.mock.calls.find(
      ([url]) => String(url).includes("/api/v1/sandbox/session/"),
    );
    const headers = new Headers(options.headers);
    expect(headers.get("X-CSRFToken")).toBe("second-session-token");
    expect(headers.get("Content-Type")).toBe("application/json");
    expect(headers.get("Authorization")).toBeNull();
    expect(options.credentials).toBe("same-origin");
    expect(JSON.parse(options.body).role).toBe("parent");
    document.cookie = "csrftoken=; Max-Age=0; path=/";
  });

  it("preserves the server-issued dashboard route for self-guided demo", async () => {
    const { default: SandboxLandingPage } = await import("../pages/SandboxLandingPage.jsx");
    render(<SandboxLandingPage />);
    fireEvent.click(screen.getByText("Self-guided exploration"));
    fireEvent.click(screen.getAllByText("Start self-guided")[0]);
    await waitFor(() => expect(window.location.href).toBe("/school-admin-dashboard"));
  });

  it("preserves the server-issued route even for a hosted invite opened on loopback", async () => {
    window.location.search = "?invite=sbx_inv_test";
    vi.stubGlobal("fetch", vi.fn((url) => Promise.resolve(new Response(JSON.stringify(
      String(url).includes("/api/v1/sandbox/invites/")
        ? { organization_label: "Fictional hosted evaluator", track: "school", usable: true, allowed_roles: ["school_admin"] }
        : String(url).includes("/api/v1/sandbox/session/")
          ? { access: "access", refresh: "refresh", school_id: "19801b59-8c05-4c84-9312-5d792e4e839d", role: "school_admin", route: "/school-admin-dashboard" }
          : { ok: true },
    ), { status: 200, headers: { "Content-Type": "application/json" } }))));
    const { default: SandboxLandingPage } = await import("../pages/SandboxLandingPage.jsx");
    render(<SandboxLandingPage />);
    await screen.findByText(/Invite loaded for Fictional hosted evaluator/);
    fireEvent.click(screen.getByRole("button", { name: "Start guided" }));
    await waitFor(() => expect(window.location.href).toBe("/school-admin-dashboard"));
  });

  it("shows no persona launch buttons for an unusable hosted invitation", async () => {
    window.location.search = "?invite=sbx_inv_expired";
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify({
      organization_label: "Expired fictional evaluator",
      track: "school",
      usable: false,
      allowed_roles: ["daycare_director"],
    }), { status: 200, headers: { "Content-Type": "application/json" } }))));
    const { default: SandboxLandingPage } = await import("../pages/SandboxLandingPage.jsx");
    render(<SandboxLandingPage />);
    await screen.findByText(/Invite loaded for Expired fictional evaluator/);
    expect(screen.queryByRole("button", { name: /Start guided/ })).toBeNull();
    expect(screen.queryByText("Diadem Daycare Director")).toBeNull();
  });

  it("shows only explicitly invited hosted childcare roles", async () => {
    window.location.search = "?invite=sbx_inv_director";
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify({
      organization_label: "Fictional director evaluator",
      track: "school",
      usable: true,
      allowed_roles: ["daycare_director"],
    }), { status: 200, headers: { "Content-Type": "application/json" } }))));
    const { default: SandboxLandingPage } = await import("../pages/SandboxLandingPage.jsx");
    render(<SandboxLandingPage />);
    await screen.findByText(/Invite loaded for Fictional director evaluator/);
    expect(screen.getByText("Diadem Daycare Director")).toBeTruthy();
    expect(screen.queryByText("Diadem Daycare Staff")).toBeNull();
    expect(screen.getAllByRole("button", { name: /Start guided/ })).toHaveLength(1);
  });

  it("sends authenticated tenant-scoped sandbox feedback telemetry from the command center", async () => {
    sessionStorage.setItem("crown.jwt.access", "feedback-test-access");
    sessionStorage.setItem("crown.school.id", "19801b59-8c05-4c84-9312-5d792e4e839d");
    const { default: SandboxCommandCenter } = await import("../sandbox/SandboxCommandCenter.jsx");
    render(
      <MemoryRouter>
        <SandboxCommandCenter />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: /^Send feedback/ }));

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/v1/sandbox/events/",
        expect.objectContaining({
          method: "POST",
          credentials: "include",
          body: JSON.stringify({
            event: "feedback_requested",
            track: "school",
            guidance: "guided",
            persona: "school_admin",
            school: "heritage-core",
            tour: "Daily operating picture",
          }),
        })
      );
    });
    const [, options] = globalThis.fetch.mock.calls.find(([url]) => url === "/api/v1/sandbox/events/");
    const headers = new Headers(options.headers);
    expect(headers.get("Content-Type")).toBe("application/json");
    expect(headers.get("Authorization")).toBe("Bearer feedback-test-access");
    expect(headers.get("X-School-Id")).toBe("19801b59-8c05-4c84-9312-5d792e4e839d");
  });
});
