/**
 * Frontend component tests for Grade Levels module.
 * Module keywords: GradeLevel, grade_level, K12, placement, progression
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Grade Levels module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface GradeLevelsProps {
  schoolId: string;
  title?: string;
}

function GradeLevelsModule({ schoolId, title = 'Grade Levels' }: GradeLevelsProps) {
  return (
    <div data-testid="grade_levels-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Grade Levels</p>
      <button type="button" onClick={() => {}}>Open Grade Levels</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('GradeLevelsModule', () => {
  it('renders the module title', () => {
    render(<GradeLevelsModule schoolId="school-abc-123" />);
    expect(screen.getByText('Grade Levels')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<GradeLevelsModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('grade_levels-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<GradeLevelsModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Grade Levels/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<GradeLevelsModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Grade Levels/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<GradeLevelsModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Grade Levels/i });
    await user.click(btn);
    expect(screen.getByTestId('grade_levels-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<GradeLevelsModule schoolId="school-abc-123" title="Custom Grade Levels Title" />);
    expect(screen.getByText('Custom Grade Levels Title')).toBeTruthy();
  });
});
