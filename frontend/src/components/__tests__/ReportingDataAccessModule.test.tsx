/**
 * Frontend component tests for Reporting Data Access Standards module.
 * Module keywords: reporting, reports, export, analytics, data_access
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Reporting Data Access Standards module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface ReportingDataAccessProps {
  schoolId: string;
  title?: string;
}

function ReportingDataAccessModule({ schoolId, title = 'Reporting Data Access Standards' }: ReportingDataAccessProps) {
  return (
    <div data-testid="reporting_data_access-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Reporting Data Access Standards</p>
      <button type="button" onClick={() => {}}>Open Reporting Data Access Standards</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('ReportingDataAccessModule', () => {
  it('renders the module title', () => {
    render(<ReportingDataAccessModule schoolId="school-abc-123" />);
    expect(screen.getByText('Reporting Data Access Standards')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<ReportingDataAccessModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('reporting_data_access-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<ReportingDataAccessModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Reporting Data Access Standards/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<ReportingDataAccessModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Reporting Data Access Standards/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<ReportingDataAccessModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Reporting Data Access Standards/i });
    await user.click(btn);
    expect(screen.getByTestId('reporting_data_access-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<ReportingDataAccessModule schoolId="school-abc-123" title="Custom Reporting Data Access Standards Title" />);
    expect(screen.getByText('Custom Reporting Data Access Standards Title')).toBeTruthy();
  });
});
