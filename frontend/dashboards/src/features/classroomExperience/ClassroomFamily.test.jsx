import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import ClassroomFamily from './ClassroomFamily.jsx';
import { crownApiClient as api } from '../../api/client';
vi.mock('../../api/client', () => ({ crownApiClient: { get: vi.fn(), post: vi.fn() } }));
afterEach(() => { cleanup(); vi.clearAllMocks(); });
const props = { audience: 'parent', sections: [], students: [], assignments: [] };
const data = { source: 'live', threads: [{ id: 't', kind: 'consent', title: 'Trip permission', state: 'open', version: 1, messages: [] }], slots: [], guardians: [], notices: [], disclosures: [], preferences: { in_app: true, digest_day: 0, timezone: 'UTC' }, digest: { from: '2026-10-01', to: '2026-10-07', prepared_at: '2026-10-01T12:00:00Z', assignments: [], recorded_submissions: 0, open_conversations: 1 } };
it('records guardian consent only after a server confirmation and retains failed text', async () => {
  api.get.mockResolvedValue({ data });
  api.post.mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce({ data: { saved: true } });
  render(<ClassroomFamily {...props} />);
  fireEvent.change(await screen.findByLabelText('Reply or follow-up for Trip permission'), { target: { value: 'I grant permission' } });
  fireEvent.click(screen.getByText('Grant permission'));
  await screen.findByText(/Save not confirmed/);
  expect(screen.queryByText('Saved to your classroom.')).toBeNull();
  expect(screen.getByLabelText('Reply or follow-up for Trip permission').value).toBe('I grant permission');
  fireEvent.click(screen.getByText('Grant permission'));
  await screen.findByText('Saved to your classroom.');
  expect(api.post.mock.calls[0][1]).toEqual(api.post.mock.calls[1][1]);
  expect(api.post.mock.calls[0][1].decision).toBe('agreed');
});
it('does not invent a successful empty family workspace from malformed data', async () => {
  api.get.mockResolvedValue({ data: { source: 'live' } });
  render(<ClassroomFamily {...props} />);
  await screen.findByText(/could not be loaded/);
  expect(screen.queryByText('No family classroom conversations yet.')).toBeNull();
});
it('shows staff follow-through without guardian consent controls', async () => {
  api.get.mockResolvedValue({ data });
  render(<ClassroomFamily {...props} audience="teacher" />);
  await screen.findByText('Trip permission');
  expect(screen.queryByText('Grant permission')).toBeNull();
  expect(screen.queryByText('Decline permission')).toBeNull();
});

it('hides prior audience records while a new audience is loading', async () => {
  api.get.mockResolvedValueOnce({ data }).mockImplementationOnce(() => new Promise(() => {}));
  const { rerender } = render(<ClassroomFamily {...props} />);
  await screen.findByText('Trip permission');
  rerender(<ClassroomFamily {...props} audience="teacher" />);
  expect(screen.queryByText('Trip permission')).toBeNull();
});

it('withholds old homework after a failed refresh and recovers on retry', async () => {
  api.get.mockResolvedValueOnce({ data }).mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce({ data });
  render(<ClassroomFamily {...props} />);
  await screen.findByText('Trip permission');
  fireEvent.click(screen.getByText('Refresh family workspace'));
  await screen.findByText(/could not be loaded/);
  expect(screen.queryByText('Trip permission')).toBeNull();
  fireEvent.click(screen.getByText('Refresh family workspace'));
  await screen.findByText('Trip permission');
  expect(screen.queryByText(/could not be loaded/)).toBeNull();
});
