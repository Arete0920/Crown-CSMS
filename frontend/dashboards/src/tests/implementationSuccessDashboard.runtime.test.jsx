// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import ImplementationSuccessDashboard from '../pages/ImplementationSuccessDashboard.jsx';

afterEach(() => {
  cleanup();
});

describe('implementation-success dashboard runtime template proof', () => {
  it('withholds static live KPIs while runtime dashboard data is loading', () => {
    render(<ImplementationSuccessDashboard />);

    expect(screen.getByText('Good morning, Implementation Team!')).toBeTruthy();
    expect(screen.getByText('Source and sync status')).toBeTruthy();
    expect(screen.queryByText('Schools Onboarding')).toBeNull();
    expect(screen.queryByText('Milestones Completed')).toBeNull();
    expect(screen.queryByText('Active Blockers')).toBeNull();
    expect(screen.queryByText('Go-Lives YTD')).toBeNull();
  });
});
