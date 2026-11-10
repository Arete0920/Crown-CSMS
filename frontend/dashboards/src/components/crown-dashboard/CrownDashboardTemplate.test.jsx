// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import CrownDashboardTemplate from './CrownDashboardTemplate.jsx';
import { BASE_NOTE } from '../../config/dashboardTemplates/_baseData.js';
import { getDashboardTemplate } from '../../config/dashboardTemplates/index.js';

const captured = {
  metrics: [],
  modules: [],
  communications: [],
  truthStatus: [],
  headers: [],
  activities: [],
  insights: [],
  actions: [],
  statuses: [],
  faith: [],
};
const mockUseDashboardData = vi.fn(() => ({
  data: null,
  error: null,
  loading: false,
  source: 'none',
  config: null,
}));

vi.mock('../launch/CrownCard.jsx', () => ({
  default: ({ children }) => <div>{children}</div>,
}));

vi.mock('./CrownDashboardShell.jsx', () => ({
  default: ({ children, topbarSlot }) => <div>{topbarSlot}{children}</div>,
}));

vi.mock('./CrownHeroHeader.jsx', () => ({ default: (props) => { captured.headers.push(props); return null; } }));
vi.mock('./CrownDashboardMetricGrid.jsx', () => ({ default: ({ children }) => <div>{children}</div> }));
vi.mock('./CrownInsightPanel.jsx', () => ({ default: (props) => { captured.insights.push(props); return null; } }));
vi.mock('./CrownQuickActions.jsx', () => ({ default: (props) => { captured.actions.push(props); return null; } }));
vi.mock('./CrownDashboardActivityFeed.jsx', () => ({ default: (props) => { captured.activities.push(props); return null; } }));
vi.mock('./CrownDashboardStatusPanel.jsx', () => ({ default: (props) => { captured.statuses.push(props); return null; } }));
vi.mock('./CrownModuleSection.jsx', () => ({ default: () => null }));
vi.mock('./CrownDashboardRightRail.jsx', () => ({ default: () => null }));
vi.mock('./CrownFaithCommunityStrip.jsx', () => ({ default: (props) => { captured.faith.push(props); return null; } }));
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

vi.mock('../../hooks/useDashboardData.js', () => ({
  default: (...args) => mockUseDashboardData(...args),
}));

vi.mock('react-router', () => ({
  Link: ({ children, to, ...rest }) => <a href={to} {...rest}>{children}</a>,
  useInRouterContext: () => false,
}));

describe('CrownDashboardTemplate data truth defaults', () => {
  afterEach(() => { cleanup(); localStorage.clear(); });
  beforeEach(() => {
    localStorage.setItem('schoolId', 'school-a');
    captured.metrics = [];
    captured.modules = [];
    captured.communications = [];
    captured.truthStatus = [];
    captured.headers = [];
    captured.activities = [];
    captured.insights = [];
    captured.actions = [];
    captured.statuses = [];
    captured.faith = [];
    mockUseDashboardData.mockReset();
    mockUseDashboardData.mockReturnValue({
      data: null,
      error: null,
      loading: false,
      source: 'none',
      config: null,
    });
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
    expect(captured.metrics[0].sourceLabel).toBe('Static dashboard scaffold');
    expect(captured.modules).toHaveLength(1);
    expect(captured.modules[0].dataState).toBe('fallback');
    expect(captured.modules[0].sourceLabel).toBe('Static dashboard scaffold');
    expect(captured.communications).toHaveLength(1);
    expect(captured.communications[0].communications.inboxTitle).toBe('Unread and waiting');
    expect(captured.truthStatus).toHaveLength(1);
    expect(captured.truthStatus[0].dataState).toBe('fallback');
    expect(captured.truthStatus[0].sourceLabel).toBe('Static dashboard scaffold');
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

    expect(screen.getByText(/School Administrator Command Center/i)).toBeTruthy();
    expect(screen.getByText(/Illustrative department readiness/i)).toBeTruthy();
    expect(captured.truthStatus[0]).toMatchObject({ dataState: 'sample', sourceLabel: 'Illustrative Heritage school operations — sample data, not live school records' });
    expect(mockUseDashboardData).toHaveBeenCalledWith('school-administrator', { enabled: false });
    expect(screen.getByText(/^Admissions$/i)).toBeTruthy();
    expect(screen.getByText(/^Student Life$/i)).toBeTruthy();
  });

  it('surfaces sample API data and does not mark template modules as live', () => {
    mockUseDashboardData.mockReturnValue({
      data: {
        metrics: [{ label: 'Donors YTD', value: '188', secondary: 'Served from dashboard summary API.' }],
        alerts: [{ title: 'Campaign pacing alert', level: 'High', secondary: 'Review weekly giving variance.' }],
        queue: ['Review weekly campaign pacing'],
        meta: { served_from: 'sample' },
      },
      error: null,
      loading: false,
      source: 'live',
      config: { endpoint: '/api/v1/dashboards/advancement/summary' },
    });

    render(
      <CrownDashboardTemplate
        roleKey="advancement"
        config={{
          key: 'advancement',
          liveDataKey: 'advancement',
          title: 'Advancement Dashboard',
          note: 'Widget badges disclose data provenance and non-live states.',
          metrics: [{ label: 'Donors YTD', value: '152', detail: 'template metric' }],
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

    expect(captured.metrics[0].value).toBe('188');
    expect(captured.metrics[0].dataState).toBe('sample');
    expect(captured.metrics[0].sourceLabel).toContain('Dashboard summary service sample');
    expect(captured.modules[0].dataState).toBe('sample');
    expect(captured.modules[0].sourceLabel).toContain('Dashboard summary service sample');
  });

  it('withholds configured parent example cards when authenticated household metrics are live', () => {
    mockUseDashboardData.mockReturnValue({
      data: {
        metrics: [
          { label: 'Linked Active Students', value: '0', secondary: 'No active students linked.' },
          { label: 'Outstanding Family Balance', value: '$0.00' },
        ],
        queue: ['Review authenticated family record'],
        alerts: [{ title: 'Authenticated family alert', level: 'info' }],
        meta: { served_from: 'database' },
      },
      error: null,
      loading: false,
      source: 'live',
      config: { endpoint: '/api/v1/dashboards/parent/summary/' },
    });

    render(<CrownDashboardTemplate roleKey="parent" config={getDashboardTemplate('parent')} />);

    expect(captured.metrics.map((metric) => metric.value)).toEqual(['0', '$0.00']);
    expect(captured.metrics.every((metric) => metric.dataState === 'live')).toBe(true);
    expect(captured.metrics[1].detail).toContain('Dashboard summary service');
    expect(captured.metrics[1].detail).not.toContain('November');
    expect(captured.modules).toHaveLength(0);
    expect(captured.activities[0].items).toEqual([]);
    expect(captured.insights).toHaveLength(0);
    expect(screen.getByText('Review authenticated family record')).toBeTruthy();
    expect(screen.getByText('Authenticated family alert')).toBeTruthy();
    expect(captured.headers[0].title).toBe('Parent Dashboard');
    expect(captured.headers[0].userInitials).toBe('PG');
    expect(captured.headers[0].updatesCount).toBeNull();
    expect(captured.communications).toHaveLength(0);
    expect(captured.faith).toHaveLength(0);
    expect(captured.statuses[0].statuses).toHaveLength(2);
    expect(captured.actions[0].actions).toHaveLength(4);
    expect(JSON.stringify(captured)).not.toMatch(/Aiden|Sophie|Parker|\$425|both students|Attendance Sync/);
  });

  it('never labels configured example cards or missing metric fallbacks as live', () => {
    mockUseDashboardData.mockReturnValue({
      data: { metrics: [], queue: [], alerts: [], meta: { served_from: 'database' } },
      error: null,
      loading: false,
      source: 'live',
      config: { endpoint: '/api/v1/dashboards/advancement/summary/' },
    });
    render(
      <CrownDashboardTemplate roleKey="advancement" config={{
        key: 'advancement',
        liveDataKey: 'advancement',
        metrics: [{ label: 'Donors YTD', value: '152', detail: 'Example donors.' }],
        commandModules: [{ key: 'donors', title: 'Donor Management', mainKpi: '152' }],
      }} />,
    );
    expect(captured.metrics).toHaveLength(0);
    expect(captured.modules).toHaveLength(1);
    expect(captured.modules[0].dataState).toBe('sample');
    expect(captured.modules[0].sourceLabel).toContain('illustrative');
    expect(captured.truthStatus[0].dataState).toBe('live');
  });

  it('skips live data loading when disableLiveData is set', () => {
    render(
      <CrownDashboardTemplate
        roleKey="admissions"
        config={{
          key: 'admissions',
          liveDataKey: 'admissions',
          disableLiveData: true,
          title: 'Admissions Dashboard',
          metrics: [{ label: 'Open Applications', value: '12' }],
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

    expect(mockUseDashboardData).toHaveBeenCalledWith('admissions', { enabled: false });
    expect(captured.metrics[0].value).toBe('12');
    expect(captured.metrics[0].dataState).toBe('fallback');
  });

  it('withholds stale queue items, alerts and status during an API failure', () => {
    mockUseDashboardData.mockReturnValue({
      data: {
        metrics: [{ label: 'Donors YTD', value: '999' }],
        queue: ['Send cached notice'],
        alerts: [{ title: 'Cached approval required', level: 'High' }],
        meta: { served_from: 'sample' },
      },
      error: new Error('refresh failed'),
      loading: false,
      source: 'none',
      config: { endpoint: '/api/v1/dashboards/advancement/summary' },
    });
    render(<CrownDashboardTemplate roleKey="advancement" config={{
      key: 'advancement',
      title: 'Advancement Dashboard',
      liveDataKey: 'advancement',
      metrics: [{ label: 'Donors YTD', value: '152' }],
      statuses: [{ label: 'Compliance', state: 'Healthy' }],
      commandModules: [{ key: 'donors', title: 'Donors' }],
      quickActions: [], activities: [], trendPanels: [],
      priorities: [], alerts: [],
    }} />);

    expect(captured.truthStatus[0].dataState).toBe('error');
    expect(captured.truthStatus[0].sourceLabel).toContain('unavailable');
    expect(captured.metrics).toHaveLength(0);
    expect(captured.statuses[0].statuses.map((row) => row.label)).toEqual([
      'Dashboard Data State', 'Dashboard Data Source',
    ]);
    expect(screen.queryByText('Send cached notice')).toBeNull();
    expect(screen.queryByText('Cached approval required')).toBeNull();
    expect(screen.queryByText('Healthy')).toBeNull();
  });


  it('does not surface cached financial aid tasks or alerts during loading', () => {
    mockUseDashboardData.mockReturnValue({
      data: {
        metrics: [{ label: 'Aid Applications', value: '112' }],
        queue: ['Release stale award'],
        alerts: [{ title: 'Stale disbursement action', level: 'High' }],
        meta: { served_from: 'database' },
      },
      error: null,
      loading: true,
      source: 'live',
      config: { endpoint: '/api/v1/dashboards/financial-aid/summary' },
    });
    render(<CrownDashboardTemplate roleKey="financialAid" config={{
      key: 'financialAid',
      title: 'Financial Aid Dashboard',
      liveDataKey: 'financialAid',
      metrics: [{ label: 'Aid Applications', value: '112' }],
      statuses: [{ label: 'Aid system', state: 'Healthy' }],
      commandModules: [{ key: 'applications', title: 'Applications' }],
      quickActions: [], activities: [], trendPanels: [],
      priorities: [], alerts: [],
    }} />);

    expect(captured.truthStatus[0].dataState).toBe('loading');
    expect(captured.metrics).toHaveLength(0);
    expect(captured.statuses[0].statuses).toHaveLength(2);
    expect(screen.queryByText('Release stale award')).toBeNull();
    expect(screen.queryByText('Stale disbursement action')).toBeNull();
    expect(screen.queryByText('Healthy')).toBeNull();
  });

  it.each(['summerCamp', 'extendedCare'])('does not render unverified %s operational figures or notifications', (key) => {
    mockUseDashboardData.mockReturnValue({
      data: {
        metrics: [{ label: 'Registered Campers', value: '79' }],
        queue: ['Call nine families with supposedly available places'],
        alerts: [{ title: 'Fabricated staffing alert', level: 'High' }],
        meta: { served_from: 'sample' },
      },
      error: null, loading: false, source: 'live',
      config: { endpoint: '/api/v1/dashboards/test/summary' },
    });
    render(<CrownDashboardTemplate roleKey="master_control" config={getDashboardTemplate(key)} />);
    expect(captured.truthStatus[0].dataState).toBe('unavailable');
    expect(captured.metrics).toHaveLength(4);
    expect(captured.metrics.every((metric) => metric.value === 'Not available')).toBe(true);
    expect(captured.metrics.every((metric) => metric.dataState === 'unavailable')).toBe(true);
    expect(captured.modules).toHaveLength(0);
    expect(captured.activities[0].items).toEqual([]);
    expect(captured.communications).toHaveLength(0);
    expect(captured.faith).toHaveLength(1);
    expect(captured.faith[0].faithCommunity).toEqual({ unverified: true });
    expect(screen.queryByText('Fabricated staffing alert')).toBeNull();
    expect(screen.queryByText('Call nine families with supposedly available places')).toBeNull();
    expect(JSON.stringify(captured)).not.toMatch(/79 registered|\\$4,200|92% complete/);
  });

  it.each(['summerCamp', 'extendedCare'])('requires as-of time and aggregation window for %s live provenance', (key) => {
    mockUseDashboardData.mockReturnValue({
      data: { metrics: [{ label: 'Live only', value: '4' }], meta: { served_from: 'live_db' } },
      error: null, loading: false, source: 'live',
      config: { endpoint: '/api/v1/dashboards/test/summary' },
    });
    render(<CrownDashboardTemplate roleKey="master_control" config={getDashboardTemplate(key)} />);
    expect(captured.truthStatus[0].dataState).toBe('unavailable');
    expect(captured.metrics.every((metric) => metric.value === 'Not available')).toBe(true);
  });

  it.each(['summerCamp', 'extendedCare'])('accepts current verified %s metrics without template numbers', (key) => {
    mockUseDashboardData.mockReturnValue({
      data: {
        metrics: [{ label: 'Verified campers or care attendance', value: '4' }],
        queue: ['Review current source records'],
        alerts: [],
        meta: {
          school_id: 'school-a',
          served_from: 'live_db',
          observed_at: '2026-10-31T16:00:00Z',
          aggregation_window: 'school-local-day:2026-10-31',
        },
      },
      error: null, loading: false, source: 'live',
      config: { endpoint: '/api/v1/dashboards/test/summary' },
    });
    render(<CrownDashboardTemplate roleKey="master_control" config={getDashboardTemplate(key)} />);
    expect(captured.truthStatus[0].dataState).toBe('live');
    expect(captured.truthStatus[0].sourceLabel).toContain('2026-10-31T16:00:00Z');
    expect(captured.truthStatus[0].sourceLabel).toContain('school-local-day:2026-10-31');
    expect(captured.metrics.map((metric) => metric.value)).toEqual(['4']);
    expect(captured.metrics[0].dataState).toBe('live');
    expect(captured.activities[0].items).toEqual([]);
    expect(captured.modules).toHaveLength(0);
    expect(captured.faith).toHaveLength(1);
    expect(captured.faith[0].faithCommunity).toEqual({ unverified: true });
  });

  describe.each(['summerCamp', 'extendedCare'])('%s current-request provenance', (key) => {
    const meta = {
      school_id: 'school-a', served_from: 'live_db',
      observed_at: '2026-10-31T16:00:00Z', aggregation_window: 'school-local-day:2026-10-31',
    };
    const response = (overrides = {}) => ({
      data: {
        metrics: [{ label: 'Current enrollment', value: '7' }],
        queue: ['Current operational task'], alerts: [{ title: 'Current safety alert', level: 'High' }], meta,
      },
      error: null, loading: false, source: 'live', config: { endpoint: '/api/v1/dashboards/test/summary' },
      ...overrides,
    });
    const renderProgram = () => render(<CrownDashboardTemplate roleKey="master_control" config={getDashboardTemplate(key)} />);

    it.each([
      ['sample', { served_from: 'sample' }], ['snapshot', { served_from: 'snapshot' }],
      ['fallback', { served_from: 'fallback' }], ['stale', { served_from: 'stale' }],
      ['stale snapshot', { served_from: 'stale_snapshot' }],
      ['missing source', { served_from: undefined }],
      ['missing observed time', { observed_at: undefined }], ['invalid time', { observed_at: 'invalid' }],
      ['missing window', { aggregation_window: undefined }], ['blank window', { aggregation_window: '  ' }],
      ['invalid window type', { aggregation_window: {} }], ['missing scope', { school_id: undefined }],
      ['foreign scope', { school_id: 'school-b' }], ['uncertified', { live_certified: false }],
    ])('rejects %s even with otherwise valid metadata', (_name, invalid) => {
      const result = response();
      result.data = { ...result.data, meta: { ...meta, ...invalid } };
      mockUseDashboardData.mockReturnValue(result);
      renderProgram();
      expect(captured.truthStatus[0].dataState).toBe('unavailable');
      expect(captured.metrics.map((item) => item.value)).toEqual(Array(4).fill('Not available'));
      expect(screen.queryByText('Current operational task')).toBeNull();
      expect(screen.queryByText('Current safety alert')).toBeNull();
      expect(screen.getByRole('heading', { name: 'Operational metrics unavailable' })).toBeTruthy();
    });

    it.each([
      ['loading', { loading: true }, 'loading'],
      ['failed with stale live source', { error: new Error('Forbidden') }, 'unavailable'],
      ['failed transport', { source: 'none', error: new Error('Unauthorized') }, 'unavailable'],
      ['fallback transport', { source: 'fallback' }, 'unavailable'],
    ])('removes previously verified figures while %s', (_name, next, state) => {
      mockUseDashboardData.mockReturnValue(response());
      const view = renderProgram();
      expect(captured.metrics.map((item) => item.value)).toEqual(['7']);
      expect(screen.getByText('Current operational task')).toBeTruthy();
      expect(screen.getByText('Current safety alert')).toBeTruthy();
      captured.metrics = []; captured.truthStatus = []; captured.statuses = [];
      mockUseDashboardData.mockReturnValue(response(next));
      view.rerender(<CrownDashboardTemplate roleKey="master_control" config={getDashboardTemplate(key)} />);
      expect(captured.truthStatus[0].dataState).toBe(state);
      expect(captured.metrics.map((item) => item.value)).toEqual(Array(4).fill('Not available'));
      expect(screen.queryByText('Current operational task')).toBeNull();
      expect(screen.queryByText('Current safety alert')).toBeNull();
      expect(captured.statuses[0].statuses).toEqual([{ label: 'Operational source', state: 'Not available' }]);
    });

    it('requires an active school context', () => {
      localStorage.clear();
      mockUseDashboardData.mockReturnValue(response());
      renderProgram();
      expect(captured.truthStatus[0].dataState).toBe('unavailable');
    });

    it.each(['live', 'live_db'])('renders only API metrics from %s and no template operational claims', (served_from) => {
      const result = response();
      result.data = { ...result.data, meta: { ...meta, served_from }, metrics: [] };
      mockUseDashboardData.mockReturnValue(result);
      render(<CrownDashboardTemplate roleKey="master_control" config={{
        ...getDashboardTemplate(key),
        activities: ['Invented child activity'], statuses: [{ label: 'Staff', state: 'Invented staffing' }],
        operations: [{ area: 'Invented child record', owner: 'Example' }],
        commandModules: [{ key: 'fake', title: 'Invented module' }],
        insight: { title: 'Invented trend' }, trendPanels: [{ title: 'Invented trend' }],
        moduleSection: { title: 'Invented section' },
      }} />);
      expect(captured.truthStatus[0].dataState).toBe('live');
      expect(captured.metrics).toEqual([]);
      expect(captured.modules).toEqual([]);
      expect(captured.activities[0].items).toEqual([]);
      expect(captured.insights).toEqual([]);
      expect(JSON.stringify(captured)).not.toContain('Invented');
      expect(screen.queryByText('Invented child record')).toBeNull();
    });
  });

});

