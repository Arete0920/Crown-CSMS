import { describe, expect, it } from 'vitest';
import { navItems } from '../components/navigation/navItems';
import { DASHBOARD_REGISTRY } from '../config/dashboardRegistry';
import { PATHS } from '../routes/paths';

describe('sidebar contract', () => {
  it('all sidebar hrefs are unique', () => {
    const hrefs = navItems.map((item) => item.href).filter(Boolean);
    const unique = new Set(hrefs);
    expect(unique.size).toBe(hrefs.length);
  });

  it('every sidebar href matches a known registry path or explicit utility path', () => {
    const registryPaths = new Set(DASHBOARD_REGISTRY.map((item) => item.path).filter(Boolean));
    const allowedExtras = new Set([
      PATHS.HOME,
      PATHS.DASHBOARD,
      PATHS.SETTINGS,
      PATHS.PROFILE,
      PATHS.FORBIDDEN,
      PATHS.ADMISSIONS,
      PATHS.ENROLLMENT,
      PATHS.BILLING,
      PATHS.FINANCIAL_AID,
      PATHS.ATTENDANCE,
      PATHS.GRADEBOOK,
      PATHS.COMMUNICATIONS,
      PATHS.REPORTING,
      PATHS.SYSTEM_STATUS,
      PATHS.RELEASE_READINESS,
      PATHS.DEMO_READINESS,
    ]);

    for (const item of navItems) {
      if (!item.href) continue;
      expect(registryPaths.has(item.href) || allowedExtras.has(item.href)).toBe(true);
    }
  });
});
