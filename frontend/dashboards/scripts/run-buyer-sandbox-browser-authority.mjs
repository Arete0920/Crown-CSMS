import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';

const liveUrl = String(process.env.CROWN_LIVE_FRONTEND_URL || '').trim().replace(/\/$/, '');

if (!liveUrl) {
  console.error('ERROR: CROWN_LIVE_FRONTEND_URL is required.');
  console.error('Example: CROWN_LIVE_FRONTEND_URL=https://your-sandbox-host.example npm run certify:buyer-sandbox-browser');
  process.exit(2);
}

let parsed;
try {
  parsed = new URL(liveUrl);
} catch {
  console.error(`ERROR: CROWN_LIVE_FRONTEND_URL is not a valid URL: ${liveUrl}`);
  process.exit(2);
}

if (parsed.protocol !== 'https:' && parsed.hostname !== 'localhost') {
  console.error('ERROR: buyer browser authority requires HTTPS except for localhost development.');
  process.exit(2);
}

const output = process.env.CROWN_BROWSER_AUTHORITY_OUTPUT || resolve('test-results/buyer-sandbox-browser-authority.json');
const args = [
  'playwright',
  'test',
  'tests/certification/buyer-sandbox-browser-authority.spec.ts',
  '--workers=1',
  '--reporter=line',
];

if (process.env.CROWN_DEMO_HEADED === '1') args.push('--headed');

console.log('CROWN BUYER SANDBOX BROWSER AUTHORITY');
console.log(`LIVE_FRONTEND_URL=${liveUrl}`);
console.log(`AUTHORITY_OUTPUT=${output}`);
console.log(`HEADED=${process.env.CROWN_DEMO_HEADED === '1' ? 'yes' : 'no'}`);

const result = spawnSync('npx', args, {
  stdio: 'inherit',
  shell: process.platform === 'win32',
  env: {
    ...process.env,
    CROWN_CERTIFICATION_LIVE_RUNTIME: '1',
    CROWN_LIVE_FRONTEND_URL: liveUrl,
    CROWN_BROWSER_AUTHORITY_OUTPUT: output,
  },
});

if (result.error) {
  console.error(`ERROR: could not launch Playwright: ${result.error.message}`);
  process.exit(2);
}

process.exit(result.status ?? 1);
