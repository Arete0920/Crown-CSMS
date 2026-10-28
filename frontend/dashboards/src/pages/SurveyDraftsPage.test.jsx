import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import SurveyDraftsPage from './SurveyDraftsPage.jsx';
import { createSurveyDraft, listSurveyDrafts, readSurveyDraft, replaceSurveyDraft } from '../api/surveyDrafts.js';

vi.mock('../components/crown/CrownLayout.jsx', () => ({ default: ({ children }) => <main>{children}</main> }));
vi.mock('../api/surveyDrafts.js', () => ({ listSurveyDrafts: vi.fn(), readSurveyDraft: vi.fn(), createSurveyDraft: vi.fn(), replaceSurveyDraft: vi.fn() }));

const revision = 'a'.repeat(64);
const newerRevision = 'b'.repeat(64);
const saved = { id: 'saved-1', name: 'School pulse', purpose: 'parent_pulse', status: 'draft', revision, questions: [{ key: 'question_1', prompt: 'How clear are updates?', question_type: 'choice', choices: ['Clear', 'Unclear'], required: true }] };

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

async function beginSavedEdit(definition = saved, can_create = true) {
  listSurveyDrafts.mockResolvedValue({ results: [definition], can_create });
  readSurveyDraft.mockResolvedValue(definition);
  const view = render(<SurveyDraftsPage />);
  fireEvent.click(await screen.findByRole('button', { name: `${definition.name} · ${definition.status}` }));
  await screen.findByRole('region', { name: 'Saved survey preview' });
  if (can_create && definition.status === 'draft') {
    fireEvent.click(screen.getByRole('button', { name: 'Edit saved draft' }));
  }
  return view;
}

it('loads a current saved questionnaire into the same administrator editing flow', async () => {
  await beginSavedEdit();
  expect(screen.getByRole('form', { name: 'Edit saved survey draft' })).toBeTruthy();
  expect(screen.queryByRole('form', { name: 'Create survey draft' })).toBeNull();
  expect(screen.getByLabelText('Survey name').value).toBe('School pulse');
  expect(screen.getByLabelText('Question text').value).toBe('How clear are updates?');
  expect(screen.getByLabelText('Answer type').value).toBe('choice');
  expect(screen.getByLabelText('Required question').checked).toBe(true);
  expect(screen.getByLabelText(/Choices \(one per line/).value).toBe('Clear\nUnclear');
  expect(replaceSurveyDraft).not.toHaveBeenCalled();
});

it('updates retained question keys, adds a fresh key, and refreshes the saved preview after success', async () => {
  const updated = {
    ...saved, name: 'Edited pulse', revision: newerRevision,
    questions: [
      { ...saved.questions[0], prompt: 'Updated clarity?' },
      { key: 'question_2', prompt: 'Would you return?', question_type: 'boolean', choices: [], required: false },
    ],
  };
  replaceSurveyDraft.mockResolvedValue(updated);
  await beginSavedEdit();
  fireEvent.change(screen.getByLabelText('Survey name'), { target: { value: 'Edited pulse' } });
  fireEvent.change(screen.getByLabelText('Question text'), { target: { value: 'Updated clarity?' } });
  fireEvent.click(screen.getByRole('button', { name: 'Add question' }));
  const questionText = screen.getAllByLabelText('Question text');
  fireEvent.change(questionText[1], { target: { value: 'Would you return?' } });
  const answerType = screen.getAllByLabelText('Answer type');
  fireEvent.change(answerType[1], { target: { value: 'boolean' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save changes' }));
  await screen.findByText('Saved changes to this draft. It is not published and cannot collect responses.');
  expect(replaceSurveyDraft).toHaveBeenCalledExactlyOnceWith('school-a', 'saved-1', revision, {
    name: 'Edited pulse', purpose: 'parent_pulse',
    questions: [
      { key: 'question_1', prompt: 'Updated clarity?', question_type: 'choice', choices: ['Clear', 'Unclear'], required: true },
      { key: 'question_2', prompt: 'Would you return?', question_type: 'boolean', choices: [], required: false },
    ],
  });
  const preview = screen.getByRole('region', { name: 'Saved survey preview' });
  expect(within(preview).getByText('Updated clarity? (required)')).toBeTruthy();
  expect(within(preview).getByText('Would you return?')).toBeTruthy();
  expect(screen.getByRole('form', { name: 'Create survey draft' })).toBeTruthy();
});

it('rejects duplicate options locally without changing the saved definition', async () => {
  await beginSavedEdit();
  fireEvent.change(screen.getByLabelText(/Choices \(one per line/), { target: { value: 'Same\nsame' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save changes' }));
  expect((await screen.findByRole('alert')).textContent).toContain('distinct options');
  expect(replaceSurveyDraft).not.toHaveBeenCalled();
  expect(screen.getByLabelText(/Choices \(one per line/).value).toBe('Same\nsame');
});

it('preserves edits on server validation errors and allows corrected retry', async () => {
  replaceSurveyDraft.mockRejectedValueOnce({ status: 400 }).mockResolvedValueOnce({ ...saved, revision: newerRevision });
  await beginSavedEdit();
  fireEvent.change(screen.getByLabelText('Survey name'), { target: { value: 'Edited pulse' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save changes' }));
  expect((await screen.findByRole('alert')).textContent).toContain('changes were rejected');
  expect(screen.getByLabelText('Survey name').value).toBe('Edited pulse');
  fireEvent.click(screen.getByRole('button', { name: 'Save changes' }));
  await screen.findByText('Saved changes to this draft. It is not published and cannot collect responses.');
  expect(replaceSurveyDraft).toHaveBeenCalledTimes(2);
});

it('handles a stale revision without automatic overwrite or blind retry', async () => {
  const server = { ...saved, name: 'Other editor version', revision: newerRevision };
  replaceSurveyDraft.mockRejectedValueOnce({ status: 412 });
  await beginSavedEdit();
  fireEvent.change(screen.getByLabelText('Survey name'), { target: { value: 'My unsaved changes' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save changes' }));
  expect((await screen.findByRole('alert')).textContent).toContain('stale revision');
  expect(screen.getByLabelText('Survey name').value).toBe('My unsaved changes');
  expect(screen.getByRole('button', { name: 'Save changes' }).disabled).toBe(true);
  expect(replaceSurveyDraft).toHaveBeenCalledTimes(1);
  readSurveyDraft.mockResolvedValueOnce(server);
  fireEvent.click(screen.getByRole('button', { name: 'Check latest saved version' }));
  const serverPreview = await screen.findByRole('region', { name: 'Current saved survey (server)' });
  expect(within(serverPreview).getByText('Other editor version')).toBeTruthy();
  expect(screen.getByLabelText('Survey name').value).toBe('My unsaved changes');
  fireEvent.click(screen.getByRole('button', { name: 'Discard my edits and use latest saved version' }));
  expect(screen.getByLabelText('Survey name').value).toBe('Other editor version');
  replaceSurveyDraft.mockResolvedValueOnce({ ...server, revision: 'c'.repeat(64) });
  fireEvent.click(screen.getByRole('button', { name: 'Save changes' }));
  await screen.findByText('Saved changes to this draft. It is not published and cannot collect responses.');
  expect(replaceSurveyDraft.mock.calls[1][2]).toBe(newerRevision);
});

it('blocks edits on 409 publication or response conflict, without losing local input', async () => {
  replaceSurveyDraft.mockRejectedValueOnce({ status: 409 });
  await beginSavedEdit();
  fireEvent.change(screen.getByLabelText('Survey name'), { target: { value: 'Do not publish me' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save changes' }));
  expect((await screen.findByRole('alert')).textContent).toContain('no longer eligible');
  expect(screen.getByLabelText('Survey name').value).toBe('Do not publish me');
  expect(screen.getByRole('button', { name: 'Save changes' }).disabled).toBe(true);
  fireEvent.click(screen.getByRole('button', { name: 'Save changes' }));
  expect(replaceSurveyDraft).toHaveBeenCalledTimes(1);
});

it('requires readback after an indeterminate save and does not silently retry', async () => {
  replaceSurveyDraft.mockRejectedValueOnce(new Error('timeout'));
  await beginSavedEdit();
  fireEvent.change(screen.getByLabelText('Survey name'), { target: { value: 'Draft during timeout' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save changes' }));
  expect((await screen.findByRole('alert')).textContent).toContain('save result is unknown');
  expect(screen.getByLabelText('Survey name').value).toBe('Draft during timeout');
  expect(screen.getByRole('button', { name: 'Save changes' }).disabled).toBe(true);
  readSurveyDraft.mockResolvedValueOnce({ ...saved, name: 'Latest from server', revision: newerRevision });
  fireEvent.click(screen.getByRole('button', { name: 'Check latest saved version' }));
  await screen.findByRole('region', { name: 'Current saved survey (server)' });
  expect(replaceSurveyDraft).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole('button', { name: 'Cancel editing' }));
  expect(screen.queryByRole('form', { name: 'Edit saved survey draft' })).toBeNull();
});

it('keeps published or read-only saved definitions out of the edit flow', async () => {
  const published = { ...saved, status: 'active' };
  await beginSavedEdit(published);
  expect(screen.getByRole('button', { name: 'Edit saved draft' }).disabled).toBe(true);
  expect(screen.queryByRole('form', { name: 'Edit saved survey draft' })).toBeNull();
  cleanup();
  await beginSavedEdit(saved, false);
  expect(screen.queryByRole('button', { name: 'Edit saved draft' })).toBeNull();
  expect(replaceSurveyDraft).not.toHaveBeenCalled();
});

it('clears saved editing state when school selection changes', async () => {
  const view = await beginSavedEdit();
  fireEvent.change(screen.getByLabelText('Survey name'), { target: { value: 'Old school notes' } });
  sessionStorage.setItem('crown.school.id', 'school-b');
  listSurveyDrafts.mockResolvedValue({ results: [], can_create: true });
  view.rerender(<SurveyDraftsPage />);
  await waitFor(() => expect(listSurveyDrafts).toHaveBeenLastCalledWith('school-b'));
  expect(screen.queryByRole('form', { name: 'Edit saved survey draft' })).toBeNull();
  expect(screen.getByLabelText('Survey name').value).toBe('');
  expect(replaceSurveyDraft).not.toHaveBeenCalled();
});

it('prevents concurrent saved-draft writes from double submission', async () => {
  let resolve;
  replaceSurveyDraft.mockReturnValue(new Promise((done) => { resolve = done; }));
  await beginSavedEdit();
  const form = screen.getByRole('form', { name: 'Edit saved survey draft' });
  fireEvent.submit(form); fireEvent.submit(form);
  expect(replaceSurveyDraft).toHaveBeenCalledTimes(1);
  await act(async () => resolve({ ...saved, revision: newerRevision }));
});
