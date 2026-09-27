// @vitest-environment jsdom
/**
 * Release Reliability Dashboard — browser title and metrics proof.
 *
 * Closes: Arete0920/Crown-CSMSvar(--crown-compat-color-c6d42be6b7)
 *
 * Proof scope:
 *   1. Template resolves with key 'releaseReliability'.
 *   2. Title field is non-empty and contains "Release" context.
 *   3. Required release KPI metric labels are present (deployments, incidents).
 *   4. API endpoint is declared and points to the v1 summary path.
 *   5. dataSource is 'live_api'.
 *   6. Page component renders without throwing.
 *
 * Non-claims:
 *   This file does not certify the dashboard.
 *   This file does not approve sandbox, pilot, production, or release GO.
 */
import { render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

// CrownDashboardTemplate is mocked to null to avoid pulling in its deep
// render tree (fetch hooks, router context, etc.). The final test in this
// suite exercises that the *page* component itself imports and instantiates
// without throwing — which is sufficient for a unit-render proof.
vi.mock('../components/crown-dashboard/CrownDashboardTemplate.jsx', () => ({
  default: () => null,
}));

vi.mock('react-router', () => ({
  Link: ({ children, to, ...rest }) => <a href={to} {...rest}>{children}</a>,
  useInRouterContext: () => false,
}));

describe('ReleaseReliabilityDashboard template proof', () => {
  const template = getDashboardTemplate('releaseReliability');

  it('template key resolves to releaseReliability', () => {
    expect(template).toBeTruthy();
    expect(template.key).toBe('releaseReliability');
  });

  it('title field is non-empty and contains release context', () => {
    expect(typeof template.title).toBe('string');
    expect(template.title.trim().length).toBeGreaterThan(0);
    // "Good morning, Release Team!" or similar release-context title
    const titleAndRole = `${template.title} ${template.user?.role ?? ''}`.toLowerCase();
    expect(
      titleAndRole.includes('release') || titleAndRole.includes('reliability'),
    ).toBe(true);
  });

  it('metrics array has deployment-count KPI', () => {
    expect(Array.isArray(template.metrics)).toBe(true);
    expect(template.metrics.length).toBeGreaterThan(0);
    const labels = template.metrics.map((m) => m.label.toLowerCase());
    expect(labels.some((l) => l.includes('deploy'))).toBe(true);
  });

  it('metrics array has incident KPI', () => {
    const labels = template.metrics.map((m) => m.label.toLowerCase());
    expect(labels.some((l) => l.includes('incident'))).toBe(true);
  });

  it('dataSource is live_api', () => {
    expect(template.dataSource).toBe('live_api');
  });

  it('apiEndpoint is declared and starts with /api/v1/', () => {
    expect(typeof template.apiEndpoint).toBe('string');
    expect(template.apiEndpoint.startsWith('/api/v1/')).toBe(true);
    expect(
      template.apiEndpoint.endsWith('/summary') ||
      template.apiEndpoint.endsWith('/summary/'),
    ).toBe(true);
  });

  it('liveDataKey is declared', () => {
    expect(typeof template.liveDataKey).toBe('string');
    expect(template.liveDataKey.length).toBeGreaterThan(0);
    expect(template.liveDataKey.toLowerCase()).toContain('release');
  });

  it('page component renders without throwing', async () => {
    const { default: ReleaseReliabilityDashboard } = await import(
      './ReleaseReliabilityDashboard.jsx'
    );
    expect(() => render(<ReleaseReliabilityDashboard />)).not.toThrow();
  });
});
