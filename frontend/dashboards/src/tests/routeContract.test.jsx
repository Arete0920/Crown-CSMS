import { describe, expect, it } from 'vitest';
import { PATHS } from '../routes/paths';
import { DASHBOARD_REGISTRY } from '../config/dashboardRegistry';

describe('route contract', () => {
  it('all dashboard registry paths are unique', () => {
    const paths = DASHBOARD_REGISTRY.map((item) => item.path).filter(Boolean);
    const unique = new Set(paths);
    expect(unique.size).toBe(paths.length);
  });

  it('all registry paths begin with slash', () => {
    for (const item of DASHBOARD_REGISTRY) {
      if (!item.path) continue;
      expect(item.path.startsWith('/')).toBe(true);
    }
  });

  it('core path constants exist', () => {
    expect(PATHS.HOME).toBeDefined();
    expect(PATHS.ADMISSIONS).toBeDefined();
    expect(PATHS.BILLING).toBeDefined();
    expect(PATHS.FINANCIAL_AID).toBeDefined();
    expect(PATHS.ATTENDANCE).toBeDefined();
    expect(PATHS.GRADEBOOK).toBeDefined();
    expect(PATHS.SYSTEM_STATUS).toBeDefined();
  });
});
