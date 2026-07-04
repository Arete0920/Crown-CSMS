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

function readStorageValue(storageName, key) {
  if (typeof window === 'undefined') return '';

  try {
    const storage = window[storageName];
    if (!storage) return '';
    return storage.getItem(key) || '';
  } catch {
    return '';
  }
}

function readJsonCandidate(raw) {
  if (!raw) return null;

  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

function readStoredJson(key) {
  return (
    readJsonCandidate(readStorageValue('sessionStorage', key)) ||
    readJsonCandidate(readStorageValue('localStorage', key)) ||
    null
  );
}

function firstNonEmpty(...values) {
  return values.find((value) => value !== undefined && value !== null && String(value).trim() !== '') || '';
}

function getTenantId() {
  if (typeof window === 'undefined') return '';

  if (window.__CROWN_SCHOOL_ID__) {
    return String(window.__CROWN_SCHOOL_ID__);
  }

  const currentUser = readStoredJson('crown_current_user');

  return String(firstNonEmpty(
    readStorageValue('sessionStorage', 'crown.school.id'),
    readStorageValue('sessionStorage', 'crown_school_id'),
    readStorageValue('sessionStorage', 'schoolId'),
    readStorageValue('sessionStorage', 'school_id'),
    readStorageValue('localStorage', 'crown.school.id'),
    readStorageValue('localStorage', 'crown_school_id'),
    readStorageValue('localStorage', 'schoolId'),
    readStorageValue('localStorage', 'school_id'),
    currentUser && currentUser.school_id,
    currentUser && currentUser.schoolId,
  ));
}

function getAuthToken() {
  if (typeof window === 'undefined') return '';

  if (window.__CROWN_AUTH_TOKEN__) {
    return String(window.__CROWN_AUTH_TOKEN__);
  }

  const currentUser = readStoredJson('crown_current_user');

  return String(firstNonEmpty(
    readStorageValue('sessionStorage', 'crown.jwt.access'),
    readStorageValue('sessionStorage', 'crown_auth_token'),
    readStorageValue('sessionStorage', 'access_token'),
    readStorageValue('localStorage', 'crown.jwt.access'),
    readStorageValue('localStorage', 'crown_auth_token'),
    readStorageValue('localStorage', 'access_token'),
    currentUser && currentUser.token,
    currentUser && currentUser.access,
    currentUser && currentUser.access_token,
  ));
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
    const response = await globalThis.fetch(buildUrl(path, query), {
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
