import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(scriptDir, '..', '..');
const filePath = path.join(
  root,
  'frontend',
  'dashboards',
  'src',
  'config',
  'apiContracts.js',
);

if (!fs.existsSync(filePath)) {
  console.error('API CONTRACT VERIFY FAIL: apiContracts.js missing');
  process.exit(1);
}

const content = fs.readFileSync(filePath, 'utf8');

const requiredKeys = [
  'admissions.applications.list',
  'admissions.enroll',
  'finance.invoices.list',
  'communications.threads.list',
  'communications.threads.detail',
  'system.health',
];

for (const key of requiredKeys) {
  if (!content.includes(`'${key}'`) && !content.includes(`\"${key}\"`)) {
    console.error(`API CONTRACT VERIFY FAIL: missing contract key ${key}`);
    process.exit(1);
  }
}

console.log('API CONTRACT VERIFY PASS');
