import { beforeEach, describe, expect, it, vi } from 'vitest';

const { authenticatedFetch } = vi.hoisted(() => ({ authenticatedFetch: vi.fn() }));
vi.mock('../utils/authClient', () => ({ authenticatedFetch }));

import * as attendanceCodes from '../api/attendance_codes_wizard';
import * as attendanceRules from '../api/attendance_rules_wizard';
import * as bellSchedule from '../api/bell_schedule_wizard';
import * as enrollmentConversion from '../api/enrollment_conversion_wizard';

function jsonResponse(body = { ok: true }, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}

const cases = [
  [attendanceCodes.createAttendanceCodesSession, [], '/api/v1/attendance-codes-wizard/sessions/', 'POST', {}],
  [attendanceCodes.configureAttendanceCodesSession, ['s1', { school_year: '2026' }], '/api/v1/attendance-codes-wizard/sessions/s1/configure/', 'POST', { policy_config: { school_year: '2026' } }],
  [attendanceCodes.stageCodes, ['s1', [{ code: 'A' }]], '/api/v1/attendance-codes-wizard/sessions/s1/stage_codes/', 'POST', { codes_staged: [{ code: 'A' }] }],
  [attendanceCodes.commitAttendanceCodesSession, ['s1'], '/api/v1/attendance-codes-wizard/sessions/s1/commit/', 'POST', { confirm: true }],
  [attendanceCodes.verifyAttendanceCodesSession, ['s1'], '/api/v1/attendance-codes-wizard/sessions/s1/verify/', 'GET', undefined],
  [attendanceRules.createAttendanceRulesSession, [], '/api/v1/attendance-rules-wizard/sessions/', 'POST', {}],
  [attendanceRules.configureAttendanceRulesSession, ['s1', 'Policy', '2026'], '/api/v1/attendance-rules-wizard/sessions/s1/configure/', 'POST', { label: 'Policy', school_year: '2026' }],
  [attendanceRules.defineCodes, ['s1', [{ code: 'A' }]], '/api/v1/attendance-rules-wizard/sessions/s1/codes/', 'POST', { codes: [{ code: 'A' }] }],
  [attendanceRules.commitAttendanceRulesSession, ['s1'], '/api/v1/attendance-rules-wizard/sessions/s1/commit/', 'POST', { confirm: true }],
  [attendanceRules.verifyAttendanceRulesSession, ['s1'], '/api/v1/attendance-rules-wizard/sessions/s1/verify/', 'GET', undefined],
  [bellSchedule.createBellScheduleSession, [], '/api/v1/bell-schedule-wizard/sessions/', 'POST', {}],
  [bellSchedule.configureBellScheduleSession, ['s1', 'Default', '2026'], '/api/v1/bell-schedule-wizard/sessions/s1/configure/', 'POST', { label: 'Default', school_year: '2026' }],
  [bellSchedule.definePeriods, ['s1', [{ name: 'First' }]], '/api/v1/bell-schedule-wizard/sessions/s1/periods/', 'POST', { periods: [{ name: 'First' }] }],
  [bellSchedule.commitBellScheduleSession, ['s1'], '/api/v1/bell-schedule-wizard/sessions/s1/commit/', 'POST', { confirm: true }],
  [bellSchedule.verifyBellScheduleSession, ['s1'], '/api/v1/bell-schedule-wizard/sessions/s1/verify/', 'GET', undefined],
  [enrollmentConversion.createEnrollmentConversionSession, [], '/api/v1/enrollment-conversion-wizard/sessions/', 'POST', {}],
  [enrollmentConversion.configureEnrollmentConversionSession, ['s1', '2026-2027', 'accepted'], '/api/v1/enrollment-conversion-wizard/sessions/s1/configure/', 'POST', { academic_year_label: '2026-2027', from_status: 'accepted' }],
  [enrollmentConversion.loadApplicants, ['s1'], '/api/v1/enrollment-conversion-wizard/sessions/s1/load/', 'POST', {}],
  [enrollmentConversion.commitEnrollmentConversionSession, ['s1'], '/api/v1/enrollment-conversion-wizard/sessions/s1/commit/', 'POST', { confirm: true }],
  [enrollmentConversion.verifyEnrollmentConversionSession, ['s1'], '/api/v1/enrollment-conversion-wizard/sessions/s1/verify/', 'GET', undefined],
];

function apiPath(url) {
  return new URL(url, 'http://crown.local').pathname;
}

describe('wizard canonical transport behavior', () => {
  beforeEach(() => {
    authenticatedFetch.mockReset();
    authenticatedFetch.mockResolvedValue(jsonResponse());
  });

  it.each(cases)('routes every exported operation through authenticatedFetch', async (operation, args, expectedPath, method, expectedBody) => {
    await operation(...args);

    expect(authenticatedFetch).toHaveBeenCalledTimes(1);
    const [url, init] = authenticatedFetch.mock.calls[0];
    expect(apiPath(url)).toBe(expectedPath);
    expect(init.method).toBe(method);
    expect(typeof init.validateStatus).toBe('function');
    expect(init.validateStatus(400)).toBe(true);
    if (expectedBody === undefined) expect(init.body).toBeUndefined();
    else expect(JSON.parse(init.body)).toEqual(expectedBody);
  });

  it('preserves parsed validation payloads for wizard UIs', async () => {
    authenticatedFetch.mockResolvedValueOnce(jsonResponse({ error: 'Periods overlap', errors: ['p1'] }, 400));

    await expect(bellSchedule.definePeriods('s1', [])).rejects.toMatchObject({
      status: 400,
      body: { error: 'Periods overlap', errors: ['p1'] },
    });
  });
});
