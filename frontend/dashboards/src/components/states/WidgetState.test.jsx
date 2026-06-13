// @vitest-environment jsdom
import { render, screen } from '@testing-library/react';
import { describe, it } from 'vitest';
import WidgetState from './WidgetState.jsx';

describe('WidgetState', () => {
  it('renders loading, error, empty, and content states', () => {
    const { rerender } = render(<WidgetState title="Widget" loading />);
    screen.getByText('Loading...');

    rerender(<WidgetState title="Widget" error="Widget failed" />);
    screen.getByText('Widget failed');

    rerender(<WidgetState title="Widget" empty emptyMessage="Nothing yet" />);
    screen.getByText('Nothing yet');

    rerender(
      <WidgetState title="Widget">
        <div>Loaded content</div>
      </WidgetState>,
    );
    screen.getByText('Loaded content');
  });
});
