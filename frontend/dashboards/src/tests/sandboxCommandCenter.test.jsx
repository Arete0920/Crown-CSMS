// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import SandboxCommandCenter from "../sandbox/SandboxCommandCenter";

vi.mock("../sandbox/sandboxApi", () => ({
  recordSandboxEvent: vi.fn(),
  submitSandboxFeedback: vi.fn(),
}));

function renderCommandCenter(props = {}) {
  return render(
    <MemoryRouter>
      <SandboxCommandCenter {...props} />
    </MemoryRouter>,
  );
}

afterEach(() => {
  cleanup();
  localStorage.clear();
  globalThis.history.pushState({}, "", "/");
  vi.clearAllMocks();
});

describe("SandboxCommandCenter", () => {
  it("normalizes legacy guided URL context to the Heritage school experience", () => {
    globalThis.history.pushState(
      {},
      "",
      "/dashboard?experience=camp&guidance=guided&role=school_admin&school=sandbox-school-cedar-summer-camp&tour=Camp%20Proof"
    );

    renderCommandCenter();

    expect(screen.getByRole("main", { name: "Sandbox command center" })).toBeTruthy();
    expect(screen.getByRole("heading", { level: 1, name: "Guided proof path" })).toBeTruthy();
    expect(screen.getAllByText("Camp Proof").length).toBeGreaterThan(0);
    expect(screen.getAllByText("School Demo").length).toBeGreaterThan(0);
    expect(screen.getAllByText("School Administrator").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Heritage Christian Academy").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Demo data only/).length).toBeGreaterThan(0);

    const evaluatorLink = screen.getByRole("link", { name: /Return to evaluator/i });
    expect(evaluatorLink.getAttribute("href")).toBe("/sandbox");

    const teacherProofLink = screen.getByRole("link", { name: /Teacher \/ Staff.*Load this role's proof path/i });
    expect(teacherProofLink.getAttribute("href")).toContain("/sandbox/command-center?");
    expect(teacherProofLink.getAttribute("href")).toContain("role=teacher");

    expect(screen.queryByText("Switch track")).toBeNull();
    expect(screen.queryByText("Open this role workspace")).toBeNull();
    expect(screen.queryByRole("link", { name: /Heritage Christian Academy/i })).toBeNull();
  });

  it("uses section and h2 semantics when embedded compactly", () => {
    renderCommandCenter({ compact: true });

    expect(screen.queryByRole("main", { name: "Sandbox command center" })).toBeNull();
    expect(screen.getByRole("region", { name: "Sandbox command center" })).toBeTruthy();
    expect(screen.getByRole("heading", { level: 2, name: "Guided proof path" })).toBeTruthy();
  });

  it("renders self-guided mode without expanding checklist as the primary copy", () => {
    globalThis.history.pushState(
      {},
      "",
      "/dashboard?experience=school&guidance=self-guided&role=parent&school=19801b59-8c05-4c84-9312-5d792e4e839d"
    );

    renderCommandCenter();

    expect(screen.getByText("Self-guided sandbox")).toBeTruthy();
    expect(
      screen.getByText(
        "Explore freely. Every page should retain clear role, track, organization, and demo-data context.",
      ),
    ).toBeTruthy();
    expect(screen.getAllByText("Parent / Guardian").length).toBeGreaterThan(0);
  });

  it("records normalized Heritage feedback context without exposing entered personal data", async () => {
    const telemetry = await import("../sandbox/sandboxApi");
    globalThis.history.pushState({}, "", "/dashboard?experience=daycare&guidance=guided&role=teacher");

    renderCommandCenter();
    fireEvent.click(screen.getByRole("button", { name: /Send feedback/i }));

    expect(telemetry.recordSandboxEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        event: "feedback_requested",
        track: "school",
        guidance: "guided",
        persona: "teacher",
      })
    );
  });
});
