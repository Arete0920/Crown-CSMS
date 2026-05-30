import { describe, expect, it } from 'vitest';

import { DASHBOARD_REGISTRY } from './dashboardRegistry';
import {
  DASHBOARD_TEMPLATE_MAP,
  getDashboardTemplate,
} from './dashboardTemplates';
import {
  PLACEHOLDER_TEXT_PATTERN,
  isProductionReady,
} from './releaseState';

const COLLECTIONS_WITH_CARDS_OR_WIDGETS = [
  'metrics',
  'priorities',
  'alerts',
  'commandModules',
  'trendPanels',
  'activities',
  'quickActions',
  'statuses',
];

function activePathTemplateMap() {
  const map = new Map();
  Object.keys(DASHBOARD_TEMPLATE_MAP).forEach((key) => {
    const template = getDashboardTemplate(key);
    if (template?.activePath && !map.has(template.activePath)) {
      map.set(template.activePath, template);
    }
  });
  return map;
}

describe('dashboard data-source and placeholder contracts', () => {
  it('064: requires explicit data-source declarations for dashboard card/widget collections', () => {
    Object.keys(DASHBOARD_TEMPLATE_MAP).forEach((key) => {
      const template = getDashboardTemplate(key);
      expect(typeof template.dataSource).toBe('string');
      expect(template.dataSource.trim().length).toBeGreaterThan(0);

      COLLECTIONS_WITH_CARDS_OR_WIDGETS.forEach((collection) => {
        const items = template[collection];
        if (!Array.isArray(items)) {
          return;
        }

        items.forEach((item) => {
          if (!item || typeof item !== 'object' || Array.isArray(item)) {
            return;
          }
          expect(typeof item.dataSource).toBe('string');
          expect(item.dataSource.trim().length).toBeGreaterThan(0);
        });
      });
    });
  });

  it('065: blocks placeholder-like copy for dashboards marked ready', () => {
    const byActivePath = activePathTemplateMap();

    DASHBOARD_REGISTRY.filter(isProductionReady).forEach((entry) => {
      const template = byActivePath.get(entry.path);
      expect(template, `missing dashboard template for path ${entry.path}`).toBeTruthy();

      const candidates = [
        entry.label,
        entry.title,
        entry.path,
        template.title,
        template.subtitle,
        template.note,
        template.sourceLabel,
      ].filter(Boolean).join(' ');

      expect(PLACEHOLDER_TEXT_PATTERN.test(candidates)).toBe(false);
    });
  });
});
