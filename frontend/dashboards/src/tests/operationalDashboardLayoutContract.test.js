import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function load(relativePath) {
  return readFileSync(path.resolve(__dirname, relativePath), "utf8");
}

const TARGET_PATHS = [
  "/academic-support",
  "/communications-director",
  "/library",
  "/pd",
  "/security",
  "/student-services",
];

describe("legacy operational dashboard canonical layout contract", () => {
  it("limits the canonical operational layout bridge to exactly the six verified legacy routes", () => {
    const source = load("../components/crown/CrownLayout.jsx");
    const pathSetDeclaration = source.match(
      /const\s+CANONICAL_OPERATIONAL_DASHBOARD_PATHS\s*=\s*new\s+Set\s*\(\s*\[([\s\S]*?)\]\s*\)\s*;?/
    );

    expect(source).toContain('import "../../styles/operational-dashboard-canonical.css";');
    expect(pathSetDeclaration).not.toBeNull();
    expect(source).toContain('"crown-operational-canonical"');

    const configuredPaths = [
      ...(pathSetDeclaration?.[1] || "").matchAll(/["'](\/[^"']+)["']/g),
    ].map((match) => match[1]);

    expect(configuredPaths).toEqual(TARGET_PATHS);
  });

  it("keeps the repair presentation-only and backed by responsive geometry rules", () => {
    const layout = load("../components/crown/CrownLayout.jsx");
    const css = load("../styles/operational-dashboard-canonical.css");

    expect(layout).toContain("CANONICAL_OPERATIONAL_DASHBOARD_PATHS.has(pathname)");
    expect(css).toContain(".crown-operational-canonical > :first-child");
    expect(css).toContain(".crown-operational-canonical .crown-pagehead");
    expect(css).toContain(".crown-operational-canonical .crown-grid");
    expect(css).toContain(".crown-operational-canonical .crown-card");
    expect(css).toContain("overflow-x: hidden");
    expect(css).toContain("padding: 12px 16px 24px !important");
    expect(css).toContain("flex-direction: column");
    expect(css).toContain("color: var(--crown-text)");
    expect(css).not.toContain("color: var(--crown-ink)");
    expect(css).not.toContain("> div:first-child");
    expect(css).toContain("@media (max-width: 760px)");
    expect(css).toContain("padding: 8px 8px 18px !important");
    expect(css).toContain("grid-column: 1 / -1 !important");

    expect(layout).not.toContain("/api/v1/academic-support/metrics/");
    expect(layout).not.toContain("submitSandboxFeedback");
  });
});
