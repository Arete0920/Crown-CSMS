import fs from "node:fs";
import path from "node:path";
import { cwd } from "node:process";
import { describe, expect, it } from "vitest";

function loadStaticWebAppConfig() {
  const configPath = path.resolve(cwd(), "public/staticwebapp.config.json");
  return JSON.parse(fs.readFileSync(configPath, "utf8"));
}

describe("static web app security headers", () => {
  it("enforces the browser security baseline", () => {
    const headers = loadStaticWebAppConfig().globalHeaders || {};
    const csp = headers["Content-Security-Policy"] || "";

    expect(headers["X-Content-Type-Options"]).toBe("nosniff");
    expect(headers["Referrer-Policy"]).toBe("strict-origin-when-cross-origin");
    expect(headers["Cross-Origin-Opener-Policy"]).toBe("same-origin");
    expect(headers["Permissions-Policy"]).toContain("camera=()");
    expect(headers["Permissions-Policy"]).toContain("microphone=()");
    expect(csp).toContain("default-src 'self'");
    expect(csp).toContain("object-src 'none'");
    expect(csp).toContain("base-uri 'self'");
    expect(csp).toContain("frame-ancestors 'self'");
    expect(csp).toContain("script-src 'self'");
    expect(csp).not.toContain("script-src 'self' 'unsafe-inline'");
    expect(csp).not.toContain("script-src *");
  });
});
