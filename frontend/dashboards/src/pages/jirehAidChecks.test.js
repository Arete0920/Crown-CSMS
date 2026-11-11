import { describe, expect, it } from 'vitest';
import {
  requireAidOverview, requireCurrentAidYear, dollarsToCents,
  verifiedAcceptedAward, acceptedFaceValue,
} from './jirehAidChecks.js';

const base = { applications: [], budgets: [], awards: [] };

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
