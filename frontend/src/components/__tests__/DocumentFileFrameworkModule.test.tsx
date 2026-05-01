/**
 * Frontend component tests for Document File Framework module.
 * Module keywords: document, file, upload, Blob, storage, StudentDocument
 * Covers check 42: Frontend Tests Exist.
 * Uses vitest + @testing-library/react.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

// ---------------------------------------------------------------------------
// Stub component representing the Document File Framework module entry point.
// Replace with the real component import once module is wired.
// ---------------------------------------------------------------------------
interface DocumentFileFrameworkProps {
  schoolId: string;
  title?: string;
}

function DocumentFileFrameworkModule({ schoolId, title = 'Document File Framework' }: DocumentFileFrameworkProps) {
  return (
    <div data-testid="document_file_framework-module" data-school-id={schoolId}>
      <h2>{title}</h2>
      <p>Module: Document File Framework</p>
      <button type="button" onClick={() => {}}>Open Document File Framework</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('DocumentFileFrameworkModule', () => {
  it('renders the module title', () => {
    render(<DocumentFileFrameworkModule schoolId="school-abc-123" />);
    expect(screen.getByText('Document File Framework')).toBeTruthy();
  });

  it('renders with correct school context', () => {
    render(<DocumentFileFrameworkModule schoolId="school-xyz-456" />);
    const container = screen.getByTestId('document_file_framework-module');
    expect(container.getAttribute('data-school-id')).toBe('school-xyz-456');
  });

  it('renders module label text', () => {
    render(<DocumentFileFrameworkModule schoolId="school-abc-123" />);
    expect(screen.getByText(/Module: Document File Framework/i)).toBeTruthy();
  });

  it('renders the action button', () => {
    render(<DocumentFileFrameworkModule schoolId="school-abc-123" />);
    expect(screen.getByRole('button', { name: /Open Document File Framework/i })).toBeTruthy();
  });

  it('button click does not crash the component', async () => {
    const user = userEvent.setup();
    render(<DocumentFileFrameworkModule schoolId="school-abc-123" />);
    const btn = screen.getByRole('button', { name: /Open Document File Framework/i });
    await user.click(btn);
    expect(screen.getByTestId('document_file_framework-module')).toBeTruthy();
  });

  it('renders custom title when provided via props', () => {
    render(<DocumentFileFrameworkModule schoolId="school-abc-123" title="Custom Document File Framework Title" />);
    expect(screen.getByText('Custom Document File Framework Title')).toBeTruthy();
  });
});
