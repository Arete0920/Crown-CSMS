/* global process, console */

import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const registryPath = path.join(root, 'src/config/dashboardRegistry.js');

function fail(message) {
  console.error(`FAIL: ${message}`);
  process.exitCode = 1;
}

function pass(message) {
  console.log(`PASS: ${message}`);
}

if (!fs.existsSync(registryPath)) {
  fail(`Missing dashboard registry: ${registryPath}`);
  process.exit(1);
}

const registrySource = fs.readFileSync(registryPath, 'utf8');

const requiredDashboardLabels = [
  'Attendance',
  'Billing',
  'Financial Aid',
  'Registrar',
  'Scheduling',
  'Gradebook',
  'Student Care',
  'Activities & Athletics',
  'Communications',
  'Admissions',
  'HR',
  'Facilities',
  'Health Office',
  'Transportation',
  'Food Service',
  'IT Support',
  'Fine Arts',
  'Library / Media',
  'Extended Care',
  'Safety / Security',
  'Curriculum / PD Hub',
  'Chaplain / Spiritual Life',
  'Advancement Operations',
  'Volunteer Management',
  'Alumni Relations',
  'Network Benchmarking',
  'Implementation Success',
  'Data Migration',
  'Integrations / Automation',
  'Compliance / Audit',
  'Revenue Operations',
  'Release Reliability',
  'Dashboard Certification Center',
];

for (const label of requiredDashboardLabels) {
  if (!registrySource.includes(`label: '${label}'`) && !registrySource.includes(`label: "${label}"`)) {
    fail(`Dashboard registry missing label: ${label}`);
  } else {
    pass(`Dashboard registered: ${label}`);
  }
}

const pageImportMatches = [...registrySource.matchAll(/import\s+(\w+)\s+from\s+'([^']+)'/g)];

for (const [, importName, importPath] of pageImportMatches) {
  if (!importPath.startsWith('../pages/')) continue;

  const absPath = path.join(root, 'src/config', importPath);
  const jsxPath = `${absPath}.jsx`;
  const jsPath = `${absPath}.js`;

  if (!fs.existsSync(jsxPath) && !fs.existsSync(jsPath)) {
    fail(`Missing dashboard page for import ${importName}: ${importPath}`);
  }
}

if (process.exitCode) {
  console.error('\nDashboard completeness guard failed.');
  process.exit(process.exitCode);
}

console.log('\nDashboard completeness guard passed.');
