import { describe, expect, it } from 'vitest';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function resolvePath(relativePath) {
  return path.resolve(__dirname, relativePath);
}

function read(relativePath) {
  return readFileSync(resolvePath(relativePath), 'utf8');
}

describe('frontend API transport consolidation', () => {
  it('uses authenticatedFetch as the only authentication and tenant transport owner', () => {
    const clientSource = read('../api/client.js');
    const canonicalSource = read('../utils/authClient.js');

    expect(clientSource).toContain('authenticatedFetch');
    expect(clientSource).not.toContain('axios.create');
    expect(canonicalSource).toContain('Authorization');
    expect(canonicalSource).toContain('X-School-Id');
    expect(canonicalSource).toContain('X-Correlation-Id');
    expect(canonicalSource).toContain('VITE_API_BASE_URL');
  });

  it('keeps the compatibility client surface for existing feature modules', () => {
    const clientSource = read('../api/client.js');
    ['request', 'get', 'post', 'put', 'patch', 'delete'].forEach((method) => {
      expect(clientSource).toContain(method);
    });
  });

  it('supports accepted non-2xx responses without duplicating transport logic', () => {
    const clientSource = read('../api/client.js');
    const canonicalSource = read('../utils/authClient.js');
    expect(clientSource).toContain('validateStatus');
    expect(canonicalSource).toContain('validateStatus');
    expect(canonicalSource).toContain('error.response');
  });

  it('preserves migration compatibility for current and legacy token storage', () => {
    const canonicalSource = read('../utils/authClient.js');
    ['crown.jwt.access', 'crown_auth_token', 'access_token', 'crown_auth', 'tokenFromStoredAuth']
      .forEach((storageContract) => expect(canonicalSource).toContain(storageContract));
  });

  it('preserves binary release export responses through the canonical client', () => {
    const clientSource = read('../api/client.js');
    const exportSource = read('../components/release/ReleaseExportButton.tsx');
    expect(clientSource).toContain("responseType === 'blob'");
    expect(clientSource).toContain('response.blob()');
    expect(exportSource).toContain('crownApiClient');
    expect(exportSource).toContain('responseType: "blob"');
    expect(exportSource).not.toContain('releaseApi');
  });

  it('retires the residual release transport and migrates all known consumers', () => {
    const releaseApiPath = resolvePath('../lib/releaseApi.ts');
    const statusSource = read('../components/release/ReleaseStatusMatrix.tsx');
    const exportSource = read('../components/release/ReleaseExportButton.tsx');
    expect(existsSync(releaseApiPath)).toBe(false);
    expect(statusSource).toContain('crownApiClient');
    expect(statusSource).not.toContain('releaseApi');
    expect(exportSource).toContain('crownApiClient');
    expect(exportSource).not.toContain('releaseApi');
  });
});
