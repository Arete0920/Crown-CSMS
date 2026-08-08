import { describe, expect, it } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function load(relativePath) {
  return readFileSync(path.resolve(__dirname, relativePath), "utf8");
}

describe("canonical frontend API client contracts", () => {
  it("routes Crown navigation through authenticatedFetch", () => {
    const source = load("../components/crown/CrownLayout.jsx");
    expect(source).toContain('import { authenticatedFetch } from "../../utils/authClient.js";');
    expect(source).toContain('authenticatedFetch("/api/v1/nav/")');
    expect(source).not.toContain('globalThis.fetch("/api/v1/nav/"');
    expect(source).not.toContain("function getSchoolId()");
    expect(source).not.toContain("function getToken()");
  });

  it("routes generic dashboard requests through authenticatedFetch", () => {
    const source = load("../api/dashboards.js");
    expect(source).toContain('import { authenticatedFetch } from "../utils/authClient.js";');
    expect(source).toContain("await authenticatedFetch(path");
    expect(source).not.toMatch(/globalThis\.fetch\(\s*["'`]\/api\/dashboards/);
    expect(source).not.toMatch(/fetch\(\s*["'`]\/api\/dashboards/);
  });

  it("routes registry-backed dashboard data through authenticatedJson", () => {
    const source = load("../hooks/useDashboardData.js");
    expect(source).toContain("import { authenticatedJson } from '../utils/authClient.js';");
    expect(source).toContain("await authenticatedJson(config.endpoint");
    expect(source).not.toContain("dashboardFetch");
    expect(source).not.toContain("../api/dashboardClient");
  });

  it("keeps Board Executive protected data on canonical transport with all-or-nothing live provenance", () => {
    const source = load("../hooks/useBoardExecutiveData.js");

    expect(source).toContain('import { authenticatedJson } from "../utils/authClient.js";');
    expect(source).toContain("await Promise.all([");
    expect(source).toContain("authenticatedJson(URLS.kpis)");
    expect(source).toContain("authenticatedJson(URLS.trends)");
    expect(source).toContain("authenticatedJson(URLS.risk)");
    expect(source).toContain("authenticatedJson(URLS.drivers)");
    expect(source).not.toContain("globalThis.fetch");
    expect(source).not.toContain('h["Authorization"]');
    expect(source).not.toContain('h["X-School-Id"]');
    expect(source).not.toContain("Promise.allSettled");
    expect(source).not.toContain("anyLive");
    expect(source).toContain("setData({ kpis, trends, risk, topDrivers });");
    expect(source).toContain("setLive(true);");
    expect(source).toContain("setData(DEMO);");
    expect(source).toContain("setLive(false);");
  });

  it("keeps the compatibility API wrapper on the canonical transport", () => {
    const source = load("../lib/api.js");
    expect(source).toContain("authenticatedFetch, getAccessToken, getSelectedSchoolId");
    expect(source).toContain("return authenticatedFetch(path, opts)");
    expect(source).toContain("return getAccessToken()");
    expect(source).toContain("return getSelectedSchoolId()");
    expect(source).not.toContain("globalThis.fetch");
    expect(source).not.toContain("auth === false");
    expect(source).not.toContain("sessionStorage.getItem");
  });

  it("removes deprecated duplicate transports", () => {
    expect(existsSync(path.resolve(__dirname, "../api/dashboardClient.js"))).toBe(false);
    expect(existsSync(path.resolve(__dirname, "../lib/http.js"))).toBe(false);
  });
});
