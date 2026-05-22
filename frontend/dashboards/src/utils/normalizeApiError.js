function readRequestIds(response, data) {
  const headers = response?.headers || {};
  return {
    correlationId:
      headers['x-correlation-id'] ||
      headers['X-Correlation-Id'] ||
      data?.correlation_id ||
      null,
    requestId:
      headers['x-request-id'] ||
      headers['X-Request-Id'] ||
      null,
  };
}

function isNetworkFailure(error, response) {
  return error?.code === 'ERR_NETWORK' || (!response && !error?.status && !error?.body);
}

function resolveMessage(error, data, fallbackMessage) {
  if (typeof data === 'string' && data.trim()) {
    return data.trim();
  }

  if (typeof data?.detail === 'string' && data.detail.trim()) {
    return data.detail.trim();
  }

  if (typeof data?.message === 'string' && data.message.trim()) {
    return data.message.trim();
  }

  if (Array.isArray(data?.non_field_errors) && data.non_field_errors.length > 0) {
    return data.non_field_errors.join(', ');
  }

  if (typeof error?.message === 'string' && /^HTTP\s\d+/i.test(error.message)) {
    return error.message;
  }

  return fallbackMessage;
}

function buildFieldErrors(data) {
  if (!data || typeof data !== 'object') {
    return {};
  }

  const fieldErrors = {};
  for (const [key, value] of Object.entries(data)) {
    if (['detail', 'message', 'non_field_errors', 'correlation_id'].includes(key)) continue;
    fieldErrors[key] = Array.isArray(value) ? value.join(', ') : String(value);
  }
  return fieldErrors;
}

export function normalizeApiError(error) {
  const response = error?.response;
  const data = response?.data;
  const ids = readRequestIds(response, data);

  const normalized = {
    message: 'Something went wrong.',
    status: response?.status ?? error?.status ?? null,
    details: data ?? error?.body ?? null,
    fieldErrors: {},
    isNetworkError: false,
    correlationId: ids.correlationId,
    requestId: ids.requestId,
  };

  if (isNetworkFailure(error, response)) {
    normalized.message = 'Network error. Check API connectivity and try again.';
    normalized.isNetworkError = true;
    return normalized;
  }

  normalized.message = resolveMessage(error, data, normalized.message);
  normalized.fieldErrors = buildFieldErrors(data);
  return normalized;
}
