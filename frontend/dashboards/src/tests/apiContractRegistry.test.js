import { describe, expect, it } from 'vitest';
import { API_CONTRACTS } from '../config/apiContracts';

describe('api contract registry', () => {
  it('all keys are unique', () => {
    const keys = Object.keys(API_CONTRACTS);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it('all contracts have required fields', () => {
    for (const [key, contract] of Object.entries(API_CONTRACTS)) {
      expect(Boolean(key)).toBe(true);
      expect(Boolean(contract.method)).toBe(true);
      expect(Boolean(contract.path)).toBe(true);
      expect(Boolean(contract.owner)).toBe(true);
      expect(Boolean(contract.permission)).toBe(true);
      expect(Boolean(contract.responseType)).toBe(true);
      expect(contract.path.startsWith('/')).toBe(true);
    }
  });

  it('all contract paths are unique per method', () => {
    const pairs = Object.values(API_CONTRACTS).map(
      (contract) => `${contract.method}:${contract.path}`,
    );
    expect(new Set(pairs).size).toBe(pairs.length);
  });
});
