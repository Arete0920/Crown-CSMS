export function unwrapApiResponse(response) {
  const data = response?.data;

  if (data == null) return null;

  if (Array.isArray(data)) return data;

  if (Array.isArray(data?.results)) return data.results;

  if (data?.data !== undefined) return data.data;

  return data;
}

export function unwrapApiList(response) {
  const data = unwrapApiResponse(response);

  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;

  return [];
}
