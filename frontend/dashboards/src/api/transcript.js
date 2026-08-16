import { authenticatedFetch } from "../utils/authClient.js";

const rawBase = import.meta.env.VITE_API_BASE_URL || "";
const API_BASE = rawBase.endsWith("/") ? rawBase.slice(0, -1) : rawBase;

async function errorText(response) {
  const text = await response.text();
  return text || response.statusText || "Request failed";
}

export async function issueOfficialTranscript(studentId) {
  if (!studentId) throw new Error("studentId is required");
  const response = await authenticatedFetch(
    `${API_BASE}/api/v1/academics/students/${encodeURIComponent(studentId)}/transcript/issue/`,
    { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" },
  );
  if (!response.ok) {
    throw new Error(`Official transcript issuance failed (${response.status}): ${await errorText(response)}`);
  }
  return response.json();
}

export async function downloadOfficialTranscript(issuanceId, filename = "official-transcript.pdf") {
  if (!issuanceId) throw new Error("issuanceId is required");
  const response = await authenticatedFetch(
    `${API_BASE}/api/v1/academics/transcript-issuances/${encodeURIComponent(issuanceId)}/pdf/`,
  );
  if (!response.ok) {
    throw new Error(`Official transcript download failed (${response.status}): ${await errorText(response)}`);
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
