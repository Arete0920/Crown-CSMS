import { authenticatedJson, getSelectedSchoolId } from '../utils/authClient.js';

const ROOT = '/api/v1/survey-intelligence/surveys/';

function assertSchool(schoolId) {
  if (!schoolId || getSelectedSchoolId() !== schoolId) {
    throw new Error('School changed. Reload this page before continuing.');
  }
}

async function request(schoolId, path, init = {}) {
  assertSchool(schoolId);
  const result = await authenticatedJson(path, {
    ...init,
    headers: { ...(init.headers || {}), 'Content-Type': 'application/json', 'X-School-Id': schoolId },
  });
  assertSchool(schoolId);
  return result;
}

function definition(value) {
  if (!value || typeof value.id !== 'string' || typeof value.name !== 'string'
      || !Array.isArray(value.questions)) throw new Error('Survey data is unavailable.');
  return value;
}

export async function listSurveyDrafts(schoolId) {
  const result = await request(schoolId, ROOT);
  if (!Array.isArray(result?.results)) throw new Error('Survey data is unavailable.');
  return { results: result.results.map(definition), can_create: result.can_create === true };
}

export async function readSurveyDraft(schoolId, id) {
  const result = definition(await request(schoolId, `${ROOT}${encodeURIComponent(id)}/`));
  if (result.id !== id) throw new Error('Survey data is unavailable.');
  return result;
}

function draftPayload(draft) {
  return {
    name: draft.name, purpose: draft.purpose,
    questions: draft.questions.map(({ key, prompt, question_type, choices, required }) => ({
      key, prompt, question_type, choices, required,
    })),
  };
}

export async function createSurveyDraft(schoolId, draft) {
  const result = definition(await request(schoolId, ROOT, {
    method: 'POST', body: JSON.stringify(draftPayload(draft)),
  }));
  if (result.status !== 'draft') throw new Error('Draft creation could not be confirmed.');
  return result;
}

/** The backend requires its opaque strong ETag, not a locally calculated version. */
export async function replaceSurveyDraft(schoolId, id, revision, draft) {
  if (typeof id !== 'string' || !id || typeof revision !== 'string'
      || !/^[0-9a-f]{64}$/.test(revision)) {
    throw new Error('Reload the current saved draft before editing.');
  }
  const result = definition(await request(schoolId, `${ROOT}${encodeURIComponent(id)}/`, {
    method: 'PUT',
    headers: { 'If-Match': `"${revision}"` },
    body: JSON.stringify(draftPayload(draft)),
  }));
  if (result.id !== id || result.status !== 'draft'
      || typeof result.revision !== 'string' || !/^[0-9a-f]{64}$/.test(result.revision)
      || result.revision === revision) {
    throw new Error('The saved revision could not be confirmed. Reload before another write.');
  }
  return result;
}
