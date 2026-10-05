import { describe, expect, it } from 'vitest';

import { APP_PERMISSIONS, userHasPermission } from '../auth/permissions';
import { PATHS } from '../routes/paths';
import {
  activateHomeAcademyRegistration,
  completeHomeAcademyRegistration,
  fetchHomeAcademyOfferings,
  fetchParentHomeAcademySummary,
  postHomeAcademyTranscript,
} from '../api/homeAcademyApi';

describe('Home Academy contract', () => {
  it('defines stable staff and parent paths', () => {
    expect(PATHS.HOME_ACADEMY).toBe('/home-academy');
    expect(PATHS.PARENT_HOME_ACADEMY).toBe('/parent/home-academy');
  });

  it('maps Home Academy permissions to intended roles', () => {
    expect(userHasPermission({ role: 'registrar' }, APP_PERMISSIONS.HOME_ACADEMY_VIEW)).toBe(true);
    expect(userHasPermission({ role: 'registrar' }, APP_PERMISSIONS.HOME_ACADEMY_EDIT)).toBe(true);
    expect(userHasPermission({ role: 'parent' }, APP_PERMISSIONS.HOME_ACADEMY_VIEW)).toBe(true);
    expect(userHasPermission({ role: 'parent' }, APP_PERMISSIONS.HOME_ACADEMY_EDIT)).toBe(false);
  });

  it('exports the required lifecycle API surface', () => {
    expect(fetchHomeAcademyOfferings).toBeTypeOf('function');
    expect(fetchParentHomeAcademySummary).toBeTypeOf('function');
    expect(activateHomeAcademyRegistration).toBeTypeOf('function');
    expect(completeHomeAcademyRegistration).toBeTypeOf('function');
    expect(postHomeAcademyTranscript).toBeTypeOf('function');
  });
});
