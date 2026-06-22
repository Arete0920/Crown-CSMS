// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import ImplementationSuccessDashboard from '../pages/ImplementationSuccessDashboard.jsx';

afterEach(() => {
  cleanup();
});
describe('implementation-success dashboard runtime template proof', () => {
  it('renders expected title and metrics for /implementation-success-dashboard', () => {
    render(<ImplementationSuccessDashboard />);

    expect(screen.getByText('Good morning, Implementation Team!')).toBeTruthy();
    expect(screen.getByText('Schools Onboarding')).toBeTruthy();
    expect(screen.getByText('Milestones Completed')).toBeTruthy();
    expect(screen.getByText('Active Blockers')).toBeTruthy();
    expect(screen.getByText('Go-Lives YTD')).toBeTruthy();
  });
});
