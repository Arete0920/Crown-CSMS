// @vitest-environment jsdom
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import TableWidget from './TableWidget.jsx';

describe('TableWidget', () => {
  it('renders headers and rows', () => {
    render(
      <TableWidget
        widget={{
          title: 'Open Tasks',
          data: {
            columns: ['Owner', 'Count'],
            rows: [['Admissions', 3]],
          },
        }}
      />,
    );

    expect(screen.getByText('Owner')).toBeTruthy();
    expect(screen.getByText('Admissions')).toBeTruthy();
    expect(screen.getByText('3')).toBeTruthy();
  });

  it('renders the empty state when no rows exist', () => {
    render(
      <TableWidget
        widget={{
          title: 'Open Tasks',
          data: { columns: ['Owner'], rows: [] },
        }}
      />,
    );

    expect(screen.getByText('No items')).toBeTruthy();
  });
});
