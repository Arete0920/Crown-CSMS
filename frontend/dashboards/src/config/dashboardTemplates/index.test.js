import { describe, expect, it } from 'vitest';
import { DASHBOARD_DATA_REGISTRY } from '../dashboardDataRegistry.js';
import { getDashboardTemplate } from './index.js';

describe('dashboard template live-data aliases', () => {
  const aliases = {
    finance: 'billing',
    board: 'school-board',
    it: 'it-support',
    spiritualLife: 'chaplain-spiritual-life',
    health: 'health-office',
    food: 'food-service',
    athletics: 'athletics-director',
  };

  for (const [templateKey, registryKey] of Object.entries(aliases)) {
    it(`${templateKey} resolves to canonical live registry key ${registryKey}`, () => {
      const template = getDashboardTemplate(templateKey);
      expect(template.liveDataKey).toBe(registryKey);
      expect(DASHBOARD_DATA_REGISTRY[template.liveDataKey]?.endpoint).toBeTruthy();
    });
  }
});
