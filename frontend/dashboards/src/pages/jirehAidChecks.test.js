import { describe, expect, it } from 'vitest';
import {
  requireAidOverview, requireCurrentAidYear, requireLiveAidYear, dollarsToCents,
  verifiedAcceptedAward, acceptedFaceValue,
} from './jirehAidChecks.js';

const base = { applications: [], budgets: [], awards: [] };
const SCHOOL = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
const YEAR = '11111111-1111-4111-8111-111111111111';
const live = {
  dashboard_key: 'financial-aid',
  meta: { served_from: 'live_db', school_id: SCHOOL, academic_year_id: YEAR },
};

describe('live Jireh officer academic-year contract', () => {
  it('accepts the exact school and authoritative live year identifier', () => {
    expect(requireLiveAidYear(live, SCHOOL)).toBe(YEAR);
  });
  it.each([
    ['missing payload', undefined],
    ['missing metadata', { dashboard_key: 'financial-aid' }],
    ['missing dashboard key', { meta: live.meta }],
    ['different dashboard', { ...live, dashboard_key: 'academics' }],
    ['foreign school', { ...live, meta: { ...live.meta, school_id: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb' } }],
    ...[undefined, null, '', 42, {}].map((school_id) =>
      ['invalid school ' + JSON.stringify(school_id), { ...live, meta: { ...live.meta, school_id } }]),
    ...[undefined, 'sample', 'snapshot', 'fallback', 'live'].map((served_from) =>
      ['non-live provenance ' + served_from, { ...live, meta: { ...live.meta, served_from } }]),
    ...[undefined, null, '', ' ', 42, {}, [], 'not-a-year', '2026-2027', ' ' + YEAR, YEAR + '\n'].map((academic_year_id) =>
      ['invalid year ' + JSON.stringify(academic_year_id), { ...live, meta: { ...live.meta, academic_year_id } }]),
  ])('rejects %s', (_case, payload) => {
    expect(() => requireLiveAidYear(payload, SCHOOL)).toThrow('live Financial Aid summary');
  });
  it.each([undefined, null, '', ' ', 42, {}])('rejects an invalid selected school: %j', (schoolId) => {
    expect(() => requireLiveAidYear(live, schoolId)).toThrow();
  });
  it('does not coerce school identifiers into an apparent match', () => {
    expect(() => requireLiveAidYear({ ...live, meta: { ...live.meta, school_id: 42 } }, '42')).toThrow();
  });
});

describe('canonical Jireh officer readback contracts', () => {
  it('rejects missing arrays instead of showing sample data', () => {
    expect(() => requireAidOverview({ awards: [] })).toThrow('invalid contract');
  });
  it('requires exactly one current school year', () => {
    const current = { year_id: 'y1', school_id: 'A', is_current: true };
    expect(requireCurrentAidYear({ results: [current] }, 'A')).toBe(current);
    expect(() => requireCurrentAidYear({ results: [current, current] }, 'A')).toThrow();
    expect(() => requireCurrentAidYear({ results: [current] }, 'B')).toThrow();
  });
  it('uses precise integer cents for tuition', () => {
    expect(dollarsToCents('12500.50')).toBe(1250050);
    expect(() => dollarsToCents('1.999')).toThrow();
    expect(() => dollarsToCents('0')).toThrow();
  });
  it('does not count OFFERED as accepted or cash disbursement', () => {
    expect(acceptedFaceValue({ ...base, awards: [{ decision_status: 'OFFERED', awarded_cents: 50000 }] })).toBe(0);
  });
  it('requires canonical linked accepted award and ledger', () => {
    const accepted = {
      id: 9, aid_application_id: 2, student_id: 'student-a',
      decision_status: 'ACCEPTED', awarded_cents: 25000, ledger_entry_id: 17,
    };
    expect(verifiedAcceptedAward({ ...base, awards: [accepted] }, 9, 2, 'student-a')).toEqual(accepted);
    expect(verifiedAcceptedAward({ ...base, awards: [accepted] }, 9, 2, 'foreign-student')).toBeUndefined();
    expect(verifiedAcceptedAward({ ...base, awards: [{ ...accepted, ledger_entry_id: null }] }, 9, 2, 'student-a')).toBeUndefined();
    expect(acceptedFaceValue({ ...base, awards: [accepted] })).toBe(25000);
  });
});
