import { useMemo } from 'react';

function readStoredUser() {
  if (typeof window === 'undefined') {
    return null;
  }

  const sources = [
    window.localStorage.getItem('crown_user'),
    window.sessionStorage.getItem('crown_user'),
    window.localStorage.getItem('crown_current_user'),
    window.sessionStorage.getItem('crown_current_user'),
  ];

  for (const raw of sources) {
    if (!raw) {
      continue;
    }

    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  return null;
}

export function useCurrentUserRole() {
  return useMemo(() => {
    try {
      const parsed = readStoredUser();

      if (!parsed) {
        // Fallback: read the simpler role key used by demo/test session seeding.
        const simpleRole =
          sessionStorage.getItem('crown.role') ||
          localStorage.getItem('crown.role') ||
          localStorage.getItem('crown.demo.role');
        if (simpleRole) return simpleRole.trim().toLowerCase();
        return 'guest';
      }

      if (typeof parsed?.role === 'string' && parsed.role.trim()) {
        return parsed.role.trim().toLowerCase();
      }

      if (Array.isArray(parsed?.roles) && parsed.roles.length > 0) {
        return String(parsed.roles[0]).trim().toLowerCase();
      }

      return 'guest';
    } catch {
      return 'guest';
    }
  }, []);
}
