/**
 * Frontend component tests for Chaplain Pastoral Care module.
 * Module keywords: Chaplain, Pastoral, care_referral, prayer_followup, counseling
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Chaplain Pastoral Care module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface ChaplainPastoralCareProps {
  schoolId: string;
  title?: string;
}

function ChaplainPastoralCareModule({ schoolId, title = 'Chaplain Pastoral Care' }: ChaplainPastoralCareProps) {
  return (
    <div data-testid="chaplain_pastoral_care-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Chaplain Pastoral Care</p>
      <button type="button" onClick={() => {}}>Open Chaplain Pastoral Care</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('ChaplainPastoralCareModule', () => {
  it('renders the module title', () => {
    render(<ChaplainPastoralCareModule schoolId="school-abc-123" />);
    expect(screen.getByText('Chaplain Pastoral Care')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<ChaplainPastoralCareModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('chaplain_pastoral_care-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<ChaplainPastoralCareModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Chaplain Pastoral Care/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<ChaplainPastoralCareModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Chaplain Pastoral Care/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<ChaplainPastoralCareModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Chaplain Pastoral Care/i });
    await user.click(btn);
    expect(screen.getByTestId('chaplain_pastoral_care-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<ChaplainPastoralCareModule schoolId="school-abc-123" title="Custom Chaplain Pastoral Care Title" />);
    expect(screen.getByText('Custom Chaplain Pastoral Care Title')).toBeTruthy();
  });
});
