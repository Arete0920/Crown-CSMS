import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import ClassroomSupport from './ClassroomSupport.jsx';
import { crownApiClient as api } from '../../api/client';
vi.mock('../../api/client', () => ({ crownApiClient: { get: vi.fn(), post: vi.fn() } }));
afterEach(() => { cleanup(); vi.clearAllMocks(); });
const props = { audience: 'teacher', sections: [], students: [] };
const row = { id: 'case', section_id: 'section', student_id: 'student', reason: 'Evidence support', state: 'IN_PROGRESS', version: 2, review_at: '2026-10-10T12:00:00Z', actions: [], overdue_review: false };
it('records closure evidence only after confirmation and preserves failed notes', async () => {
  api.get.mockResolvedValue({ data: { source: 'live', cases: [row], restorative: [] } });
  api.post.mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce({ data: { saved: true } });
  render(<ClassroomSupport {...props} />);
  fireEvent.change(await screen.findByLabelText('Follow-through evidence: Evidence support'), { target: { value: 'Independent evidence explanation confirmed' } });
  fireEvent.click(screen.getByText('Close with outcome evidence'));
  await screen.findByText(/Save not confirmed/);
  expect(screen.queryByText('Support follow-through confirmed.')).toBeNull();
  fireEvent.click(screen.getByText('Close with outcome evidence'));
  await screen.findByText('Support follow-through confirmed.');
  expect(api.post.mock.calls[0][1]).toEqual(api.post.mock.calls[1][1]);
  expect(api.post.mock.calls[0][1].version).toBe(2);
});
it('does not present an unavailable support queue as no concerns', async () => {
  api.get.mockRejectedValue(new Error('offline'));
  render(<ClassroomSupport {...props} />);
  await screen.findByText(/could not be loaded/);
  expect(screen.queryByText('No owned classroom support plans recorded.')).toBeNull();
});
