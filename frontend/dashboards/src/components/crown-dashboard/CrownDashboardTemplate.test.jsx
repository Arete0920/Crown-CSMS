// @vitest-environment jsdom
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import CrownDashboardTemplate from './CrownDashboardTemplate.jsx';
import { BASE_NOTE } from '../../config/dashboardTemplates/_baseData.js';
import { getDashboardTemplate } from '../../config/dashboardTemplates/index.js';

const captured = {
  metrics: [],
  modules: [],
  communications: [],
  truthStatus: [],
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
vi.mock('./CrownDashboardCommunicationsStrip.jsx', () => ({
  default: (props) => {
    captured.communications.push(props);
    return null;
  },
}));
vi.mock('./CrownDashboardDataTruthStatus.jsx', () => ({
  default: (props) => {
    captured.truthStatus.push(props);
    return null;
  },
}));

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
    captured.communications = [];
    captured.truthStatus = [];
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
    expect(captured.communications).toHaveLength(1);
    expect(captured.communications[0].communications.inboxTitle).toBe('Unread and waiting');
    expect(captured.truthStatus).toHaveLength(1);
    expect(captured.truthStatus[0].dataState).toBe('fallback');
    expect(captured.truthStatus[0].sourceLabel).toBe('Dashboard template data');
    expect(captured.truthStatus[0].lastSyncLabel).toBe('Using configured fallback data');
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
          lastSyncLabel: 'Last sync failed at 8:42 AM',
          communications: {
            inboxTitle: 'Advancement inbox',
            inboxItems: ['2 donor replies waiting'],
          },
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
    expect(captured.communications[0].communications.inboxTitle).toBe('Advancement inbox');
    expect(captured.truthStatus[0].dataState).toBe('unavailable');
    expect(captured.truthStatus[0].sourceLabel).toBe('Advancement data service unavailable');
    expect(captured.truthStatus[0].lastSyncLabel).toBe('Last sync failed at 8:42 AM');
  });

  it('contains generic BASE_NOTE but still shows custom notes', () => {
    const { rerender } = render(
      <CrownDashboardTemplate
        roleKey="advancement"
        config={{
          key: 'advancement',
          title: 'Advancement Dashboard',
          note: BASE_NOTE,
          metrics: [],
          commandModules: [],
          quickActions: [],
          statuses: [],
          activities: [],
          trendPanels: [],
          priorities: [],
          alerts: [],
        }}
      />,
    );

    expect(screen.queryByText(BASE_NOTE)).toBeNull();

    rerender(
      <CrownDashboardTemplate
        roleKey="parent"
        config={{
          key: 'parent',
          title: 'Parent Dashboard',
          note: 'Family preview experience active. Cards show seeded household examples until live parent data sync completes for each area.',
          metrics: [],
          commandModules: [],
          quickActions: [],
          statuses: [],
          activities: [],
          trendPanels: [],
          priorities: [],
          alerts: [],
        }}
      />,
    );

    expect(screen.getByText('Family preview experience active. Cards show seeded household examples until live parent data sync completes for each area.')).toBeTruthy();
  });

  it('renders the school administrator decision panel before broad dashboard content', () => {
    render(
      <CrownDashboardTemplate
        config={getDashboardTemplate('schoolAdministrator')}
        roleKey="schoolAdministrator"
      />,
    );

    expect(screen.getByText(/What needs administrator action now/i)).toBeTruthy();
    expect(screen.getByText(/pending approvals/i)).toBeTruthy();
    expect(screen.getByText(/Enrollment packets/i)).toBeTruthy();
    expect(screen.getByText(/Staff coverage/i)).toBeTruthy();
  });
});
