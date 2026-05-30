// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import SandboxCommandCenter from "../sandbox/SandboxCommandCenter";

vi.mock("../sandbox/sandboxTelemetry", () => ({
  recordSandboxEvent: vi.fn(),
}));

afterEach(() => {
  cleanup();
  localStorage.clear();
  window.history.pushState({}, "", "/");
  vi.clearAllMocks();
});

describe("SandboxCommandCenter", () => {
  it("renders guided context from URL params", () => {
    window.history.pushState(
      {},
      "",
      "/dashboard?experience=camp&guidance=guided&role=school_admin&school=sandbox-school-cedar-summer-camp&tour=Camp%20Proof"
    );

    render(<SandboxCommandCenter />);

    expect(screen.getByText("Guided proof path")).toBeTruthy();
    expect(screen.getByText("Camp Proof")).toBeTruthy();
    expect(screen.getByText("Camp / Summer Program Demo")).toBeTruthy();
    expect(screen.getByText("Program Director")).toBeTruthy();
    expect(screen.getByText("Cedar Ridge Summer Camp")).toBeTruthy();
    expect(screen.getByText(/Demo data only/)).toBeTruthy();
  });

  it("renders self-guided mode without expanding checklist as the primary copy", () => {
    window.history.pushState(
      {},
      "",
      "/dashboard?experience=school&guidance=self-guided&role=parent&school=19801b59-8c05-4c84-9312-5d792e4e839d"
    );

    render(<SandboxCommandCenter />);

    expect(screen.getByText("Self-guided sandbox")).toBeTruthy();
    expect(screen.getByText(/Explore freely/)).toBeTruthy();
    expect(screen.getByText("Parent / Guardian")).toBeTruthy();
  });

  it("records feedback request without exposing entered personal data", async () => {
    const telemetry = await import("../sandbox/sandboxTelemetry");
    window.history.pushState({}, "", "/dashboard?experience=daycare&guidance=guided&role=teacher");

    render(<SandboxCommandCenter />);
    fireEvent.click(screen.getByRole("button", { name: "Send feedback" }));

    expect(telemetry.recordSandboxEvent).toHaveBeenCalledWith(
      "feedback_requested",
      expect.objectContaining({
        track: "daycare",
        guidance: "guided",
        persona: "teacher",
      })
    );
  });
});
