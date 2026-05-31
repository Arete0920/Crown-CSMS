import { describe, expect, it } from 'vitest';

import { PATHS } from '../routes/paths';
import { navItems } from '../components/navigation/navItems';
import { DASHBOARD_REGISTRY } from '../config/dashboardRegistry';
import { getOwnedShellPaths } from '../config/shellOwnership';

describe('summer camp contract', () => {
  it('defines required Summer Camp path constants', () => {
    expect(PATHS.SUMMER_CAMP_DASHBOARD).toBe('/summer-camp-dashboard');
    expect(PATHS.SUMMER_CAMP_ROSTER).toBe('/summer-camp-dashboard/roster');
    expect(PATHS.SUMMER_CAMP_SETUP).toBe('/summer-camp-dashboard/setup');
  });

  it('registers Summer Camp in the dashboard registry', () => {
    const entry = DASHBOARD_REGISTRY.find((item) => item.key === 'summer-camp');

    expect(entry).toBeDefined();
    expect(entry?.path).toBe(PATHS.SUMMER_CAMP_DASHBOARD);
    expect(entry?.roles || entry?.allowedRoles || []).toContain('summer_camp_coordinator');
  });

  it('surfaces Summer Camp in navigation', () => {
    const summerCampNav = navItems.find((item) => item.label === 'Summer Camp');

    expect(summerCampNav).toBeDefined();
    expect(summerCampNav?.href).toBe(PATHS.SUMMER_CAMP_DASHBOARD);
  });

  it('marks Summer Camp routes as shell-owned', () => {
    const owned = getOwnedShellPaths();

    expect(owned).toContain(PATHS.SUMMER_CAMP_DASHBOARD);
    expect(owned).toContain(PATHS.SUMMER_CAMP_ROSTER);
    expect(owned).toContain(PATHS.SUMMER_CAMP_SETUP);
  });
});
