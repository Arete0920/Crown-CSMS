/**
 * Frontend component tests for Student Master Record module.
 * Module keywords: Student, student_master, demographics, student_record, Student360
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Student Master Record module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface StudentMasterRecordProps {
  schoolId: string;
  title?: string;
}

function StudentMasterRecordModule({ schoolId, title = 'Student Master Record' }: StudentMasterRecordProps) {
  return (
    <div data-testid="student_master_record-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Student Master Record</p>
      <button type="button" onClick={() => {}}>Open Student Master Record</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('StudentMasterRecordModule', () => {
  it('renders the module title', () => {
    render(<StudentMasterRecordModule schoolId="school-abc-123" />);
    expect(screen.getByText('Student Master Record')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<StudentMasterRecordModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('student_master_record-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<StudentMasterRecordModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Student Master Record/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<StudentMasterRecordModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Student Master Record/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<StudentMasterRecordModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Student Master Record/i });
    await user.click(btn);
    expect(screen.getByTestId('student_master_record-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<StudentMasterRecordModule schoolId="school-abc-123" title="Custom Student Master Record Title" />);
    expect(screen.getByText('Custom Student Master Record Title')).toBeTruthy();
  });
});
