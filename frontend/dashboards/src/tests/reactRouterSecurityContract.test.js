import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { describe, expect, it } from 'vitest';

const dashboardRoot = process.cwd();
const sourceRoot = path.join(dashboardRoot, 'src');
const forbiddenPackage = ['react', 'router', 'dom'].join('-');
const sourceExtensions = new Set(['.js', '.jsx', '.ts', '.tsx']);

function collectSourceFiles(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const entryPath = path.join(directory, entry.name);
    if (entry.isDirectory()) return collectSourceFiles(entryPath);
    return sourceExtensions.has(path.extname(entry.name)) ? [entryPath] : [];
  });
}

describe('React Router security dependency contract', () => {
  it('pins the patched manifest and lockfile dependency graph', () => {
    const manifest = JSON.parse(fs.readFileSync(path.join(dashboardRoot, 'package.json'), 'utf8'));
    const lockfile = JSON.parse(fs.readFileSync(path.join(dashboardRoot, 'package-lock.json'), 'utf8'));
    expect(manifest.dependencies['react-router']).toBe('8.4.0');
    expect(manifest.dependencies).not.toHaveProperty(forbiddenPackage);
    expect(manifest.dependencies.react).toBe('19.3.0');
    expect(manifest.dependencies['react-dom']).toBe('19.3.0');
    expect(manifest.dependencies['@azure/msal-browser']).toBe('5.23.0');
    expect(manifest.dependencies['@azure/msal-react']).toBe('5.7.1');
    expect(manifest.overrides.postcss).toBe('8.5.23');
    expect(lockfile.packages['node_modules/react-router'].version).toBe('8.4.0');
    expect(lockfile.packages).not.toHaveProperty(`node_modules/${forbiddenPackage}`);
    expect(lockfile.packages['node_modules/postcss'].version).toBe('8.5.23');
  });

  it('contains no source imports from the removed compatibility package', () => {
    const offenders = collectSourceFiles(sourceRoot)
      .filter((filePath) => filePath !== import.meta.filename)
      .filter((filePath) => fs.readFileSync(filePath, 'utf8').includes(forbiddenPackage))
      .map((filePath) => path.relative(dashboardRoot, filePath));
    expect(offenders).toEqual([]);
  });

  it('loads RouterProvider from the DOM-specific entrypoint', () => {
    const main = fs.readFileSync(path.join(sourceRoot, 'main.jsx'), 'utf8');
    expect(main).toContain("from 'react-router/dom'");
  });
});