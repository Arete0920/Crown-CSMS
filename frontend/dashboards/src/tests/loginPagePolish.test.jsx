// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("axios", () => {
  return {
    default: {
      get: vi.fn((url) => {
        if (url.includes("schools_manifest")) {
          return Promise.resolve({ data: { schools: [] } });
        }
        if (url.includes("heritage_demo_credentials")) {
          return Promise.resolve({
            data: {
              required_personas: [{ key: "school_admin", email: "admin@heritage.example.org" }],
            },
          });
        }
        return Promise.resolve({ data: {} });
      }),
    },
  };
});

beforeEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
  vi.stubEnv("VITE_DEMO_MODE", "sandbox");
  vi.stubEnv("VITE_SANDBOX_MODE", "1");
  vi.stubGlobal("fetch", vi.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ access: "token", school_id: "school-1" }),
    })
  ));
});

afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
});

async function renderSandboxLogin() {
  vi.resetModules();
  const { default: LoginPage } = await import("../pages/LoginPage.jsx");
  render(<LoginPage />);
}

describe("login page polish", () => {
  it("renders sandbox heading and warning", async () => {
    await renderSandboxLogin();

    expect(screen.getByText("Sandbox Environment")).toBeTruthy();
    expect(screen.getByText("Use demo data only. Do not enter real school records.")).toBeTruthy();
    expect(screen.getByText("CROWN Sandbox Access")).toBeTruthy();
    expect(screen.getByText("CROWN")).toBeTruthy();
    expect(screen.getAllByText("Christian School Management Solution").length).toBeGreaterThan(0);
    expect(screen.queryByText("Crown2026")).toBeNull();
    expect(screen.queryByText("Dev JWT Login")).toBeNull();
    expect(screen.queryByText("Offline / Fallback")).toBeNull();
    expect(screen.queryByText("Build: missing")).toBeNull();
  });

  it("shows school selector and role selector with school admin", async () => {
    await renderSandboxLogin();

    const schoolSelect = screen.getByLabelText("School");
    const roleSelect = screen.getByLabelText("Role");

    expect(schoolSelect).toBeTruthy();
    expect(roleSelect).toBeTruthy();

    await waitFor(() => {
      expect(screen.getByRole("option", { name: "Heritage Christian Academy" })).toBeTruthy();
    });

    fireEvent.change(roleSelect, { target: { value: "school_admin" } });
    expect(roleSelect.value).toBe("school_admin");
  });

  it("prefills sandbox credentials and shows sign-in action", async () => {
    await renderSandboxLogin();

    const email = screen.getByLabelText("Email");
    const password = screen.getByLabelText("Password");

    await waitFor(() => {
      expect(email.value).toBe("admin@heritage.example.org");
    });
      expect(password.value).toBe("demo-password");
    expect(screen.getByRole("button", { name: "Use Sandbox Credentials" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Sign In" })).toBeTruthy();
  });

  it("does not expose sandbox fill control outside sandbox mode", async () => {
    vi.unstubAllEnvs();
    vi.stubEnv("VITE_DEMO_MODE", "production");
    vi.stubEnv("VITE_SANDBOX_MODE", "0");

    vi.resetModules();
    const { default: LoginPage } = await import("../pages/LoginPage.jsx");
    render(<LoginPage />);

    expect(screen.queryByText("Sandbox Environment")).toBeNull();
    expect(screen.queryByRole("button", { name: "Use Sandbox Credentials" })).toBeNull();
  });
});
