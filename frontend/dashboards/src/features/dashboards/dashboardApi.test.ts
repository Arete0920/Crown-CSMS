// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { loadSchoolAdministratorLiveSnapshot } from './dashboardApi';

const mocks = vi.hoisted(() => ({ me: vi.fn(), summary: vi.fn(), alerts: vi.fn() }));
vi.mock('../../api/dashboards.js', () => ({
  fetchDashboardMe: mocks.me,
  fetchDashboardSummary: mocks.summary,
  fetchDashboardAlerts: mocks.alerts,
}));

const SCHOOL_ID = '19801b59-8c05-4c84-9312-5d792e4e839d';
const good = (data: object) => ({ ok: true, status: 200, data, error: '', correlationId: '' });
const bad = (status = 503) => ({ ok: false, status, data: null, error: 'Unavailable', correlationId: '' });

function setConnectedResponses() {
  mocks.me.mockResolvedValue(good({ school_id: SCHOOL_ID, roles: ['HEAD_OF_SCHOOL'], default_route: '/director/', meta: { served_from: 'live' } }));
  mocks.summary.mockResolvedValue(good({ school_id: SCHOOL_ID, widgets: [{ key: 'quick_actions' }], meta: { served_from: 'live' } }));
  mocks.alerts.mockResolvedValue(good({ alerts: [], meta: { served_from: 'live', school_id: SCHOOL_ID } }));
}

describe('School administrator API connectivity versus business-data provenance', () => {
  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
    sessionStorage.setItem('crown.school.id', SCHOOL_ID);
    mocks.me.mockReset();
    mocks.summary.mockReset();
    mocks.alerts.mockReset();
    setConnectedResponses();
  });

  it('classifies complete connectivity without claiming business metrics are live', async () => {
    const value = await loadSchoolAdministratorLiveSnapshot();
    expect(value.serviceState).toBe('connected');
    expect(value.successfulEndpointCount).toBe(3);
    expect(value.dataState).toBe('sample');
    expect(value.dashboardSummary?.widgets).toHaveLength(1);
    expect(mocks.me).toHaveBeenCalledWith(SCHOOL_ID, 'school-administrator');
  });

  it('classifies a 502 summary endpoint as partial, not total failure or live KPIs', async () => {
    mocks.summary.mockResolvedValue(bad(502));
    const value = await loadSchoolAdministratorLiveSnapshot();
    expect(value.serviceState).toBe('partial');
    expect(value.successfulEndpointCount).toBe(2);
    expect(value.dashboardSummary).toBeNull();
    expect(value.endpointStatuses.summary).toBe(502);
    expect(value.dataState).toBe('sample');
  });

  it('reports unavailable when all endpoints fail', async () => {
    mocks.me.mockResolvedValue(bad(401));
    mocks.summary.mockResolvedValue(bad(502));
    mocks.alerts.mockResolvedValue(bad(503));
    const value = await loadSchoolAdministratorLiveSnapshot();
    expect(value.serviceState).toBe('unavailable');
    expect(value.successfulEndpointCount).toBe(0);
    expect(value.dashboardMe).toBeNull();
  });

  it('rejects malformed and foreign-school payloads', async () => {
    mocks.summary.mockResolvedValue(good({ school_id: SCHOOL_ID, message: 'missing widgets' }));
    mocks.alerts.mockResolvedValue(good({ alerts: [], meta: { school_id: 'foreign-school' } }));
    const value = await loadSchoolAdministratorLiveSnapshot();
    expect(value.serviceState).toBe('partial');
    expect(value.successfulEndpointCount).toBe(1);
    expect(value.dashboardSummary).toBeNull();
    expect(value.dashboardAlerts).toBeNull();
  });

  it('does not treat a sample-marked response as authoritative business data', async () => {
    mocks.summary.mockResolvedValue(good({ school_id: SCHOOL_ID, widgets: [], meta: { served_from: 'sample' } }));
    const value = await loadSchoolAdministratorLiveSnapshot();
    expect(value.dataState).toBe('sample');
    expect(value.lastSyncLabel).toContain('3 of 3');
  });
});
