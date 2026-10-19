// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fetchAdmissionsInquiries } from '../api/admissionsInquiries.js';

const transport = vi.hoisted(() => ({ authenticatedFetch: vi.fn() }));
vi.mock('../utils/authClient', async (importOriginal) => ({
  ...(await importOriginal()),
  authenticatedFetch: transport.authenticatedFetch,
}));

beforeEach(() => {
  transport.authenticatedFetch.mockReset();
  localStorage.clear();
  sessionStorage.clear();
});

describe('staff inquiry list transport', () => {
  it.each([
    ['populated', false],
    ['populated', true],
    ['empty', false],
    ['empty', true],
  ])('preserves the %s envelope with notifications_enabled=%s', async (queue, enabled) => {
    const results = queue === 'empty' ? [] : [{
      id: 'inquiry-1',
      parent_name: 'Jordan Reed',
      stage: 'inquiry',
      notification_status: { enabled, notifications: [] },
    }];
    const envelope = {
      results,
      count: queue === 'empty' ? 0 : 3,
      owners: [{ id: 'counselor-1', name: 'Pat Counselor' }],
      can_edit: queue === 'populated',
      notifications_enabled: enabled,
    };
    transport.authenticatedFetch.mockResolvedValueOnce(new Response(JSON.stringify(envelope), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }));

    const response = await fetchAdmissionsInquiries({ stage: 'all', unassigned: 1, overdue: false });

    expect(response).toEqual(envelope);
    expect(transport.authenticatedFetch).toHaveBeenCalledTimes(1);
    const [requestUrl, options] = transport.authenticatedFetch.mock.calls[0];
    const url = new URL(requestUrl, 'http://localhost');
    expect(url.pathname).toBe('/api/v1/crm/inquiries/');
    expect(Object.fromEntries(url.searchParams)).toEqual({ stage: 'all', unassigned: '1' });
    expect(options).toMatchObject({ method: 'GET', credentials: 'include' });
    expect(options.body).toBeUndefined();
  });

  it('retains normalized permission errors from the authenticated transport', async () => {
    transport.authenticatedFetch.mockRejectedValueOnce(Object.assign(new Error('HTTP 403 Forbidden'), {
      status: 403,
      response: {
        status: 403,
        statusText: 'Forbidden',
        data: { detail: 'Permission denied.' },
        headers: { 'x-request-id': 'synthetic-request-id' },
      },
    }));

    await expect(fetchAdmissionsInquiries()).rejects.toMatchObject({
      status: 403,
      message: 'Permission denied.',
      details: { detail: 'Permission denied.' },
      requestId: 'synthetic-request-id',
      isNetworkError: false,
    });
    expect(transport.authenticatedFetch).toHaveBeenCalledTimes(1);
  });
});
