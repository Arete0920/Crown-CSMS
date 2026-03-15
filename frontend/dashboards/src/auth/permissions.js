export const APP_PERMISSIONS = {
  DASHBOARD_VIEW: 'dashboard.view',

  ADMISSIONS_VIEW: 'admissions.view',
  ADMISSIONS_EDIT: 'admissions.edit',

  ENROLLMENT_VIEW: 'enrollment.view',
  ENROLLMENT_EDIT: 'enrollment.edit',

  STUDENTS_VIEW: 'students.view',
  STUDENTS_EDIT: 'students.edit',

  BILLING_VIEW: 'billing.view',
  BILLING_EDIT: 'billing.edit',

  FINANCIAL_AID_VIEW: 'financial_aid.view',
  FINANCIAL_AID_EDIT: 'financial_aid.edit',

  ATTENDANCE_VIEW: 'attendance.view',
  ATTENDANCE_EDIT: 'attendance.edit',

  GRADEBOOK_VIEW: 'gradebook.view',
  GRADEBOOK_EDIT: 'gradebook.edit',

  COMMUNICATIONS_VIEW: 'communications.view',
  COMMUNICATIONS_EDIT: 'communications.edit',

  REPORTING_VIEW: 'reporting.view',
  SYSTEM_VIEW: 'system.view',
  RELEASE_VIEW: 'release.view',
  DEMO_VIEW: 'demo.view',
};

export const PERMISSIONS_BY_ROLE = {
  owner: ['*'],
  admin: ['*'],
  super_admin: ['*'],
  school_admin: ['*'],

  registrar: [
    APP_PERMISSIONS.DASHBOARD_VIEW,
    APP_PERMISSIONS.ADMISSIONS_VIEW,
    APP_PERMISSIONS.ADMISSIONS_EDIT,
    APP_PERMISSIONS.ENROLLMENT_VIEW,
    APP_PERMISSIONS.ENROLLMENT_EDIT,
    APP_PERMISSIONS.STUDENTS_VIEW,
    APP_PERMISSIONS.STUDENTS_EDIT,
    APP_PERMISSIONS.REPORTING_VIEW,
  ],

  finance: [
    APP_PERMISSIONS.DASHBOARD_VIEW,
    APP_PERMISSIONS.BILLING_VIEW,
    APP_PERMISSIONS.BILLING_EDIT,
    APP_PERMISSIONS.FINANCIAL_AID_VIEW,
    APP_PERMISSIONS.FINANCIAL_AID_EDIT,
    APP_PERMISSIONS.REPORTING_VIEW,
  ],

  finance_admin: [
    APP_PERMISSIONS.DASHBOARD_VIEW,
    APP_PERMISSIONS.BILLING_VIEW,
    APP_PERMISSIONS.BILLING_EDIT,
    APP_PERMISSIONS.FINANCIAL_AID_VIEW,
    APP_PERMISSIONS.FINANCIAL_AID_EDIT,
    APP_PERMISSIONS.REPORTING_VIEW,
  ],

  teacher: [
    APP_PERMISSIONS.DASHBOARD_VIEW,
    APP_PERMISSIONS.ATTENDANCE_VIEW,
    APP_PERMISSIONS.ATTENDANCE_EDIT,
    APP_PERMISSIONS.GRADEBOOK_VIEW,
    APP_PERMISSIONS.GRADEBOOK_EDIT,
    APP_PERMISSIONS.COMMUNICATIONS_VIEW,
  ],

  parent: [
    APP_PERMISSIONS.DASHBOARD_VIEW,
    APP_PERMISSIONS.COMMUNICATIONS_VIEW,
  ],

  student: [
    APP_PERMISSIONS.DASHBOARD_VIEW,
    APP_PERMISSIONS.COMMUNICATIONS_VIEW,
  ],

  staff: [
    APP_PERMISSIONS.DASHBOARD_VIEW,
  ],

  head_of_school: [
    APP_PERMISSIONS.DASHBOARD_VIEW,
    APP_PERMISSIONS.REPORTING_VIEW,
    APP_PERMISSIONS.SYSTEM_VIEW,
    APP_PERMISSIONS.RELEASE_VIEW,
    APP_PERMISSIONS.DEMO_VIEW,
  ],
};

export function normalizeRoles(input) {
  if (!input) return [];
  if (Array.isArray(input)) return input.map((x) => String(x).trim().toLowerCase());
  return [String(input).trim().toLowerCase()];
}

export function resolvePermissions(user) {
  const explicit = Array.isArray(user?.permissions)
    ? user.permissions.map((x) => String(x).trim())
    : [];

  if (explicit.length > 0) {
    return explicit;
  }

  const roles = normalizeRoles(user?.roles?.length ? user.roles : user?.role);
  const combined = new Set();

  roles.forEach((role) => {
    const perms = PERMISSIONS_BY_ROLE[role] ?? [];
    perms.forEach((permission) => combined.add(permission));
  });

  return Array.from(combined);
}

export function userHasPermission(user, permission) {
  const permissions = resolvePermissions(user);
  return permissions.includes('*') || permissions.includes(permission);
}

export function userHasAnyPermission(user, needed = []) {
  return needed.some((permission) => userHasPermission(user, permission));
}
