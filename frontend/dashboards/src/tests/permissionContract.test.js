import { describe, expect, it } from 'vitest';
import {
  APP_PERMISSIONS,
  resolvePermissions,
  userHasPermission,
} from '../auth/permissions';

describe('permission contract', () => {
  it('admin resolves to wildcard access', () => {
    const permissions = resolvePermissions({ role: 'admin' });
    expect(permissions.includes('*')).toBe(true);
  });

  it('finance can view billing', () => {
    expect(
      userHasPermission({ role: 'finance' }, APP_PERMISSIONS.BILLING_VIEW),
    ).toBe(true);
  });

  it('parent cannot edit billing', () => {
    expect(
      userHasPermission({ role: 'parent' }, APP_PERMISSIONS.BILLING_EDIT),
    ).toBe(false);
  });

  it('explicit permissions override role fallback', () => {
    const permissions = resolvePermissions({
      role: 'parent',
      permissions: [APP_PERMISSIONS.RELEASE_VIEW],
    });

    expect(permissions).toContain(APP_PERMISSIONS.RELEASE_VIEW);
  });
});
