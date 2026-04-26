/* global process, console */
import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const routes = [
  '/login',
  '/dashboard',
  '/admin',
  '/school-admin',
  '/school-administrator',
  '/teacher',
  '/parent',
  '/student',
  '/admissions',
  '/attendance',
  '/gradebook',
  '/finance',
  '/communications',
];

const stamp = new Date().toISOString().replace(/[-:TZ.]/g, '').slice(0, 14);
const repoRoot = path.resolve(process.cwd(), '..', '..');
const outDir = path.join(repoRoot, 'audit-artifacts', 'crown-launch-ui-takeover', stamp);
await fs.mkdir(outDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1024 } });

for (let i = 0; i < routes.length; i += 1) {
  const route = routes[i];
  const target = `http://127.0.0.1:5173${route}`;
  await page.goto(target, { waitUntil: 'networkidle' });
  const fileSafe = route === '/' ? 'root' : route.replace(/\//g, '_').replace(/^_/, '');
  const outPath = path.join(outDir, `${String(i + 1).padStart(2, '0')}_${fileSafe}.png`);
  await page.screenshot({ path: outPath, fullPage: true });
  console.log(`captured\t${route}\t${outPath}`);
}

await browser.close();
console.log(`artifact_dir\t${outDir}`);
