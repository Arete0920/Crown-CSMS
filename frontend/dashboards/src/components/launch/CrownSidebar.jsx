import { Link, useInRouterContext } from 'react-router-dom';
import { getCurrentUserRoles } from '../../auth/roleAdapter';
import { hasAnyRole } from '../../auth/roleAccess';

const NAV_ITEMS = [
  {
    key: 'dashboard',
    label: 'Dashboard',
    href: '/dashboard',
    glyph: 'D',
    activePrefixes: ['/dashboard', '/teacher', '/teacher/dashboard', '/parent', '/parent/dashboard', '/student', '/student/dashboard'],
  },
  {
    key: 'school',
    label: 'School',
    href: '/school-admin',
    glyph: 'S',
    roles: ['school_admin', 'head_of_school', 'admin', 'director', 'principal', 'super_admin'],
    activePrefixes: ['/school-admin', '/school-administrator', '/school-admin-dashboard'],
  },
  {
    key: 'administration',
    label: 'Control Center',
    href: '/master-control',
    glyph: 'A',
    roles: ['school_admin', 'head_of_school', 'admin', 'director', 'principal', 'super_admin'],
    activePrefixes: ['/master-control', '/master-control-dashboard'],
  },
  {
    key: 'admissions',
    label: 'Admissions',
    href: '/admissions',
    glyph: 'Ad',
    roles: ['school_admin', 'head_of_school', 'admin', 'director', 'principal', 'admissions', 'admissions_manager'],
    activePrefixes: ['/admissions', '/admissions-dashboard'],
  },
  {
    key: 'academics',
    label: 'Academics',
    href: '/gradebook',
    glyph: 'Ac',
    roles: ['school_admin', 'head_of_school', 'admin', 'director', 'principal', 'teacher', 'academic_admin', 'academics'],
    activePrefixes: ['/gradebook', '/gradebook-dashboard', '/scheduling-dashboard', '/curriculum-pd-dashboard', '/library-media-dashboard'],
  },
  {
    key: 'student-life',
    label: 'Student Life',
    href: '/student-life',
    glyph: 'SL',
    roles: ['school_admin', 'head_of_school', 'admin', 'director', 'principal', 'teacher', 'parent', 'student'],
    activePrefixes: ['/student-life', '/spiritual-life', '/athletics', '/activities-dashboard', '/activities-athletics-dashboard', '/student-care-dashboard', '/chaplain-dashboard', '/portrait-service-dashboard', '/volunteer-management-dashboard', '/alumni-relations-dashboard', '/extended-care-dashboard', '/safety-security-dashboard'],
  },
  {
    key: 'attendance',
    label: 'Attendance',
    href: '/attendance',
    glyph: 'At',
    roles: ['school_admin', 'head_of_school', 'admin', 'director', 'principal', 'teacher', 'parent', 'student'],
    activePrefixes: ['/attendance', '/attendance-dashboard', '/teacher/attendance', '/parent/attendance'],
  },
  {
    key: 'finance',
    label: 'Finance',
    href: '/finance',
    glyph: 'F',
    roles: ['school_admin', 'head_of_school', 'admin', 'director', 'principal', 'finance', 'finance_admin', 'finance_director', 'biz_office', 'super_admin'],
    activePrefixes: ['/finance', '/billing', '/billing-dashboard', '/financial-aid', '/financial-aid-dashboard', '/revenue-operations-dashboard'],
  },
  {
    key: 'communications',
    label: 'Communications',
    href: '/communications',
    glyph: 'C',
    activePrefixes: ['/communications', '/communications-dashboard', '/communications-director'],
  },
  {
    key: 'reports',
    label: 'Reports',
    href: '/integrity',
    glyph: 'R',
    roles: ['school_admin', 'head_of_school', 'admin', 'director', 'principal', 'board', 'board_member', 'super_admin'],
    activePrefixes: ['/integrity', '/compliance-audit-dashboard', '/release-reliability-dashboard', '/dashboard-certification-center', '/network-benchmarking-dashboard'],
  },
  {
    key: 'settings',
    label: 'Settings',
    href: '/settings',
    glyph: 'Se',
    roles: ['school_admin', 'head_of_school', 'admin', 'director', 'principal', 'super_admin'],
    activePrefixes: ['/settings'],
  },
];

function resolveActiveNavKey(pathname = '') {
  if (!pathname) return null;

  const normalizedPath = pathname.toLowerCase();
  const match = NAV_ITEMS.find((item) => {
    const prefixes = Array.isArray(item.activePrefixes) && item.activePrefixes.length > 0
      ? item.activePrefixes
      : [item.href];

    return prefixes.some((prefix) => normalizedPath.startsWith(prefix.toLowerCase()));
  });

  return match?.key ?? null;
}

function BrandLockup() {
  return (
    <div className="launch-brand-lockup">
      <div className="launch-brand-crest" aria-hidden="true">
        <svg viewBox="0 0 64 64" role="presentation" focusable="false">
          <defs>
            <linearGradient id="crownCrest" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#1D4ED8" />
              <stop offset="100%" stopColor="#60A5FA" />
            </linearGradient>
          </defs>
          <path d="M32 5 L52 13 L49 39 C48 48 41 55 32 58 C23 55 16 48 15 39 L12 13 Z" fill="url(#crownCrest)" />
          <path d="M21 24 L27 19 L32 25 L37 19 L43 24 L41 35 H23 Z" fill="#FBBF24" opacity="0.96" />
          <rect x="23" y="36" width="18" height="4" rx="2" fill="#FFFFFF" opacity="0.9" />
        </svg>
      </div>
      <div>
        <div className="launch-brand-title">CROWN</div>
        <div className="launch-brand-tagline">Christian School Management Solution</div>
      </div>
    </div>
  );
}

export default function CrownSidebar({
  activePath = '/dashboard',
  user = { initials: 'SJ', name: 'Sarah James', role: 'Head of School' },
}) {
  const hasRouterContext = useInRouterContext();
  const userRoles = getCurrentUserRoles();
  const visibleItems = NAV_ITEMS.filter((item) => !Array.isArray(item.roles) || hasAnyRole(userRoles, item.roles));
  const activeNavKey = resolveActiveNavKey(activePath);

  return (
    <aside className="launch-sidebar">
      <BrandLockup />

      <nav className="launch-sidebar-nav" aria-label="Primary">
        {visibleItems.map((item) => {
          const active = item.key === activeNavKey;
          const classes = active ? 'is-active' : '';
          const content = (
            <>
              <span className="launch-nav-icon" aria-hidden="true">{item.glyph}</span>
              <span>{item.label}</span>
            </>
          );

          if (hasRouterContext) {
            return (
              <Link key={item.href + item.label} to={item.href} className={classes}>
                {content}
              </Link>
            );
          }

          return (
            <a key={item.href + item.label} href={item.href} className={classes}>
              {content}
            </a>
          );
        })}
      </nav>

      <div className="launch-user-card">
        <div className="launch-user-avatar">{user.initials || 'SJ'}</div>
        <div>
          <div className="launch-user-name">{user.name || 'Sarah James'}</div>
          <div className="launch-user-role">{user.role || 'Head of School'}</div>
        </div>
      </div>
    </aside>
  );
}
