import { getAccessibleDashboardSections } from '../../config/dashboardRegistry';
import { getCurrentUserRoles } from '../../auth/roleAdapter';

const STATIC_NAV_SECTIONS = [
  {
    label: 'Academics',
    children: [
      { key: 'gradebook-workspace', label: 'Gradebook', href: '/gradebook', tier: 0 },
      { key: 'classrooms', label: 'Classrooms', href: '/classrooms', tier: 0 },
      { key: 'attendance-workspace', label: 'Attendance', href: '/attendance', tier: 0 },
    ],
  },
  {
    label: 'Board',
    children: [
      { key: 'board', label: 'Board', href: '/board', tier: 0 },
      { key: 'integrity', label: 'Integrity', href: '/integrity', tier: 0 },
    ],
  },
  {
    label: 'Family',
    children: [
      { key: 'parent', label: 'Family', href: '/parent', tier: 0 },
      { key: 'parent-grades', label: 'Grades', href: '/academics/parent-snapshot', tier: 0 },
      { key: 'family-tuition', label: 'Tuition', href: '/finance/invoices', tier: 0 },
    ],
  },
  {
    label: 'Student',
    children: [
      { key: 'student', label: 'Student', href: '/student', tier: 0 },
      { key: 'student-work', label: 'Assignments', href: '/academics/student-work', tier: 0 },
      { key: 'student-grades', label: 'Grades', href: '/gradebook', tier: 0 },
    ],
  },
  {
    label: 'Operations',
    children: [
      { key: 'admissions', label: 'Admissions', href: '/admissions', tier: 0 },
      { key: 'admissions-pipeline', label: 'Admissions Pipeline', href: '/admissions/pipeline', tier: 0 },
      { key: 'aftercare-roster', label: 'Roster Workspace', href: '/aftercare/roster', tier: 0 },
      { key: 'wizards', label: 'Wizard Hub', href: '/wizards', tier: 0 },
    ],
  },
  {
    label: 'Communications',
    children: [
      { key: 'communications', label: 'Communications', href: '/communications', tier: 0 },
      { key: 'communications-director', label: 'Communications Director', href: '/communications-director', tier: 0 },
    ],
  },
];

const DASHBOARD_ALIAS_TO_ROUTE = {
  '/activities-dashboard': '/athletics',
  '/admissions-dashboard': '/admissions',
  '/advancement-dashboard': '/advancement',
  '/athletics-director-dashboard': '/athletics',
  '/attendance-dashboard': '/attendance',
  '/billing-dashboard': '/billing',
  '/chaplain-dashboard': '/spiritual-life',
  '/communications-dashboard': '/communications',
  '/extended-care-dashboard': '/extended-care',
  '/facilities-dashboard': '/facilities',
  '/financial-aid-dashboard': '/financial-aid',
  '/fine-arts-dashboard': '/fine-arts',
  '/food-service-dashboard': '/food',
  '/gradebook-dashboard': '/gradebook',
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

  const dynamicSections = getAccessibleDashboardSections(userRoles).map((section) => ({
    label: section.sectionLabel,
    children: section.items.map((item) => ({
      key: item.key,
      label: item.label,
      href: item.path,
      tier: item.tier,
    })),
  }));

  return normalizeAndDedupeSections([...STATIC_NAV_SECTIONS, ...dynamicSections]);
}
