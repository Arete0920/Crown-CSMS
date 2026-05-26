// @vitest-environment jsdom
import { render } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import CrownDashboardTemplate from './CrownDashboardTemplate.jsx';

const captured = {
  metrics: [],
  modules: [],
};

vi.mock('../launch/CrownCard.jsx', () => ({
  default: ({ children }) => <div>{children}</div>,
}));

vi.mock('./CrownDashboardShell.jsx', () => ({
  default: ({ children }) => <div>{children}</div>,
}));

vi.mock('./CrownHeroHeader.jsx', () => ({ default: () => null }));
vi.mock('./CrownDashboardMetricGrid.jsx', () => ({ default: ({ children }) => <div>{children}</div> }));
vi.mock('./CrownInsightPanel.jsx', () => ({ default: () => null }));
vi.mock('./CrownQuickActions.jsx', () => ({ default: () => null }));
vi.mock('./CrownDashboardActivityFeed.jsx', () => ({ default: () => null }));
vi.mock('./CrownDashboardStatusPanel.jsx', () => ({ default: () => null }));
vi.mock('./CrownModuleSection.jsx', () => ({ default: () => null }));
vi.mock('./CrownDashboardErrorState.jsx', () => ({ default: () => null }));
vi.mock('./CrownDashboardRightRail.jsx', () => ({ default: () => null }));
vi.mock('./CrownFaithCommunityStrip.jsx', () => ({ default: () => null }));

vi.mock('./CrownDashboardMetricCard.jsx', () => ({
  default: (props) => {
    captured.metrics.push(props);
    return null;
  },
}));

vi.mock('./CrownDashboardFlipCard.jsx', () => ({
  default: ({ module }) => {
    captured.modules.push(module);
    return null;
  },
}));

vi.mock('react-router-dom', () => ({
  Link: ({ children, to, ...rest }) => <a href={to} {...rest}>{children}</a>,
  useInRouterContext: () => false,
}));

describe('CrownDashboardTemplate data truth defaults', () => {
  beforeEach(() => {
    captured.metrics = [];
    captured.modules = [];
  });

  it('applies fallback data truth to template-backed metrics and modules by default', () => {
    render(
      <CrownDashboardTemplate
        roleKey="advancement"
        config={{
          key: 'advancement',
          title: 'Advancement Dashboard',
          metrics: [{ label: 'Donors YTD', value: '152' }],
          commandModules: [{ key: 'donors', title: 'Donor Management' }],
          quickActions: [],
          statuses: [],
          activities: [],
          trendPanels: [],
          priorities: [],
          alerts: [],
        }}
      />,
    );

    expect(captured.metrics).toHaveLength(1);
    expect(captured.metrics[0].dataState).toBe('fallback');
    expect(captured.metrics[0].sourceLabel).toBe('Dashboard template data');
    expect(captured.modules).toHaveLength(1);
    expect(captured.modules[0].dataState).toBe('fallback');
    expect(captured.modules[0].sourceLabel).toBe('Dashboard template data');
  });

  it('preserves explicit top-level data truth defaults when provided', () => {
    render(
      <CrownDashboardTemplate
        roleKey="advancement"
        config={{
          key: 'advancement',
          title: 'Advancement Dashboard',
          dataState: 'unavailable',
          sourceLabel: 'Advancement data service unavailable',
          metrics: [{ label: 'Donors YTD', value: '152' }],
          commandModules: [{ key: 'donors', title: 'Donor Management' }],
          quickActions: [],
          statuses: [],
          activities: [],
          trendPanels: [],
          priorities: [],
          alerts: [],
        }}
      />,
    );

    expect(captured.metrics[0].dataState).toBe('unavailable');
    expect(captured.metrics[0].sourceLabel).toBe('Advancement data service unavailable');
    expect(captured.modules[0].dataState).toBe('unavailable');
    expect(captured.modules[0].sourceLabel).toBe('Advancement data service unavailable');
  });
});
