import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { describe, expect, it } from 'vitest';

const dashboardRoot = process.cwd();
const forbiddenPackage = ['react', 'router', 'dom'].join('-');

describe('React Router secure transition contract', () => {
  it('pins the patched manifest and lockfile dependency graph', () => {
    const manifest = JSON.parse(fs.readFileSync(path.join(dashboardRoot, 'package.json'), 'utf8'));
    const lockfile = JSON.parse(fs.readFileSync(path.join(dashboardRoot, 'package-lock.json'), 'utf8'));
    expect(manifest.dependencies['react-router']).toBe('8.3.0');
    expect(manifest.dependencies).not.toHaveProperty(forbiddenPackage);
    expect(manifest.dependencies.react).toBe('19.2.7');
    expect(manifest.dependencies['react-dom']).toBe('19.2.7');
    expect(manifest.dependencies['@azure/msal-browser']).toBe('5.17.1');
    expect(manifest.dependencies['@azure/msal-react']).toBe('5.5.3');
    expect(manifest.overrides.postcss).toBe('8.5.18');
    expect(lockfile.packages['node_modules/react-router'].version).toBe('8.3.0');
    expect(lockfile.packages).not.toHaveProperty(`node_modules/${forbiddenPackage}`);
    expect(lockfile.packages['node_modules/postcss'].version).toBe('8.5.18');
  });

  it('routes remaining compatibility imports through the patched package', () => {
    const vite = fs.readFileSync(path.join(dashboardRoot, 'vite.config.js'), 'utf8');
    expect(vite).toContain("'react-router-dom': 'react-router'");
  });

  it('loads RouterProvider from the DOM-specific entrypoint', () => {
    const main = fs.readFileSync(path.join(dashboardRoot, 'src/main.jsx'), 'utf8');
    expect(main).toContain("from 'react-router/dom'");
  });
});
