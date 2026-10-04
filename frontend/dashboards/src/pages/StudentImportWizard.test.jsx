import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import StudentImportWizard from './StudentImportWizard';
import { apiFetch } from '../lib/api';
vi.mock('../lib/api', () => ({ apiFetch: vi.fn() }));
vi.mock('../components/crown/CrownLayout.jsx', () => ({ default: (props) => <div>{props.children}</div> }));
afterEach(() => { cleanup(); vi.clearAllMocks(); });
const session = '00000000-0000-0000-0000-000000000001';
const row = { row: 0, action: 'create', before: null, household_id: 'household-id', grade_code: '',
  after: { student_number: 'SYNTHETIC-001', first_name: 'Sample', last_name: 'Student', dob: '2014-01-01', status: 'ACTIVE', family_id: 'family-id', grade_level_id: null } };
const preview = { schema: 2, valid: 1, rows: [row], errors: [], fingerprint: 'review-fingerprint' };
const verified = { schema: 2, source: 'live', session_id: session, verified: true, verified_count: 1,
  records: [{ ...row, student_id: 'canonical-student-id' }], created: 1, updated: 0, differences: [], verified_at: '2026-10-04T04:00:00Z' };
const response = (data, status = 200) => ({ ok: status < 400, status, json: async () => data });
async function start(review = preview, proof = verified) {
  apiFetch.mockImplementation(async (url) => response(url.endsWith('/preview/') ? review : url.endsWith('/verify/') ? proof : { session_id: session, schema: 2, created: 1, updated: 0, records: verified.records }));
  render(<StudentImportWizard />); fireEvent.click(screen.getByText('Configure import'));
  await screen.findByText('Run canonical preview'); fireEvent.click(screen.getByText('Run canonical preview'));
  await screen.findByText('Review before committing');
}
function approve() {
  fireEvent.change(screen.getByLabelText('Import review reason'), { target: { value: 'Reviewed roster source and mappings' } });
  fireEvent.click(screen.getByRole('checkbox', { name: 'I reviewed every proposed change and its identity mappings' }));
}
it('requires a valid review, reason and explicit confirmation before the canonical write', async () => {
  await start(); const button = screen.getByText('Commit reviewed batch and verify');
  expect(button.disabled).toBe(true); approve(); expect(button.disabled).toBe(false);
  fireEvent.click(button); await screen.findByText('Canonical import verified');
  const [, options] = apiFetch.mock.calls.find(([url]) => url.endsWith('/commit/'));
  expect(JSON.parse(options.body)).toEqual({ confirm: true, fingerprint: preview.fingerprint, reason: 'Reviewed roster source and mappings' });
});
it('blocks the whole batch when any row requires correction', async () => {
  await start({ ...preview, errors: [{ row: 1, messages: ['Family mapping needs review'] }] });
  expect(screen.getByText('Row 2: Family mapping needs review')).toBeTruthy();
  expect(screen.getByText('Commit reviewed batch and verify').disabled).toBe(true);
  expect(screen.getByRole('checkbox').disabled).toBe(true);
});
it('retains the reviewed payload after an unconfirmed commit', async () => {
  await start(); const original = apiFetch.getMockImplementation();
  apiFetch.mockImplementation(async (url, options) => url.endsWith('/commit/') ? Promise.reject(new Error('Network interruption')) : original(url, options));
  approve(); fireEvent.click(screen.getByText('Commit reviewed batch and verify')); await screen.findByText('Network interruption');
  fireEvent.click(screen.getByText('Commit reviewed batch and verify'));
  await waitFor(() => expect(apiFetch.mock.calls.filter(([url]) => url.endsWith('/commit/')).length).toBe(2));
  const calls = apiFetch.mock.calls.filter(([url]) => url.endsWith('/commit/'));
  expect(calls[0][1].body).toBe(calls[1][1].body);
});
it('separates saved writes from pending verification and retries only verification', async () => {
  await start(); const original = apiFetch.getMockImplementation();
  apiFetch.mockImplementation(async (url, options) => url.endsWith('/verify/') ? Promise.reject(new Error('Verification unavailable')) : original(url, options));
  approve(); fireEvent.click(screen.getByText('Commit reviewed batch and verify'));
  await screen.findByText('The batch was saved; canonical verification is still pending.');
  expect(screen.queryByText('Canonical import verified')).toBeNull();
  apiFetch.mockImplementation(original); fireEvent.click(screen.getByText('Recheck canonical records'));
  await screen.findByText('Canonical import verified');
  expect(apiFetch.mock.calls.filter(([url]) => url.endsWith('/commit/')).length).toBe(1);
});
it('reports changed saved rows as reconciliation rather than successful verification', async () => {
  await start(preview, { ...verified, verified: false, verified_count: 0, differences: [{ row: 0, detail: 'Canonical mapping changed.' }] });
  approve(); fireEvent.click(screen.getByText('Commit reviewed batch and verify'));
  await screen.findByText('Imported records need reconciliation');
  expect(screen.queryByText('Canonical import verified')).toBeNull();
});
it('clears record previews when roster access is revoked', async () => {
  await start(); const original = apiFetch.getMockImplementation();
  apiFetch.mockImplementation(async (url, options) => url.endsWith('/commit/') ? response({ detail: 'Roster access revoked' }, 403) : original(url, options));
  approve(); fireEvent.click(screen.getByText('Commit reviewed batch and verify')); await screen.findByText('Roster access revoked');
  expect(screen.queryByText(/Row 1 · create/)).toBeNull();
  expect(screen.queryByLabelText('Import review reason')).toBeNull();
});
it('makes every proposed row reachable without changing reviewed evidence', async () => {
  const rows = Array.from({ length: 101 }, (_, i) => ({ ...row, row: i, after: { ...row.after, student_number: `SOURCE-${i}` } }));
  await start({ ...preview, rows, valid: 101 });
  expect(screen.queryByText(/Row 101 · create/)).toBeNull();
  fireEvent.click(screen.getByText('Next proposed rows')); expect(await screen.findByText(/Row 101 · create/)).toBeTruthy();
});
it('rejects incomplete verification metadata', async () => {
  await start(preview, { ...verified, verified_count: 0 }); approve();
  fireEvent.click(screen.getByText('Commit reviewed batch and verify'));
  await screen.findByText('Canonical verification evidence unavailable. Retry verification.');
  expect(screen.queryByText('Canonical import verified')).toBeNull();
});
