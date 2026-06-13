// @vitest-environment jsdom
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import QuickActionsWidget from './QuickActionsWidget.jsx';

describe('QuickActionsWidget', () => {
  it('renders action links', () => {
    render(
      <QuickActionsWidget
        widget={{
          title: 'Shortcuts',
          data: {
            actions: [{ label: 'Open Billing', to: '/billing-dashboard' }],
          },
        }}
      />,
    );

    const link = screen.getByRole('link', { name: '→Open Billing' });
    expect(link.getAttribute('href')).toBe('/billing-dashboard');
  });
});
