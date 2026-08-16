import { authenticatedFetch } from "../utils/authClient.js";

const rawBase = import.meta.env.VITE_API_BASE_URL || "";
const API_BASE = rawBase.endsWith("/") ? rawBase.slice(0, -1) : rawBase;

export async function issueOfficialTranscript(studentId) {
  if (!studentId) throw new Error("studentId is required");
  const response = await authenticatedFetch(
    `${API_BASE}/api/v1/academics/students/${encodeURIComponent(studentId)}/transcript/issuances/`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    },
  );
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Official transcript issuance failed (${response.status}): ${text}`);
  }
  return response.json();
}

export async function downloadOfficialTranscriptPdf(issuanceId) {
  if (!issuanceId) throw new Error("issuanceId is required");
  const response = await authenticatedFetch(
    `${API_BASE}/api/v1/academics/transcript-issuances/${encodeURIComponent(issuanceId)}/pdf/`,
  );
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Official transcript download failed (${response.status}): ${text}`);
  }
  return response.blob();
}
