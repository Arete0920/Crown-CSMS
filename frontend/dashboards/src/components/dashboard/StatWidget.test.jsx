// @vitest-environment jsdom
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import StatWidget from './StatWidget.jsx';

describe('StatWidget', () => {
  it('renders formatted currency values and expands on request', () => {
    const onExpand = vi.fn();

    render(
      <StatWidget
        onExpand={onExpand}
        widget={{
          title: 'Tuition Collected',
          subtitle: 'Current month',
          data: { amount: 12500, currency: 'USD', status: 'good' },
        }}
      />,
    );

    expect(screen.getByText('Tuition Collected')).toBeTruthy();
    expect(screen.getByText('$12,500.00')).toBeTruthy();
    fireEvent.click(screen.getByLabelText('Expand Tuition Collected'));
    expect(onExpand).toHaveBeenCalledTimes(1);
  });
});
