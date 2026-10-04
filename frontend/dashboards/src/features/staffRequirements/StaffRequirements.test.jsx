import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import StaffRequirements from './StaffRequirements';
import { crownApiClient as api } from '../../api/client';
vi.mock('../../api/client', () => ({ crownApiClient: { get: vi.fn(), post: vi.fn() } }));
afterEach(() => { cleanup(); vi.clearAllMocks(); });
const row = { id: 'requirement', staff_id: 'staff', staff_name: 'Grace Teacher', staff_status: 'ACTIVE',
  title: 'Annual training', category: 'training', status: 'overdue', due_date: '2026-10-01',
  completed_on: null, valid_until: null, evidence_reference: '', version: 2 };
const data = { source: 'live', can_edit: true, requirements: [row], total: 1, offset: 0, next_offset: null,
  summary: { overdue: 1 }, staff: [{ id: 'staff', first_name: 'Grace', last_name: 'Teacher' }], staff_total: 1, history: null };

async function start(response = data) {
  api.get.mockResolvedValue({ data: response }); render(<StaffRequirements />);
  await screen.findByText('Grace Teacher · Annual training');
}

it('loads real requirement states and requires evidence and a reason before completion', async () => {
  await start(); api.post.mockResolvedValue({ data: { version: 3 } });
  expect(screen.getByText(/1 requirements · 1 overdue/)).toBeTruthy();
  expect(screen.getByText('Record reviewed completion').disabled).toBe(true);
  fireEvent.change(screen.getByLabelText('Review reason for Annual training'), { target: { value: 'Reviewed school record' } });
  fireEvent.change(screen.getByLabelText('Evidence reference for Annual training'), { target: { value: 'school-record:001' } });
  fireEvent.click(screen.getByText('Record reviewed completion'));
  await waitFor(() => expect(api.post).toHaveBeenCalled());
  expect(api.post.mock.calls[0][1]).toMatchObject({ operation: 'complete', requirement_id: 'requirement', version: 2,
    reason: 'Reviewed school record', evidence_reference: 'school-record:001' });
});

it('retains inputs and the retry key when a save is not confirmed', async () => {
  await start(); api.post.mockRejectedValue(new Error('offline'));
  fireEvent.change(screen.getByLabelText('Review reason for Annual training'), { target: { value: 'Confirmed completion' } });
  fireEvent.change(screen.getByLabelText('Evidence reference for Annual training'), { target: { value: 'school-record:002' } });
  fireEvent.click(screen.getByText('Record reviewed completion'));
  await screen.findByText(/Save not confirmed/);
  fireEvent.click(screen.getByText('Record reviewed completion'));
  await waitFor(() => expect(api.post).toHaveBeenCalledTimes(2));
  expect(api.post.mock.calls[0][1].request_key).toBe(api.post.mock.calls[1][1].request_key);
});

it('does not show edit actions to a read-only HR account', async () => {
  await start({ ...data, can_edit: false });
  expect(screen.queryByText('Assign staff requirement')).toBeNull();
  expect(screen.queryByText('Record reviewed completion')).toBeNull();
  expect(screen.getByText('Load review history')).toBeTruthy();
});

it('creates requirements using the selected canonical staff identifier', async () => {
  await start(); api.post.mockResolvedValue({ data: { id: 'new' } });
  fireEvent.click(screen.getByText('Add a staff requirement'));
  fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Canonical staff member' }));
  fireEvent.click(within(screen.getByRole('listbox')).getByText('Grace Teacher'));
  fireEvent.change(screen.getByLabelText('Requirement title'), { target: { value: 'School orientation' } });
  fireEvent.change(screen.getByLabelText('Requirement due date'), { target: { value: '2026-10-10' } });
  fireEvent.change(screen.getByLabelText('Assignment reason'), { target: { value: 'New staff onboarding' } });
  fireEvent.click(screen.getByText('Assign staff requirement'));
  await waitFor(() => expect(api.post).toHaveBeenCalled());
  expect(api.post.mock.calls[0][1]).toMatchObject({ operation: 'create', staff_id: 'staff',
    title: 'School orientation', category: 'training', due_date: '2026-10-10', reason: 'New staff onboarding' });
});

it('shows bounded pages and requests the next offset', async () => {
  await start({ ...data, total: 105, next_offset: 100, staff_total: 205 });
  expect(screen.getByText(/Showing 1 of 205 matching active staff/)).toBeTruthy();
  fireEvent.click(screen.getByText('Next requirement page'));
  await waitFor(() => expect(api.get.mock.calls.some(([url]) => url.includes('offset=100'))).toBe(true));
});

it('loads retained history without replacing it with completion claims', async () => {
  await start(); api.get.mockResolvedValue({ data: { ...data, history: { requirement_id: row.id, total: 2, offset: 0, next_offset: null,
    events: [{ version: 3, action: 'reopen', reason: 'Correction needed', before: { evidence_reference: 'school-record:old' }, after: {} }] } } });
  fireEvent.click(screen.getByText('Load review history'));
  expect(await screen.findByText(/Previous evidence: school-record:old/)).toBeTruthy();
  expect(screen.getByText(/Showing 1–1 of 2 review events/)).toBeTruthy();
});

it('does not show stale requirements after a failed refresh', async () => {
  await start(); api.get.mockRejectedValue(new Error('offline'));
  fireEvent.click(screen.getByText('Refresh staff requirements'));
  await screen.findByText(/Staff requirements could not be loaded/);
  expect(screen.queryByText('Grace Teacher · Annual training')).toBeNull();
});


it('requests older review evidence through bounded history pages', async () => {
  await start(); api.get.mockResolvedValue({ data: { ...data, history: { requirement_id: row.id,
    total: 105, offset: 0, next_offset: 100, events: [{ version: 105, action: 'reschedule',
    reason: 'Annual review', before: {}, after: {} }] } } });
  fireEvent.click(screen.getByText('Load review history'));
  await screen.findByText(/Version 105/);
  fireEvent.click(screen.getByText('Next history page'));
  await waitFor(() => expect(api.get.mock.calls.some(([url]) => url.includes('history_offset=100'))).toBe(true));
});


it('uses the school calendar completion default and clears revoked access', async () => {
  await start({ ...data, today: '2026-10-03' });
  expect(screen.getByLabelText('Completion date for Annual training').value).toBe('2026-10-03');
  api.post.mockRejectedValue({ response: { status: 403, data: { detail: 'Access revoked' } } });
  fireEvent.change(screen.getByLabelText('Review reason for Annual training'), { target: { value: 'Reviewed' } });
  fireEvent.change(screen.getByLabelText('Evidence reference for Annual training'), { target: { value: 'source' } });
  fireEvent.click(screen.getByText('Record reviewed completion'));
  await screen.findByText('Access revoked');
  expect(screen.queryByText('Grace Teacher · Annual training')).toBeNull();
});
