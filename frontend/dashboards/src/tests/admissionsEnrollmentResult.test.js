import { describe, expect, it, vi } from 'vitest';
import {
  VERIFIED_SIS_ENROLLMENT_GATE,
  admissionsEnrollmentErrorMessage,
  performVerifiedAdmissionsEnrollment,
  verifyAdmissionsEnrollmentResponse,
} from '../pages/admissionsEnrollmentResult.js';

const valid = {
  ok: true,
  student_id: '19a7f25f-48d5-4122-822b-cdb7301237bc',
  canonical_gate: VERIFIED_SIS_ENROLLMENT_GATE,
  already_enrolled: false,
};

describe('Admissions Enroll Child verified SIS feedback', () => {
  it('accepts only a verified SIS result and refreshes the selected record', async () => {
    const enroll = vi.fn().mockResolvedValue(valid);
    const readback = vi.fn().mockResolvedValue(undefined);
    const result = await performVerifiedAdmissionsEnrollment({
      applicationId: 17, enroll, readback,
    });
    expect(enroll).toHaveBeenCalledTimes(1);
    expect(enroll).toHaveBeenCalledWith(17);
    expect(readback).toHaveBeenCalledTimes(1);
    expect(readback).toHaveBeenCalledWith(17);
    expect(result.ok).toBe(true);
    expect(result.message).toContain('server confirms a verified SIS enrollment');
  });

  it('distinguishes verified idempotent replay', () => {
    const result = verifyAdmissionsEnrollmentResponse({ ...valid, already_enrolled: true });
    expect(result.ok).toBe(true);
    expect(result.message).toContain('existing verified SIS enrollment');
  });

  it.each([
    [null, 'no response'],
    [{ ok: false, student_id: '1', canonical_gate: VERIFIED_SIS_ENROLLMENT_GATE }, 'failure'],
    [{ ok: true, student_id: '1', canonical_gate: 'contract_countersigned_and_deposit_paid_or_waived' }, 'event-only legacy gate'],
    [{ ok: true, canonical_gate: VERIFIED_SIS_ENROLLMENT_GATE, student_id: null }, 'missing student'],
    [{ ok: true, canonical_gate: VERIFIED_SIS_ENROLLMENT_GATE, student_id: '  ' }, 'blank student'],
    [{ ok: true, student_id: '1' }, 'missing gate'],
    [{ status: 200, message: 'Enrolled successfully.' }, 'legacy success text'],
  ])('refuses unverified HTTP result %s (%s)', async (response) => {
    const readback = vi.fn();
    const result = await performVerifiedAdmissionsEnrollment({
      applicationId: 9, enroll: vi.fn().mockResolvedValue(response), readback,
    });
    expect(result.ok).toBe(false);
    expect(result.message).toContain('Enrollment is not confirmed');
    expect(readback).not.toHaveBeenCalled();
  });

  it.each([
    ['canonical_enrollment_required', 'canonical SIS enrollment'],
    ['student_identity_link_required', 'Student identity evidence'],
    ['student_dob_verification_required', 'Student identity evidence'],
    ['canonical_enrollment_identity_mismatch', 'Student identity evidence'],
  ])('provides actionable 409 guidance for %s', (code, expected) => {
    const message = admissionsEnrollmentErrorMessage({
      status: 409, details: { code, detail: 'raw-private-server-message' },
    });
    expect(message).toContain(expected);
    expect(message).not.toContain('raw-private-server-message');
  });

  it('explains readiness, permission and school errors without claiming a completed enrollment', () => {
    expect(admissionsEnrollmentErrorMessage({ status: 409, details: { detail: 'internal/private/trace' } })).toContain('Enrollment is not ready');
    expect(admissionsEnrollmentErrorMessage({ status: 403 })).toContain('not authorized');
    expect(admissionsEnrollmentErrorMessage({ status: 404 })).toContain('selected school');
  });

  it('handles normalized network and legacy response errors without leaking backend detail', () => {
    expect(admissionsEnrollmentErrorMessage({
      status: null, isNetworkError: true, message: 'arbitrary transport error',
    })).toContain('do not assume the student was enrolled');
    expect(admissionsEnrollmentErrorMessage({
      response: { status: 409, data: { code: 'student_identity_link_required' } },
    })).toContain('Student identity evidence');
  });

  it('does not refresh a rejected enrollment', async () => {
    const readback = vi.fn();
    const result = await performVerifiedAdmissionsEnrollment({
      applicationId: 2,
      enroll: vi.fn().mockRejectedValue({ status: 409, details: { code: 'canonical_enrollment_required' } }),
      readback,
    });
    expect(result.ok).toBe(false);
    expect(result.message).toContain('canonical SIS enrollment');
    expect(readback).not.toHaveBeenCalled();
  });

  it('does not claim independent readback if refreshing the admissions list fails', async () => {
    const result = await performVerifiedAdmissionsEnrollment({
      applicationId: 2,
      enroll: vi.fn().mockResolvedValue(valid),
      readback: vi.fn().mockRejectedValue(new Error('readback-test-failure')),
    });
    expect(result.ok).toBe(false);
    expect(result.message).toContain('server reported verified enrollment');
    expect(result.message).toContain('could not be refreshed');
  });
});
