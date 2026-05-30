import { describe, expect, it } from 'vitest';
import { ROLE_GROUPS } from '../routes/routeGroups';
import { isRoleAllowed } from '../routes/roleGuardRules';

function unique(values) {
  return [...new Set(values)];
}

describe('route guard matrix contract', () => {
  const groupEntries = Object.entries(ROLE_GROUPS);

  it('defines role groups for guard matrix coverage', () => {
    expect(groupEntries.length).toBeGreaterThan(0);
  });

  for (const [groupName, roles] of groupEntries) {
    it(`${groupName} contains at least one role`, () => {
      expect(Array.isArray(roles)).toBe(true);
      expect(roles.length).toBeGreaterThan(0);
    });

    it(`${groupName} does not contain duplicate roles`, () => {
      expect(unique(roles).length).toBe(roles.length);
    });

    it(`${groupName} allows every listed role`, () => {
      for (const role of roles) {
        expect(isRoleAllowed(role, roles)).toBe(true);
      }
    });

    it(`${groupName} denies guest role`, () => {
      expect(isRoleAllowed('guest', roles)).toBe(false);
    });
  }

  it('normalizes role values while evaluating membership', () => {
    expect(isRoleAllowed('  TeAcHeR  ', ROLE_GROUPS.ACADEMIC_TEAM)).toBe(true);
  });
});
