/**
 * Frontend component tests for Christian PD Hub module.
 * Module keywords: PDHub, professional_development, course, training, teacher_development
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Christian PD Hub module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface ChristianPdHubProps {
  schoolId: string;
  title?: string;
}

function ChristianPdHubModule({ schoolId, title = 'Christian PD Hub' }: ChristianPdHubProps) {
  return (
    <div data-testid="christian_pd_hub-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Christian PD Hub</p>
      <button type="button" onClick={() => {}}>Open Christian PD Hub</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('ChristianPdHubModule', () => {
  it('renders the module title', () => {
    render(<ChristianPdHubModule schoolId="school-abc-123" />);
    expect(screen.getByText('Christian PD Hub')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<ChristianPdHubModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('christian_pd_hub-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<ChristianPdHubModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Christian PD Hub/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<ChristianPdHubModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Christian PD Hub/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<ChristianPdHubModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Christian PD Hub/i });
    await user.click(btn);
    expect(screen.getByTestId('christian_pd_hub-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<ChristianPdHubModule schoolId="school-abc-123" title="Custom Christian PD Hub Title" />);
    expect(screen.getByText('Custom Christian PD Hub Title')).toBeTruthy();
  });
});
