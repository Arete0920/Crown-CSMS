import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import ClassroomInstruction from './ClassroomInstruction.jsx';
import { crownApiClient as api } from '../../api/client';
vi.mock('../../api/client', () => ({ crownApiClient: { get: vi.fn(), post: vi.fn() } }));
afterEach(() => { cleanup(); vi.clearAllMocks(); });
const props = { audience: 'student', sections: [], students: [], assignments: [] };
const data = { source: 'live', lessons: [], objectives: [], plans: [], rubrics: [], adjustments: [], resources: [], mastery_history: [], progress: [{ section_id: 's', student_id: 'p', weighted_preview_percent: null, recorded_scored_assignments: 0, published_assignments: 1, policy_weight_total: 0, categories: [], limitation: 'Unscored work is not zero.' }] };
it('withholds a weighted preview when evidence or policy is incomplete', async () => {
  api.get.mockResolvedValue({ data });
  render(<ClassroomInstruction {...props} />);
  await screen.findByText(/Weighted preview withheld/);
  expect(screen.queryByText(/Provisional weighted evidence: 0/)).toBeNull();
  expect(screen.queryByText('Save instruction change')).toBeNull();
});
it('shows real recorded zero and accessible alternatives without turning them into a report-card grade', async () => {
  api.get.mockResolvedValue({ data: { ...data, progress: [{ ...data.progress[0], weighted_preview_percent: 0 }], resources: [{ id: 'r', title: 'Observation guide', url: 'https://example.com/guide', accessible_description: 'Written diagram description', alternative_instructions: 'Follow the written steps' }] } });
  render(<ClassroomInstruction {...props} />);
  await screen.findByText('Provisional weighted evidence: 0.0%');
  expect(screen.getByText('Follow the written steps')).toBeTruthy();
  expect(screen.getByRole('link', { name: 'Open Observation guide' }).getAttribute('href')).toBe('https://example.com/guide');
});
it('does not invent instruction evidence when a load is unavailable', async () => {
  api.get.mockRejectedValue(new Error('offline'));
  render(<ClassroomInstruction {...props} />);
  await screen.findByText(/could not be loaded/);
  expect(screen.queryByText('Dated mastery evidence')).toBeNull();
});
