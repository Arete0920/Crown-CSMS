import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createSurveyDraft, listSurveyDrafts, readSurveyDraft } from './surveyDrafts.js';

const draft = { id: 'saved-1', name: 'School pulse', purpose: 'parent_pulse', status: 'draft', questions: [] };
const response = (data) => new Response(JSON.stringify(data), { status: 200, headers: { 'content-type': 'application/json' } });

beforeEach(() => {
  sessionStorage.clear(); localStorage.clear();
  sessionStorage.setItem('crown.school.id', 'school-a');
  sessionStorage.setItem('crown.jwt.access', 'synthetic-access');
  vi.stubGlobal('fetch', vi.fn());
});
afterEach(() => vi.unstubAllGlobals());

describe('survey draft transport', () => {
  it('uses canonical authentication and the captured school', async () => {
    globalThis.fetch.mockResolvedValue(response({ results: [draft], can_create: true }));
    expect((await listSurveyDrafts('school-a')).can_create).toBe(true);
    const [url, init] = globalThis.fetch.mock.calls[0];
    expect(url).toContain('/api/v1/survey-intelligence/surveys/');
    expect(init.headers.get('Authorization')).toBe('Bearer synthetic-access');
    expect(init.headers.get('X-School-Id')).toBe('school-a');
  });

  it('fails closed on missing or changed school before sending', async () => {
    await expect(listSurveyDrafts('school-b')).rejects.toThrow('School changed');
    await expect(listSurveyDrafts('')).rejects.toThrow('School changed');
    expect(globalThis.fetch).not.toHaveBeenCalled();
  });

  it('discards a response if school selection changes in flight', async () => {
    let resolve;
    globalThis.fetch.mockReturnValue(new Promise((done) => { resolve = done; }));
    const pending = listSurveyDrafts('school-a');
    sessionStorage.setItem('crown.school.id', 'school-b');
    resolve(response({ results: [draft], can_create: true }));
    await expect(pending).rejects.toThrow('School changed');
  });

  it('does not infer write permission from a missing or string capability', async () => {
    globalThis.fetch.mockResolvedValue(response({ results: [], can_create: 'true' }));
    expect((await listSurveyDrafts('school-a')).can_create).toBe(false);
  });

  it('does not misrepresent malformed library data as an empty school', async () => {
    globalThis.fetch.mockResolvedValue(response({ detail: 'unavailable' }));
    await expect(listSurveyDrafts('school-a')).rejects.toThrow('unavailable');
  });

  it('requires the returned detail to match the selected definition', async () => {
    globalThis.fetch.mockResolvedValue(response(draft));
    await expect(readSurveyDraft('school-a', 'wrong-id')).rejects.toThrow('unavailable');
  });

  it('sends only draft fields and never publication or school-body controls', async () => {
    globalThis.fetch.mockResolvedValue(response(draft));
    await createSurveyDraft('school-a', {
      name: 'School pulse', purpose: 'parent_pulse', school_id: 'school-b', public_enabled: true,
      questions: [{ key: 'q1', prompt: 'Clear?', question_type: 'boolean', required: false, choices: [], private: 'omit' }],
    });
    expect(JSON.parse(globalThis.fetch.mock.calls[0][1].body)).toEqual({
      name: 'School pulse', purpose: 'parent_pulse',
      questions: [{ key: 'q1', prompt: 'Clear?', question_type: 'boolean', choices: [], required: false }],
    });
    expect(globalThis.fetch.mock.calls[0][1].method).toBe('POST');
  });
});
