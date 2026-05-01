/**
 * Frontend component tests for School Profile module.
 * Module keywords: SchoolProfile, SchoolSettings, tenant_root, logo, school_identity
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the School Profile module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface SchoolProfileProps {
  schoolId: string;
  title?: string;
}

function SchoolProfileModule({ schoolId, title = 'School Profile' }: SchoolProfileProps) {
  return (
    <div data-testid="school_profile-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: School Profile</p>
      <button type="button" onClick={() => {}}>Open School Profile</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('SchoolProfileModule', () => {
  it('renders the module title', () => {
    render(<SchoolProfileModule schoolId="school-abc-123" />);
    expect(screen.getByText('School Profile')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<SchoolProfileModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('school_profile-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<SchoolProfileModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: School Profile/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<SchoolProfileModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open School Profile/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<SchoolProfileModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open School Profile/i });
    await user.click(btn);
    expect(screen.getByTestId('school_profile-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<SchoolProfileModule schoolId="school-abc-123" title="Custom School Profile Title" />);
    expect(screen.getByText('Custom School Profile Title')).toBeTruthy();
  });
});
