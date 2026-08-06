import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const ROOT = path.resolve(process.cwd(), 'src');
const REPORT_PATH = path.resolve(process.cwd(), 'visual-system-report.json');
const TOKEN_FILE = path.normalize('styles/crown-theme.css');
const EXTENSIONS = new Set(['.js', '.jsx', '.ts', '.tsx', '.css']);
const COLOR = /#[0-9a-fA-F]{3,8}\b|\brgba?\([^)]*\)|\bhsla?\([^)]*\)/g;
const TOKEN = /--crown-[a-z0-9-]+\s*:/gi;
const FONT = /font-family\s*:\s*([^;}{]+)/gi;
const FONT_STACK = /Inter\s*,\s*['"]Segoe UI['"]\s*,\s*Roboto\s*,\s*Helvetica\s*,\s*Arial\s*,\s*sans-serif/i;
const FONT_TOKEN = /^var\(--crown-font(?:-[a-z0-9-]+)?\)$/i;
const FONT_EXCEPTIONS = new Map([
  [path.normalize('pages/GradebookRO.jsx'), new Set(['monospace', 'system-ui'])],
]);

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

function allowedFont(file, value) {
  const normalized = value.trim();
  return (
    FONT_STACK.test(normalized) ||
    FONT_TOKEN.test(normalized) ||
    FONT_EXCEPTIONS.get(file)?.has(normalized) ||
    false
  );
}

function visualContexts(text, extension) {
  if (extension === '.css') return [{ text, offset: 0, kind: 'stylesheet' }];
  const result = [];
  for (const match of text.matchAll(/<style(?:\s[^>]*)?>\s*\{`([\s\S]*?)`\}\s*<\/style>/g)) {
    result.push({
      text: match[1],
      offset: match.index + match[0].indexOf(match[1]),
      kind: 'style-template',
    });
  }
  for (const match of text.matchAll(/(?:style|sx)\s*=\s*\{\s*\{([\s\S]*?)\}\s*\}/g)) {
    result.push({
      text: match[1],
      offset: match.index + match[0].indexOf(match[1]),
      kind: 'inline-style',
    });
  }
  return result;
}

if (!fs.existsSync(ROOT)) {
  process.stderr.write('Run this command from frontend/dashboards.\n');
  process.exit(1);
}

const findings = [];
const classifiedExceptions = [];

for (const file of walk(ROOT)) {
  const relative = path.normalize(path.relative(ROOT, file));
  const extension = path.extname(file);
  const text = fs.readFileSync(file, 'utf8');

  for (const match of text.matchAll(TOKEN)) {
    if (relative !== TOKEN_FILE) {
      findings.push({
        severity: 'error',
        rule: 'duplicate-crown-token',
        file: relative,
        line: lineFor(text, match.index),
        value: match[0],
      });
    }
  }

  for (const match of text.matchAll(FONT)) {
    if (!allowedFont(relative, match[1])) {
      findings.push({
        severity: 'error',
        rule: 'font-family-drift',
        file: relative,
        line: lineFor(text, match.index),
        value: match[1].trim(),
      });
    }
  }

  const contexts = visualContexts(text, extension);
  const ranges = contexts.map((item) => [item.offset, item.offset + item.text.length]);

  for (const context of contexts) {
    if (relative === TOKEN_FILE) continue;
    for (const match of context.text.matchAll(COLOR)) {
      findings.push({
        severity: 'error',
        rule: context.kind === 'inline-style' ? 'inline-visual-style' : 'raw-color-literal',
        file: relative,
        line: lineFor(text, context.offset + match.index),
        value: match[0],
      });
    }
  }

  if (extension !== '.css') {
    for (const match of text.matchAll(COLOR)) {
      if (!ranges.some(([start, end]) => match.index >= start && match.index < end)) {
        classifiedExceptions.push({
          rule: 'runtime-chart-svg-theme-color',
          file: relative,
          line: lineFor(text, match.index),
          value: match[0],
        });
      }
    }
  }
}

const counts = {
  'inline-visual-style': 0,
  'raw-color-literal': 0,
  'duplicate-crown-token': 0,
  'font-family-drift': 0,
};
for (const item of findings) counts[item.rule] += 1;

const exceptionCounts = {};
for (const item of classifiedExceptions) {
  exceptionCounts[item.rule] = (exceptionCounts[item.rule] || 0) + 1;
}

fs.writeFileSync(
  REPORT_PATH,
  JSON.stringify(
    {
      schemaVersion: 2,
      generatedAt: new Date().toISOString(),
      policy:
        'CSS and JSX style contexts must consume central tokens. Runtime MUI, chart, SVG, and data-series colors are classified exceptions.',
      counts,
      exceptionCounts,
      findings,
      classifiedExceptions,
    },
    null,
    2
  ) + '\n'
);

process.stdout.write(`CROWN visual-system scan: ${findings.length} blocking finding(s)\n`);
for (const [rule, count] of Object.entries(counts).sort()) {
  process.stdout.write(`${rule}: ${count}\n`);
}
for (const [rule, count] of Object.entries(exceptionCounts).sort()) {
  process.stdout.write(`classified-exception ${rule}: ${count}\n`);
}

if (findings.length) {
  for (const item of findings.slice(0, 200)) {
    process.stderr.write(`ERROR ${item.rule} ${item.file}:${item.line} ${item.value}\n`);
  }
  process.exit(1);
}
