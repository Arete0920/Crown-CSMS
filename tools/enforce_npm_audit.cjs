#!/usr/bin/env node
// Enforces npm audit results (high/critical) with narrow, expiring, documented exceptions.
// Usage: node enforce_npm_audit.cjs <audit.json> <exit-code.txt> <exceptions.json> <directory>
const fs = require('fs');

const [reportPath, exitCodePath, exceptionsPath, directory] = process.argv.slice(2);
const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
const auditExitCode = Number(fs.readFileSync(exitCodePath, 'utf8').trim());
const now = new Date(process.env.AUDIT_NOW || Date.now());

const config = fs.existsSync(exceptionsPath) ? JSON.parse(fs.readFileSync(exceptionsPath, 'utf8')) : { exceptions: [] };
const active = [];
for (const entry of config.exceptions || []) {
  if (entry.directory !== directory) continue;
  if (!(new Date(`${entry.expires}T23:59:59Z`) >= now)) {
    console.log(`NPM_AUDIT_EXCEPTION_EXPIRED advisory=${entry.advisory} expires=${entry.expires}`);
    continue;
  }
  active.push(entry);
}

const isExcepted = (name, value) => {
  const vias = (value.via || []).filter((v) => typeof v !== 'string');
  return active.some((entry) =>
    entry.packages.includes(name) &&
    vias.every((v) => String(v.url || '').endsWith(entry.advisory)) &&
    (value.via || []).filter((v) => typeof v === 'string').every((dep) => entry.packages.includes(dep)));
};

let unexcepted = 0;
for (const [name, value] of Object.entries(report.vulnerabilities || {})) {
  if (!['high', 'critical'].includes(value.severity)) continue;
  const via = (value.via || []).map((v) => typeof v === 'string' ? v : `${v.source}:${v.title}`).join(' | ');
  const fix = value.fixAvailable === true ? 'available' : value.fixAvailable === false ? 'none' : JSON.stringify(value.fixAvailable);
  const excepted = isExcepted(name, value);
  if (!excepted) unexcepted += 1;
  console.log(`NPM_AUDIT_BLOCKER package=${name} severity=${value.severity} direct=${Boolean(value.isDirect)} range=${value.range} fix=${fix} excepted=${excepted} via=${via}`);
}
const counts = report.metadata?.vulnerabilities || {};
console.log(`NPM_AUDIT_COUNTS high=${counts.high || 0} critical=${counts.critical || 0} total=${counts.total || 0} unexcepted=${unexcepted}`);

if (auditExitCode === 0) process.exit(0);
// A non-zero audit exit with no reported high/critical findings is an audit failure, not a pass.
const hasFindings = Object.values(report.vulnerabilities || {}).some((v) => ['high', 'critical'].includes(v.severity));
process.exit(hasFindings && unexcepted === 0 ? 0 : 1);
