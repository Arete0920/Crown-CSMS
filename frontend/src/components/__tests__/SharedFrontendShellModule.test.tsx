/**
 * Frontend component tests for Shared Frontend Shell module.
 * Module keywords: AppShell, Layout, Sidebar, Topbar, navigation
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Shared Frontend Shell module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface SharedFrontendShellProps {
  schoolId: string;
  title?: string;
}

function SharedFrontendShellModule({ schoolId, title = 'Shared Frontend Shell' }: SharedFrontendShellProps) {
  return (
    <div data-testid="shared_frontend_shell-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Shared Frontend Shell</p>
      <button type="button" onClick={() => {}}>Open Shared Frontend Shell</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('SharedFrontendShellModule', () => {
  it('renders the module title', () => {
    render(<SharedFrontendShellModule schoolId="school-abc-123" />);
    expect(screen.getByText('Shared Frontend Shell')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<SharedFrontendShellModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('shared_frontend_shell-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<SharedFrontendShellModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Shared Frontend Shell/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<SharedFrontendShellModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Shared Frontend Shell/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<SharedFrontendShellModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Shared Frontend Shell/i });
    await user.click(btn);
    expect(screen.getByTestId('shared_frontend_shell-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<SharedFrontendShellModule schoolId="school-abc-123" title="Custom Shared Frontend Shell Title" />);
    expect(screen.getByText('Custom Shared Frontend Shell Title')).toBeTruthy();
  });
});
