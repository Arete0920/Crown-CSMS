import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const ROOT = path.resolve(process.cwd(), 'src');
const REPORT_PATH = path.resolve(process.cwd(), 'visual-system-report.json');
const AUTHORITATIVE = path.normalize('styles/crown-theme.css');
const EXTENSIONS = new Set(['.js', '.jsx', '.ts', '.tsx', '.css']);
const COLOR = /#[0-9a-fA-F]{3,8}\b|\brgba?\([^)]*\)|\bhsla?\([^)]*\)/g;
const TOKEN = /--crown-[a-z0-9-]+\s*:/gi;
const CSS_FONT = /font-family\s*:\s*([^;}{]+)/gi;
const INLINE_FONT = /fontFamily\s*:\s*(['"`])([^'"`]+)\1/g;
const ALLOWED_CSS_FONT = /^var\(--crown-font(?:-[a-z0-9-]+)?\)$/i;
const ALLOWED_INLINE_FONT = /^(?:inherit|var\(--crown-font(?:-[a-z0-9-]+)?\))$/i;

function walk(dir) {
return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
const full = path.join(dir, entry.name);
if (entry.isDirectory()) return walk(full);
return EXTENSIONS.has(path.extname(entry.name)) ? [full] : [];
});
}
function lineFor(text, index) { return text.slice(0, index).split('\n').length; }
function finding(rule, file, text, match, value = match[0]) {
return { severity: 'error', rule, file, line: lineFor(text, match.index), value };
}
function rootOnly(text) {
const start = text.indexOf(':root');
if (start < 0) return false;
const open = text.indexOf('{', start);
let depth = 0;
for (let index = open; index < text.length; index += 1) {
if (text[index] === '{') depth += 1;
if (text[index] === '}') {
depth -= 1;
if (depth === 0) {
const remainder = text.slice(index + 1).replace(/\/\*[\s\S]*?\*\//g, '').trim();
return remainder.length === 0;
}
}
}
return false;
}

const findings = [];
for (const file of walk(ROOT)) {
const relative = path.normalize(path.relative(ROOT, file));
const text = fs.readFileSync(file, 'utf8');
if (relative === AUTHORITATIVE) {
if (!rootOnly(text)) findings.push({ severity: 'error', rule: 'theme-authority-violation', file: relative, line: 1, value: 'crown-theme.css must contain tokens only' });
continue;
}
for (const match of text.matchAll(TOKEN)) findings.push(finding('duplicate-crown-token', relative, text, match));
for (const match of text.matchAll(COLOR)) findings.push(finding('raw-color-literal', relative, text, match));
if (relative.endsWith('.css')) {
for (const match of text.matchAll(CSS_FONT)) {
const value = match[1].trim();
if (!ALLOWED_CSS_FONT.test(value)) findings.push(finding('font-family-drift', relative, text, match, value));
}
} else {
for (const match of text.matchAll(INLINE_FONT)) {
const value = match[2].trim();
if (!ALLOWED_INLINE_FONT.test(value)) findings.push(finding('inline-font-family-drift', relative, text, match, value));
}
}
}
const counts = findings.reduce((result, item) => {
result[item.rule] = (result[item.rule] || 0) + 1;
return result;
}, {});
fs.writeFileSync(REPORT_PATH, `${JSON.stringify({ generated_at: new Date().toISOString(), counts, findings }, null, 2)}\n`);
console.log(`CROWN visual-system scan: ${findings.length} violation(s)`);
for (const [rule, count] of Object.entries(counts).sort()) console.log(`${rule}: ${count}`);
if (findings.length) {
for (const item of findings) console.error(`ERROR ${item.rule} ${item.file}:${item.line} ${item.value}`);
process.exit(1);
}
