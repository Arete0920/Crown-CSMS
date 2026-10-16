import { describe, expect, it } from 'vitest';
import schedulingDashboard from './schedulingDashboard.js';
import { getDashboardTemplate } from './index.js';

describe('Kairos scheduling dashboard data integrity', () => {
  it('requires a canonical source rather than fabricated operational statistics', () => {
    expect(schedulingDashboard.dataSource).toBe('live_api');
    expect(schedulingDashboard.liveDataKey).toBe('scheduling');
    expect(schedulingDashboard.apiEndpoint).toBe('/api/v1/dashboards/scheduling/summary/');
    for (const key of ['metrics', 'priorities', 'alerts', 'commandModules', 'trendPanels', 'activities']) {
      expect(schedulingDashboard[key]).toEqual([]);
    }
  });

  it('preserves truthful empty state and navigation while forbidding publishing affordances', () => {
    const template = getDashboardTemplate('scheduling');
    expect(template.metrics).toEqual([]);
    expect(template.commandModules).toEqual([]);
    expect(template.sourceSyncTruth.liveDataKey).toBe('scheduling');
    expect(template.statuses).toEqual([
      { label: 'Scheduling statistics', state: 'Awaiting verified live data', dataSource: 'scheduling.statuses[0]' },
    ]);
    expect(template.quickActions.every(item => item.href.startsWith('/'))).toBe(true);
    expect(template.quickActions.some(item => /export|publish|commit/i.test(item.label))).toBe(false);
  });
});
