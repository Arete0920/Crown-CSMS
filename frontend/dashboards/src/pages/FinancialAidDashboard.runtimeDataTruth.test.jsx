// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getFinancialAidDashboardConfig } from './FinancialAidDashboard.jsx';

const captured = {
  metrics: [],
  truth: [],
  status: [],
  activities: [],
};
const mockUseDashboardData = vi.fn();

vi.mock('../hooks/useDashboardData.js', () => ({
  default: (...args) => mockUseDashboardData(...args),
}));
vi.mock('react-router', () => ({
  Link: ({ children, to, ...rest }) => <a href={to} {...rest}>{children}</a>,
  useInRouterContext: () => false,
}));
vi.mock('../components/launch/CrownCard.jsx', () => ({ default: ({ children }) => <div>{children}</div> }));
vi.mock('../components/crown-dashboard/CrownDashboardShell.jsx', () => ({
  default: ({ children }) => <div>{children}</div>,
}));
vi.mock('../components/crown-dashboard/CrownHeroHeader.jsx', () => ({ default: () => null }));
vi.mock('../components/crown-dashboard/CrownDashboardMetricGrid.jsx', () => ({
  default: ({ children }) => <div>{children}</div>,
}));
vi.mock('../components/crown-dashboard/CrownDashboardMetricCard.jsx', () => ({
  default: (props) => { captured.metrics.push(props); return null; },
}));
vi.mock('../components/crown-dashboard/CrownDashboardDataTruthStatus.jsx', () => ({
  default: (props) => { captured.truth.push(props); return null; },
}));
vi.mock('../components/crown-dashboard/CrownDashboardStatusPanel.jsx', () => ({
  default: (props) => { captured.status.push(props); return null; },
}));
vi.mock('../components/crown-dashboard/CrownDashboardActivityFeed.jsx', () => ({
  default: (props) => { captured.activities.push(props); return null; },
}));
vi.mock('../components/crown-dashboard/CrownDashboardErrorState.jsx', () => ({
  default: ({ title }) => <div data-testid="dashboard-error">{title}</div>,
}));
vi.mock('../components/crown-dashboard/CrownInsightPanel.jsx', () => ({ default: () => null }));
vi.mock('../components/crown-dashboard/CrownQuickActions.jsx', () => ({ default: () => null }));
vi.mock('../components/crown-dashboard/CrownDashboardFlipCard.jsx', () => ({ default: () => null }));
vi.mock('../components/crown-dashboard/CrownDashboardRightRail.jsx', () => ({ default: () => null }));
vi.mock('../components/crown-dashboard/CrownModuleSection.jsx', () => ({ default: () => null }));
vi.mock('../components/crown-dashboard/CrownDashboardDecisionPanel.jsx', () => ({ default: () => null }));
vi.mock('../components/crown-dashboard/CrownFaithCommunityStrip.jsx', () => ({ default: () => null }));
vi.mock('../components/crown-dashboard/CrownDashboardCommunicationsStrip.jsx', () => ({ default: () => null }));

function renderFinancialAid() {
  render(<CrownDashboardTemplate roleKey="financialAid" config={getFinancialAidDashboardConfig()} />);
}

afterEach(() => cleanup());

beforeEach(() => {
  captured.metrics = [];
  captured.truth = [];
  captured.status = [];
  captured.activities = [];
  mockUseDashboardData.mockReset();
});

describe('Financial Aid dashboard runtime data truth', () => {
  it('does not substitute illustrative amounts or healthy statuses for a failed API', () => {
    mockUseDashboardData.mockReturnValue({
      data: null,
      error: new Error('finance summary unavailable'),
      loading: false,
      source: 'none',
      config: { endpoint: '/api/v1/dashboards/financial-aid/summary' },
    });
    renderFinancialAid();
    expect(mockUseDashboardData).toHaveBeenCalledWith('financial-aid', { enabled: true });
    expect(captured.truth[0].dataState).toBe('error');
    expect(captured.truth[0].lastSyncLabel).toBe('Last sync unavailable');
    expect(captured.metrics).toEqual([]);
    expect(captured.activities[0].items).toEqual([]);
    expect(captured.status[0].statuses.map((entry) => entry.label)).toEqual([
      'Dashboard Data State', 'Dashboard Data Source',
    ]);
    expect(screen.getByTestId('dashboard-error').textContent).toBe('Dashboard data unavailable');
    expect(JSON.stringify(captured)).not.toMatch(/\$210K|\$42K|Compliance: Clean|Healthy|April disbursement batch/);
  });

  it('withholds retained Financial Aid metrics while a fresh request is loading', () => {
    mockUseDashboardData.mockReturnValue({
      data: {
        metrics: [{ label: 'Aid Applications', value: '112' }],
        meta: { served_from: 'fallback' },
      },
      error: null,
      loading: true,
      source: 'fallback',
      config: { endpoint: '/api/v1/dashboards/financial-aid/summary' },
    });
    renderFinancialAid();
    expect(captured.truth[0].dataState).toBe('loading');
    expect(captured.truth[0].sourceLabel).toContain('Loading dashboard');
    expect(captured.metrics).toEqual([]);
    expect(captured.activities[0].items).toEqual([]);
    expect(screen.queryByTestId('dashboard-error')).toBeNull();
  });

  it('fails closed when an old sample payload remains after an API error', () => {
    mockUseDashboardData.mockReturnValue({
      data: {
        metrics: [{ label: 'Aid Applications', value: '112' }],
        meta: { served_from: 'sample' },
      },
      error: new Error('refresh failed'),
      loading: false,
      source: 'none',
      config: { endpoint: '/api/v1/dashboards/financial-aid/summary' },
    });
    renderFinancialAid();
    expect(captured.truth[0].dataState).toBe('error');
    expect(captured.metrics).toEqual([]);
    expect(captured.truth[0].lastSyncLabel).toBe('Last sync unavailable');
    expect(captured.truth[0].sourceLabel).toContain('unavailable');
    expect(captured.truth[0].sourceLabel).not.toContain('sample');
    expect(screen.getByTestId('dashboard-error')).toBeTruthy();
  });

  it.each([
    ['missing provenance', {}],
    ['unknown provenance', { served_from: 'unknown' }],
    ['explicit noncertification', { served_from: 'live', live_certified: false }],
    ['explicit noncertification for live_db', { served_from: 'live_db', live_certified: false }],
  ])('refuses to certify %s as live financial-aid figures', (_case, meta) => {
    mockUseDashboardData.mockReturnValue({
      data: {
        metrics: [{ label: 'Aid Applications', value: '112' }],
        queue: ['Approve payment batch'],
        alerts: [{ title: 'Approval due', level: 'High' }],
        meta,
      },
      error: null,
      loading: false,
      source: 'live',
      config: { endpoint: '/api/v1/dashboards/financial-aid/summary' },
    });
    renderFinancialAid();
    expect(captured.truth[0].dataState).toBe('unavailable');
    expect(captured.truth[0].sourceLabel).toContain('unavailable');
    expect(captured.metrics).toEqual([]);
    expect(captured.activities[0].items).toEqual([]);
    expect(captured.status[0].statuses.map((entry) => entry.label)).toEqual([
      'Dashboard Data State', 'Dashboard Data Source',
    ]);
    expect(screen.getByTestId('dashboard-error')).toBeTruthy();
  });

  it('labels an API-served sample-derived snapshot as sample, never live', () => {
    mockUseDashboardData.mockReturnValue({
      data: {
        metrics: [{ label: 'Aid Applications', value: '64' }],
        queue: [],
        alerts: [],
        meta: {
          served_from: 'snapshot',
          snapshot_derived_from: 'sample',
          seed_source: 'sample-derived-snapshot',
          live_certified: false,
          snapshot_source: 'sample-derived-snapshot',
        },
      },
      error: null,
      loading: false,
      source: 'live',
      config: { endpoint: '/api/v1/dashboards/financial-aid/summary' },
    });
    renderFinancialAid();
    expect(captured.truth[0].dataState).toBe('sample');
    expect(captured.truth[0].sourceLabel).toContain('Sample-derived dashboard snapshot');
    expect(captured.truth[0].sourceLabel).toContain('not live');
    expect(captured.metrics[0]).toMatchObject({ value: '64', dataState: 'sample' });
  });

  it('labels any other stored dashboard snapshot as non-live fallback', () => {
    mockUseDashboardData.mockReturnValue({
      data: {
        metrics: [{ label: 'Aid Applications', value: '3' }],
        queue: [],
        alerts: [],
        meta: { served_from: 'snapshot', snapshot_source: 'verified-school-snapshot', live_certified: false },
      },
      error: null,
      loading: false,
      source: 'live',
      config: { endpoint: '/api/v1/dashboards/financial-aid/summary' },
    });
    renderFinancialAid();
    expect(captured.truth[0].dataState).toBe('fallback');
    expect(captured.truth[0].sourceLabel).toContain('Dashboard snapshot service');
    expect(captured.truth[0].sourceLabel).toContain('not live');
    expect(captured.metrics[0]).toMatchObject({ value: '3', dataState: 'fallback' });
  });

  it('does not promote a stale snapshot to live status', () => {
    mockUseDashboardData.mockReturnValue({
      data: {
        metrics: [{ label: 'Aid Applications', value: '2' }],
        meta: { served_from: 'stale_snapshot' },
      },
      error: null,
      loading: false,
      source: 'live',
      config: { endpoint: '/api/v1/dashboards/financial-aid/summary' },
    });
    renderFinancialAid();
    expect(captured.truth[0].dataState).toBe('fallback');
    expect(captured.truth[0].sourceLabel).toContain('Stale dashboard snapshot');
    expect(captured.metrics[0].dataState).toBe('fallback');
  });

  it('displays authenticated live metrics only from the returned API payload', () => {
    mockUseDashboardData.mockReturnValue({
      data: {
        metrics: [{ label: 'Aid Applications', value: '2', secondary: 'Verified synthetic school' }],
        queue: [],
        alerts: [],
        meta: { served_from: 'database' },
      },
      error: null,
      loading: false,
      source: 'live',
      config: { endpoint: '/api/v1/dashboards/financial-aid/summary' },
    });
    renderFinancialAid();
    expect(captured.truth[0].dataState).toBe('live');
    expect(captured.metrics).toHaveLength(1);
    expect(captured.metrics[0]).toMatchObject({
      label: 'Aid Applications', value: '2', dataState: 'live',
    });
    expect(captured.activities[0].items).toEqual([]);
    expect(screen.queryByTestId('dashboard-error')).toBeNull();
  });

  it('labels a sample API payload as sample instead of treating it as live', () => {
    mockUseDashboardData.mockReturnValue({
      data: {
        metrics: [{ label: 'Aid Applications', value: '7' }],
        queue: [],
        alerts: [],
        meta: { served_from: 'sample' },
      },
      error: null,
      loading: false,
      source: 'live',
      config: { endpoint: '/api/v1/dashboards/financial-aid/summary' },
    });
    renderFinancialAid();
    expect(captured.truth[0].dataState).toBe('sample');
    expect(captured.metrics).toHaveLength(1);
    expect(captured.metrics[0].dataState).toBe('sample');
    expect(captured.metrics[0].value).toBe('7');
    expect(captured.activities[0].items).toEqual([]);
  });
});
