import { describe, expect, it } from 'vitest';
import { DASHBOARD_REGISTRY } from './dashboardRegistry';
import { DASHBOARD_CERTIFICATION_REGISTRY } from './dashboardCertificationRegistry';

describe('dashboard certification registry', () => {
  it('covers every dashboard key', () => {
    DASHBOARD_REGISTRY.forEach((dashboard) => {
      expect(DASHBOARD_CERTIFICATION_REGISTRY[dashboard.key]).toBeTruthy();
    });
  });

  it('uses supported statuses only', () => {
    const allowed = new Set(['scaffold', 'hybrid', 'live', 'certified']);

    Object.values(DASHBOARD_CERTIFICATION_REGISTRY).forEach((entry) => {
      expect(allowed.has(entry.status)).toBe(true);
    });
  });
});
