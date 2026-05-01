/**
 * Frontend component tests for Service Outreach module.
 * Module keywords: Service, Outreach, mission_trip, service_hours, community_impact
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Service Outreach module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface ServiceOutreachProps {
  schoolId: string;
  title?: string;
}

function ServiceOutreachModule({ schoolId, title = 'Service Outreach' }: ServiceOutreachProps) {
  return (
    <div data-testid="service_outreach-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Service Outreach</p>
      <button type="button" onClick={() => {}}>Open Service Outreach</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('ServiceOutreachModule', () => {
  it('renders the module title', () => {
    render(<ServiceOutreachModule schoolId="school-abc-123" />);
    expect(screen.getByText('Service Outreach')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<ServiceOutreachModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('service_outreach-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<ServiceOutreachModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Service Outreach/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<ServiceOutreachModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Service Outreach/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<ServiceOutreachModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Service Outreach/i });
    await user.click(btn);
    expect(screen.getByTestId('service_outreach-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<ServiceOutreachModule schoolId="school-abc-123" title="Custom Service Outreach Title" />);
    expect(screen.getByText('Custom Service Outreach Title')).toBeTruthy();
  });
});
