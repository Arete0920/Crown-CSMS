import { describe, expect, it } from 'vitest';
import { normalizeApiError } from '../utils/normalizeApiError';

describe('normalizeApiError', () => {
  it('normalizes DRF detail message', () => {
    const result = normalizeApiError({
      response: {
        status: 400,
        data: { detail: 'Bad request.' },
      },
    });

    expect(result.message).toBe('Bad request.');
    expect(result.status).toBe(400);
  });

  it('normalizes field errors', () => {
    const result = normalizeApiError({
      response: {
        status: 400,
        data: { first_name: ['This field is required.'] },
      },
    });

    expect(result.fieldErrors.first_name).toBe('This field is required.');
  });
});
