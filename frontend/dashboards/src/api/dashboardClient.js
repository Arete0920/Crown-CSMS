const DEFAULT_TIMEOUT_MS = 15000;

function trimTrailingSlash(value) {
  return String(value || '').replace(/\/+$/, '');
}

function getApiBaseUrl() {
  const envBaseUrl =
    typeof import.meta !== 'undefined' &&
    import.meta.env &&
    import.meta.env.VITE_API_BASE_URL
      ? import.meta.env.VITE_API_BASE_URL
      : '';

  return trimTrailingSlash(envBaseUrl);
}

function readLocalJson(key) {
  if (typeof window === 'undefined') return null;

  const raw = window.localStorage.getItem(key);
  if (!raw) return null;

  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

function getTenantId() {
  if (typeof window === 'undefined') return '';

  if (window.__CROWN_SCHOOL_ID__) {
    return String(window.__CROWN_SCHOOL_ID__);
  }

  const direct = window.localStorage.getItem('crown_school_id');
  if (direct) {
    return String(direct);
  }

  const currentUser = readLocalJson('crown_current_user');
  if (currentUser && currentUser.school_id) {
    return String(currentUser.school_id);
  }

  return '';
}

function getAuthToken() {
  if (typeof window === 'undefined') return '';

  if (window.__CROWN_AUTH_TOKEN__) {
    return String(window.__CROWN_AUTH_TOKEN__);
  }

  const direct = window.localStorage.getItem('crown_auth_token');
  if (direct) {
    return String(direct);
  }

  const currentUser = readLocalJson('crown_current_user');
  if (currentUser && currentUser.token) {
    return String(currentUser.token);
  }

  return '';
}

function buildUrl(path, query = {}) {
  const baseUrl = getApiBaseUrl();
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const url = new URL(`${baseUrl}${normalizedPath}`, window.location.origin);

  Object.entries(query || {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return;
    }

    url.searchParams.set(key, String(value));
  });

  return url.toString();
}

async function parseResponse(response) {
  const contentType = response.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');

  const payload = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const error = new Error(
      `Dashboard request failed with status ${response.status}.`
    );
    error.status = response.status;
    error.payload = payload;
    throw error;
  }

  return payload;
}

export async function dashboardFetch(path, options = {}) {
  const {
    method = 'GET',
    query,
    body,
    headers = {},
    timeoutMs = DEFAULT_TIMEOUT_MS,
    signal,
  } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  if (signal) {
    signal.addEventListener('abort', () => controller.abort(), { once: true });
  }

  const tenantId = getTenantId();
  const authToken = getAuthToken();

  const mergedHeaders = {
    Accept: 'application/json',
    ...headers,
  };

  if (body !== undefined && body !== null) {
    mergedHeaders['Content-Type'] = 'application/json';
  }

  if (tenantId) {
    mergedHeaders['X-School-Id'] = tenantId;
  }

  if (authToken) {
    mergedHeaders.Authorization = `Bearer ${authToken}`;
  }

  try {
    const response = await fetch(buildUrl(path, query), {
      method,
      headers: mergedHeaders,
      body: body !== undefined && body !== null ? JSON.stringify(body) : undefined,
      signal: controller.signal,
      credentials: 'include',
    });

    return await parseResponse(response);
  } finally {
    clearTimeout(timeoutId);
  }
}
