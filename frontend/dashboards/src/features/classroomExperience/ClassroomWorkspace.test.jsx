import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import ClassroomWorkspace from './ClassroomWorkspace.jsx';
import { crownApiClient as api } from '../../api/client';
vi.mock('../../api/client', () => ({ crownApiClient: { get: vi.fn() } }));
afterEach(() => { cleanup(); vi.clearAllMocks(); });
const payload = { audience: 'student', from: '2026-09-30', to: '2026-10-14', generated_at: '2026-09-30T12:00:00Z', terms: [], sections: [], students: [], lesson_plans: [], limitations: [], assignments: [{ id: 'a', student_id: 's', name: 'Observation', course: 'Science', due_date: '2026-10-01', state: 'awaiting_grading', points_earned: null, points_possible: 10, category: 'Practice', submitted_at: '2026-09-30T12:00:00Z' }] };
it('shows submission evidence without calling it missing or a zero grade', async () => {
  api.get.mockResolvedValue({ data: payload });
  render(<ClassroomWorkspace audience="student" />);
  expect(await screen.findByText('Submitted — awaiting grading')).toBeTruthy();
  expect(screen.queryByText(/Recorded points/)).toBeNull();
  expect(screen.getByText(/Submission recorded/)).toBeTruthy();
});
it('does not show empty success counts after a failed load', async () => {
  api.get.mockRejectedValue(new Error('offline'));
  render(<ClassroomWorkspace audience="parent" />);
  expect((await screen.findByRole('alert')).textContent).toContain('could not be loaded');
  expect(screen.queryByText(/No assignments recorded/)).toBeNull();
});
it('renders board definitions without individual work', async () => {
  api.get.mockResolvedValue({ data: { ...payload, audience: 'board', summary: { sections: 3, definitions: { sections: 'Recorded course sections.' } } } });
  render(<ClassroomWorkspace audience="board" />);
  expect(await screen.findByText('Recorded course sections.')).toBeTruthy();
  expect(screen.queryByText('Observation')).toBeNull();
});
