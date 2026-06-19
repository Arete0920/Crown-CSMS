// @vitest-environment jsdom
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';

import ComplianceAuditDashboard from './ComplianceAuditDashboard.jsx';

const mockUseDashboardData = vi.fn();

vi.mock('../hooks/useDashboardData.js', () => ({
  default: (...args) => mockUseDashboardData(...args),
}));

describe('ComplianceAuditDashboard truth alignment', () => {
  beforeEach(() => {
    mockUseDashboardData.mockReset();
    mockUseDashboardData.mockReturnValue({
      data: {
        dashboard_key: 'compliance-audit',
        metrics: [
          { label: 'Open Compliance Items', value: '11', secondary: 'Sample compliance summary payload.' },
          { label: 'Audits Completed This Year', value: '4', secondary: 'Sample compliance summary payload.' },
          { label: 'Policies Reviewed', value: '23', secondary: 'Sample compliance summary payload.' },
          { label: 'Training Completion Rate', value: '87%', secondary: 'Sample compliance summary payload.' },
        ],
        alerts: [
          {
            title: '3 compliance items are past due by 14+ days',
            level: 'High',
            secondary: 'Escalate to administration immediately.',
          },
        ],
        queue: ['Escalate 3 overdue compliance items to administration'],
        meta: {
          served_from: 'sample',
          truth_source: 'backend/crown_api/dashboards/sample_payloads.py:compliance_audit_sample_payload',
        },
      },
      error: null,
      loading: false,
      source: 'live',
      lastLoadedAt: '2026-06-19T21:42:00Z',
      certification: {
        status: 'scaffold',
        owner: 'Compliance Team',
        notes: '',
      },
      config: {
        endpoint: '/api/v1/dashboards/compliance-audit/summary',
      },
    });
  });

  it('renders the compliance dashboard title, sample-backed metrics, and source disclosure', () => {
    render(
      <MemoryRouter>
        <ComplianceAuditDashboard />
      </MemoryRouter>,
    );

    expect(screen.getByText('Good morning, Compliance Team!')).toBeTruthy();
    expect(screen.getByText('Open Compliance Items')).toBeTruthy();
    expect(screen.getByText('11')).toBeTruthy();
    expect(screen.getByText('Audits Completed This Year')).toBeTruthy();
    expect(screen.getAllByText('4').length).toBeGreaterThan(0);
    expect(screen.getByText('Policies Reviewed')).toBeTruthy();
    expect(screen.getByText('23')).toBeTruthy();
    expect(screen.getByText('Training Completion Rate')).toBeTruthy();
    expect(screen.getByText('87%')).toBeTruthy();
    expect(screen.getAllByText(/Dashboard summary service sample/i).length).toBeGreaterThan(0);
  });
});
