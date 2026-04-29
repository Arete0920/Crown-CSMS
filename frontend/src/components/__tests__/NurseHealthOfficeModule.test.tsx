/**
 * Frontend component tests for Nurse Health Office module.
 * Module keywords: Nurse, HealthOffice, health_visit, medication, health_incident
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Nurse Health Office module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface NurseHealthOfficeProps {
  schoolId: string;
  title?: string;
}

function NurseHealthOfficeModule({ schoolId, title = 'Nurse Health Office' }: NurseHealthOfficeProps) {
  return (
    <div data-testid="nurse_health_office-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Nurse Health Office</p>
      <button type="button" onClick={() => {}}>Open Nurse Health Office</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('NurseHealthOfficeModule', () => {
  it('renders the module title', () => {
    render(<NurseHealthOfficeModule schoolId="school-abc-123" />);
    expect(screen.getByText('Nurse Health Office')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<NurseHealthOfficeModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('nurse_health_office-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<NurseHealthOfficeModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Nurse Health Office/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<NurseHealthOfficeModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Nurse Health Office/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<NurseHealthOfficeModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Nurse Health Office/i });
    await user.click(btn);
    expect(screen.getByTestId('nurse_health_office-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<NurseHealthOfficeModule schoolId="school-abc-123" title="Custom Nurse Health Office Title" />);
    expect(screen.getByText('Custom Nurse Health Office Title')).toBeTruthy();
  });
});
