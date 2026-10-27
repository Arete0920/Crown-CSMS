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
    headers: { 'Content-Type': 'application/json', 'X-School-Id': schoolId },
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

export async function createSurveyDraft(schoolId, draft) {
  const result = definition(await request(schoolId, ROOT, {
    method: 'POST', body: JSON.stringify({
      name: draft.name, purpose: draft.purpose,
      questions: draft.questions.map(({ key, prompt, question_type, choices, required }) => ({
        key, prompt, question_type, choices, required,
      })),
    }),
  }));
  if (result.status !== 'draft') throw new Error('Draft creation could not be confirmed.');
  return result;
}
