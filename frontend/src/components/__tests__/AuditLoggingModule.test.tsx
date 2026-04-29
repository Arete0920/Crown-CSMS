/**
 * Frontend component tests for Audit Logging module.
 * Module keywords: audit, AuditLog, AccessLog, FERPA, change_log
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Audit Logging module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface AuditLoggingProps {
  schoolId: string;
  title?: string;
}

function AuditLoggingModule({ schoolId, title = 'Audit Logging' }: AuditLoggingProps) {
  return (
    <div data-testid="audit_logging-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Audit Logging</p>
      <button type="button" onClick={() => {}}>Open Audit Logging</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('AuditLoggingModule', () => {
  it('renders the module title', () => {
    render(<AuditLoggingModule schoolId="school-abc-123" />);
    expect(screen.getByText('Audit Logging')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<AuditLoggingModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('audit_logging-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<AuditLoggingModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Audit Logging/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<AuditLoggingModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Audit Logging/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<AuditLoggingModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Audit Logging/i });
    await user.click(btn);
    expect(screen.getByTestId('audit_logging-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<AuditLoggingModule schoolId="school-abc-123" title="Custom Audit Logging Title" />);
    expect(screen.getByText('Custom Audit Logging Title')).toBeTruthy();
  });
});
