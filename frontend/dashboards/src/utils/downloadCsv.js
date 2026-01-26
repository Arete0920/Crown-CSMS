import { getAccessToken, getSelectedSchoolId } from "./authClient.js";

export async function downloadCsv(url, { filename = 'export.csv' } = {}) {
  const token = getAccessToken();
  const schoolId = getSelectedSchoolId();
  const headers = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  if (schoolId) {
    headers["X-Crown-School-Id"] = schoolId;
  }

  const resp = await fetch(url, {
    credentials: 'include',
    headers,
  });

  const blob = await resp.blob();
  const contentType = resp.headers.get('content-type') || '';

  // If backend returns error.csv for 403, we still download it (UI toast comes later).
  const effectiveName =
    resp.status === 403 && contentType.includes('text/csv') ? 'error.csv' : filename;

  const href = URL.createObjectURL(blob);
  try {
    const a = document.createElement('a');
    a.href = href;
    a.download = effectiveName;
    document.body.appendChild(a);
    a.click();
    a.remove();
  } finally {
    URL.revokeObjectURL(href);
  }

  return { ok: resp.ok, status: resp.status };
}
