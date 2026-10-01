import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import ClassroomOperations from './ClassroomOperations.jsx';
import { crownApiClient as api } from '../../api/client';
vi.mock('../../api/client', () => ({ crownApiClient: { get: vi.fn(), post: vi.fn() } }));
afterEach(() => { cleanup(); vi.clearAllMocks(); });
const base = { source: 'live', sections: [{ id: 'section', 'course__name': 'Science', term: 'Fall' }], substitute_candidates: [] };
const selected = { ...base, attendance_version: 0, roster: [{ id: 'student', name: 'Student One', identity_verified: false, attendance: null }], attendance_history: [], packet: { prepared_at: '2026-10-01T12:00:00Z', lesson_plans: [], substitute_instructions: [], limitations: [] }, delegations: [], emergencies: [], can_delegate: false };
it('requires a verified student identity and never defaults unmarked attendance to present', async () => {
  api.get.mockResolvedValueOnce({ data: base }).mockResolvedValue({ data: selected });
  render(<ClassroomOperations audience="teacher" />);
  fireEvent.mouseDown(await screen.findByLabelText('Operational classroom'));
  fireEvent.click(await screen.findByRole('option', { name: 'Science · Fall' }));
  const control = await screen.findByLabelText('Student One — verified identity required');
  expect(control.getAttribute('aria-disabled')).toBe('true');
  expect(screen.getByText('Save confirmed attendance').disabled).toBe(true);
  expect(api.post).not.toHaveBeenCalled();
});
it('does not expose a print packet or empty success after an unavailable load', async () => {
  api.get.mockRejectedValue(new Error('offline'));
  render(<ClassroomOperations audience="teacher" />);
  await screen.findByText(/could not be loaded/);
  expect(screen.queryByText('Print selected packet')).toBeNull();
});
