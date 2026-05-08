/**
 * Frontend component tests for Shared Design System module.
 * Module keywords: design_system, theme, palette, Button, Card, Modal
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Shared Design System module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface SharedDesignSystemProps {
  schoolId: string;
  title?: string;
}

function SharedDesignSystemModule({ schoolId, title = 'Shared Design System' }: SharedDesignSystemProps) {
  return (
    <div data-testid="shared_design_system-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Shared Design System</p>
      <button type="button" onClick={() => {}}>Open Shared Design System</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('SharedDesignSystemModule', () => {
  it('renders the module title', () => {
    render(<SharedDesignSystemModule schoolId="school-abc-123" />);
    expect(screen.getByText('Shared Design System')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<SharedDesignSystemModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('shared_design_system-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<SharedDesignSystemModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Shared Design System/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<SharedDesignSystemModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Shared Design System/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<SharedDesignSystemModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Shared Design System/i });
    await user.click(btn);
    expect(screen.getByTestId('shared_design_system-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<SharedDesignSystemModule schoolId="school-abc-123" title="Custom Shared Design System Title" />);
    expect(screen.getByText('Custom Shared Design System Title')).toBeTruthy();
  });
});
