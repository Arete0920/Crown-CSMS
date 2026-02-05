import { getToken, getSchoolId } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * Fetch message threads list
 * @returns {Promise<Array>} - array of thread objects
 */
export const getThreads = async () => {
  const token = getToken();
  const schoolId = getSchoolId();

  if (!token || !schoolId) {
    throw new Error("Missing authentication credentials");
  }

  const url = `${API_BASE}/api/threads/`;

  const response = await fetch(url, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const body = await response.text();
    const err = new Error(`Communications API error: ${response.status}`);
    err.status = response.status;
    err.body = body;
    throw err;
  }

  const data = await response.json();
  return Array.isArray(data) ? data : [];
};

/**
 * Fetch thread detail with messages
 * @param {string} threadId - UUID of the thread
 * @returns {Promise<Object>} - thread object with messages array
 */
export const getThreadDetail = async (threadId) => {
  const token = getToken();
  const schoolId = getSchoolId();

  if (!token || !schoolId) {
    throw new Error("Missing authentication credentials");
  }

  const url = `${API_BASE}/api/threads/${threadId}/`;

  const response = await fetch(url, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const body = await response.text();
    const err = new Error(`Thread detail API error: ${response.status}`);
    err.status = response.status;
    err.body = body;
    throw err;
  }

  return await response.json();
};
