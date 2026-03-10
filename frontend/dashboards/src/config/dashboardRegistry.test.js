import { describe, expect, it } from 'vitest';
import { DASHBOARD_REGISTRY } from './dashboardRegistry';
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
      expect(item.path.endsWith('-dashboard')).toBe(true);
    });
  });
});
