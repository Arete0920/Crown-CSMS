import { getSelectedSchoolId } from './authClient';

// Routing only. Server runtime, owned provenance, role and tenant checks are
// authoritative. Keep this closed identity list aligned with the bounded
// backend generation namespace; do not enable a generic customer-school flag.
export const UNIVERSAL_PRESENTER_SCHOOLS = Object.freeze([
  'cd216908-b692-5fa7-997b-743f811f1ea9',
  '9986e823-3fe1-5dde-9e3d-b42e3f139179',
  'ef543061-ad43-5677-9bc8-72310053c517',
  'e92c0a65-2bb8-5804-9f77-a3ebee494868',
  '18e08b7c-4bf7-51dd-9efe-b8694b6ca236',
]);

export function isUniversalPresenterSchool(schoolId = getSelectedSchoolId()) {
  return typeof schoolId === 'string' && UNIVERSAL_PRESENTER_SCHOOLS.includes(schoolId.toLowerCase());
}
