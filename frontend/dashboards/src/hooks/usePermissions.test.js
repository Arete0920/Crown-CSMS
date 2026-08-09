import { describe, expect, it } from 'vitest';
import { APP_PERMISSIONS, userHasPermission } from '../auth/permissions';
import { mergePermissionIdentity } from './usePermissions';

describe('permission identity reconciliation', () => {
  it('uses the seeded sandbox role when no stored user object exists', () => {
    const user = mergePermissionIdentity(null, ['school_admin']);
    expect(userHasPermission(user, APP_PERMISSIONS.BILLING_VIEW)).toBe(true);
    expect(userHasPermission(user, APP_PERMISSIONS.REPORTING_VIEW)).toBe(true);
  });

  it('preserves stored explicit permissions while adding seeded roles', () => {
    const user = mergePermissionIdentity(
      { permissions: [APP_PERMISSIONS.RELEASE_VIEW] },
      ['school_admin'],
    );
    expect(user.permissions).toEqual([APP_PERMISSIONS.RELEASE_VIEW]);
    expect(user.roles).toEqual(['school_admin']);
  });

  it('preserves the stored identity when no seeded role exists', () => {
    const stored = { role: 'finance' };
    expect(mergePermissionIdentity(stored, [])).toBe(stored);
  });
});
