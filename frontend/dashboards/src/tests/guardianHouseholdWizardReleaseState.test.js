import { describe, expect, it } from 'vitest';

import { WIZARD_REGISTRY } from '../routes/wizards';

const ROUTE_PATH = '/guardian-household-setup';
const READY_STATES = new Set(['ready', 'live', 'production']);

describe('guardian household wizard release state', () => {
  it('remains non-production until current full-flow evidence is approved', () => {
    const route = WIZARD_REGISTRY.find((entry) => entry.path === ROUTE_PATH);

    expect(route).toBeTruthy();
    expect(route.releaseState).toBe('certification');
    expect(READY_STATES.has(route.releaseState)).toBe(false);
    expect(route.evidence).toBeUndefined();
    expect(route.readiness).toEqual({
      shellReady: true,
      uxReady: true,
      accessReady: true,
      dataReady: true,
    });
  });
});
