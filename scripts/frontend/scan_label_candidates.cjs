const fs = require("fs");
const path = require("path");

const root = path.resolve("frontend/dashboards/src");
const outDir = path.resolve("audit-artifacts/frontend-a11y");
fs.mkdirSync(outDir, { recursive: true });

const exts = new Set([".js", ".jsx", ".ts", ".tsx"]);
const ignore = new Set(["node_modules", "dist", "build"]);

function walk(dir, files = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (ignore.has(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, files);
    else if (exts.has(path.extname(entry.name))) files.push(full);
  }
  return files;
}

const files = walk(root);
const rows = [];
const likelyWizard = [];

for (const file of files) {
  const rel = path.relative(process.cwd(), file).replace(/\\/g, "/");
  const text = fs.readFileSync(file, "utf8");
  const lines = text.split(/\r?\n/);

  const labelMatches = [];
  lines.forEach((line, idx) => {
    if (/<label\b/i.test(line) || /<Label\b/i.test(line) || /<FormLabel\b/i.test(line)) {
      labelMatches.push({ line: idx + 1, text: line.trim() });
    }
  });

  if (labelMatches.length > 0) {
    rows.push({
      file: rel,
      labels: labelMatches.length,
      firstLine: labelMatches[0].line,
      sample: labelMatches[0].text,
    });
  }

  if (/wizard/i.test(rel)) {
    likelyWizard.push(rel);
  }
}

rows.sort((a, b) => {
  if (b.labels !== a.labels) return b.labels - a.labels;
  return a.file.localeCompare(b.file);
});

fs.writeFileSync(
  path.join(outDir, "01_label_candidates.json"),
  JSON.stringify(rows, null, 2),
  "utf8"
);

fs.writeFileSync(
  path.join(outDir, "02_wizard_files.txt"),
  likelyWizard.join("\n"),
  "utf8"
);

const top = rows
  .filter(r => /wizard|setup|student|transcript|dashboard/i.test(r.file))
  .slice(0, 40)
  .map(r => `${r.labels}\t${r.file}\tline ${r.firstLine}\t${r.sample}`)
  .join("\n");

fs.writeFileSync(
  path.join(outDir, "03_top_label_candidates.txt"),
  top,
  "utf8"
);

console.log(`label_files=${rows.length}`);
console.log(`wizard_files=${likelyWizard.length}`);
