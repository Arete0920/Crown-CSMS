const fs = require("node:fs");
const path = require("node:path");

const targetFiles = [
  "frontend/dashboards/src/pages/Student360Page.jsx",
  "frontend/dashboards/src/pages/RoleDashboardPage.jsx",
  "frontend/dashboards/src/pages/TranscriptRO.jsx",
];

function safeId(base, n) {
  return `${base}-${n}`.toLowerCase().replaceAll(/[^a-z0-9_-]/g, "-");
}

for (const rel of targetFiles) {
  const file = path.resolve(rel);
  if (!fs.existsSync(file)) {
    console.log(`skip_missing ${rel}`);
    continue;
  }

  let text = fs.readFileSync(file, "utf8");
  const lines = text.split(/\r?\n/);
  let changed = 0;

  for (let i = 0; i < lines.length - 1; i++) {
    const labelLine = lines[i];
    const nextLine = lines[i + 1];

    const plainLabel =
      /<label(?![^>]*htmlFor=)(?![^>]*aria-label=)([^>]*)>/.test(labelLine);

    const plainControl =
      /<(input|select|textarea)(?![^>]*id=)([^>]*)>/.test(nextLine);

    if (!plainLabel || !plainControl) continue;

    const labelTextMatch = labelLine.match(/<label[^>]*>(.*?)<\/label>/);
    const labelText = labelTextMatch ? labelTextMatch[1].replace(/[<>&"]/g, "").trim() : "field";
    const id = safeId(labelText || "field", i + 1);

    lines[i] = labelLine.replace("<label", `<label htmlFor="${id}"`);
    lines[i + 1] = nextLine.replace(
      /<(input|select|textarea)\b/,
      `<$1 id="${id}"`
    );

    changed++;
  }

  if (changed > 0) {
    fs.writeFileSync(file, lines.join("\n"), "utf8");
  }

  console.log(`${rel} changed=${changed}`);
}

