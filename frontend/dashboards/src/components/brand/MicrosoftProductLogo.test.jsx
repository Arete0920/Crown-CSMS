// @vitest-environment jsdom
import { fireEvent, render, screen } from '@testing-library/react';
import { cleanup } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import MicrosoftProductLogo from './MicrosoftProductLogo';

afterEach(() => {
  cleanup();
});

describe('MicrosoftProductLogo', () => {
  it('renders image for known product', () => {
    render(<MicrosoftProductLogo product="teams" label="Microsoft Teams" />);

    const logo = screen.getByRole('img', { name: 'Microsoft Teams' });
    expect(logo.getAttribute('src')).toBe('/brand/third-party/microsoft/apps/teams-logo.svg');
  });

  it('falls back to compact glyph when image fails', () => {
    render(<MicrosoftProductLogo product="teams" label="Microsoft Teams" />);

    const logo = screen.getByRole('img', { name: 'Microsoft Teams' });
    fireEvent.error(logo);

    const fallback = screen.getByLabelText('Microsoft Teams');
    expect(fallback.textContent).toBe('T');
    expect(fallback.getAttribute('title')).toMatch(/Official Microsoft assets only/i);
  });

  it('falls back to compact glyph when product is unknown', () => {
    render(<MicrosoftProductLogo product="unknown_app" label="Unknown App" />);

    const fallback = screen.getByLabelText('Unknown App');
    expect(fallback.textContent).toBe('U');
  });
});
