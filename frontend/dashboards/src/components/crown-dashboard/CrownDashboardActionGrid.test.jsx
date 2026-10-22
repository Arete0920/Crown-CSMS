import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { MemoryRouter } from 'react-router';
import CrownDashboardActionGrid from './CrownDashboardActionGrid.jsx';
import billing from '../../config/dashboardTemplates/billingDashboard.js';

afterEach(cleanup);

describe('dashboard quick-action accessible names', () => {
  it.each([false, true])('labels billing links and headings with router=%s', (withRouter) => {
    const grid = <CrownDashboardActionGrid actions={billing.quickActions} />;
    render(withRouter ? <MemoryRouter>{grid}</MemoryRouter> : grid);

    for (const action of billing.quickActions) {
      expect(screen.getByRole('heading', { level: 3, name: action.label })).toBeTruthy();
      expect(screen.getByRole('link', { name: action.label }).getAttribute('href')).toBe(action.href);
    }
  });

  it('preserves explicit titles and action labels', () => {
    render(<CrownDashboardActionGrid actions={[{
      title: 'Invoice review', label: 'Legacy label', actionLabel: 'Review invoices',
      description: 'Review current invoice records.', href: '/finance',
    }]} />);
    expect(screen.getByRole('heading', { level: 3, name: 'Invoice review' })).toBeTruthy();
    expect(screen.getByRole('link', { name: 'Review invoices' }).getAttribute('href')).toBe('/finance');
  });

  it('uses an existing title when no separate action label is supplied', () => {
    render(<CrownDashboardActionGrid actions={[{ title: 'Open finance', href: '/finance' }]} />);
    expect(screen.getByRole('link', { name: 'Open finance' })).toBeTruthy();
  });
});
