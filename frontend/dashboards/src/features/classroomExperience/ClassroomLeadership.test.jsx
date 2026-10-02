import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import ClassroomLeadership from './ClassroomLeadership.jsx';
import { crownApiClient as api } from '../../api/client';
vi.mock('../../api/client', () => ({ crownApiClient: { get: vi.fn() } }));
afterEach(() => { cleanup(); vi.clearAllMocks(); });
const data = { source: 'live', from: '2026-10-01', to: '2026-10-01', generated_at: '2026-10-01T12:00:00Z', terms: [], summary: { recorded_actual_minutes: null, recorded_resource_cost_cents: 0, definitions: { minutes: 'Only recorded minutes are summed.' } }, provenance: ['academics.LessonPlanLesson'], limitations: [] };
it('preserves unknown values and source definitions', async () => {
  api.get.mockResolvedValue({ data });
  render(<ClassroomLeadership audience="admin" />);
  expect(await screen.findByText('No recorded value')).toBeTruthy();
  expect(screen.getByText('0')).toBeTruthy();
  expect(screen.getByText('Only recorded minutes are summed.')).toBeTruthy();
});
it('board UI does not render supplied individual staff rows', async () => {
  api.get.mockResolvedValue({ data: { ...data, teacher_workload: [{ teacher_id: '1', teacher: 'Private teacher' }] } });
  render(<ClassroomLeadership audience="board" />);
  await screen.findByText('Only recorded minutes are summed.');
  expect(screen.queryByText(/Private teacher/)).toBeNull();
  expect(screen.queryByText('Recorded teacher workload')).toBeNull();
});
it('failed fetch does not render successful empty counts', async () => {
  api.get.mockRejectedValue(new Error('offline'));
  render(<ClassroomLeadership audience="board" />);
  expect((await screen.findByRole('alert')).textContent).toContain('could not be loaded');
  expect(screen.queryByText('Definitions and sources')).toBeNull();
});
it('sends an explicit planning target while labeling it a scenario', async () => {
  api.get.mockResolvedValue({ data });
  render(<ClassroomLeadership audience="admin" />);
  await screen.findByText('Only recorded minutes are summed.');
  fireEvent.change(screen.getByLabelText('Planning target: students per section'), { target: { value: '20' } });
  await waitFor(() => expect(api.get.mock.lastCall[1].params.target_class_size).toBe('20'));
  expect(screen.getByText('Optional scenario using current rosters')).toBeTruthy();
});
it('shows recorded objective coverage and withholds an empty inventory', async () => {
  api.get.mockResolvedValue({ data: { ...data, sections: [{ id: 's1', course: 'Science' }, { id: 's2', course: 'History' }], curriculum_coverage: [
    { section_id: 's1', known_objectives: 2, planned_objectives: 1, confirmed_taught_objectives: 1, unplanned_objectives: 1, alignment_issues: 0, known_objective_delivery_percent: 50 },
    { section_id: 's2', known_objectives: 0, planned_objectives: 0, confirmed_taught_objectives: 0, unplanned_objectives: 0, alignment_issues: 0, known_objective_delivery_percent: null },
  ] } });
  render(<ClassroomLeadership audience="admin" />);
  expect(await screen.findByText(/Science: 2 known objectives.*50%/)).toBeTruthy();
  expect(screen.getByText(/History: 0 known objectives.*withheld/)).toBeTruthy();
});
