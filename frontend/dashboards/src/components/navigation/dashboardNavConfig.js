import { getAccessibleDashboardSections } from '../../config/dashboardRegistry';
import { isProductionReady } from '../../config/releaseState';
import { getCurrentUserRoles } from '../../auth/roleAdapter';
import { filterVisibleNav } from '../../auth/roleAccess';
import { PATHS } from '../../routes/paths';
import { ROLE_GROUPS } from '../../routes/routeGroups';
import { APP_PERMISSIONS } from '../../auth/permissions';

function sandboxReadyOnlyEnabled() {
  const env = import.meta.env || {};
  return String(env.VITE_SANDBOX_READY_ONLY || '').toLowerCase() === 'true'
    || String(env.VITE_HIDE_UNREADY_NAV || '').toLowerCase() === 'true'
    || String(env.VITE_SANDBOX_MODE || '') === '1';
}

const STATIC_NAV_SECTIONS = [
  {
    label: 'Academics',
    children: [
      { key: 'academics-workspace', label: 'Academics', href: PATHS.ACADEMICS, tier: 0, roles: ROLE_GROUPS.ACADEMIC_TEAM },
      { key: 'gradebook-workspace', label: 'Gradebook', href: PATHS.GRADEBOOK, tier: 0, roles: ROLE_GROUPS.ACADEMIC_TEAM },
      { key: 'teacher-grading', label: 'Teacher Grading', href: PATHS.ACADEMICS_TEACHER_GRADING, tier: 0, roles: ROLE_GROUPS.ACADEMIC_TEAM },
      { key: 'classrooms', label: 'Classrooms', href: '/classrooms', tier: 0, roles: ROLE_GROUPS.ACADEMIC_TEAM },
      { key: 'attendance-workspace', label: 'Attendance', href: PATHS.ATTENDANCE, tier: 0, roles: ROLE_GROUPS.ACADEMIC_TEAM },
    ],
  },
  {
    label: 'Board',
    children: [
      { key: 'board', label: 'Board', href: '/board', tier: 0, roles: ROLE_GROUPS.ADMIN_ONLY },
      { key: 'integrity', label: 'Integrity', href: PATHS.REPORTING, tier: 0, roles: ROLE_GROUPS.ADMIN_ONLY, permissions: [APP_PERMISSIONS.REPORTING_VIEW] },
    ],
  },
  {
    label: 'Family',
    children: [
      { key: 'parent', label: 'Family', href: '/parent', tier: 0, roles: ROLE_GROUPS.FAMILY_VIEW },
      { key: 'parent-grades', label: 'Grades', href: '/academics/parent-snapshot', tier: 0, roles: ROLE_GROUPS.FAMILY_VIEW },
      { key: 'family-tuition', label: 'Tuition', href: '/finance/invoices', tier: 0, roles: ROLE_GROUPS.FAMILY_VIEW },
    ],
  },
  {
    label: 'Student',
    children: [
      { key: 'student', label: 'Student', href: '/student', tier: 0, roles: ROLE_GROUPS.FAMILY_VIEW },
      { key: 'student-work', label: 'Assignments', href: '/academics/student-work', tier: 0, roles: ROLE_GROUPS.FAMILY_VIEW },
      { key: 'student-grades', label: 'Grades', href: PATHS.GRADEBOOK, tier: 0, roles: ROLE_GROUPS.FAMILY_VIEW },
    ],
  },
  {
    label: 'Operations',
    children: [
      { key: 'admissions', label: 'Admissions', href: PATHS.ADMISSIONS, tier: 0, roles: ROLE_GROUPS.ADMIN_REGISTRAR, permissions: [APP_PERMISSIONS.ADMISSIONS_VIEW] },
      { key: 'admissions-pipeline', label: 'Admissions Pipeline', href: PATHS.ADMISSIONS_PIPELINE, tier: 0, roles: ROLE_GROUPS.ADMIN_REGISTRAR },
      { key: 'aftercare-roster', label: 'Roster Workspace', href: '/aftercare/roster', tier: 0 },
      { key: 'wizards', label: 'Wizard Hub', href: PATHS.WIZARDS, tier: 0, roles: ROLE_GROUPS.ADMIN_REGISTRAR },
    ],
  },
  {
    label: 'Communications',
    children: [
      { key: 'communications', label: 'Communications', href: PATHS.COMMUNICATIONS, tier: 0, roles: ROLE_GROUPS.ALL_AUTHENTICATED, permissions: [APP_PERMISSIONS.COMMUNICATIONS_VIEW] },
      { key: 'communications-director', label: 'Communications Director', href: '/communications-director', tier: 0 },
    ],
  },
];

const DASHBOARD_ALIAS_TO_ROUTE = {
  '/activities-dashboard': '/athletics',
  [PATHS.ADMISSIONS_DASHBOARD]: PATHS.ADMISSIONS,
  '/advancement-dashboard': '/advancement',
  '/athletics-director-dashboard': '/athletics',
  [PATHS.ATTENDANCE_DASHBOARD]: PATHS.ATTENDANCE,
  [PATHS.BILLING_DASHBOARD]: PATHS.BILLING,
  '/chaplain-dashboard': '/spiritual-life',
  [PATHS.COMMUNICATIONS_DASHBOARD]: PATHS.COMMUNICATIONS,
  '/extended-care-dashboard': '/extended-care',
  '/facilities-dashboard': '/facilities',
  [PATHS.FINANCIAL_AID_DASHBOARD]: PATHS.FINANCIAL_AID,
  '/fine-arts-dashboard': '/fine-arts',
  '/food-service-dashboard': '/food',
  [PATHS.GRADEBOOK_DASHBOARD]: PATHS.GRADEBOOK,
  '/health-office-dashboard': '/health',
  '/hr-dashboard': '/hr',
  '/it-support-dashboard': '/it',
  '/library-media-dashboard': '/library',
  '/master-control-dashboard': '/master-control',
  '/registrar-dashboard': '/registrar',
  '/safety-security-dashboard': '/safety',
  '/scheduling-dashboard': '/scheduling-dashboard',
  '/school-admin-dashboard': '/admin',
  '/school-board-dashboard': '/board',
  '/student-care-dashboard': '/student-services',
  '/transportation-dashboard': '/transportation',
};

function normalizePath(path) {
  return DASHBOARD_ALIAS_TO_ROUTE[path] || path;
}

function normalizeAndDedupeSections(sections) {
  const seen = new Set();

  return sections
    .map((section) => {
      const children = (section.children || []).map((item) => {
        const href = normalizePath(item.href);
        if (!href || seen.has(href)) return null;
        seen.add(href);
        return {
          key: item.key,
          label: item.label,
          href,
          tier: item.tier,
          roles: item.roles,
          permissions: item.permissions,
        };
      }).filter(Boolean);

      return {
        label: section.label,
        children,
      };
    })
    .filter((section) => section.children.length > 0);
}

export function getDashboardNavSections() {
  const userRoles = getCurrentUserRoles();
  const readyOnly = sandboxReadyOnlyEnabled();
  const visibleStaticSections = readyOnly
    ? []
    : filterVisibleNav(STATIC_NAV_SECTIONS, userRoles);

  const dynamicSections = getAccessibleDashboardSections(userRoles).map((section) => ({
    label: section.sectionLabel,
    children: section.items
      .filter((item) => !readyOnly || isProductionReady(item))
      .map((item) => ({
        key: item.key,
        label: item.label,
        href: item.path,
        tier: item.tier,
        roles: item.roles || item.allowedRoles,
      })),
  }));

  return normalizeAndDedupeSections([...visibleStaticSections, ...dynamicSections]);
}

export default STATIC_NAV_SECTIONS;
