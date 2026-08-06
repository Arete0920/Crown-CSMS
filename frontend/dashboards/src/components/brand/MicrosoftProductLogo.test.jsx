// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import MicrosoftProductLogo from './MicrosoftProductLogo';

afterEach(() => {
  cleanup();
});

describe('MicrosoftProductLogo', () => {
  it('renders a professional labelled fallback when licensed product assets are unavailable', () => {
    render(<MicrosoftProductLogo product="teams" label="Microsoft Teams" />);

    const fallback = screen.getByLabelText('Microsoft Teams');
    expect(fallback.tagName).toBe('SPAN');
    expect(fallback.textContent).toBe('Microsoft Teams');
    expect(fallback.querySelector('svg')).not.toBeNull();
    expect(fallback.getAttribute('title')).toMatch(/Official Microsoft assets only/i);
  });

  it('renders no logo when the asset is unverified and fallback content is disabled', () => {
    render(<MicrosoftProductLogo product="teams" label="Microsoft Teams" showTextWhenMissing={false} />);

    expect(screen.queryByLabelText('Microsoft Teams')).toBeNull();
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
