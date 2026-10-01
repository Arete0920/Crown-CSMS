import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import ClassroomRecords from './ClassroomRecords.jsx';
import { crownApiClient as api } from '../../api/client';
vi.mock('../../api/client', () => ({ crownApiClient: { get: vi.fn(), post: vi.fn() } }));
afterEach(() => { cleanup(); vi.clearAllMocks(); });
const props = { audience: 'student', sections: [], students: [{ id: 'student', first_name: 'Student', last_name: 'One' }], assignments: [] };
const record = { id: 'record', title: 'Understanding check', kind: 'formative_check', body: 'Explain your evidence', visibility: 'class', state: 'open', version: 1, metadata: { questions: ['Why?'] }, responses: [], history: [], can_manage: false };
it('keeps a failed response and reuses its retry key until confirmed', async () => {
  api.get.mockResolvedValue({ data: { source: 'live', records: [record] } });
  api.post.mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce({ data: record });
  render(<ClassroomRecords {...props} />);
  fireEvent.change(await screen.findByLabelText('Your response or contribution'), { target: { value: 'My evidence' } });
  fireEvent.click(screen.getByText('Save response'));
  await screen.findByText(/Save not confirmed/);
  expect(screen.getByLabelText('Your response or contribution').value).toBe('My evidence');
  fireEvent.click(screen.getByText('Save response'));
  await screen.findByText('Saved to your classroom.');
  expect(api.post.mock.calls[0][1]).toEqual(api.post.mock.calls[1][1]);
  expect(api.post.mock.calls[0][1].version).toBe(1);
});
it('does not represent an unavailable or malformed record feed as empty success', async () => {
  api.get.mockResolvedValue({ data: { records: [] } });
  render(<ClassroomRecords {...props} />);
  await screen.findByText(/could not be loaded/);
  expect(screen.queryByText('No classroom records yet.')).toBeNull();
});
it('parents have no controls to submit a student response', async () => {
  api.get.mockResolvedValue({ data: { source: 'live', records: [record] } });
  render(<ClassroomRecords {...props} audience="parent" />);
  await waitFor(() => expect(screen.getByText('Understanding check')).toBeTruthy());
  expect(screen.queryByText('Save response')).toBeNull();
  expect(screen.queryByLabelText('Your response or contribution')).toBeNull();
});

it('offers family service participation alongside absence explanations', async () => {
  api.get.mockResolvedValue({ data: { source: 'live', records: [], portrait_domains: [], worldview_priorities: [] } });
  render(<ClassroomRecords audience="parent" sections={[]} students={[]} assignments={[]} />);
  await screen.findByText('No classroom records yet.');
  expect(screen.getByLabelText('Record type').textContent).toContain('absence explanation');
});
