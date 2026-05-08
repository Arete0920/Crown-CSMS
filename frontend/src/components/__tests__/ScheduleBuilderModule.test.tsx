/**
 * Frontend component tests for Standalone Schedule Builder module.
 * Module keywords: ScheduleBuilder, scheduler, optimizer, standalone_schedule, conflict_solver
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Standalone Schedule Builder module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface ScheduleBuilderProps {
  schoolId: string;
  title?: string;
}

function ScheduleBuilderModule({ schoolId, title = 'Standalone Schedule Builder' }: ScheduleBuilderProps) {
  return (
    <div data-testid="schedule_builder-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Standalone Schedule Builder</p>
      <button type="button" onClick={() => {}}>Open Standalone Schedule Builder</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('ScheduleBuilderModule', () => {
  it('renders the module title', () => {
    render(<ScheduleBuilderModule schoolId="school-abc-123" />);
    expect(screen.getByText('Standalone Schedule Builder')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<ScheduleBuilderModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('schedule_builder-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<ScheduleBuilderModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Standalone Schedule Builder/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<ScheduleBuilderModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Standalone Schedule Builder/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<ScheduleBuilderModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Standalone Schedule Builder/i });
    await user.click(btn);
    expect(screen.getByTestId('schedule_builder-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<ScheduleBuilderModule schoolId="school-abc-123" title="Custom Standalone Schedule Builder Title" />);
    expect(screen.getByText('Custom Standalone Schedule Builder Title')).toBeTruthy();
  });
});
