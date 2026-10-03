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
    origin: "http://localhost",
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
    expect(window.location.href).toBe("/school-admin-dashboard");
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
