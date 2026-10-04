import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import StudentHealth from './StudentHealth';
import { crownApiClient as api } from '../../api/client';
vi.mock('../../api/client', () => ({ crownApiClient: { get: vi.fn(), post: vi.fn() } }));
afterEach(() => { cleanup(); vi.clearAllMocks(); });
const student = { id: 'student-1', first_name: 'Casey', last_name: 'Student', student_number: '001', status: 'ACTIVE' };
const entry = { id: 'entry-1', kind: 'visit', occurred_at: '2026-10-03T10:00:00-04:00', topic: 'Recorded visit', summary: 'Recorded school observation', corrects_id: null, superseded: false };
const base = { source: 'live', can_edit: true, students: [student], students_total: 1 };
const chart = { ...base, student_id: student.id, student_status: 'ACTIVE', entries: [entry], entries_total: 1,
  offset: 0, next_offset: null, summary: { visit: 1 }, follow_up_due: 0, guardians: [], authorizations: [],
  authorizations_total: 0, authorizations_next_offset: null, history: [], history_total: 0, history_next_offset: null };
async function start(data = chart) {
  api.get.mockImplementation(async (url) => ({ data: url.includes('student_id=') ? data : base }));
  render(<StudentHealth />);
  fireEvent.mouseDown(await screen.findByRole('combobox', { name: 'Canonical student health record' }));
  fireEvent.click(within(screen.getByRole('listbox')).getByText(/Casey Student/));
  await screen.findByText('Recorded school observation');
}
function fill() {
  fireEvent.change(screen.getByLabelText('Event timestamp with timezone'), { target: { value: '2026-10-03T10:00:00-04:00' } });
  fireEvent.change(screen.getByLabelText('Record topic'), { target: { value: 'School visit' } });
  fireEvent.change(screen.getByLabelText('Recorded observations or source details'), { target: { value: 'Actual observation' } });
  fireEvent.change(screen.getByLabelText('Record or correction reason'), { target: { value: 'Reviewed source' } });
}
it('uses canonical patient identity and explicit actual observations', async () => {
  await start(); expect(screen.getByText('Save health entry').disabled).toBe(true);
  api.post.mockResolvedValue({ data: { saved: true } }); fill(); fireEvent.click(screen.getByText('Save health entry'));
  await waitFor(() => expect(api.post).toHaveBeenCalled());
  expect(api.post.mock.calls[0][1]).toMatchObject({ operation: 'record', student_id: student.id, kind: 'visit',
    occurred_at: '2026-10-03T10:00:00-04:00', summary: 'Actual observation', reason: 'Reviewed source' });
});
it('retains entry inputs and retry identity after an unconfirmed save', async () => {
  await start(); api.post.mockRejectedValue(new Error('offline')); fill();
  fireEvent.click(screen.getByText('Save health entry')); await screen.findByText(/Save not confirmed/);
  expect(screen.getByLabelText('Record topic').value).toBe('School visit');
  fireEvent.click(screen.getByText('Save health entry')); await waitFor(() => expect(api.post).toHaveBeenCalledTimes(2));
  expect(api.post.mock.calls[0][1].request_key).toBe(api.post.mock.calls[1][1].request_key);
});
it('appends a correction to the selected entry instead of changing the original', async () => {
  await start(); api.post.mockRejectedValue(new Error('offline'));
  fireEvent.click(screen.getByText('Correct entry entry-1'));
  expect(screen.getByText('Append a correction; retain the original entry')).toBeTruthy();
  expect(screen.getByRole('combobox', { name: 'Health record kind' }).getAttribute('aria-disabled')).toBe('true');
  fireEvent.change(screen.getByLabelText('Record or correction reason'), { target: { value: 'Source clarified' } });
  fireEvent.click(screen.getByText('Save health entry')); await waitFor(() => expect(api.post).toHaveBeenCalled());
  expect(api.post.mock.calls[0][1]).toMatchObject({ corrects_id: entry.id, student_id: student.id, kind: 'visit', reason: 'Source clarified' });
});
it('hides chart edit actions for read-only clinical access', async () => {
  await start({ ...chart, can_edit: false });
  expect(screen.queryByText('Save health entry')).toBeNull();
  expect(screen.queryByText('Record a reviewed medication authorization')).toBeNull();
  expect(screen.queryByText('Correct entry entry-1')).toBeNull();
});
it('exposes bounded chart, authorization and audit pagination', async () => {
  await start({ ...chart, next_offset: 100, authorizations_next_offset: 100, history_next_offset: 100 });
  fireEvent.click(screen.getByText('Next authorization page'));
  await waitFor(() => expect(api.get.mock.calls.some(([url]) => url.includes('authorization_offset=100'))).toBe(true));
  await screen.findByText('Recorded school observation'); fireEvent.click(screen.getByText('Next audit page'));
  await waitFor(() => expect(api.get.mock.calls.some(([url]) => url.includes('history_offset=100'))).toBe(true));
});
it('clears chart data after a failed refresh', async () => {
  await start(); api.get.mockRejectedValue(new Error('denied'));
  fireEvent.click(screen.getByText('Refresh health records')); await screen.findByText(/Health workspace unavailable/);
  expect(screen.queryByText('Recorded school observation')).toBeNull();
});
it('clears the previous patient chart when search changes', async () => {
  await start(); api.get.mockResolvedValue({ data: { ...base, students: [], students_total: 0 } });
  fireEvent.change(screen.getByLabelText('Search canonical students'), { target: { value: 'Other patient' } });
  await waitFor(() => expect(screen.queryByText('Recorded school observation')).toBeNull());
});


it('clears clinical records when write access is revoked', async () => {
  await start(); api.post.mockRejectedValue({ response: { status: 403, data: { detail: 'Clinical access revoked' } } });
  fill(); fireEvent.click(screen.getByText('Save health entry'));
  await screen.findByText('Clinical access revoked');
  expect(screen.queryByText('Recorded school observation')).toBeNull();
  expect(screen.queryByLabelText('Recorded observations or source details')).toBeNull();
});
