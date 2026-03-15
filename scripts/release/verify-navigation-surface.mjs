import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(scriptDir, '..', '..');
const navItemsPath = path.join(
  root,
  'frontend',
  'dashboards',
  'src',
  'components',
  'navigation',
  'navItems.js',
);

const dashboardRegistryPath = path.join(
  root,
  'frontend',
  'dashboards',
  'src',
  'config',
  'dashboardRegistry.js',
);

if (!fs.existsSync(navItemsPath)) {
  console.error('NAV VERIFY FAIL: navItems.js missing');
  process.exit(1);
}

if (!fs.existsSync(dashboardRegistryPath)) {
  console.error('NAV VERIFY FAIL: dashboardRegistry.js missing');
  process.exit(1);
}

console.log('NAV VERIFY PASS');
