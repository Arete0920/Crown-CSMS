export function normalizeApiError(error) {
  const response = error?.response;
  const data = response?.data;

  const normalized = {
    message: 'Something went wrong.',
    status: response?.status ?? error?.status ?? null,
    details: data ?? error?.body ?? null,
    fieldErrors: {},
    isNetworkError: false,
  };

  if (error?.code === 'ERR_NETWORK' || (!response && !error?.status && !error?.body)) {
    normalized.message = 'Network error. Check API connectivity and try again.';
    normalized.isNetworkError = true;
    return normalized;
  }

  if (typeof data === 'string' && data.trim()) {
    normalized.message = data.trim();
    return normalized;
  }

  if (typeof error?.message === 'string' && /^HTTP\s\d+/i.test(error.message)) {
    normalized.message = error.message;
  }

  if (typeof data?.detail === 'string' && data.detail.trim()) {
    normalized.message = data.detail.trim();
  } else if (typeof data?.message === 'string' && data.message.trim()) {
    normalized.message = data.message.trim();
  } else if (Array.isArray(data?.non_field_errors) && data.non_field_errors.length > 0) {
    normalized.message = data.non_field_errors.join(', ');
  }

  if (data && typeof data === 'object') {
    const fieldErrors = {};

    for (const [key, value] of Object.entries(data)) {
      if (['detail', 'message', 'non_field_errors'].includes(key)) continue;
      fieldErrors[key] = Array.isArray(value) ? value.join(', ') : String(value);
    }

    normalized.fieldErrors = fieldErrors;
  }

  return normalized;
}
