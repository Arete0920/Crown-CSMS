// @vitest-environment jsdom
import { render, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import SchoolAdministratorDashboard from './SchoolAdministratorDashboard.jsx';

const { captured, loadSchoolAdministratorLiveSnapshot } = vi.hoisted(() => ({
  captured: {
    config: null,
    roleKey: null,
  },
  loadSchoolAdministratorLiveSnapshot: vi.fn(),
}));

vi.mock('../components/crown-dashboard/CrownDashboardTemplate.jsx', () => ({
  default: ({ config, roleKey }) => {
    captured.config = config;
    captured.roleKey = roleKey;
    return null;
  },
}));

vi.mock('../features/dashboards/dashboardApi', () => ({
  loadSchoolAdministratorLiveSnapshot,
}));

describe('SchoolAdministratorDashboard data source contract', () => {
  beforeEach(() => {
    captured.config = null;
    captured.roleKey = null;
    loadSchoolAdministratorLiveSnapshot.mockReset();
    loadSchoolAdministratorLiveSnapshot.mockResolvedValue({
      dataState: 'live',
      sourceLabel: 'Live dashboard APIs',
      lastSyncLabel: 'Last synced just now',
      dashboardMe: {
        roles: ['HEAD_OF_SCHOOL'],
        default_route: '/school-admin-dashboard',
      },
      dashboardSummary: { widgets: [{ key: 'quick_actions' }] },
      dashboardAlerts: { alerts: [] },
    });
  });

  it('uses the page-owned canonical snapshot and disables the duplicate role-specific fetch', async () => {
    render(<SchoolAdministratorDashboard />);

    await waitFor(() => {
      expect(captured.config?.dataState).toBe('live');
    });

    expect(captured.roleKey).toBe('schoolAdministrator');
    expect(captured.config.disableLiveData).toBe(true);
    expect(loadSchoolAdministratorLiveSnapshot).toHaveBeenCalledTimes(1);
  });
});
