import { PATHS } from '../../routes/paths';
import { ROLE_GROUPS } from '../../routes/routeGroups';
import { APP_PERMISSIONS } from '../../auth/permissions';

export const navItems = [
  { label: 'Dashboard', href: PATHS.HOME, roles: ROLE_GROUPS.ALL_AUTHENTICATED, permissions: [APP_PERMISSIONS.DASHBOARD_VIEW] },
  { label: 'Admissions', href: PATHS.ADMISSIONS, roles: ROLE_GROUPS.ADMIN_REGISTRAR, permissions: [APP_PERMISSIONS.ADMISSIONS_VIEW] },
  { label: 'Enrollment', href: PATHS.ENROLLMENT, roles: ROLE_GROUPS.ADMIN_REGISTRAR, permissions: [APP_PERMISSIONS.ENROLLMENT_VIEW] },
  { label: 'Billing', href: PATHS.BILLING, roles: ROLE_GROUPS.ADMIN_FINANCE, permissions: [APP_PERMISSIONS.BILLING_VIEW] },
  { label: 'Financial Aid', href: PATHS.FINANCIAL_AID, roles: ROLE_GROUPS.ADMIN_FINANCE, permissions: [APP_PERMISSIONS.FINANCIAL_AID_VIEW] },
  { label: 'Attendance', href: PATHS.ATTENDANCE, roles: ROLE_GROUPS.ACADEMIC_TEAM, permissions: [APP_PERMISSIONS.ATTENDANCE_VIEW] },
  { label: 'Gradebook', href: PATHS.GRADEBOOK, roles: ROLE_GROUPS.ACADEMIC_TEAM, permissions: [APP_PERMISSIONS.GRADEBOOK_VIEW] },
  { label: 'Communications', href: PATHS.COMMUNICATIONS, roles: ROLE_GROUPS.ALL_AUTHENTICATED, permissions: [APP_PERMISSIONS.COMMUNICATIONS_VIEW] },
  { label: 'Reporting', href: PATHS.REPORTING, roles: ROLE_GROUPS.ADMIN_ONLY, permissions: [APP_PERMISSIONS.REPORTING_VIEW] },
  { label: 'System Status', href: PATHS.SYSTEM_STATUS, roles: ROLE_GROUPS.ADMIN_ONLY, permissions: [APP_PERMISSIONS.SYSTEM_VIEW] },
  { label: 'Release Readiness', href: PATHS.RELEASE_READINESS, roles: ROLE_GROUPS.ADMIN_ONLY, permissions: [APP_PERMISSIONS.RELEASE_VIEW] },
  { label: 'Demo Readiness', href: PATHS.DEMO_READINESS, roles: ROLE_GROUPS.ADMIN_ONLY, permissions: [APP_PERMISSIONS.DEMO_VIEW] },
];
