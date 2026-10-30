// @vitest-environment jsdom
import { render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import FinancialAidDashboard, { getFinancialAidDashboardConfig } from './FinancialAidDashboard.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

const observed = vi.hoisted(() => ({ config: null, roleKey: null }));
vi.mock('../components/crown-dashboard/CrownDashboardTemplate.jsx', () => ({
  default: ({ config, roleKey }) => {
    observed.config = config;
    observed.roleKey = roleKey;
    return null;
  },
}));

describe('Financial Aid dashboard data truth', () => {
  it('preserves the live API binding and authenticated dashboard role', () => {
    const original = getDashboardTemplate('financialAid');
    const config = getFinancialAidDashboardConfig();
    expect(config.key).toBe('financialAid');
    expect(config.liveDataKey).toBe('financialAid');
    expect(config.liveDataKey).toBe(original.liveDataKey);
    expect(config.disableLiveData).not.toBe(true);
    expect(config.activePath).toBe(original.activePath);
    expect(config.schoolName).toBeNull();
  });

  it('never forwards illustrative financial figures, activity or status as operational facts', () => {
    const config = getFinancialAidDashboardConfig();
    for (const field of ['metrics', 'priorities', 'alerts', 'commandModules', 'trendPanels', 'activities', 'statuses']) {
      expect(config[field], field).toEqual([]);
    }
    expect(config.communications).toBe(false);
    expect(config.faithCommunity).toBe(false);
    expect(config.updatesCount).toBeNull();
    const content = JSON.stringify(config);
    expect(content).not.toContain('$210K');
    expect(content).not.toContain('$42K');
    expect(content).not.toContain('Compliance: Clean');
    expect(content).not.toContain('April disbursement batch prepared');
    expect(config.quickActions).toEqual([
      { label: 'Open Financial Aid Setup', href: '/aid-setup' },
      { label: 'Open Finance', href: '/finance' },
    ]);
  });

  it('renders using sanitized config instead of the illustrative module inventory', () => {
    observed.config = null;
    observed.roleKey = null;
    render(<FinancialAidDashboard />);
    expect(observed.roleKey).toBe('financialAid');
    expect(observed.config).not.toBeNull();
    expect(observed.config.metrics).toEqual([]);
    expect(observed.config.commandModules).toEqual([]);
    expect(observed.config.activities).toEqual([]);
    expect(observed.config.liveDataKey).toBe('financialAid');
  });
});
