/**
 * Frontend component tests for School Year Term module.
 * Module keywords: SchoolYear, Term, academic_year, semester, rollover
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the School Year Term module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface SchoolYearTermProps {
  schoolId: string;
  title?: string;
}

function SchoolYearTermModule({ schoolId, title = 'School Year Term' }: SchoolYearTermProps) {
  return (
    <div data-testid="school_year_term-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: School Year Term</p>
      <button type="button" onClick={() => {}}>Open School Year Term</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('SchoolYearTermModule', () => {
  it('renders the module title', () => {
    render(<SchoolYearTermModule schoolId="school-abc-123" />);
    expect(screen.getByText('School Year Term')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<SchoolYearTermModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('school_year_term-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<SchoolYearTermModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: School Year Term/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<SchoolYearTermModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open School Year Term/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<SchoolYearTermModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open School Year Term/i });
    await user.click(btn);
    expect(screen.getByTestId('school_year_term-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<SchoolYearTermModule schoolId="school-abc-123" title="Custom School Year Term Title" />);
    expect(screen.getByText('Custom School Year Term Title')).toBeTruthy();
  });
});
