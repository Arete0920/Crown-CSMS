// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../components/brand/CrownLogo", () => ({
  default: () => <div>CROWN</div>,
}));

beforeEach(() => {
  vi.restoreAllMocks();
  vi.stubGlobal("fetch", vi.fn((url) => {
    if (String(url).includes("/api/v1/sandbox/session/")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          access: "access-token",
          refresh: "refresh-token",
          school_id: "19801b59-8c05-4c84-9312-5d792e4e839d",
          school_name: "Heritage Christian Academy",
          role: "school_admin",
          route: "/school-admin-dashboard",
          guidance: "guided",
          tour: "Daily operating picture",
          command_center: {},
        }),
      });
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve({ ok: true }) });
  }));
  delete window.location;
  window.location = {
    href: "",
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

  it("sends structured sandbox feedback telemetry from the command center", async () => {
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
          headers: { "Content-Type": "application/json" },
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
  });
});
