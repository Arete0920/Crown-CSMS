import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import SurveyDraftsPage from './SurveyDraftsPage.jsx';
import { createSurveyDraft, listSurveyDrafts, readSurveyDraft } from '../api/surveyDrafts.js';

vi.mock('../components/crown/CrownLayout.jsx', () => ({ default: ({ children }) => <main>{children}</main> }));
vi.mock('../api/surveyDrafts.js', () => ({ listSurveyDrafts: vi.fn(), readSurveyDraft: vi.fn(), createSurveyDraft: vi.fn() }));

const saved = { id: 'saved-1', name: 'School pulse', purpose: 'parent_pulse', status: 'draft', questions: [{ key: 'question_1', prompt: 'How clear are updates?', question_type: 'choice', choices: ['Clear', 'Unclear'], required: true }] };

beforeEach(() => {
  vi.resetAllMocks(); sessionStorage.clear();
  sessionStorage.setItem('crown.school.id', 'school-a');
  listSurveyDrafts.mockResolvedValue({ results: [], can_create: true });
});
afterEach(cleanup);

async function fill() {
  await screen.findByRole('form', { name: 'Create survey draft' });
  fireEvent.change(screen.getByLabelText('Survey name'), { target: { value: 'School pulse' } });
  fireEvent.change(screen.getByLabelText('Question text'), { target: { value: 'How clear are updates?' } });
}

it('shows truthful empty state and permits only server-authorized creation', async () => {
  listSurveyDrafts.mockResolvedValue({ results: [], can_create: false });
  render(<SurveyDraftsPage />);
  await screen.findByText('No saved surveys for this school.');
  expect(screen.getByText('You have read-only survey access.')).toBeTruthy();
  expect(screen.queryByRole('form')).toBeNull();
});

it('creates typed questions and previews the server-saved definition', async () => {
  createSurveyDraft.mockResolvedValue(saved);
  render(<SurveyDraftsPage />); await fill();
  fireEvent.change(screen.getByLabelText('Answer type'), { target: { value: 'choice' } });
  fireEvent.change(screen.getByLabelText(/Choices \(one per line/), { target: { value: 'Clear\nUnclear' } });
  fireEvent.click(screen.getByLabelText('Required question'));
  fireEvent.click(screen.getByRole('button', { name: 'Save draft' }));
  await screen.findByText('Draft saved. It is not published and cannot collect responses.');
  expect(createSurveyDraft).toHaveBeenCalledExactlyOnceWith('school-a', {
    name: 'School pulse', purpose: 'parent_pulse', questions: saved.questions,
  });
  expect(within(screen.getByRole('region', { name: 'Saved survey preview' })).getByText('Clear')).toBeTruthy();
  expect(screen.getByLabelText('Survey name').value).toBe('');
});

it('preserves the draft after a validation rejection', async () => {
  createSurveyDraft.mockRejectedValue({ status: 400 });
  render(<SurveyDraftsPage />); await fill();
  fireEvent.click(screen.getByRole('button', { name: 'Save draft' }));
  expect((await screen.findByRole('alert')).textContent).toContain('draft was rejected');
  expect(screen.getByLabelText('Survey name').value).toBe('School pulse');
  expect(screen.getByLabelText('Question text').value).toBe('How clear are updates?');
});

it('prevents duplicate submission while a write is pending', async () => {
  let resolve;
  createSurveyDraft.mockReturnValue(new Promise((done) => { resolve = done; }));
  render(<SurveyDraftsPage />); await fill();
  const form = screen.getByRole('form', { name: 'Create survey draft' });
  fireEvent.submit(form); fireEvent.submit(form);
  expect(createSurveyDraft).toHaveBeenCalledTimes(1);
  await act(async () => resolve(saved));
});

it('requires library reconciliation before retrying an uncertain write', async () => {
  createSurveyDraft.mockRejectedValue(new Error('network unavailable'));
  render(<SurveyDraftsPage />); await fill();
  fireEvent.click(screen.getByRole('button', { name: 'Save draft' }));
  await screen.findByRole('alert');
  expect(screen.getByRole('button', { name: 'Save draft' }).disabled).toBe(true);
  listSurveyDrafts.mockResolvedValue({ results: [saved], can_create: true });
  fireEvent.click(screen.getByRole('button', { name: 'Refresh library' }));
  await screen.findByRole('button', { name: 'School pulse · draft' });
  expect(screen.getByRole('button', { name: 'Save draft' }).disabled).toBe(false);
  expect(screen.getByLabelText('Survey name').value).toBe('School pulse');
});

it('reads a selected saved definition and never renders a failed detail as a preview', async () => {
  listSurveyDrafts.mockResolvedValue({ results: [saved], can_create: false });
  readSurveyDraft.mockRejectedValue({ status: 404 });
  render(<SurveyDraftsPage />);
  fireEvent.click(await screen.findByRole('button', { name: 'School pulse · draft' }));
  await screen.findByRole('alert');
  expect(screen.queryByRole('region', { name: 'Saved survey preview' })).toBeNull();
  expect(readSurveyDraft).toHaveBeenCalledWith('school-a', 'saved-1');
});

it('loads current saved questions instead of presenting the list snapshot as detail', async () => {
  listSurveyDrafts.mockResolvedValue({ results: [saved], can_create: false });
  readSurveyDraft.mockResolvedValue({ ...saved, questions: [{ ...saved.questions[0], prompt: 'Current saved question' }] });
  render(<SurveyDraftsPage />);
  fireEvent.click(await screen.findByRole('button', { name: 'School pulse · draft' }));
  const preview = await screen.findByRole('region', { name: 'Saved survey preview' });
  expect(within(preview).getByText('Current saved question (required)')).toBeTruthy();
  expect(within(preview).queryByText('How clear are updates? (required)')).toBeNull();
});

it('keeps question keys stable across additions and removal', async () => {
  createSurveyDraft.mockResolvedValue(saved);
  render(<SurveyDraftsPage />); await fill();
  fireEvent.click(screen.getByRole('button', { name: 'Add question' }));
  const fields = screen.getAllByLabelText('Question text');
  fireEvent.change(fields[1], { target: { value: 'Second question' } });
  fireEvent.click(screen.getByRole('button', { name: 'Remove question 1' }));
  fireEvent.click(screen.getByRole('button', { name: 'Save draft' }));
  await screen.findByText('Draft saved. It is not published and cannot collect responses.');
  expect(createSurveyDraft.mock.calls[0][1].questions).toEqual([
    { key: 'question_2', prompt: 'Second question', question_type: 'scale', choices: [], required: false },
  ]);
});

it('does not turn denied library access into an empty or editable library', async () => {
  listSurveyDrafts.mockRejectedValue({ status: 403 });
  render(<SurveyDraftsPage />);
  expect((await screen.findByRole('alert')).textContent).toContain('do not have permission');
  expect(screen.queryByText('No saved surveys for this school.')).toBeNull();
  expect(screen.queryByRole('form')).toBeNull();
  await waitFor(() => expect(screen.getByRole('button', { name: 'Refresh library' }).disabled).toBe(false));
});

it('clears unsaved school content when the selected school changes', async () => {
  const view = render(<SurveyDraftsPage />); await fill();
  sessionStorage.setItem('crown.school.id', 'school-b');
  view.rerender(<SurveyDraftsPage />);
  await waitFor(() => expect(listSurveyDrafts).toHaveBeenLastCalledWith('school-b'));
  expect(screen.getByLabelText('Survey name').value).toBe('');
  expect(screen.getByLabelText('Question text').value).toBe('');
  expect(createSurveyDraft).not.toHaveBeenCalled();
});
