import { describe, it, expect } from 'vitest';
import { UNIVERSAL_PRESENTER_SCHOOLS, isUniversalPresenterSchool } from './universalPresenterScope';

describe('closed presenter identity routing', () => {
  it('routes each bounded owned generation and denies historical Heritage/customer/invalid IDs', () => {
    expect(UNIVERSAL_PRESENTER_SCHOOLS).toHaveLength(5);
    for (const school of UNIVERSAL_PRESENTER_SCHOOLS) expect(isUniversalPresenterSchool(school)).toBe(true);
    for (const other of ['19801b59-8c05-4c84-9312-5d792e4e839d', '00000000-0000-4000-8000-000000000001', '', null, undefined]) {
      expect(isUniversalPresenterSchool(other ?? null)).toBe(false);
    }
  });
});
