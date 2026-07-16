import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
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
});
