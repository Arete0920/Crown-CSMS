import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import AssignmentWork from './AssignmentWork.jsx';
import { crownApiClient as api } from '../../api/client';
vi.mock('../../api/client', () => ({ crownApiClient: { get: vi.fn(), post: vi.fn() } }));
afterEach(() => { cleanup(); vi.clearAllMocks(); });
const work = { version: 0, state: 'assigned', content: '', revisions: [] };
it('confirms saved drafts only after the server accepts them', async () => {
  api.get.mockResolvedValue({ data: work });
  api.post.mockResolvedValue({ data: { ...work, version: 1, state: 'draft', content: 'Evidence' } });
  render(<AssignmentWork audience="student" assignment={{ id: 'a', student_id: 's' }} students={[]} />);
  const field = await screen.findByLabelText('Your work');
  fireEvent.change(field, { target: { value: 'Evidence' } });
  fireEvent.click(screen.getByText('Save draft'));
  expect(await screen.findByText('Draft saved to your school account.')).toBeTruthy();
});
it('retains text and reuses the same retry key after an unconfirmed save', async () => {
  api.get.mockResolvedValue({ data: work });
  api.post.mockRejectedValue(new Error('offline'));
  render(<AssignmentWork audience="student" assignment={{ id: 'a', student_id: 's' }} students={[]} />);
  const field = await screen.findByLabelText('Your work');
  fireEvent.change(field, { target: { value: 'Evidence' } });
  fireEvent.click(screen.getByText('Save draft'));
  await screen.findByRole('alert');
  expect(field.value).toBe('Evidence');
  fireEvent.click(screen.getByText('Save draft'));
  await waitFor(() => expect(api.post).toHaveBeenCalledTimes(2));
  expect(api.post.mock.calls[0][1].request_key).toBe(api.post.mock.calls[1][1].request_key);
});
it('parents have no save or submit controls', async () => {
  api.get.mockResolvedValue({ data: work });
  render(<AssignmentWork audience="parent" assignment={{ id: 'a', student_id: 's' }} students={[]} />);
  await screen.findByText('No shared written work available.');
  expect(screen.queryByText('Submit work')).toBeNull();
  expect(screen.queryByText('Save draft')).toBeNull();
});
