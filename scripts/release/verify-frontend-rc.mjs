import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const frontendDir = path.join(root, 'frontend', 'dashboards');
const distDir = path.join(frontendDir, 'dist');

function fail(message) {
  console.error(`RC VERIFY FAIL: ${message}`);
  process.exit(1);
}

function requireFile(filePath) {
  if (!fs.existsSync(filePath)) {
    fail(`Missing required file: ${filePath}`);
  }
}

function requireDir(dirPath) {
  if (!fs.existsSync(dirPath) || !fs.statSync(dirPath).isDirectory()) {
    fail(`Missing required directory: ${dirPath}`);
  }
}

function requireEnv(name) {
  const value = process.env[name];
  if (!value || !String(value).trim()) {
    fail(`Missing required environment variable: ${name}`);
  }
  return value;
}

requireFile(path.join(frontendDir, 'src', 'routes', 'paths.js'));
requireFile(path.join(frontendDir, 'src', 'components', 'navigation', 'navItems.js'));
requireFile(path.join(frontendDir, 'src', 'components', 'system', 'AppErrorBoundary.jsx'));
requireFile(path.join(frontendDir, 'src', 'pages', 'ReleaseReadinessPage.jsx'));
requireFile(path.join(frontendDir, '.env.local.example'));
requireFile(path.join(frontendDir, 'dist', 'index.html'));

const assetsDir = path.join(distDir, 'assets');
requireDir(assetsDir);

const buildSha = requireEnv('VITE_BUILD_SHA');
const buildTag = requireEnv('VITE_BUILD_TAG');
const buildTime = requireEnv('VITE_BUILD_TIME');
const apiBaseUrl = requireEnv('VITE_API_BASE_URL');

const manifest = {
  build_sha: buildSha,
  build_tag: buildTag,
  build_time: buildTime,
  api_base_url: apiBaseUrl,
  verified_at: new Date().toISOString(),
};

fs.writeFileSync(
  path.join(distDir, 'release-candidate.json'),
  JSON.stringify(manifest, null, 2),
  'utf8',
);

console.log('RC VERIFY PASS');
console.log(JSON.stringify(manifest, null, 2));
