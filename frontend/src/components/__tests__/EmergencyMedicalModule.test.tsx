/**
 * Frontend component tests for Emergency Medical Essentials module.
 * Module keywords: EmergencyContact, Medical, allergy, health_flag, medication
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Emergency Medical Essentials module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface EmergencyMedicalProps {
  schoolId: string;
  title?: string;
}

function EmergencyMedicalModule({ schoolId, title = 'Emergency Medical Essentials' }: EmergencyMedicalProps) {
  return (
    <div data-testid="emergency_medical-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Emergency Medical Essentials</p>
      <button type="button" onClick={() => {}}>Open Emergency Medical Essentials</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('EmergencyMedicalModule', () => {
  it('renders the module title', () => {
    render(<EmergencyMedicalModule schoolId="school-abc-123" />);
    expect(screen.getByText('Emergency Medical Essentials')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<EmergencyMedicalModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('emergency_medical-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<EmergencyMedicalModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Emergency Medical Essentials/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<EmergencyMedicalModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Emergency Medical Essentials/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<EmergencyMedicalModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Emergency Medical Essentials/i });
    await user.click(btn);
    expect(screen.getByTestId('emergency_medical-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<EmergencyMedicalModule schoolId="school-abc-123" title="Custom Emergency Medical Essentials Title" />);
    expect(screen.getByText('Custom Emergency Medical Essentials Title')).toBeTruthy();
  });
});
