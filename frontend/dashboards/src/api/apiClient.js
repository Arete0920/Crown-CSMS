import { crownApiClient } from './client';
import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from './request';

export function useApiClient() {
  async function request(path, opts = {}) {
    const method = String(opts.method || 'GET').toUpperCase();

    if (method === 'GET') {
      return apiGet(path, opts);
    }

    if (method === 'POST') {
      return apiPost(path, opts.body, opts);
    }

    if (method === 'PATCH') {
      return apiPatch(path, opts.body, opts);
    }

    if (method === 'PUT') {
      return apiPut(path, opts.body, opts);
    }

    if (method === 'DELETE') {
      return apiDelete(path, opts);
    }

    throw new Error(`Unsupported API method: ${method}`);
  }

  return { request };
}

export { crownApiClient };
