import { describe, expect, it } from 'vitest';
import { DASHBOARD_REGISTRY } from './dashboardRegistry';
import { DASHBOARD_DATA_REGISTRY } from './dashboardDataRegistry';

describe('dashboard data registry', () => {
  it('covers every dashboard key', () => {
    DASHBOARD_REGISTRY.forEach((dashboard) => {
      expect(DASHBOARD_DATA_REGISTRY[dashboard.key]).toBeTruthy();
    });
  });

  it('every data config has an endpoint', () => {
    Object.values(DASHBOARD_DATA_REGISTRY).forEach((config) => {
      expect(typeof config.endpoint).toBe('string');
      expect(config.endpoint.startsWith('/')).toBe(true);
    });
  });
});
