import { afterEach, expect, it } from 'vitest';
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import FamilyWeeklyAgenda from './FamilyWeeklyAgenda';

afterEach(cleanup);
const digest = {
  from: '2026-10-01', to: '2026-10-07', prepared_at: '2026-10-01T12:00:00Z',
  recorded_submissions: 1, open_conversations: 0, assignments_total: 2, truncated: false,
  assignments: [
    { id: 'shared', student_id: 'one', student_name: 'Alex One', course: 'Science', name: 'Observation',
      due_date: '2026-10-01', original_due_date: '2026-10-01', submission_state: 'submitted' },
    { id: 'shared', student_id: 'two', student_name: 'Sam Two', course: 'Science', name: 'Observation',
      due_date: '2026-10-03', original_due_date: '2026-10-01', submission_state: 'returned',
      makeup_instructions: 'Repeat the observation', home_support: 'Discuss the results' },
  ],
};

it('shows each child with their own deadline and recorded status', () => {
  render(<FamilyWeeklyAgenda digest={digest} manager={false} />);
  expect(screen.getByText('Alex One · Science')).toBeTruthy();
  expect(screen.getByText('Sam Two · Science')).toBeTruthy();
  expect(screen.getByText('Observation · Due 2026-10-03')).toBeTruthy();
  expect(screen.getByText('Returned for revision')).toBeTruthy();
  expect(screen.getByText('Makeup instructions: Repeat the observation')).toBeTruthy();
  expect(screen.getByText(/Adjusted deadline/)).toBeTruthy();
  expect(screen.getByText('Submitted')).toBeTruthy();
});

it('filters to a child and restores the combined family agenda', () => {
  render(<FamilyWeeklyAgenda digest={digest} manager={false} />);
  fireEvent.mouseDown(screen.getByRole('combobox'));
  fireEvent.click(within(screen.getByRole('listbox')).getByText('Sam Two'));
  expect(screen.queryByText('Alex One · Science')).toBeNull();
  expect(screen.getByText('Sam Two · Science')).toBeTruthy();
  fireEvent.mouseDown(screen.getByRole('combobox'));
  fireEvent.click(within(screen.getByRole('listbox')).getByText('All children'));
  expect(screen.getByText('Alex One · Science')).toBeTruthy();
});

it('qualifies empty windows and displays truncation accurately', () => {
  const { rerender } = render(<FamilyWeeklyAgenda digest={{ ...digest, assignments: [], assignments_total: 0 }} manager={false} />);
  expect(screen.getByText(/No published assignments with a due date/)).toBeTruthy();
  rerender(<FamilyWeeklyAgenda digest={{ ...digest, assignments_total: 105, truncated: true }} manager={false} />);
  expect(screen.getByText(/Showing the first 2 of 105 assignment items/)).toBeTruthy();
});

it('supports staff class summaries without inventing child identities or status', () => {
  render(<FamilyWeeklyAgenda digest={{ ...digest, assignments: [{ id: 'class', name: 'Class work', due_date: '2026-10-01' }] }} manager />);
  expect(screen.getByText('Class work · Due 2026-10-01')).toBeTruthy();
  expect(screen.queryByLabelText('Homework for child')).toBeNull();
  expect(screen.queryByText('Not submitted')).toBeNull();
});
