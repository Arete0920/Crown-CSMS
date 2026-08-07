// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import MicrosoftProductLogo from './MicrosoftProductLogo';

afterEach(() => {
  cleanup();
});

describe('MicrosoftProductLogo', () => {
  it('renders the approved Microsoft-hosted product image when configured', () => {
    render(<MicrosoftProductLogo product="teams" label="Microsoft Teams" />);

    const image = screen.getByRole('img', { name: 'Microsoft Teams' });
    expect(image.getAttribute('src')).toMatch(/res-1\.cdn\.office\.net\/.*teams_48x1\.svg$/);
    expect(image.getAttribute('width')).toBe('24');
    expect(image.getAttribute('height')).toBe('24');
  });

  it('falls back to a professional full-label treatment when the image fails', () => {
    render(<MicrosoftProductLogo product="teams" label="Microsoft Teams" />);

    fireEvent.error(screen.getByRole('img', { name: 'Microsoft Teams' }));

    const fallback = screen.getByLabelText('Microsoft Teams');
    expect(fallback.tagName).toBe('SPAN');
    expect(fallback.textContent).toBe('Microsoft Teams');
    expect(fallback.querySelector('svg')).not.toBeNull();
    expect(fallback.getAttribute('title')).toMatch(/Official Microsoft-hosted product assets only/i);
  });

  it('uses a decorative compact fallback inside an already labelled launcher', () => {
    const { container } = render(
      <MicrosoftProductLogo
        product="unknown_app"
        label="Unknown App"
        compactFallback
        decorative
      />,
    );

    const fallback = container.querySelector('.microsoft-product-approved-fallback.is-compact');
    expect(fallback).not.toBeNull();
    expect(fallback.getAttribute('aria-hidden')).toBe('true');
    expect(fallback.textContent).toBe('');
    expect(fallback.querySelector('svg')).not.toBeNull();
  });

  it('returns null when the product is unknown and fallback content is disabled', () => {
    render(<MicrosoftProductLogo product="unknown_app" label="Unknown App" showTextWhenMissing={false} />);

    expect(screen.queryByLabelText('Unknown App')).toBeNull();
  });

  it('uses the full product label for an unknown product fallback', () => {
    render(<MicrosoftProductLogo product="unknown_app" label="Unknown App" />);

    const fallback = screen.getByLabelText('Unknown App');
    expect(fallback.textContent).toBe('Unknown App');
    expect(fallback.querySelector('svg')).not.toBeNull();
  });
});
