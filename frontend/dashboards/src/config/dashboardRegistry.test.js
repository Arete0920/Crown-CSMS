import { describe, expect, it } from 'vitest';
import { DASHBOARD_REGISTRY, hasRouteAccess, normalizeRoles } from './dashboardRegistry';
import { validateDashboardRegistry } from './validateDashboardRegistry';

describe('dashboard registry', () => {
  it('is valid', () => {
    expect(validateDashboardRegistry(DASHBOARD_REGISTRY)).toBe(true);
  });

  it('has unique keys', () => {
    const keys = DASHBOARD_REGISTRY.map((item) => item.key);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it('has unique paths', () => {
    const paths = DASHBOARD_REGISTRY.map((item) => item.path);
    expect(new Set(paths).size).toBe(paths.length);
  });

  it('has at least one allowed role for each dashboard', () => {
    DASHBOARD_REGISTRY.forEach((item) => {
      expect(Array.isArray(item.allowedRoles)).toBe(true);
      expect(item.allowedRoles.length).toBeGreaterThan(0);
    });
  });

  it('uses dashboard-style route names', () => {
    DASHBOARD_REGISTRY.forEach((item) => {
      expect(item.path.startsWith('/')).toBe(true);
      expect(item.path.endsWith('-dashboard') || item.path === '/dashboard-certification-center').toBe(true);
    });
  });

  it('normalizes role aliases used across backend and frontend role vocabularies', () => {
    expect(normalizeRoles(['HEAD_OF_SCHOOL'])).toContain('school_admin');
    expect(normalizeRoles(['facilities'])).toContain('facilities_manager');
    expect(normalizeRoles(['it_support'])).toContain('it');
  });

  it('grants access when role aliases match equivalent roles', () => {
    expect(hasRouteAccess(['facilities'], ['facilities_manager'])).toBe(true);
    expect(hasRouteAccess(['HEAD_OF_SCHOOL'], ['school_admin'])).toBe(true);
    expect(hasRouteAccess(['it'], ['it_support'])).toBe(true);
  });
});
