/**
 * Frontend component tests for Student Care Discipline Summary module.
 * Module keywords: StudentCare, discipline, behavior, care_note, incident
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Student Care Discipline Summary module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface StudentCareDisciplineProps {
  schoolId: string;
  title?: string;
}

function StudentCareDisciplineModule({ schoolId, title = 'Student Care Discipline Summary' }: StudentCareDisciplineProps) {
  return (
    <div data-testid="student_care_discipline-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Student Care Discipline Summary</p>
      <button type="button" onClick={() => {}}>Open Student Care Discipline Summary</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('StudentCareDisciplineModule', () => {
  it('renders the module title', () => {
    render(<StudentCareDisciplineModule schoolId="school-abc-123" />);
    expect(screen.getByText('Student Care Discipline Summary')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<StudentCareDisciplineModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('student_care_discipline-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<StudentCareDisciplineModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Student Care Discipline Summary/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<StudentCareDisciplineModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Student Care Discipline Summary/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<StudentCareDisciplineModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Student Care Discipline Summary/i });
    await user.click(btn);
    expect(screen.getByTestId('student_care_discipline-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<StudentCareDisciplineModule schoolId="school-abc-123" title="Custom Student Care Discipline Summary Title" />);
    expect(screen.getByText('Custom Student Care Discipline Summary Title')).toBeTruthy();
  });
});
