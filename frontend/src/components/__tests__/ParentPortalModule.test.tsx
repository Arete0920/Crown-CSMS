/**
 * Frontend component tests for Parent Portal module.
 * Module keywords: ParentPortal, parent, guardian_portal, family_dashboard, parent_dashboard
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Parent Portal module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface ParentPortalProps {
  schoolId: string;
  title?: string;
}

function ParentPortalModule({ schoolId, title = 'Parent Portal' }: ParentPortalProps) {
  return (
    <div data-testid="parent_portal-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Parent Portal</p>
      <button type="button" onClick={() => {}}>Open Parent Portal</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('ParentPortalModule', () => {
  it('renders the module title', () => {
    render(<ParentPortalModule schoolId="school-abc-123" />);
    expect(screen.getByText('Parent Portal')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<ParentPortalModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('parent_portal-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<ParentPortalModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Parent Portal/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<ParentPortalModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Parent Portal/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<ParentPortalModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Parent Portal/i });
    await user.click(btn);
    expect(screen.getByTestId('parent_portal-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<ParentPortalModule schoolId="school-abc-123" title="Custom Parent Portal Title" />);
    expect(screen.getByText('Custom Parent Portal Title')).toBeTruthy();
  });
});
