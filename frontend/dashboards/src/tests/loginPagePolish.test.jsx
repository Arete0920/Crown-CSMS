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
  sessionStorage.clear();
  localStorage.clear();
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
  it("renders no-login Heritage preview heading and warning", async () => {
    await renderSandboxLogin();

    expect(screen.getByText("CROWN Heritage Preview")).toBeTruthy();
    expect(
      screen.getByText("A controlled no-login preview of Heritage Christian Academy demo workflows.")
    ).toBeTruthy();
    expect(
      screen.getByText(
        "Choose a role and continue into demo-only CROWN workflows. No password is required for this preview."
      )
    ).toBeTruthy();
    expect(screen.getByText("Use demo data only. Do not enter real school records.")).toBeTruthy();
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

  it("does not render credential fields in sandbox preview mode", async () => {
    await renderSandboxLogin();

    expect(screen.queryByLabelText("Email")).toBeNull();
    expect(screen.queryByLabelText("Password")).toBeNull();
    expect(screen.queryByRole("button", { name: "Use Sandbox Credentials" })).toBeNull();
    expect(screen.getByRole("button", { name: "Continue to Heritage Preview" })).toBeTruthy();
  });

  it("does not expose sandbox preview outside sandbox mode", async () => {
    vi.unstubAllEnvs();
    vi.stubEnv("VITE_DEMO_MODE", "production");
    vi.stubEnv("VITE_SANDBOX_MODE", "0");

    vi.resetModules();
    const { default: LoginPage } = await import("../pages/LoginPage.jsx");
    render(<LoginPage />);

    expect(screen.queryByText("CROWN Heritage Preview")).toBeNull();
    expect(screen.queryByRole("button", { name: "Continue to Heritage Preview" })).toBeNull();
    expect(screen.getByRole("button", { name: "Sign In" })).toBeTruthy();
  });

  it("starts a no-login sandbox session against the configured API base", async () => {
    vi.unstubAllEnvs();
    vi.stubEnv("VITE_DEMO_MODE", "sandbox");
    vi.stubEnv("VITE_SANDBOX_MODE", "1");
    vi.stubEnv("VITE_API_BASE_URL", "https://api.example.test");

    await renderSandboxLogin();

    fireEvent.click(screen.getByRole("button", { name: "Continue to Heritage Preview" }));

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        "https://api.example.test/api/v1/sandbox/session/",
        expect.objectContaining({ method: "POST" }),
      );
    });

    const [, requestInit] = globalThis.fetch.mock.calls.find(
      ([url]) => url === "https://api.example.test/api/v1/sandbox/session/"
    );
    const body = JSON.parse(requestInit.body);
    expect(body.school).toBe("heritage-core");
    expect(body.role).toBeTruthy();

    const tokenCalls = globalThis.fetch.mock.calls.filter(([url]) =>
      String(url).includes("/api/v1/auth/token/")
    );
    expect(tokenCalls.length).toBe(0);
  });


  it("verifies the selected production role against the authenticated school context", async () => {
    vi.unstubAllEnvs();
    vi.stubEnv("VITE_DEMO_MODE", "production");
    vi.stubEnv("VITE_SANDBOX_MODE", "0");
    vi.stubEnv("VITE_API_BASE_URL", "https://api.example.test");

    const fetchMock = vi.fn((url) => {
      if (String(url).endsWith("/api/v1/auth/token/")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ access: "prod-token", refresh: "refresh-token" }),
        });
      }
      if (String(url).endsWith("/api/system/whoami/")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            user: { school_id: "19801b59-8c05-4c84-9312-5d792e4e839d" },
          }),
        });
      }
      if (String(url).endsWith("/api/v1/dashboards/me/")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            school_id: "19801b59-8c05-4c84-9312-5d792e4e839d",
            roles: ["TEACHER"],
          }),
        });
      }
      return Promise.resolve({ ok: false, json: () => Promise.resolve({}) });
    });
    vi.stubGlobal("fetch", fetchMock);

    vi.resetModules();
    const { default: LoginPage } = await import("../pages/LoginPage.jsx");
    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("Role"), { target: { value: "teacher" } });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "teacher@example.test" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "ValidPass1!" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "https://api.example.test/api/system/whoami/",
        expect.objectContaining({
          method: "GET",
          headers: expect.objectContaining({
            Authorization: "Bearer prod-token",
          }),
        }),
      );
      expect(fetchMock).toHaveBeenCalledWith(
        "https://api.example.test/api/v1/dashboards/me/",
        expect.objectContaining({
          method: "GET",
          headers: expect.objectContaining({
            Authorization: "Bearer prod-token",
            "X-School-Id": "19801b59-8c05-4c84-9312-5d792e4e839d",
          }),
        }),
      );
    });
  });

  it("does not expose a browser-selectable school in production", async () => {
    vi.unstubAllEnvs();
    vi.stubEnv("VITE_DEMO_MODE", "production");
    vi.stubEnv("VITE_SANDBOX_MODE", "0");

    vi.resetModules();
    const { default: LoginPage } = await import("../pages/LoginPage.jsx");
    render(<LoginPage />);

    expect(screen.queryByLabelText("School")).toBeNull();
    expect(
      screen.getByText("School context is verified from your authenticated account and cannot be selected in the browser.")
    ).toBeTruthy();
  });

  it("rejects a production role selection that the server did not assign", async () => {
    vi.unstubAllEnvs();
    vi.stubEnv("VITE_DEMO_MODE", "production");
    vi.stubEnv("VITE_SANDBOX_MODE", "0");
    vi.stubEnv("VITE_API_BASE_URL", "https://api.example.test");

    const fetchMock = vi.fn((url) => {
      if (String(url).endsWith("/api/v1/auth/token/")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ access: "prod-token", refresh: "refresh-token" }),
        });
      }
      if (String(url).endsWith("/api/system/whoami/")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            user: { school_id: "19801b59-8c05-4c84-9312-5d792e4e839d" },
          }),
        });
      }
      if (String(url).endsWith("/api/v1/dashboards/me/")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            school_id: "19801b59-8c05-4c84-9312-5d792e4e839d",
            roles: ["TEACHER"],
          }),
        });
      }
      return Promise.resolve({ ok: false, json: () => Promise.resolve({}) });
    });
    vi.stubGlobal("fetch", fetchMock);

    vi.resetModules();
    const { default: LoginPage } = await import("../pages/LoginPage.jsx");
    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("Role"), { target: { value: "head_of_school" } });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "teacher@example.test" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "ValidPass1!" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(screen.getByText("The selected role is not assigned to this account for your authenticated school.")).toBeTruthy();
    });
    expect(sessionStorage.getItem("crown.jwt.access")).toBeNull();
  });

  it("surfaces the approved-link message when the sandbox invite is required", async () => {
    vi.unstubAllEnvs();
    vi.stubEnv("VITE_DEMO_MODE", "sandbox");
    vi.stubEnv("VITE_SANDBOX_MODE", "1");

    vi.stubGlobal("fetch", vi.fn(() =>
      Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ code: "sandbox_invite_required" }),
      })
    ));

    await renderSandboxLogin();

    fireEvent.click(screen.getByRole("button", { name: "Continue to Heritage Preview" }));

    await waitFor(() => {
      expect(
        screen.getByText("Heritage sandbox preview is not currently open. Please use an approved sandbox link.")
      ).toBeTruthy();
    });
  });
});
