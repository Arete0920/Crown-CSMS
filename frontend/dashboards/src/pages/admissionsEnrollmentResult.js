/** A 200 response or legacy status event alone is not SIS enrollment proof. */
export const VERIFIED_SIS_ENROLLMENT_GATE = 'verified_identity_and_core_enrollment';

const IDENTITY_CODES = new Set([
  'applicant_identity_required',
  'student_identity_link_required',
  'student_identity_evidence_required',
  'compatibility_student_scope_mismatch',
  'canonical_student_scope_mismatch',
  'student_dob_verification_required',
  'student_name_reconciliation_required',
  'authoritative_student_number_required',
  'household_family_link_required',
  'canonical_enrollment_identity_mismatch',
]);

export function verifyAdmissionsEnrollmentResponse(response) {
  const studentId = response?.student_id;
  const hasStudentId = (typeof studentId === 'string' || typeof studentId === 'number')
    && String(studentId).trim().length > 0;
  if (response?.ok !== true
    || response?.canonical_gate !== VERIFIED_SIS_ENROLLMENT_GATE
    || !hasStudentId) {
    return {
      ok: false,
      message: 'Enrollment is not confirmed by verified SIS identity and school-year enrollment evidence. Review the canonical student record before proceeding.',
    };
  }
  return {
    ok: true,
    message: response.already_enrolled
      ? 'The server confirms an existing verified SIS enrollment. Admissions records refreshed.'
      : 'The server confirms a verified SIS enrollment. Admissions records refreshed.',
  };
}

export function admissionsEnrollmentErrorMessage(error) {
  // The shared client normalizes errors into {status, details}. Never display
  // raw backend messages or transport exception text in the operator UI.
  const status = error?.status ?? error?.response?.status ?? null;
  const details = error?.details ?? error?.response?.data ?? null;
  const code = details && typeof details === 'object' ? details.code : null;
  if (status === 403) {
    return 'Enrollment was not authorized. Ask a school administrator to verify admissions-edit access.';
  }
  if (status === 404) {
    return 'This admissions application was not found in the selected school. Refresh the pipeline and verify the school.';
  }
  if (status === 409 && code === 'canonical_enrollment_required') {
    return 'The required canonical SIS enrollment is missing for the verified student, school year, or grade. Complete and verify the authoritative enrollment before retrying.';
  }
  if (status === 409 && IDENTITY_CODES.has(code)) {
    return 'Student identity evidence is incomplete or conflicts with the school, household, family, or applicant. Reconcile the verified SIS identity before retrying.';
  }
  if (status === 409) {
    return 'Enrollment is not ready. Verify acceptance, countersigned contract, deposit status, and canonical SIS records before retrying.';
  }
  if (status === 400) {
    return 'The enrollment request was rejected. Refresh the admissions application and verify its required fields.';
  }
  if (error?.isNetworkError || status == null) {
    return 'The enrollment response could not be verified because the API connection failed. Inspect the SIS record before retrying; do not assume the student was enrolled.';
  }
  return 'Enrollment could not be verified. Review the admissions and SIS records before retrying.';
}

/** The success claim is accepted only after a verified response and list refresh. */
export async function performVerifiedAdmissionsEnrollment({ applicationId, enroll, readback }) {
  let response;
  try {
    response = await enroll(applicationId);
  } catch (error) {
    return { ok: false, message: admissionsEnrollmentErrorMessage(error) };
  }
  const outcome = verifyAdmissionsEnrollmentResponse(response);
  if (!outcome.ok) return outcome;
  try {
    const refreshed = await readback(applicationId);
    // This is a second API observation of the *legacy admissions status*,
    // not a direct database read of core.Enrollment or identity provenance.
    if (String(refreshed?.id ?? '') !== String(applicationId)
      || refreshed?.status !== 'ENROLLED') {
      return {
        ok: false,
        message: 'The server reported verified SIS enrollment, but the refreshed admissions application is missing or not ENROLLED. Reconcile the admissions and SIS records before proceeding.',
      };
    }
  } catch {
    return {
      ok: false,
      message: 'The server reported verified enrollment, but the admissions list could not be refreshed. Verify the persisted SIS record before relying on this status.',
    };
  }
  return outcome;
}
