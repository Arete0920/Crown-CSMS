// @vitest-environment jsdom
import { render } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import AdmissionsDashboard from './AdmissionsDashboard.jsx';

const captured = {
  config: null,
  roleKey: null,
};

vi.mock('../components/crown-dashboard/CrownDashboardTemplate.jsx', () => ({
  default: ({ config, roleKey }) => {
    captured.config = config;
    captured.roleKey = roleKey;
    return null;
  },
}));

const mockUseAdmissionsDashboardData = vi.fn();

vi.mock('../hooks/useAdmissionsDashboardData.js', () => ({
  default: () => mockUseAdmissionsDashboardData(),
}));

describe('AdmissionsDashboard data truth contract', () => {
  beforeEach(() => {
    captured.config = null;
    captured.roleKey = null;
    mockUseAdmissionsDashboardData.mockReset();
  });

  it('marks metrics and modules as fallback when no live summary is available', () => {
    mockUseAdmissionsDashboardData.mockReturnValue({
      loading: false,
      error: '',
      summary: {},
      rawSummary: {},
      timeline: [],
    });

    render(<AdmissionsDashboard />);

    expect(captured.roleKey).toBe('admissions');
    expect(Array.isArray(captured.config.metrics)).toBe(true);
    expect(captured.config.metrics.every((metric) => metric.dataState === 'fallback')).toBe(true);
    expect(captured.config.metrics.every((metric) => metric.sourceLabel === 'Admissions template fallback')).toBe(true);
    expect(captured.config.commandModules.every((module) => module.dataState === 'fallback')).toBe(true);
    expect(captured.config.commandModules.every((module) => module.sourceLabel === 'Admissions template fallback')).toBe(true);
  });

  it('marks metrics and modules as live when pipeline stages are available', () => {
    mockUseAdmissionsDashboardData.mockReturnValue({
      loading: false,
      error: '',
      summary: {
        total: 9,
        submitted: 4,
        admitted: 2,
        enrolled: 1,
        underReview: 2,
      },
      rawSummary: {
        pipeline: {
          total: 9,
          by_stage: {
            inquiry: 3,
            application_submitted: 4,
            accepted: 2,
            enrolled: 1,
          },
        },
        conversion: {
          accepted_to_enrolled: 0.5,
          inquiry_to_submitted: 0.8,
          submitted_to_accepted: 0.5,
        },
      },
      timeline: [],
    });

    render(<AdmissionsDashboard />);

    expect(captured.config.metrics.every((metric) => metric.dataState === 'live')).toBe(true);
    expect(captured.config.metrics.every((metric) => metric.sourceLabel === 'Admissions summary API')).toBe(true);
    expect(captured.config.commandModules.every((module) => module.dataState === 'live')).toBe(true);
    expect(captured.config.commandModules.every((module) => module.sourceLabel === 'Admissions summary API')).toBe(true);
  });

  it('marks metrics and modules as loading while the admissions summary is in flight', () => {
    mockUseAdmissionsDashboardData.mockReturnValue({
      loading: true,
      error: '',
      summary: {},
      rawSummary: {},
      timeline: [],
    });

    render(<AdmissionsDashboard />);

    expect(captured.config.metrics.every((metric) => metric.dataState === 'loading')).toBe(true);
    expect(captured.config.metrics.every((metric) => metric.sourceLabel === 'Admissions summary API loading')).toBe(true);
    expect(captured.config.commandModules.every((module) => module.dataState === 'loading')).toBe(true);
    expect(captured.config.commandModules.every((module) => module.sourceLabel === 'Admissions summary API loading')).toBe(true);
  });

  it('marks metrics and modules as unavailable when the admissions summary API fails', () => {
    mockUseAdmissionsDashboardData.mockReturnValue({
      loading: false,
      error: 'Admissions summary failed.',
      summary: {},
      rawSummary: {},
      timeline: [],
    });

    render(<AdmissionsDashboard />);

    expect(captured.config.metrics.every((metric) => metric.dataState === 'unavailable')).toBe(true);
    expect(captured.config.metrics.every((metric) => metric.sourceLabel === 'Admissions summary API unavailable')).toBe(true);
    expect(captured.config.commandModules.every((module) => module.dataState === 'unavailable')).toBe(true);
    expect(captured.config.commandModules.every((module) => module.sourceLabel === 'Admissions summary API unavailable')).toBe(true);
  });
});
