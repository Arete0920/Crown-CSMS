import { describe, expect, it } from 'vitest';
import { isRoleAllowed } from '../routes/roleGuardRules';

describe('RoleGuard role checks', () => {
  it('allows authorized role', () => {
    expect(isRoleAllowed('admin', ['admin', 'owner'])).toBe(true);
    expect(isRoleAllowed('school_admin', ['super_admin', 'school_admin'])).toBe(true);
  });

  it('blocks unauthorized role', () => {
    expect(isRoleAllowed('student', ['admin', 'owner'])).toBe(false);
  });

  it('allows when route has no explicit role list', () => {
    expect(isRoleAllowed('student', [])).toBe(true);
  });
});
