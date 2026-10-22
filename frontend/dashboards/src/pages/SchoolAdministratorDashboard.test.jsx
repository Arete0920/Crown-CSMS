// @vitest-environment jsdom
import { cleanup, render, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
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

describe('SchoolAdministratorDashboard provenance', () => {
  beforeEach(() => {
    captured.config = null;
    captured.roleKey = null;
    loadSchoolAdministratorLiveSnapshot.mockReset();
    loadSchoolAdministratorLiveSnapshot.mockResolvedValue({
      serviceState: 'connected',
      successfulEndpointCount: 3,
    });
  });
  afterEach(() => cleanup());

  it('keeps sample business figures even when all infrastructure endpoints respond', async () => {
    render(<SchoolAdministratorDashboard />);
    await waitFor(() => expect(captured.config?.note).toContain('3 of 3'));
    const config = captured.config;
    expect(captured.roleKey).toBe('schoolAdministrator');
    expect(config.disableLiveData).toBe(true);
    expect(config.dataState).toBe('sample');
    expect(config.metrics.every((metric) => metric.dataState === 'sample')).toBe(true);
    expect(config.commandModules.every((module) => module.dataState === 'sample')).toBe(true);
    expect(config.note).toContain('API connectivity does not certify these business figures');
    expect(config.rightRailSections.every((section) => section.title.startsWith('Sample:'))).toBe(true);
    expect(config.rightRailSections.every((section) => !section.title.startsWith('Sample: Sample:'))).toBe(true);
    expect(config.user).toMatchObject({ name: 'Grace Whitaker', initials: 'GW', role: 'Head of School' });
    expect(loadSchoolAdministratorLiveSnapshot).toHaveBeenCalledTimes(1);
  });

  it('discloses partial connectivity without promoting school totals to live', async () => {
    loadSchoolAdministratorLiveSnapshot.mockResolvedValue({ serviceState: 'partial', successfulEndpointCount: 1 });
    render(<SchoolAdministratorDashboard />);
    await waitFor(() => expect(captured.config?.note).toContain('1 of 3'));
    expect(captured.config.dataState).toBe('sample');
  });

  it('handles an upstream rejection without presenting sample values as live', async () => {
    loadSchoolAdministratorLiveSnapshot.mockRejectedValue(new Error('upstream 502'));
    render(<SchoolAdministratorDashboard />);
    await waitFor(() => expect(captured.config?.note).toContain('dashboard APIs unavailable'));
    expect(captured.config.dataState).toBe('sample');
  });
});
