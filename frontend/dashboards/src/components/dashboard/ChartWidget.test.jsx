// @vitest-environment jsdom
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ChartWidget from './ChartWidget.jsx';

describe('ChartWidget', () => {
  it('renders a line chart', () => {
    render(
      <ChartWidget
        widget={{
          title: 'Trend',
          type: 'chart_line',
          data: { series: [{ name: 'Enrollment', points: [{ y: 10 }, { y: 12 }] }] },
        }}
      />,
    );

    expect(screen.getByLabelText('Trend chart')).toBeTruthy();
  });

  it('renders a donut chart and expand control', () => {
    const onExpand = vi.fn();

    render(
      <ChartWidget
        onExpand={onExpand}
        widget={{
          title: 'Alerts',
          type: 'chart_donut',
          data: { segments: [{ label: 'Open', value: 2, color: 'warn' }] },
        }}
      />,
    );

    expect(screen.getByLabelText('Donut chart')).toBeTruthy();
    fireEvent.click(screen.getByLabelText('Expand Alerts'));
    expect(onExpand).toHaveBeenCalledTimes(1);
  });
});
