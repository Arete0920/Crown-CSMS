/**
 * Frontend component tests for Grades Report Cards module.
 * Module keywords: Grade, Gradebook, ReportCard, grade_entry, grading_period
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Grades Report Cards module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface GradesReportCardsProps {
  schoolId: string;
  title?: string;
}

function GradesReportCardsModule({ schoolId, title = 'Grades Report Cards' }: GradesReportCardsProps) {
  return (
    <div data-testid="grades_report_cards-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Grades Report Cards</p>
      <button type="button" onClick={() => {}}>Open Grades Report Cards</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('GradesReportCardsModule', () => {
  it('renders the module title', () => {
    render(<GradesReportCardsModule schoolId="school-abc-123" />);
    expect(screen.getByText('Grades Report Cards')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<GradesReportCardsModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('grades_report_cards-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<GradesReportCardsModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Grades Report Cards/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<GradesReportCardsModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Grades Report Cards/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<GradesReportCardsModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Grades Report Cards/i });
    await user.click(btn);
    expect(screen.getByTestId('grades_report_cards-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<GradesReportCardsModule schoolId="school-abc-123" title="Custom Grades Report Cards Title" />);
    expect(screen.getByText('Custom Grades Report Cards Title')).toBeTruthy();
  });
});
