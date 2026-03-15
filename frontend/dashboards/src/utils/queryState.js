export function readQueryObject(searchParams) {
  const result = {};

  for (const [key, value] of searchParams.entries()) {
    result[key] = value;
  }

  return result;
}

export function writeQueryObject(searchParams, updates) {
  const next = new URLSearchParams(searchParams);

  Object.entries(updates).forEach(([key, value]) => {
    if (value == null || value === '') {
      next.delete(key);
      return;
    }

    next.set(key, String(value));
  });

  return next;
}
