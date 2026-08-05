import * as console from 'node:console';
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const ROOT = path.resolve(process.cwd(), 'src');
const REPORT_PATH = path.resolve(process.cwd(), 'visual-system-report.json');
const BASELINE_PATH = path.resolve(process.cwd(), 'visual-system-baseline.json');
const WRITE_BASELINE = process.argv.includes('--write-baseline');
const AUTHORITATIVE_TOKEN_FILE = path.normalize('styles/crown-theme.css');
const RAW_COLOR_EXEMPT_FILES = new Set([AUTHORITATIVE_TOKEN_FILE]);
const ALLOWED_FONT_STACK = /Inter\s*,\s*['"]Segoe UI['"]\s*,\s*Roboto\s*,\s*Helvetica\s*,\s*Arial\s*,\s*sans-serif/i;
const EXTENSIONS = new Set(['.js', '.jsx', '.ts', '.tsx', '.css']);
const COLOR_LITERAL = /#[0-9a-fA-F]{3,8}\b|\brgba?\([^)]*\)|\bhsla?\([^)]*\)/g;
const CROWN_TOKEN = /--crown-[a-z0-9-]+\s*:/gi;
const FONT_FAMILY = /font-family\s*:\s*([^;}{]+)/gi;
const INLINE_STYLE = /style\s*=\s*\{\s*\{/g;

function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) return walk(full);
    return EXTENSIONS.has(path.extname(entry.name)) ? [full] : [];
  });
}

function lineFor(text, index) {
  return text.slice(0, index).split('\n').length;
}

if (!fs.existsSync(ROOT)) {
  console.error(`CROWN visual-system scan failed: expected source directory at ${ROOT}. Run this command from frontend/dashboards.`);
  process.exit(1);
}

const findings = [];
for (const file of walk(ROOT)) {
  const relative = path.normalize(path.relative(ROOT, file));
  const text = fs.readFileSync(file, 'utf8');

  for (const match of text.matchAll(CROWN_TOKEN)) {
    if (relative !== AUTHORITATIVE_TOKEN_FILE) {
      findings.push({ severity: 'warning', rule: 'duplicate-crown-token', file: relative, line: lineFor(text, match.index), value: match[0] });
    }
  }

  for (const match of text.matchAll(FONT_FAMILY)) {
    if (!ALLOWED_FONT_STACK.test(match[1])) {
      findings.push({ severity: 'warning', rule: 'font-family-drift', file: relative, line: lineFor(text, match.index), value: match[1].trim() });
    }
  }

  if (!RAW_COLOR_EXEMPT_FILES.has(relative)) {
    for (const match of text.matchAll(COLOR_LITERAL)) {
      const nearby = text.slice(Math.max(0, match.index - 120), match.index + match[0].length + 120);
      const documentedException = /visual-system-exception|chart-series|svg-artwork/i.test(nearby);
      if (!documentedException) {
        findings.push({ severity: 'warning', rule: 'raw-color-literal', file: relative, line: lineFor(text, match.index), value: match[0] });
      }
    }
  }

  if (['.jsx', '.tsx'].includes(path.extname(file))) {
    for (const match of text.matchAll(INLINE_STYLE)) {
      findings.push({ severity: 'warning', rule: 'inline-visual-style', file: relative, line: lineFor(text, match.index), value: 'style={{...}}' });
    }
  }
}

const counts = findings.reduce((result, item) => {
  result[item.rule] = (result[item.rule] || 0) + 1;
  return result;
}, {});
const report = { generated_at: new Date().toISOString(), counts, findings };
fs.writeFileSync(REPORT_PATH, `${JSON.stringify(report, null, 2)}\n`);

if (WRITE_BASELINE) {
  fs.writeFileSync(BASELINE_PATH, `${JSON.stringify({ counts }, null, 2)}\n`);
  console.log(`Wrote visual-system baseline to ${BASELINE_PATH}`);
  process.exit(0);
}

const errors = findings.filter((item) => item.severity === 'error');
const warnings = findings.filter((item) => item.severity === 'warning');
console.log(`CROWN visual-system scan: ${errors.length} error(s), ${warnings.length} migration warning(s)`);
for (const [rule, count] of Object.entries(counts).sort()) console.log(`${rule}: ${count}`);

if (errors.length > 0) {
  for (const item of errors) console.error(`ERROR ${item.rule} ${item.file}:${item.line} ${item.value}`);
  process.exit(1);
}

if (fs.existsSync(BASELINE_PATH)) {
  const baseline = JSON.parse(fs.readFileSync(BASELINE_PATH, 'utf8')).counts || {};
  const regressions = Object.entries(counts).filter(([rule, count]) => count > (baseline[rule] || 0));
  if (regressions.length > 0) {
    for (const [rule, count] of regressions) console.error(`REGRESSION ${rule}: ${count} > baseline ${baseline[rule] || 0}`);
    process.exit(1);
  }
}
