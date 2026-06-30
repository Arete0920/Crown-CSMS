import AxeBuilder from "@axe-core/playwright";
import type { Page } from "@playwright/test";

export type AccessibilityResult = {
  violationCount: number;
  criticalOrSeriousCount: number;
  violations: Array<{
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
  }>;
};

export async function runAccessibilityCertification(page: Page): Promise<AccessibilityResult> {
  const result = await new AxeBuilder({ page }).analyze();
  const violations = result.violations.map((violation) => ({
    id: violation.id,
    impact: violation.impact ?? null,
    description: violation.description,
    help: violation.help,
    nodes: violation.nodes.length,
    nodeDetails: violation.nodes.map((node) => ({
      target: node.target,
      html: node.html,
      failureSummary: node.failureSummary ?? "",
    })),
  }));

  return {
    violationCount: violations.length,
    criticalOrSeriousCount: violations.filter(
      (violation) => violation.impact === "critical" || violation.impact === "serious",
    ).length,
    violations,
  };
}
