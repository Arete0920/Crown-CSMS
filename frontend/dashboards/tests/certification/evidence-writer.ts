import fs from "node:fs";
import path from "node:path";
import type { NetworkObservation } from "./network-recorder";

type AccessibilityViolationDetail = {
  id: string;
  impact: string | null;
  description: string;
  help: string;
  nodes: number;
  nodeDetails: Array<{
    target: string[];
    html: string;
    failureSummary: string;
  }>;
};

export type CertificationResultRow = {
  id: string;
  label: string;
  kind: string;
  route: string;
  persona: string;
  tenant: string;
  status: "PASS" | "FAIL";
  errors: string[];
  screenshotPath?: string;
  networkObserved: number;
  networkFailed: number;
  failedRequests: NetworkObservation[];
  consoleErrors: string[];
  missingExpectedApis: string[];
  accessibilityViolationDetails: AccessibilityViolationDetail[];
  accessibilityViolations: number;
  criticalAccessibilityViolations: number;
};

export const evidenceRoot = path.resolve(
  process.cwd(),
  "../../audit-artifacts/production-certification/current",
);

const expectedEvidenceRootSuffix = path.join("audit-artifacts", "production-certification", "current");
const expectedCwdSuffix = path.join("frontend", "dashboards");

const resultsPath = path.join(evidenceRoot, "certification-matrix.json");
const routeCsvPath = path.join(evidenceRoot, "route-results.csv");
const summaryPath = path.join(evidenceRoot, "certification-summary.md");
const failedRequestsPath = path.join(evidenceRoot, "failed-requests.json");
const consoleErrorsPath = path.join(evidenceRoot, "console-errors.json");
const accessibilityViolationsPath = path.join(evidenceRoot, "accessibility-violations.json");

export function resetEvidenceRoot(): void {
  const normalizedCwd = path.normalize(process.cwd());
  if (!normalizedCwd.endsWith(expectedCwdSuffix)) {
    throw new Error(`Refusing to delete evidence root outside frontend/dashboards cwd: ${process.cwd()}`);
  }

  if (!evidenceRoot.endsWith(expectedEvidenceRootSuffix)) {
    throw new Error(`Refusing to delete unexpected evidence root: ${evidenceRoot}`);
  }

  fs.rmSync(evidenceRoot, { recursive: true, force: true });
  fs.mkdirSync(path.join(evidenceRoot, "screenshots"), { recursive: true });
  fs.mkdirSync(path.join(evidenceRoot, "traces"), { recursive: true });
  fs.mkdirSync(path.join(evidenceRoot, "har"), { recursive: true });
  fs.writeFileSync(resultsPath, "[]\n");
  fs.writeFileSync(failedRequestsPath, "[]\n");
  fs.writeFileSync(consoleErrorsPath, "[]\n");
  fs.writeFileSync(accessibilityViolationsPath, "[]\n");
  fs.writeFileSync(
    routeCsvPath,
    "id,label,kind,route,persona,tenant,status,networkObserved,networkFailed,consoleErrors,missingExpectedApis,accessibilityViolations,criticalAccessibilityViolations,criticalViolationIds,errors\n",
  );
}

export function screenshotPathFor(id: string, persona: string, tenant: string): string {
  const safe = `${id}__${persona}__${tenant}`.replace(/[^a-zA-Z0-9_-]/g, "_");
  return path.join(evidenceRoot, "screenshots", `${safe}.png`);
}

export function appendCertificationResult(row: CertificationResultRow): void {
  const prior = JSON.parse(fs.readFileSync(resultsPath, "utf8")) as CertificationResultRow[];
  prior.push(row);
  fs.writeFileSync(resultsPath, `${JSON.stringify(prior, null, 2)}\n`);

  if (row.failedRequests.length > 0) {
    const failedRequests = JSON.parse(fs.readFileSync(failedRequestsPath, "utf8")) as Array<Record<string, unknown>>;
    failedRequests.push({
      id: row.id,
      route: row.route,
      persona: row.persona,
      tenant: row.tenant,
      failedRequests: row.failedRequests,
    });
    fs.writeFileSync(failedRequestsPath, `${JSON.stringify(failedRequests, null, 2)}\n`);
  }

  if (row.consoleErrors.length > 0) {
    const consoleErrors = JSON.parse(fs.readFileSync(consoleErrorsPath, "utf8")) as Array<Record<string, unknown>>;
    consoleErrors.push({
      id: row.id,
      route: row.route,
      persona: row.persona,
      tenant: row.tenant,
      consoleErrors: row.consoleErrors,
    });
    fs.writeFileSync(consoleErrorsPath, `${JSON.stringify(consoleErrors, null, 2)}\n`);
  }

  if (row.accessibilityViolationDetails.length > 0) {
    const accessibilityViolations = JSON.parse(fs.readFileSync(accessibilityViolationsPath, "utf8")) as Array<Record<string, unknown>>;
    accessibilityViolations.push({
      id: row.id,
      route: row.route,
      persona: row.persona,
      tenant: row.tenant,
      criticalOrSerious: row.accessibilityViolationDetails.filter(
        (violation) => violation.impact === "critical" || violation.impact === "serious",
      ),
      all: row.accessibilityViolationDetails,
    });
    fs.writeFileSync(accessibilityViolationsPath, `${JSON.stringify(accessibilityViolations, null, 2)}\n`);
  }

  const criticalIds = row.accessibilityViolationDetails
    .filter((violation) => violation.impact === "critical" || violation.impact === "serious")
    .map((violation) => violation.id)
    .join(" | ");

  const csvRow = [
    row.id,
    row.label,
    row.kind,
    row.route,
    row.persona,
    row.tenant,
    row.status,
    row.networkObserved,
    row.networkFailed,
    row.consoleErrors.length,
    row.missingExpectedApis.join(" | "),
    row.accessibilityViolations,
    row.criticalAccessibilityViolations,
    criticalIds,
    row.errors.join(" | "),
  ].map((value) => `"${String(value).replace(/"/g, '""')}"`).join(",");

  fs.appendFileSync(routeCsvPath, `${csvRow}\n`);
}

export function loadCertificationResults(): CertificationResultRow[] {
  if (!fs.existsSync(resultsPath)) {
    return [];
  }

  return JSON.parse(fs.readFileSync(resultsPath, "utf8")) as CertificationResultRow[];
}

export function writeCertificationSummary(): void {
  const rows = loadCertificationResults();
  const failed = rows.filter((row) => row.status === "FAIL");
  const criticalA11y = rows.reduce((sum, row) => sum + row.criticalAccessibilityViolations, 0);
  const failedNetwork = rows.reduce((sum, row) => sum + row.networkFailed, 0);
  const consoleErrorCount = rows.reduce((sum, row) => sum + row.consoleErrors.length, 0);

  const lines = [
    "# CROWN Live Runtime Production Certification Summary",
    "",
    `Status: **${failed.length === 0 ? "PASS" : "FAIL"}**`,
    "",
    `Total checks: ${rows.length}`,
    `Passed: ${rows.length - failed.length}`,
    `Failed: ${failed.length}`,
    `Failed network observations: ${failedNetwork}`,
    `Console errors: ${consoleErrorCount}`,
    `Critical/serious accessibility violations: ${criticalA11y}`,
    "",
    "## Failed checks",
    "",
    ...(
      failed.length === 0
        ? ["None."]
        : failed.map((row) => `- ${row.id} / ${row.persona} / ${row.tenant}: ${row.errors.join("; ")}`)
    ),
    "",
    "## Failed request detail",
    "",
    ...rows.flatMap((row) => row.failedRequests.map((request) => (
      `- ${row.id} / ${row.persona} / ${row.tenant}: ${request.method ?? "GET"} ${request.url} -> ${request.status ?? request.failure ?? "unknown failure"}`
    ))),
    "",
    "## Console error detail",
    "",
    ...rows.flatMap((row) => row.consoleErrors.map((message) => (
      `- ${row.id} / ${row.persona} / ${row.tenant}: ${message}`
    ))),
    "",
    "## Accessibility violation detail",
    "",
    ...rows.flatMap((row) => row.accessibilityViolationDetails
      .filter((violation) => violation.impact === "critical" || violation.impact === "serious")
      .map((violation) => (
        `- ${row.id} / ${row.persona} / ${row.tenant}: ${violation.id} [${violation.impact ?? "unknown"}] - ${violation.help} (nodes: ${violation.nodes})${violation.nodeDetails[0] ? ` target=${violation.nodeDetails[0].target.join(" > ")} failure=${violation.nodeDetails[0].failureSummary.replace(/\s+/g, " ").trim()}` : ""}`
      ))),
    "",
    "## Evidence files",
    "",
    "- certification-matrix.json",
    "- route-results.csv",
    "- failed-requests.json",
    "- console-errors.json",
    "- accessibility-violations.json",
    "- screenshots/",
    "- playwright-report/",
    "- traces/ (retained on failure by Playwright)",
    "",
  ];

  fs.writeFileSync(summaryPath, lines.join("\n"));
}
