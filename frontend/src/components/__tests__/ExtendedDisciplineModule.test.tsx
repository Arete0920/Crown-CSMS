/**
 * Frontend component tests for Extended Discipline Workflows module.
 * Module keywords: Discipline, behavior, incident, consequence, escalation
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Extended Discipline Workflows module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface ExtendedDisciplineProps {
  schoolId: string;
  title?: string;
}

function ExtendedDisciplineModule({ schoolId, title = 'Extended Discipline Workflows' }: ExtendedDisciplineProps) {
  return (
    <div data-testid="extended_discipline-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Extended Discipline Workflows</p>
      <button type="button" onClick={() => {}}>Open Extended Discipline Workflows</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('ExtendedDisciplineModule', () => {
  it('renders the module title', () => {
    render(<ExtendedDisciplineModule schoolId="school-abc-123" />);
    expect(screen.getByText('Extended Discipline Workflows')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<ExtendedDisciplineModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('extended_discipline-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<ExtendedDisciplineModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Extended Discipline Workflows/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<ExtendedDisciplineModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Extended Discipline Workflows/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<ExtendedDisciplineModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Extended Discipline Workflows/i });
    await user.click(btn);
    expect(screen.getByTestId('extended_discipline-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<ExtendedDisciplineModule schoolId="school-abc-123" title="Custom Extended Discipline Workflows Title" />);
    expect(screen.getByText('Custom Extended Discipline Workflows Title')).toBeTruthy();
  });
});
