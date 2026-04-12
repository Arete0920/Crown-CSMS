const fs = require("fs");
const path = require("path");

const targets = [
  "frontend/dashboards/src/pages/Student360Page.jsx",
  "frontend/dashboards/src/pages/RoleDashboardPage.jsx",
  "frontend/dashboards/src/pages/TranscriptRO.jsx",
];

const out = [];

for (const rel of targets) {
  const file = path.resolve(rel);
  if (!fs.existsSync(file)) continue;
  const lines = fs.readFileSync(file, "utf8").split(/\r?\n/);

  lines.forEach((line, idx) => {
    if (/<TextField\b/.test(line) || /<Select\b/.test(line) || /<Autocomplete\b/.test(line)) {
      const hasLabel = /\blabel=/.test(line) || /\baria-label=/.test(line) || /\binputProps=\{\{[^}]*"aria-label"/.test(line);
      if (!hasLabel) {
        out.push(`${rel}:${idx + 1}:${line.trim()}`);
      }
    }
  });
}

fs.mkdirSync("audit-artifacts/frontend-a11y", { recursive: true });
fs.writeFileSync("audit-artifacts/frontend-a11y/04_missing_control_labels.txt", out.join("\n"), "utf8");
console.log(`missing_control_labels=${out.length}`);
