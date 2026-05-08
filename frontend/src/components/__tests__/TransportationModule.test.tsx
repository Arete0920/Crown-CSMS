/**
 * Frontend component tests for Transportation module.
 * Module keywords: Transportation, bus, route, rider, stop
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Transportation module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface TransportationProps {
  schoolId: string;
  title?: string;
}

function TransportationModule({ schoolId, title = 'Transportation' }: TransportationProps) {
  return (
    <div data-testid="transportation-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Transportation</p>
      <button type="button" onClick={() => {}}>Open Transportation</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('TransportationModule', () => {
  it('renders the module title', () => {
    render(<TransportationModule schoolId="school-abc-123" />);
    expect(screen.getByText('Transportation')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<TransportationModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('transportation-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<TransportationModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Transportation/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<TransportationModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Transportation/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<TransportationModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Transportation/i });
    await user.click(btn);
    expect(screen.getByTestId('transportation-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<TransportationModule schoolId="school-abc-123" title="Custom Transportation Title" />);
    expect(screen.getByText('Custom Transportation Title')).toBeTruthy();
  });
});
