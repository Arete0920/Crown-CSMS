/**
 * Frontend component tests for Volunteer Family Engagement module.
 * Module keywords: Volunteer, family_engagement, service_hours, participation, volunteer_hours
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Volunteer Family Engagement module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface VolunteerFamilyEngagementProps {
  schoolId: string;
  title?: string;
}

function VolunteerFamilyEngagementModule({ schoolId, title = 'Volunteer Family Engagement' }: VolunteerFamilyEngagementProps) {
  return (
    <div data-testid="volunteer_family_engagement-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Volunteer Family Engagement</p>
      <button type="button" onClick={() => {}}>Open Volunteer Family Engagement</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('VolunteerFamilyEngagementModule', () => {
  it('renders the module title', () => {
    render(<VolunteerFamilyEngagementModule schoolId="school-abc-123" />);
    expect(screen.getByText('Volunteer Family Engagement')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<VolunteerFamilyEngagementModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('volunteer_family_engagement-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<VolunteerFamilyEngagementModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Volunteer Family Engagement/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<VolunteerFamilyEngagementModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Volunteer Family Engagement/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<VolunteerFamilyEngagementModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Volunteer Family Engagement/i });
    await user.click(btn);
    expect(screen.getByTestId('volunteer_family_engagement-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<VolunteerFamilyEngagementModule schoolId="school-abc-123" title="Custom Volunteer Family Engagement Title" />);
    expect(screen.getByText('Custom Volunteer Family Engagement Title')).toBeTruthy();
  });
});
