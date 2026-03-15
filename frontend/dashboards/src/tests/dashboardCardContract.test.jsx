import { describe, expect, it } from 'vitest';
import dashboardRegistry from '../config/dashboardRegistry';

describe('dashboard registry contract', () => {
  it('all dashboards have a title', () => {
    for (const item of dashboardRegistry) {
      expect(Boolean(item.title)).toBe(true);
    }
  });

  it('all dashboards have a path', () => {
    for (const item of dashboardRegistry) {
      expect(Boolean(item.path)).toBe(true);
    }
  });

  it('all dashboard paths are unique', () => {
    const paths = dashboardRegistry.map((item) => item.path);
    expect(new Set(paths).size).toBe(paths.length);
  });
});
