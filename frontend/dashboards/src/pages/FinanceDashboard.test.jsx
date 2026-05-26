// @vitest-environment jsdom
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import FinanceDashboard from './FinanceDashboard.jsx';

const mockUseFinanceDashboardData = vi.fn();

vi.mock('../hooks/useFinanceDashboardData', () => ({
  default: () => mockUseFinanceDashboardData(),
}));

vi.mock('../components/crown/CrownLayout.jsx', () => ({
  default: ({ children }) => <div>{children}</div>,
}));

describe('FinanceDashboard truth disclosure', () => {
  beforeEach(() => {
    mockUseFinanceDashboardData.mockReset();
  });

  it('shows live finance disclosure when data loads successfully', () => {
    mockUseFinanceDashboardData.mockReturnValue({
      loading: false,
      error: '',
      metrics: {},
      summary: {},
      invoices: [],
      reload: vi.fn(),
    });

    render(<FinanceDashboard />);

    expect(screen.getByText('Live finance data')).toBeTruthy();
    expect(screen.getByText('Finance metrics API')).toBeTruthy();
  });

  it('shows unavailable finance disclosure when the API fails', () => {
    mockUseFinanceDashboardData.mockReturnValue({
      loading: false,
      error: 'Unable to load finance dashboard data.',
      metrics: null,
      summary: null,
      invoices: [],
      reload: vi.fn(),
    });

    render(<FinanceDashboard />);

    expect(screen.getByText('Finance data unavailable')).toBeTruthy();
    expect(screen.getByText('Finance API unavailable')).toBeTruthy();
    expect(screen.getByText('Unable to load finance dashboard data.')).toBeTruthy();
  });
});
