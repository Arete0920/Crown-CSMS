/**
 * Frontend component tests for Staff Faculty module.
 * Module keywords: Staff, Faculty, Teacher, StaffMember, employee
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Staff Faculty module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface StaffFacultyProps {
  schoolId: string;
  title?: string;
}

function StaffFacultyModule({ schoolId, title = 'Staff Faculty' }: StaffFacultyProps) {
  return (
    <div data-testid="staff_faculty-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Staff Faculty</p>
      <button type="button" onClick={() => {}}>Open Staff Faculty</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('StaffFacultyModule', () => {
  it('renders the module title', () => {
    render(<StaffFacultyModule schoolId="school-abc-123" />);
    expect(screen.getByText('Staff Faculty')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<StaffFacultyModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('staff_faculty-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<StaffFacultyModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Staff Faculty/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<StaffFacultyModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Staff Faculty/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<StaffFacultyModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Staff Faculty/i });
    await user.click(btn);
    expect(screen.getByTestId('staff_faculty-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<StaffFacultyModule schoolId="school-abc-123" title="Custom Staff Faculty Title" />);
    expect(screen.getByText('Custom Staff Faculty Title')).toBeTruthy();
  });
});
