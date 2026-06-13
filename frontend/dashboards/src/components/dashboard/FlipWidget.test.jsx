// @vitest-environment jsdom
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import FlipWidget from './FlipWidget.jsx';

describe('FlipWidget', () => {
  it('flips between summary and action items and preserves expand action', () => {
    const onExpand = vi.fn();

    render(
      <FlipWidget
        onExpand={onExpand}
        widget={{
          title: 'Release Health',
          subtitle: 'Weekly review',
          data: {
            front: { good: 4, warn: 2, bad: 1 },
            back: { items: [{ level: 'warn', text: 'Review unresolved blocker' }] },
          },
        }}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Flip Release Health widget' }));
    expect(screen.getByText('Release Health - Action Items')).toBeTruthy();
    expect(screen.getByText('Review unresolved blocker')).toBeTruthy();

    fireEvent.click(screen.getByLabelText('Expand Release Health'));
    expect(onExpand).toHaveBeenCalledTimes(1);
  });
});
