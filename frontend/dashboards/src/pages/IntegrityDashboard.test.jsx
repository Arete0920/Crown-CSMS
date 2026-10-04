// @vitest-environment jsdom
import { act, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import IntegrityDashboard from './IntegrityDashboard.jsx';

vi.mock('../components/crown/CrownLayout.jsx', () => ({
  default: ({ children }) => <div>{children}</div>,
}));

vi.mock('../components/crown/CrownCard.jsx', () => ({
  default: ({ title, children }) => (
    <section>
      <h2>{title}</h2>
      {children}
    </section>
  ),
}));

vi.mock('../components/crown/CrownGrid.jsx', () => ({
  CrownGrid: ({ children }) => <div>{children}</div>,
  Col: ({ children }) => <div>{children}</div>,
}));

vi.mock('../components/dashboard/KpiFlipCard.jsx', () => ({
  KpiStrip: ({ cards }) => (
    <div>
      {cards.map((card) => (
        <div key={card.label}>{card.label}: {card.value}</div>
      ))}
    </div>
  ),
}));

const systemPayload = {
  ok: true,
  build_sha: '1234567890abcdef',
  github_commit_url: 'https://example.test/commit',
  github_repo: 'example/repo',
  env: 'dev',
  version: '1.0.0',
  timestamp: '2026-10-04T00:00:00Z',
  required_checks: ['pytest'],
  meta_gates: [],
};

const qualityPayload = {
  schema_version: 1,
  mode: 'read_only',
  automatic_remediation: false,
  school_id: 'school-a',
  generated_at: '2026-10-04T00:00:00Z',
  status: 'action_required',
  summary: {
    findings_count: 2,
    critical: 0,
    high: 1,
    medium: 1,
    low: 0,
  },
  checks: [
    {
      id: 'current_academic_year_configuration',
      label: 'Current academic year configuration',
      severity: 'high',
      count: 1,
      status: 'review',
      description: 'Exactly one current academic year is expected.',
      action: 'Review academic-year configuration.',
    },
    {
      id: 'active_student_grade_assignment',
      label: 'Active students without grade assignment',
      severity: 'medium',
      count: 1,
      status: 'review',
      description: 'Active students are missing a grade.',
      action: 'Review registrar placement.',
    },
    {
      id: 'cross_tenant_relationship_integrity',
      label: 'Cross-tenant relationship integrity',
      severity: 'critical',
      count: 0,
      status: 'pass',
      description: 'Cross-tenant checks.',
      action: 'Review.',
    },
  ],
};

describe('IntegrityDashboard school data quality', () => {
  beforeEach(() => {
    sessionStorage.clear();
    sessionStorage.setItem('crown.jwt.access', 'token-a');
    sessionStorage.setItem('crown.school.id', 'school-a');

    globalThis.fetch = vi.fn((url) => {
      if (String(url).includes('/api/v1/integrity/data-quality/')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(qualityPayload),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(systemPayload),
      });
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders live tenant-scoped data-quality findings without fallback metrics', async () => {
    await act(async () => {
      render(<IntegrityDashboard />);
    });

    await waitFor(() => {
      expect(screen.getByText('Open Findings: 2')).toBeTruthy();
    });

    expect(screen.getByText('Critical: 0')).toBeTruthy();
    expect(screen.getByText('High Priority: 1')).toBeTruthy();
    expect(screen.getByText('Checks Clear: 1')).toBeTruthy();
    expect(screen.getByText('Current academic year configuration')).toBeTruthy();
    expect(screen.getByText('Active students without grade assignment')).toBeTruthy();
    expect(screen.getByText('No review action required.')).toBeTruthy();

    const qualityCall = globalThis.fetch.mock.calls.find(([url]) =>
      String(url).includes('/api/v1/integrity/data-quality/')
    );
    expect(qualityCall).toBeTruthy();
    expect(qualityCall[1].headers.Authorization).toBe('Bearer token-a');
    expect(qualityCall[1].headers['X-School-Id']).toBe('school-a');
  });

  it('shows unavailable instead of invented data when the quality endpoint fails', async () => {
    globalThis.fetch = vi.fn((url) => {
      if (String(url).includes('/api/v1/integrity/data-quality/')) {
        return Promise.resolve({
          ok: false,
          json: () => Promise.resolve({ detail: 'Unavailable' }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(systemPayload),
      });
    });

    await act(async () => {
      render(<IntegrityDashboard />);
    });

    await waitFor(() => {
      expect(screen.getByText('School data quality is unavailable.')).toBeTruthy();
    });

    expect(screen.getByText('No fallback or sample findings are displayed.')).toBeTruthy();
    expect(screen.getByText('Open Findings: —')).toBeTruthy();
  });
});
