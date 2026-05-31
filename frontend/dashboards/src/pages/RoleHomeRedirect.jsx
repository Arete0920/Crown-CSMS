import { Navigate } from 'react-router-dom';

import { HomeDashboard } from './HomeDashboard.jsx';
import { getAccessToken } from '../utils/authClient.js';

function safeParseJwt(token) {
  try {
    const payload = token.split('.')[1];
    if (!payload) return {};
    const normalized = payload.replaceAll('-', '+').replaceAll('_', '/');
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

// Table-driven role routing: every token is an independent key.
// To add a new persona: add one line per token. No Set groups to forget.
// Acceptance invariant: every token in this map must appear in exactly one route's
// backend metrics endpoint AND one frontend dashboard page.
const ROLE_ROUTE_MAP = new Map([
  // Teacher
  ['teacher',           '/teacher'],
  // Parent
  ['parent',            '/parent'],
  // Student
  ['student',           '/student'],
  // Board
  ['board',             '/board'],
  ['governor',          '/board'],
  // Health / Nurse
  ['nurse',             '/health'],
  ['health',            '/health'],
  // Counseling / Discipline
  ['counselor',         '/counseling'],
  ['discipline_dean',   '/counseling'],
  ['dean_of_students',  '/counseling'],
  // Food Services
  ['food_service',      '/food'],
  ['cafeteria',         '/food'],
  // Athletics
  ['athletic_director', '/athletics'],
  ['ad',                '/athletics'],
  // Transportation
  ['transportation',    '/transportation'],
  ['bus',               '/transportation'],
  // Facilities
  ['facilities',        '/facilities'],
  ['maintenance',       '/facilities'],
  // Security / Safety
  ['security',          '/security'],
  ['safety',            '/security'],
  // Finance
  ['finance',           '/finance'],
  ['biz_office',        '/finance'],
  // Spiritual Life
  ['chaplain',          '/spiritual-life'],
  ['spiritual_life',    '/spiritual-life'],
  // IT
  ['it_director',       '/it'],
  ['it',                '/it'],
  // Financial Aid
  ['aid_director',      '/financial-aid'],
  ['financial_aid',     '/financial-aid'],
  // Marketing
  ['marketing',         '/marketing'],
  // Advancement / Fundraising
  ['advancement',       '/advancement'],
  ['fundraising',       '/advancement'],
  ['development',       '/advancement'],
  // Office / HR
  ['office_manager',    '/office'],
  ['hr',                '/office'],
  // Admin — route to /admin; router.jsx redirects /admin → /school-admin-dashboard in sandbox mode
  ['school_admin',      '/admin'],
  ['super_admin',       '/admin'],
  ['head_of_school',    '/admin'],
  ['admin',             '/admin'],
  ['director',          '/admin'],
  ['principal',         '/admin'],
  // Academic Support / SPED
  ['academic_support',          '/academic-support'],
  ['sped',                      '/academic-support'],
  ['learning_support',          '/academic-support'],
  // Fine Arts
  ['fine_arts',                 '/fine-arts'],
  ['arts_director',             '/fine-arts'],
  // Library / Media
  ['librarian',                 '/library'],
  ['library_media',             '/library'],
  // Extended Care / Aftercare
  ['extended_care',             '/extended-care'],
  ['aftercare',                 '/extended-care'],
  // Registrar / Records
  ['registrar',                 '/registrar'],
  ['records',                   '/registrar'],
  // Communications Director
  // NOTE: generic 'communications' token excluded — /communications is the comms-inbox route
  ['communications_director',   '/communications-director'],
  // PD / Staff Development
  ['pd_director',               '/pd'],
  ['staff_development',         '/pd'],
  // Student Services
  ['student_services',          '/student-services'],
]);

function resolveDashboardPath() {
  const raw    = `${getStoredRole()},${getJwtRole()}`;
  const tokens = raw.split(/[,\s]+/).filter(Boolean);
  for (const tok of tokens) {
    const route = ROLE_ROUTE_MAP.get(tok);
    if (route) return route;
  }
  return '/';
}

export default function RoleHomeRedirect() {
  const token = getAccessToken();

  // Hard redirect for sandbox admins
  const isSandbox = Boolean(import.meta.env.VITE_DEMO_MODE === "sandbox" || import.meta.env.VITE_SANDBOX_MODE === "1");
  const role = getStoredRole();
  const sandboxTarget = isSandbox && role === "school_admin" ? "/school-admin-dashboard" : "";
  const hasAuthHints = Boolean(token || role);
  const resolvedTarget = hasAuthHints ? resolveDashboardPath() : "";

  if (sandboxTarget) {
    return <Navigate to={sandboxTarget} replace />;
  }

  if (resolvedTarget && resolvedTarget !== '/') {
    return <Navigate to={resolvedTarget} replace />;
  }

  return <HomeDashboard />;
}
