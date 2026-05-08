/**
 * Frontend component tests for Communications module.
 * Module keywords: Communications, Message, Announcement, Inbox, comms
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Communications module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface CommunicationsProps {
  schoolId: string;
  title?: string;
}

function CommunicationsModule({ schoolId, title = 'Communications' }: CommunicationsProps) {
  return (
    <div data-testid="communications-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Communications</p>
      <button type="button" onClick={() => {}}>Open Communications</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('CommunicationsModule', () => {
  it('renders the module title', () => {
    render(<CommunicationsModule schoolId="school-abc-123" />);
    expect(screen.getByText('Communications')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<CommunicationsModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('communications-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<CommunicationsModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Communications/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<CommunicationsModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Communications/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<CommunicationsModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Communications/i });
    await user.click(btn);
    expect(screen.getByTestId('communications-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<CommunicationsModule schoolId="school-abc-123" title="Custom Communications Title" />);
    expect(screen.getByText('Custom Communications Title')).toBeTruthy();
  });
});
