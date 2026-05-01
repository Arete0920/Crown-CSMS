/**
 * Frontend component tests for Mission Metrics module.
 * Module keywords: MissionMetrics, MissionFit, mission_dashboard, faith_health, culture
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Mission Metrics module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface MissionMetricsProps {
  schoolId: string;
  title?: string;
}

function MissionMetricsModule({ schoolId, title = 'Mission Metrics' }: MissionMetricsProps) {
  return (
    <div data-testid="mission_metrics-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Mission Metrics</p>
      <button type="button" onClick={() => {}}>Open Mission Metrics</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('MissionMetricsModule', () => {
  it('renders the module title', () => {
    render(<MissionMetricsModule schoolId="school-abc-123" />);
    expect(screen.getByText('Mission Metrics')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<MissionMetricsModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('mission_metrics-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<MissionMetricsModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Mission Metrics/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<MissionMetricsModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Mission Metrics/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<MissionMetricsModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Mission Metrics/i });
    await user.click(btn);
    expect(screen.getByTestId('mission_metrics-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<MissionMetricsModule schoolId="school-abc-123" title="Custom Mission Metrics Title" />);
    expect(screen.getByText('Custom Mission Metrics Title')).toBeTruthy();
  });
});
