import { authenticatedFetch, buildApiUrl } from '../utils/authClient';
import { normalizeApiError } from '../utils/normalizeApiError';

function headersToObject(headers) {
  const values = {};
  headers?.forEach?.((value, key) => {
    values[key] = value;
  });
  return values;
}

async function parseBody(response) {
  const contentType = response.headers?.get?.('content-type') || '';
  if (contentType.includes('application/json')) {
    return response.json().catch(() => null);
  }
  const text = await response.text().catch(() => '');
  return text || null;
}

function buildRequestBody(data, headers) {
  if (data == null) return undefined;
  if (
    typeof data === 'string'
    || data instanceof FormData
    || data instanceof URLSearchParams
    || data instanceof Blob
    || data instanceof ArrayBuffer
  ) {
    return data;
  }
  if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  return JSON.stringify(data);
}

async function request(config = {}) {
  const {
    url,
    method = 'GET',
    data,
    params,
    headers: inputHeaders,
    timeout,
    signal,
    validateStatus,
    withCredentials = true,
  } = config;

  const headers = new Headers(inputHeaders || {});
  const resolvedUrl = buildApiUrl(url, params);

  try {
    const response = await authenticatedFetch(resolvedUrl, {
      method,
      headers,
      body: buildRequestBody(data, headers),
      timeoutMs: timeout,
      signal,
      credentials: withCredentials ? 'include' : 'same-origin',
      validateStatus: validateStatus || ((status) => status >= 200 && status < 300),
    });
    const responseData = await parseBody(response);
    return {
      data: responseData,
      status: response.status,
      statusText: response.statusText,
      headers: headersToObject(response.headers),
      config: { ...config, url: resolvedUrl },
      request: null,
    };
  } catch (error) {
    const normalized = normalizeApiError(error);
    normalized.config = { ...config, url: resolvedUrl };
    normalized.response = error?.response;
    throw normalized;
  }
}

export const crownApiClient = {
  request,
  get(url, config = {}) {
    return request({ ...config, method: 'GET', url });
  },
  delete(url, config = {}) {
    return request({ ...config, method: 'DELETE', url });
  },
  post(url, data = {}, config = {}) {
    return request({ ...config, method: 'POST', url, data });
  },
  put(url, data = {}, config = {}) {
    return request({ ...config, method: 'PUT', url, data });
  },
  patch(url, data = {}, config = {}) {
    return request({ ...config, method: 'PATCH', url, data });
  },
};
