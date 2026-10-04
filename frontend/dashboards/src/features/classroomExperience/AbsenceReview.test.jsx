import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import AbsenceReview from './AbsenceReview';
afterEach(cleanup);
const row = { id: 'explanation', student_id: 'child', title: 'Family explanation', body: 'Family evidence',
  version: 3, metadata: { absence_date: '2026-10-03' } };
const props = { rows: [row], total: 1, roster: [{ id: 'child', name: 'Student One', identity_verified: true, attendance: 'ABSENT' }],
  date: '2026-10-03', version: 4, busy: false };

it('requires a reason and submits both versions through the existing operation', () => {
  const save = vi.fn(); render(<AbsenceReview {...props} save={save} />);
  expect(screen.getByText('Excuse recorded absence').disabled).toBe(true);
  fireEvent.change(screen.getByLabelText(/Review reason shared with family/), { target: { value: 'School policy reviewed' } });
  fireEvent.click(screen.getByText('Excuse recorded absence'));
  expect(save).toHaveBeenCalledWith({ operation: 'review_absence', explanation_id: 'explanation',
    explanation_version: 3, version: 4, decision: 'excuse', reason: 'School policy reviewed', confirm_undated_date: false });
});

it('requires explicit confirmation of the selected date for an undated explanation', () => {
  const save = vi.fn(); render(<AbsenceReview {...props} rows={[{ ...row, metadata: {} }]} save={save} />);
  fireEvent.change(screen.getByLabelText(/Review reason shared with family/), { target: { value: 'Verified with family' } });
  expect(screen.getByText('Decline explanation; retain attendance').disabled).toBe(true);
  fireEvent.click(screen.getByLabelText('I verified that this explanation applies to 2026-10-03'));
  fireEvent.click(screen.getByText('Decline explanation; retain attendance'));
  expect(save.mock.calls[0][0]).toMatchObject({ decision: 'decline', confirm_undated_date: true });
});

it('does not allow review of present students or unverified identities', () => {
  const { rerender } = render(<AbsenceReview {...props} roster={[{ ...props.roster[0], attendance: 'PRESENT' }]} save={vi.fn()} />);
  fireEvent.change(screen.getByLabelText(/Review reason shared with family/), { target: { value: 'Reason' } });
  expect(screen.getByText('Excuse recorded absence').disabled).toBe(true);
  rerender(<AbsenceReview {...props} roster={[{ ...props.roster[0], identity_verified: false }]} save={vi.fn()} />);
  expect(screen.getByText('Verified student identity is required.')).toBeTruthy();
  expect(screen.getByText('Excuse recorded absence').disabled).toBe(true);
});

it('shows truthful queue limits and empty states', () => {
  const { rerender } = render(<AbsenceReview {...props} total={105} save={vi.fn()} />);
  expect(screen.getByText(/Showing 1 of 105/)).toBeTruthy();
  rerender(<AbsenceReview {...props} rows={[]} total={0} save={vi.fn()} />);
  expect(screen.getByText('No pending explanations for this roster date.')).toBeTruthy();
});
