// @vitest-environment jsdom
import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

const expectRenderedText = (container, text) => {
  expect(container.textContent).toContain(text);
};

const renderTemplate = (templateKey) => {
  const config = {
    ...getDashboardTemplate(templateKey),
    disableLiveData: true,
  };
  return render(<CrownDashboardTemplate config={config} roleKey="master_control" />);
};

afterEach(() => {
  cleanup();
});

describe('remaining Batch 5 dashboard runtime template proof', () => {
  it('renders expected title and metrics for /data-migration-dashboard', () => {
    const { container } = renderTemplate('dataMigration');

    expectRenderedText(container, 'Good morning, Data Migration Team!');
    expectRenderedText(container, 'Records Migrated');
    expectRenderedText(container, 'Validation Rate');
    expectRenderedText(container, 'Errors Remaining');
    expectRenderedText(container, 'Pending Migrations');
  });

  it('renders expected title and metrics for /integrations-automation-dashboard', () => {
    const { container } = renderTemplate('integrationsAutomation');

    expectRenderedText(container, 'Good morning, Integrations Team!');
    expectRenderedText(container, 'Active Integrations');
    expectRenderedText(container, 'API Health');
    expectRenderedText(container, 'Automations Running');
    expectRenderedText(container, 'Sync Errors');
  });

  it('renders expected title and metrics for /revenue-operations-dashboard', () => {
    const { container } = renderTemplate('revenueOperations');

    expectRenderedText(container, 'Good morning, Revenue Ops!');
    expectRenderedText(container, 'Revenue YTD');
    expectRenderedText(container, 'ARR Pipeline');
    expectRenderedText(container, 'Collection Rate');
    expectRenderedText(container, 'Churn Risk');
  });

  it('renders expected title and metrics for /summer-camp-dashboard', () => {
    const { container } = renderTemplate('summerCamp');

    expectRenderedText(container, 'Summer program command center');
    expectRenderedText(container, 'Registered Campers');
    expectRenderedText(container, 'Staffed Sessions');
    expectRenderedText(container, 'Waitlist Families');
    expectRenderedText(container, 'Transport Confirmed');
  });

  it('renders expected title and metrics for /extended-care-dashboard', () => {
    const { container } = renderTemplate('extendedCare');

    expectRenderedText(container, 'Good morning, Extended Care!');
    expectRenderedText(container, 'Enrolled Students');
    expectRenderedText(container, 'Attendance Today');
    expectRenderedText(container, 'Invoices Due');
    expectRenderedText(container, 'Staff Coverage');
  });

  it('renders expected title and metrics for /athletics-director-dashboard', () => {
    const { container } = renderTemplate('athleticsDirector');

    expectRenderedText(container, 'Good morning, Athletic Director!');
    expectRenderedText(container, 'Upcoming Events');
    expectRenderedText(container, 'Eligibility Issues');
    expectRenderedText(container, 'Active Injuries');
    expectRenderedText(container, 'Transportation Needs');
  });
});
