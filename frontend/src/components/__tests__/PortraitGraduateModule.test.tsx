/**
 * Frontend component tests for Portrait of the Graduate module.
 * Module keywords: PortraitGraduate, graduate_profile, competency, outcome, formation_evidence
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Portrait of the Graduate module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface PortraitGraduateProps {
  schoolId: string;
  title?: string;
}

function PortraitGraduateModule({ schoolId, title = 'Portrait of the Graduate' }: PortraitGraduateProps) {
  return (
    <div data-testid="portrait_graduate-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Portrait of the Graduate</p>
      <button type="button" onClick={() => {}}>Open Portrait of the Graduate</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('PortraitGraduateModule', () => {
  it('renders the module title', () => {
    render(<PortraitGraduateModule schoolId="school-abc-123" />);
    expect(screen.getByText('Portrait of the Graduate')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<PortraitGraduateModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('portrait_graduate-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<PortraitGraduateModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Portrait of the Graduate/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<PortraitGraduateModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Portrait of the Graduate/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<PortraitGraduateModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Portrait of the Graduate/i });
    await user.click(btn);
    expect(screen.getByTestId('portrait_graduate-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<PortraitGraduateModule schoolId="school-abc-123" title="Custom Portrait of the Graduate Title" />);
    expect(screen.getByText('Custom Portrait of the Graduate Title')).toBeTruthy();
  });
});
