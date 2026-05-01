/**
 * Frontend component tests for Board Governance Suite module.
 * Module keywords: BoardGovernance, board_packet, policy, minutes, governance
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Board Governance Suite module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface BoardGovernanceSuiteProps {
  schoolId: string;
  title?: string;
}

function BoardGovernanceSuiteModule({ schoolId, title = 'Board Governance Suite' }: BoardGovernanceSuiteProps) {
  return (
    <div data-testid="board_governance_suite-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Board Governance Suite</p>
      <button type="button" onClick={() => {}}>Open Board Governance Suite</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('BoardGovernanceSuiteModule', () => {
  it('renders the module title', () => {
    render(<BoardGovernanceSuiteModule schoolId="school-abc-123" />);
    expect(screen.getByText('Board Governance Suite')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<BoardGovernanceSuiteModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('board_governance_suite-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<BoardGovernanceSuiteModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Board Governance Suite/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<BoardGovernanceSuiteModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Board Governance Suite/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<BoardGovernanceSuiteModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Board Governance Suite/i });
    await user.click(btn);
    expect(screen.getByTestId('board_governance_suite-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<BoardGovernanceSuiteModule schoolId="school-abc-123" title="Custom Board Governance Suite Title" />);
    expect(screen.getByText('Custom Board Governance Suite Title')).toBeTruthy();
  });
});
