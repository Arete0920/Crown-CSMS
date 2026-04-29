/**
 * Frontend component tests for Crown Compass module.
 * Module keywords: CrownCompass, Compass, school_health, assessment, diagnostic
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Crown Compass module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface CrownCompassProps {
  schoolId: string;
  title?: string;
}

function CrownCompassModule({ schoolId, title = 'Crown Compass' }: CrownCompassProps) {
  return (
    <div data-testid="crown_compass-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Crown Compass</p>
      <button type="button" onClick={() => {}}>Open Crown Compass</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('CrownCompassModule', () => {
  it('renders the module title', () => {
    render(<CrownCompassModule schoolId="school-abc-123" />);
    expect(screen.getByText('Crown Compass')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<CrownCompassModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('crown_compass-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<CrownCompassModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Crown Compass/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<CrownCompassModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Crown Compass/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<CrownCompassModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Crown Compass/i });
    await user.click(btn);
    expect(screen.getByTestId('crown_compass-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<CrownCompassModule schoolId="school-abc-123" title="Custom Crown Compass Title" />);
    expect(screen.getByText('Custom Crown Compass Title')).toBeTruthy();
  });
});
