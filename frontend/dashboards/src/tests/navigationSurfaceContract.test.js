import { describe, expect, it } from 'vitest';
import { navItems } from '../components/navigation/navItems';
import dashboardRegistry from '../config/dashboardRegistry';
import { PATHS } from '../routes/paths';

describe('navigation surface contract', () => {
  it('nav labels are unique', () => {
    const labels = navItems.map((item) => item.label).filter(Boolean);
    expect(new Set(labels).size).toBe(labels.length);
  });

  it('nav hrefs are unique', () => {
    const hrefs = navItems.map((item) => item.href).filter(Boolean);
    expect(new Set(hrefs).size).toBe(hrefs.length);
  });

  it('dashboard registry titles are unique', () => {
    const titles = dashboardRegistry.map((item) => item.title).filter(Boolean);
    expect(new Set(titles).size).toBe(titles.length);
  });

  it('every nav href exists in dashboard registry or is a system page', () => {
    const registryPaths = new Set(dashboardRegistry.map((item) => item.path).filter(Boolean));

    const systemPaths = new Set([
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
      expect(registryPaths.has(item.href) || systemPaths.has(item.href)).toBe(true);
    }
  });
});
