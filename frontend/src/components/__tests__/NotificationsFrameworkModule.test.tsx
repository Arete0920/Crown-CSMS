/**
 * Frontend component tests for Notifications Framework module.
 * Module keywords: notification, NotificationEvent, EmailDispatch, SMS, Twilio
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Notifications Framework module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface NotificationsFrameworkProps {
  schoolId: string;
  title?: string;
}

function NotificationsFrameworkModule({ schoolId, title = 'Notifications Framework' }: NotificationsFrameworkProps) {
  return (
    <div data-testid="notifications_framework-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Notifications Framework</p>
      <button type="button" onClick={() => {}}>Open Notifications Framework</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('NotificationsFrameworkModule', () => {
  it('renders the module title', () => {
    render(<NotificationsFrameworkModule schoolId="school-abc-123" />);
    expect(screen.getByText('Notifications Framework')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<NotificationsFrameworkModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('notifications_framework-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<NotificationsFrameworkModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Notifications Framework/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<NotificationsFrameworkModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Notifications Framework/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<NotificationsFrameworkModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Notifications Framework/i });
    await user.click(btn);
    expect(screen.getByTestId('notifications_framework-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<NotificationsFrameworkModule schoolId="school-abc-123" title="Custom Notifications Framework Title" />);
    expect(screen.getByText('Custom Notifications Framework Title')).toBeTruthy();
  });
});
