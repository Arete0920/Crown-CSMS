import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { HomeDashboard } from './HomeDashboard.jsx';
import { getAccessToken } from '../utils/authClient.js';

function safeParseJwt(token) {
  try {
    const payload = token.split('.')[1];
    if (!payload) return {};
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
    const pad = normalized.length % 4;
    const base64 = normalized + (pad ? '='.repeat(4 - pad) : '');
    return JSON.parse(atob(base64));
  } catch {
    return {};
  }
}

function getStoredRole() {
  const sessionRole = sessionStorage.getItem('crown.role') || '';
  const localRole = localStorage.getItem('crown.role') || '';
  const demoRole = localStorage.getItem('crown.demo.role') || '';
  return (sessionRole || localRole || demoRole).toLowerCase().trim();
}

function getJwtRole() {
  const token = getAccessToken();
  if (!token) return '';
  const payload = safeParseJwt(token);

  const candidates = [
    payload.role,
    payload.user_role,
    payload.user_type,
    payload.persona,
    Array.isArray(payload.roles) ? payload.roles.join(',') : payload.roles,
  ]
    .filter(Boolean)
    .join(',')
    .toLowerCase();

  return candidates;
}

function resolveDashboardPath() {
  const role = `${getStoredRole()},${getJwtRole()}`;
  if (role.includes('teacher')) return '/teacher';
  if (role.includes('parent')) return '/parent';
  if (role.includes('student')) return '/student';
  if (role.includes('admin') || role.includes('director')) return '/';
  return '/';
}

export default function RoleHomeRedirect() {
  const navigate = useNavigate();
  const token = getAccessToken();

  useEffect(() => {
    if (!token) return;
    const target = resolveDashboardPath();
    if (target !== '/') {
      navigate(target, { replace: true });
    }
  }, [navigate, token]);

  return <HomeDashboard />;
}
