import { describe, expect, it } from 'vitest';
import { DASHBOARD_TEMPLATE_MAP } from './dashboardTemplates/index.js';

function hasLiveMetadata(template) {
  return (
    template
    && template.dataSource === 'live_api'
    && typeof template.apiEndpoint === 'string'
    && template.apiEndpoint.length > 0
    && typeof template.liveDataKey === 'string'
    && template.liveDataKey.length > 0
  );
}

describe('dashboard template live metadata', () => {
  it('live-api templates expose endpoint and live key metadata', () => {
    Object.entries(DASHBOARD_TEMPLATE_MAP).forEach(([templateKey, template]) => {
      if (template?.dataSource !== 'live_api') {
        return;
      }

      expect(hasLiveMetadata(template)).toBe(true);
      expect(template.apiEndpoint.startsWith('/api/v1/')).toBe(true);
      expect(template.liveDataKey).toMatch(/^[a-z][A-Za-z0-9]*$/);
      expect(template.apiEndpoint).toContain('/summary/');

      if (template.key && template.key !== 'dashboard') {
        expect(template.liveDataKey.toLowerCase()).toContain(template.key.toLowerCase());
      }

      expect(templateKey.length).toBeGreaterThan(0);
    });
  });
});
