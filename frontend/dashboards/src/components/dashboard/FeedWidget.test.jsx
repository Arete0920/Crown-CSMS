// @vitest-environment jsdom
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import FeedWidget from './FeedWidget.jsx';

describe('FeedWidget', () => {
  it('renders feed items', () => {
    render(
      <FeedWidget
        widget={{
          title: 'Inbox',
          data: {
            items: [{ subject: 'Parent follow-up', ago: '5m' }],
          },
        }}
      />,
    );

    expect(screen.getAllByText('Parent follow-up')).toHaveLength(2);
    expect(screen.getByText('5m')).toBeTruthy();
  });

  it('renders the empty state when no feed items exist', () => {
    render(<FeedWidget widget={{ title: 'Inbox', data: { items: [] } }} />);
    expect(screen.getByText('No items')).toBeTruthy();
  });
});
