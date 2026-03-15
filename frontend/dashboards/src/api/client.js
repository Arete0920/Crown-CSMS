import axios from 'axios';
import { normalizeApiError } from '../utils/normalizeApiError';

function readToken() {
  try {
    const localRaw = window.localStorage.getItem('crown_auth');
    const sessionRaw = window.sessionStorage.getItem('crown_auth');

    const localParsed = localRaw ? JSON.parse(localRaw) : null;
    const sessionParsed = sessionRaw ? JSON.parse(sessionRaw) : null;

    const fallbackToken =
      window.sessionStorage.getItem('crown.jwt.access') ||
      window.localStorage.getItem('crown.jwt.access');

    return (
      localParsed?.access_token ||
      localParsed?.token ||
      sessionParsed?.access_token ||
      sessionParsed?.token ||
      fallbackToken ||
      null
    );
  } catch {
    return null;
  }
}

function readSchoolId() {
  try {
    return (
      window.sessionStorage.getItem('crown.school.id') ||
      window.localStorage.getItem('schoolId') ||
      window.localStorage.getItem('crown.school.id') ||
      ''
    );
  } catch {
    return '';
  }
}

export const crownApiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 20000,
  withCredentials: true,
});

crownApiClient.interceptors.request.use((config) => {
  const token = readToken();
  const schoolId = readSchoolId();

  const nextConfig = {
    ...config,
    headers: {
      ...(config.headers || {}),
    },
  };

  if (token) {
    nextConfig.headers.Authorization = `Bearer ${token}`;
  }

  if (schoolId && !nextConfig.headers['X-School-Id']) {
    nextConfig.headers['X-School-Id'] = schoolId;
  }

  return nextConfig;
});

crownApiClient.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(normalizeApiError(error)),
);
