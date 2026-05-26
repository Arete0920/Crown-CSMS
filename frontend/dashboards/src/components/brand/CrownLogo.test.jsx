// @vitest-environment jsdom
import { fireEvent, render, screen } from '@testing-library/react';
import { cleanup } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import CrownLogo from './CrownLogo';

afterEach(() => {
  cleanup();
});

describe('CrownLogo', () => {
  it('renders an image for configured variant path', () => {
    render(<CrownLogo variant="horizontal" />);

    const logo = screen.getByRole('img');
    expect(logo.getAttribute('src')).toBe('/brand/crown/logo/crown-logo-horizontal-full-color.svg');
  });

  it('falls back to official text when image load fails', () => {
    render(<CrownLogo variant="horizontal" />);

    const logo = screen.getByRole('img');
    fireEvent.error(logo);

    expect(screen.getByText('CROWN')).toBeTruthy();
    expect(screen.getByText('Christian School Management Solution')).toBeTruthy();
  });
});
