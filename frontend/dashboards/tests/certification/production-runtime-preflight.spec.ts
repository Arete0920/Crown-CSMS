import fs from "fs";
import path from "path";

import { test, expect } from "@playwright/test";

const LIVE_FRONTEND_URL = requireLiveUrl("CROWN_LIVE_FRONTEND_URL");
const LIVE_API_BASE_URL = requireLiveUrl("CROWN_LIVE_API_BASE_URL").replace(/\/+$/, "");
const EXPECTED_DEPLOYED_SHA = (process.env.CROWN_EXPECTED_DEPLOYED_SHA || process.env.GITHUB_SHA || "").trim();
const SKIP_SHA_CHECK = process.env.CROWN_SKIP_DEPLOYED_SHA_CHECK === "1";

const evidenceRoot = path.resolve(process.cwd(), "../../audit-artifacts/production-certification/current");

function requireLiveUrl(name: string): string {
  const raw = process.env[name];
  if (!raw) {
    throw new Error(`${name} is required for live runtime certification.`);
  }

  const parsed = new URL(raw);
  const forbiddenHosts = new Set(["localhost", "127.0.0.1", "0.0.0.0"]);
  if (forbiddenHosts.has(parsed.hostname) || parsed.hostname.endsWith(".local")) {
    throw new Error(`${name} must target deployed runtime, not local host: ${raw}`);
  }

  return parsed.toString().replace(/\/+$/, "");
}

function shaMatches(actual: string, expected: string): boolean {
  const cleanActual = String(actual || "").trim();
  const cleanExpected = String(expected || "").trim();
  if (!cleanActual || !cleanExpected) {
    return false;
  }
  if (cleanActual === cleanExpected) {
    return true;
  }
  const minComparableLength = Math.min(cleanActual.length, cleanExpected.length);
  if (minComparableLength < 7) {
    return false;
  }
  return cleanActual.startsWith(cleanExpected) || cleanExpected.startsWith(cleanActual);
}

async function fetchJson(url: string): Promise<{ ok: boolean; status: number; payload: any; error?: string }> {
  try {
    const response = await globalThis.fetch(url, {
      method: "GET",
      headers: { Accept: "application/json" },
    });
    const text = await response.text();
    let payload: any = text;
    try {
      payload = text ? JSON.parse(text) : null;
    } catch {
      // Keep raw text for diagnostics.
    }
    return { ok: response.ok, status: response.status, payload };
  } catch (error) {
    return {
      ok: false,
      status: 0,
      payload: null,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

function writeFailureEvidence(errors: string[]): void {
  fs.mkdirSync(evidenceRoot, { recursive: true });
  fs.writeFileSync(
    path.join(evidenceRoot, "certification-summary.md"),
    [
      "# CROWN Live Runtime Production Certification Summary",
      "",
      "Status: **FAIL**",
      "",
      "Total checks: 1",
      "Passed: 0",
      "Failed: 1",
      "Failed network observations: 0",
      "Console errors: 0",
      "Critical/serious accessibility violations: 0",
      "",
      "## Failed checks",
      "",
      `- deployed-runtime-preflight / same-sha / azure: ${errors.join("; ")}`,
      "",
    ].join("\n"),
    "utf8",
  );
  fs.writeFileSync(
    path.join(evidenceRoot, "certification-matrix.json"),
    JSON.stringify(
      {
        status: "FAIL",
        checks: [
          {
            id: "deployed-runtime-preflight",
            status: "FAIL",
            errors,
          },
        ],
      },
      null,
      2,
    ) + "\n",
    "utf8",
  );
  fs.writeFileSync(
    path.join(evidenceRoot, "route-results.csv"),
    [
      "id,label,kind,route,persona,tenant,status,networkObserved,networkFailed,consoleErrors,missingExpectedApis,accessibilityViolations,criticalAccessibilityViolations,criticalViolationIds,errors",
      `deployed-runtime-preflight,Deployed runtime preflight,preflight,/same-sha,same-sha,azure,FAIL,0,0,0,,0,0,,"${errors.join(" | ").replace(/"/g, '""')}"`,
    ].join("\n") + "\n",
    "utf8",
  );
}

test.describe.configure({ mode: "serial", retries: 0 });

test("deployed runtime build SHA matches certification SHA", async () => {
  test.skip(SKIP_SHA_CHECK, "CROWN_SKIP_DEPLOYED_SHA_CHECK=1 explicitly disables deployed-runtime SHA enforcement.");

  const errors: string[] = [];
  if (!EXPECTED_DEPLOYED_SHA) {
    errors.push("DEPLOYED_RUNTIME_PREFLIGHT: EXPECTED_SHA_MISSING");
  }

  const apiUrl = `${LIVE_API_BASE_URL}/api/v1/version/`;
  const apiVersion = await fetchJson(apiUrl);
  const apiSha = String(apiVersion.payload?.build_sha || "").trim();

  if (!apiVersion.ok) {
    errors.push(`DEPLOYED_RUNTIME_PREFLIGHT: API_VERSION_UNAVAILABLE status=${apiVersion.status} url=${apiUrl} error=${apiVersion.error || ""}`);
  } else if (!shaMatches(apiSha, EXPECTED_DEPLOYED_SHA)) {
    errors.push(`DEPLOYED_RUNTIME_PREFLIGHT: API_SHA_MISMATCH expected=${EXPECTED_DEPLOYED_SHA} actual=${apiSha || "missing"} url=${apiUrl}`);
  }

  const frontendUrl = new URL("/build.json", `${LIVE_FRONTEND_URL}/`).toString();
  const frontendBuild = await fetchJson(frontendUrl);
  const frontendSha = String(frontendBuild.payload?.build_sha || "").trim();

  if (!frontendBuild.ok) {
    errors.push(`DEPLOYED_RUNTIME_PREFLIGHT: FRONTEND_BUILD_UNAVAILABLE status=${frontendBuild.status} url=${frontendUrl} error=${frontendBuild.error || ""}`);
  } else if (!shaMatches(frontendSha, EXPECTED_DEPLOYED_SHA)) {
    errors.push(`DEPLOYED_RUNTIME_PREFLIGHT: FRONTEND_SHA_MISMATCH expected=${EXPECTED_DEPLOYED_SHA} actual=${frontendSha || "missing"} url=${frontendUrl}`);
  }

  if (errors.length > 0) {
    writeFailureEvidence(errors);
  }

  expect(errors, errors.join("\n")).toEqual([]);
});
