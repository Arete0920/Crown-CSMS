// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import BoardCompassCard from './BoardCompassCard.jsx';

afterEach(cleanup);

describe('BoardCompassCard metric truth', () => {
  it('does not turn missing scores or retention into numeric health', () => {
    render(<BoardCompassCard compass={{ as_of_date: '2026-10-13' }} />);
    expect(screen.getAllByText('Not assessed')).toHaveLength(5);
    expect(screen.queryByRole('progressbar')).toBeNull();
    expect(screen.queryByText('100/100')).toBeNull();
  });

  it('preserves assessed zero and the actual risk percentage while rejecting invalid scores', () => {
    render(<BoardCompassCard compass={{
      as_of_date: '2026-10-13', enrollment_health: 0,
      financial_health: NaN, culture_health: -1, mission_health: 101,
      retention_risk: 25,
    }} />);
    expect(screen.getByText('0/100')).toBeTruthy();
    expect(screen.getByText('25%')).toBeTruthy();
    expect(screen.queryByText('75/100')).toBeNull();
    expect(screen.getAllByText('Not assessed')).toHaveLength(3);
    expect(screen.getAllByRole('progressbar')).toHaveLength(2);
    expect(screen.getByText('Aftercare students flagged high risk')).toBeTruthy();
    expect(screen.getAllByRole('progressbar')[1].getAttribute('aria-valuenow')).toBe('25');
  });

  it('does not assign a favorable health grade to a raw risk percentage', () => {
    render(<BoardCompassCard compass={{ as_of_date: '2026-10-13', retention_risk: 0 }} />);
    expect(screen.getByText('0%')).toBeTruthy();
    const bar = screen.getByRole('progressbar');
    expect(bar.classList.contains('MuiLinearProgress-colorSuccess')).toBe(false);
    expect(bar.classList.contains('MuiLinearProgress-colorError')).toBe(false);
    expect(bar.getAttribute('aria-valuenow')).toBe('0');
  });
});
