import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(scriptDir, '..', '..');
const distDir = path.join(root, 'frontend', 'dashboards', 'dist');
const rcManifestPath = path.join(distDir, 'release-candidate.json');

if (!fs.existsSync(rcManifestPath)) {
  console.error('DEMO PROOF FAIL: release-candidate.json missing');
  process.exit(1);
}

const rcManifest = JSON.parse(fs.readFileSync(rcManifestPath, 'utf8'));

const demoProof = {
  generated_at: new Date().toISOString(),
  build_sha: rcManifest.build_sha,
  build_tag: rcManifest.build_tag,
  build_time: rcManifest.build_time,
  api_base_url: rcManifest.api_base_url,
  checks: {
    release_candidate_manifest_present: true,
  },
};

fs.writeFileSync(
  path.join(distDir, 'demo-proof.json'),
  JSON.stringify(demoProof, null, 2),
  'utf8',
);

console.log('DEMO PROOF PASS');
console.log(JSON.stringify(demoProof, null, 2));
