// @vitest-environment jsdom
import { render, screen } from '@testing-library/react';
import { cleanup } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import MicrosoftProductLogo from './MicrosoftProductLogo';

afterEach(() => {
  cleanup();
});

describe('MicrosoftProductLogo', () => {
  it('renders compact fallback glyph for known but unverified product assets', () => {
    render(<MicrosoftProductLogo product="teams" label="Microsoft Teams" />);

    const fallback = screen.getByLabelText('Microsoft Teams');
    expect(fallback.tagName).toBe('SPAN');
    expect(fallback.textContent).toBe('T');
    expect(fallback.getAttribute('title')).toMatch(/Official Microsoft assets only/i);
  });

  it('renders no logo when unverified and fallback text is disabled', () => {
    render(<MicrosoftProductLogo product="teams" label="Microsoft Teams" />);

    expect(screen.queryByRole('img', { name: 'Microsoft Teams' })).toBeNull();
  });

  it('returns null when product is unknown and fallback text is disabled', () => {
    render(<MicrosoftProductLogo product="unknown_app" label="Unknown App" showTextWhenMissing={false} />);

    expect(screen.queryByLabelText('Unknown App')).toBeNull();
  });

  it('falls back to compact glyph when product is unknown', () => {
    render(<MicrosoftProductLogo product="unknown_app" label="Unknown App" />);

    const fallback = screen.getByLabelText('Unknown App');
    expect(fallback.textContent).toBe('U');
  });
});
