export async function fetchCurriculumPacingSummary({ baseUrl, token, schoolId }) {
  const res = await fetch(`${baseUrl}/api/curriculum/courses/pacing-summary/`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      "X-School-Id": schoolId,
    },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Curriculum pacing fetch failed: ${res.status} ${text}`);
  }
  return await res.json();
}
