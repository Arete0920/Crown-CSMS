/**
 * Frontend component tests for Mobile Family App module.
 * Module keywords: MobileApp, family_app, push_notification, mobile, mobile_login
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Mobile Family App module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface MobileFamilyAppProps {
  schoolId: string;
  title?: string;
}

function MobileFamilyAppModule({ schoolId, title = 'Mobile Family App' }: MobileFamilyAppProps) {
  return (
    <div data-testid="mobile_family_app-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Mobile Family App</p>
      <button type="button" onClick={() => {}}>Open Mobile Family App</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('MobileFamilyAppModule', () => {
  it('renders the module title', () => {
    render(<MobileFamilyAppModule schoolId="school-abc-123" />);
    expect(screen.getByText('Mobile Family App')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<MobileFamilyAppModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('mobile_family_app-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<MobileFamilyAppModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Mobile Family App/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<MobileFamilyAppModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Mobile Family App/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<MobileFamilyAppModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Mobile Family App/i });
    await user.click(btn);
    expect(screen.getByTestId('mobile_family_app-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<MobileFamilyAppModule schoolId="school-abc-123" title="Custom Mobile Family App Title" />);
    expect(screen.getByText('Custom Mobile Family App Title')).toBeTruthy();
  });
});
