=== SECURITY RBAC UNKNOWNS ===
## Role guard and permission references
frontend/dashboards/src\auth\roleAdapter.js:1:import { getUserRoles, normalizeRoles } from "./roleAccess";
frontend/dashboards/src\auth\roleAdapter.js:19:    sessionStorage.getItem('crown.role'),
frontend/dashboards/src\auth\roleAdapter.js:20:    localStorage.getItem('crown.role'),
frontend/dashboards/src\auth\roleAdapter.js:21:    localStorage.getItem('crown.demo.role'),
frontend/dashboards/src\auth\roleAdapter.js:33:  const directRoles = parseStorageValue(localStorage.getItem('crown_user_roles'));
frontend/dashboards/src\auth\roleAdapter.js:53:  const roles = getEffectiveRoles(authPayload);
frontend/dashboards/src\auth\roleAdapter.js:54:  return roles[0] || null;
frontend/dashboards/src\auth\roleAdapter.js:57:export function normalizeAllowedRoles(roles) {
frontend/dashboards/src\auth\roleAdapter.js:58:  return normalizeRoles(roles);
frontend/dashboards/src\views\platformOps\PlatformOpsHome.jsx:6: * Displays a searchable, paginated list of all school tenants with their
frontend/dashboards/src\views\platformOps\PlatformOpsHome.jsx:9: * Accessible only to users with is_staff=true / IsAdminUser permission.
frontend/dashboards/src\views\platformOps\PlatformOpsHome.jsx:10: * Does NOT require or send X-School-ID - these are cross-tenant ops.
frontend/dashboards/src\views\platformOps\PlatformOpsHome.jsx:251:            Super-admin console - all school tenants across the platform.
frontend/dashboards/src\auth\roleAccess.test.js:5:  hasAnyRole,
frontend/dashboards/src\auth\roleAccess.test.js:8:} from "./roleAccess";
frontend/dashboards/src\auth\roleAccess.test.js:10:describe("roleAccess", () => {
frontend/dashboards/src\auth\roleAccess.test.js:11:  it("normalizes equivalent role labels", () => {
frontend/dashboards/src\auth\roleAccess.test.js:21:  it("extracts roles from common auth payload shapes", () => {
frontend/dashboards/src\auth\roleAccess.test.js:22:    expect(getUserRoles({ role: "head_of_school" })).toContain("school_admin");
frontend/dashboards/src\auth\roleAccess.test.js:23:    expect(getUserRoles({ roles: ["finance"] })).toContain("finance_admin");
frontend/dashboards/src\auth\roleAccess.test.js:24:    expect(getUserRoles({ user: { role: "admissions" } })).toContain("admissions_manager");
frontend/dashboards/src\auth\roleAccess.test.js:25:    expect(getUserRoles({ profile: { roles: [{ code: "it" }] } })).toContain("it_support");
frontend/dashboards/src\auth\roleAccess.test.js:28:  it("passes any-role checks through alias normalization", () => {
frontend/dashboards/src\auth\roleAccess.test.js:29:    expect(hasAnyRole({ role: "head_of_school" }, ["school_admin"])).toBe(true);
frontend/dashboards/src\auth\roleAccess.test.js:30:    expect(hasAnyRole({ roles: ["finance"] }, ["finance_admin"])).toBe(true);
frontend/dashboards/src\auth\roleAccess.test.js:31:    expect(hasAnyRole({ roles: ["admissions"] }, ["admissions_manager", "registrar"])).toBe(true);
frontend/dashboards/src\auth\roleAccess.test.js:32:    expect(hasAnyRole({ roles: ["teacher"] }, ["finance_admin"])).toBe(false);
frontend/dashboards/src\auth\roleAccess.test.js:35:  it("passes all-role checks through alias normalization", () => {
frontend/dashboards/src\auth\roleAccess.test.js:38:        { roles: ["head_of_school", "finance"] },
frontend/dashboards/src\auth\roleAccess.test.js:45:        { roles: ["head_of_school"] },
frontend/dashboards/src\auth\roleAccess.test.js:51:  it("filters visible nav items by runtime role access", () => {
frontend/dashboards/src\auth\roleAccess.test.js:54:      { label: "Finance", href: "/finance", roles: ["finance_admin"] },
frontend/dashboards/src\auth\roleAccess.test.js:55:      { label: "Admissions", href: "/admissions", roles: ["admissions_manager"] },
frontend/dashboards/src\auth\roleAccess.test.js:59:          { label: "Settings", href: "/settings", roles: ["school_admin"] },
frontend/dashboards/src\auth\roleAccess.test.js:60:          { label: "IT", href: "/it", roles: ["it_support"] },
frontend/dashboards/src\auth\roleAccess.test.js:65:    const financeUserNav = filterVisibleNav(nav, { roles: ["finance"] });
frontend/dashboards/src\auth\roleAccess.test.js:77:  it("retains admin children for equivalent admin role labels", () => {
frontend/dashboards/src\auth\roleAccess.test.js:81:        children: [{ label: "Settings", href: "/settings", roles: ["school_admin"] }],
frontend/dashboards/src\auth\roleAccess.test.js:85:    const result = filterVisibleNav(nav, { role: "head_of_school" });
frontend/dashboards/src\auth\roleAccess.js:33:  group.forEach((role) => {
frontend/dashboards/src\auth\roleAccess.js:34:    lookup[role] = group;
frontend/dashboards/src\auth\roleAccess.js:52:      return [entry.code, entry.role, entry.name, entry.slug, entry.value].filter(Boolean);
frontend/dashboards/src\auth\roleAccess.js:67:      input.role,
frontend/dashboards/src\auth\roleAccess.js:69:      input.role_code,
frontend/dashboards/src\auth\roleAccess.js:70:      input.roleCode,
frontend/dashboards/src\auth\roleAccess.js:73:      ...extractArrayRoles(input.roles),
frontend/dashboards/src\auth\roleAccess.js:119:export function hasAnyRole(userLike, allowedRoles = []) {
frontend/dashboards/src\auth\roleAccess.js:126:  return effectiveAllowedRoles.some((role) => effectiveUserRoles.includes(role));
frontend/dashboards/src\auth\roleAccess.js:136:  return effectiveRequiredRoles.every((role) => effectiveUserRoles.includes(role));
frontend/dashboards/src\auth\roleAccess.js:140:  const allowedRoles = accessConfig.roles || accessConfig.allowedRoles || [];
frontend/dashboards/src\auth\roleAccess.js:141:  const requiredPermissions = accessConfig.permissions || [];
frontend/dashboards/src\auth\roleAccess.js:143:  const roleAllowed = hasAnyRole(userLike, allowedRoles);
frontend/dashboards/src\auth\roleAccess.js:146:    return roleAllowed;
frontend/dashboards/src\auth\roleAccess.js:149:  const permissionSet = Array.isArray(userLike?.permissions)
frontend/dashboards/src\auth\roleAccess.js:150:    ? new Set(userLike.permissions.map((value) => String(value).trim()))
frontend/dashboards/src\auth\roleAccess.js:153:  if (!permissionSet) {
frontend/dashboards/src\auth\roleAccess.js:154:    return roleAllowed;
frontend/dashboards/src\auth\roleAccess.js:157:  if (permissionSet.has('*')) {
frontend/dashboards/src\auth\roleAccess.js:161:  return requiredPermissions.some((permission) => permissionSet.has(permission));
frontend/dashboards/src\auth\roleAccess.js:173:      Array.isArray(item.roles) || Array.isArray(item.allowedRoles) || Array.isArray(item.permissions);
frontend/dashboards/src\auth\RequireAuth.jsx:6://   <Route path="/dash/:role" element={<RequireAuth><RoleDashboardPage /></RequireAuth>} />
frontend/dashboards/src\auth\permissions.js:111:  const explicit = Array.isArray(user?.permissions)
frontend/dashboards/src\auth\permissions.js:112:    ? user.permissions.map((x) => String(x).trim())
frontend/dashboards/src\auth\permissions.js:119:  const roles = normalizeRoles(user?.roles?.length ? user.roles : user?.role);
frontend/dashboards/src\auth\permissions.js:122:  roles.forEach((role) => {
frontend/dashboards/src\auth\permissions.js:123:    const perms = PERMISSIONS_BY_ROLE[role] ?? [];
frontend/dashboards/src\auth\permissions.js:124:    perms.forEach((permission) => combined.add(permission));
frontend/dashboards/src\auth\permissions.js:130:export function userHasPermission(user, permission) {
frontend/dashboards/src\auth\permissions.js:131:  const permissions = resolvePermissions(user);
frontend/dashboards/src\auth\permissions.js:132:  return permissions.includes('*') || permissions.includes(permission);
frontend/dashboards/src\auth\permissions.js:136:  return needed.some((permission) => userHasPermission(user, permission));
frontend/dashboards/src\hooks\usePermissions.js:6:} from '../auth/permissions';
frontend/dashboards/src\hooks\usePermissions.js:26:    permissions: resolvePermissions(user),
frontend/dashboards/src\hooks\usePermissions.js:27:    hasPermission: (permission) => userHasPermission(user, permission),
frontend/dashboards/src\utils\requestTracing.js:3: * Logs API calls with tenant headers and correlation IDs for debugging
frontend/dashboards/src\utils\requestTracing.js:17:  console.log(`Tenant (X-School-Id): ${schoolId || "none"}`);
frontend/dashboards/src\utils\requestTracing.js:28:  console.log(`Tenant (X-School-Id): ${schoolId || "none"}`);
frontend/dashboards/src\config\validateDashboardRegistry.js:38:      throw new Error(`${prefix} must define at least one allowed role.`);
frontend/dashboards/src\utils\demoAutoLogin.ts:15:  role,
frontend/dashboards/src\utils\demoAutoLogin.ts:16:  roleKey,
frontend/dashboards/src\utils\demoAutoLogin.ts:24:  role: string;
frontend/dashboards/src\utils\demoAutoLogin.ts:25:  roleKey: string;
frontend/dashboards/src\utils\demoAutoLogin.ts:54:  // Set role so RoleRouteGuard and RequirePermission resolve correctly in demo mode
frontend/dashboards/src\utils\demoAutoLogin.ts:55:  sessionStorage.setItem(roleKey, role);
frontend/dashboards/src\utils\demoAutoLogin.ts:56:  localStorage.setItem(roleKey, role);
frontend/dashboards/src\utils\demoAutoLogin.ts:57:  localStorage.setItem("crown.demo.role", role);
frontend/dashboards/src\utils\demoAutoLogin.ts:60:    role,
frontend/dashboards/src\utils\authClient.js:19:    // This ensures tenant header is sent even if user refreshed during session
frontend/dashboards/src\utils\authClient.js:70:  // Optional tenant override for staff/superusers only (backend enforces).
frontend/dashboards/src\utils\authClient.js:72:  if (schoolId && !headers.has("X-School-Id")) {
frontend/dashboards/src\utils\authClient.js:73:    headers.set("X-School-Id", schoolId);
frontend/dashboards/src\hooks\useCurrentUserRole.js:36:        // Fallback: read the simpler role key used by demo/test session seeding.
frontend/dashboards/src\hooks\useCurrentUserRole.js:38:          sessionStorage.getItem('crown.role') ||
frontend/dashboards/src\hooks\useCurrentUserRole.js:39:          localStorage.getItem('crown.role') ||
frontend/dashboards/src\hooks\useCurrentUserRole.js:40:          localStorage.getItem('crown.demo.role');
frontend/dashboards/src\hooks\useCurrentUserRole.js:45:      if (typeof parsed?.role === 'string' && parsed.role.trim()) {
frontend/dashboards/src\hooks\useCurrentUserRole.js:46:        return parsed.role.trim().toLowerCase();
frontend/dashboards/src\hooks\useCurrentUserRole.js:49:      if (Array.isArray(parsed?.roles) && parsed.roles.length > 0) {
frontend/dashboards/src\hooks\useCurrentUserRole.js:50:        return String(parsed.roles[0]).trim().toLowerCase();
frontend/dashboards/src\hooks\useBoardExecutiveData.js:71:    if (schoolId) h["X-School-Id"]   = String(schoolId);
backend\analytics\tasks.py:78:def run_all_predictive_models(self, tenant_id):
backend\analytics\tasks.py:79:    """Run the conservative predictive analytics suite for one school tenant."""
backend\analytics\tasks.py:84:        school = School.objects.get(id=tenant_id)
frontend/dashboards/src\tests\roleGuard.test.jsx:2:import { isRoleAllowed } from '../routes/roleGuardRules';
frontend/dashboards/src\tests\roleGuard.test.jsx:4:describe('RoleGuard role checks', () => {
frontend/dashboards/src\tests\roleGuard.test.jsx:5:  it('allows authorized role', () => {
frontend/dashboards/src\tests\roleGuard.test.jsx:10:  it('blocks unauthorized role', () => {
frontend/dashboards/src\tests\roleGuard.test.jsx:14:  it('allows when route has no explicit role list', () => {
backend\aftercare\wizard_api.py:5:from core.permissions import user_has_permission
backend\aftercare\wizard_api.py:6:from .tenant import school_id_from_request
backend\aftercare\wizard_api.py:20:        or user_has_permission(user, "aftercare.edit", school=school)
frontend/dashboards/src\tests\permissionContract.test.js:6:} from '../auth/permissions';
frontend/dashboards/src\tests\permissionContract.test.js:8:describe('permission contract', () => {
frontend/dashboards/src\tests\permissionContract.test.js:10:    const permissions = resolvePermissions({ role: 'admin' });
frontend/dashboards/src\tests\permissionContract.test.js:11:    expect(permissions.includes('*')).toBe(true);
frontend/dashboards/src\tests\permissionContract.test.js:16:      userHasPermission({ role: 'finance' }, APP_PERMISSIONS.BILLING_VIEW),
frontend/dashboards/src\tests\permissionContract.test.js:22:      userHasPermission({ role: 'parent' }, APP_PERMISSIONS.BILLING_EDIT),
frontend/dashboards/src\tests\permissionContract.test.js:26:  it('explicit permissions override role fallback', () => {
frontend/dashboards/src\tests\permissionContract.test.js:27:    const permissions = resolvePermissions({
frontend/dashboards/src\tests\permissionContract.test.js:28:      role: 'parent',
frontend/dashboards/src\tests\permissionContract.test.js:29:      permissions: [APP_PERMISSIONS.RELEASE_VIEW],
frontend/dashboards/src\tests\permissionContract.test.js:32:    expect(permissions).toContain(APP_PERMISSIONS.RELEASE_VIEW);
frontend/dashboards/src\tests\loginPagePolish.test.jsx:64:  it("shows school selector and role selector with school admin", async () => {
frontend/dashboards/src\tests\loginPagePolish.test.jsx:68:    const roleSelect = screen.getByLabelText("Role");
frontend/dashboards/src\tests\loginPagePolish.test.jsx:71:    expect(roleSelect).toBeTruthy();
frontend/dashboards/src\tests\loginPagePolish.test.jsx:77:    fireEvent.change(roleSelect, { target: { value: "school_admin" } });
frontend/dashboards/src\tests\loginPagePolish.test.jsx:78:    expect(roleSelect.value).toBe("school_admin");
frontend/dashboards/src\tests\apiContractRegistry.test.js:16:      expect(Boolean(contract.permission)).toBe(true);
frontend/dashboards/src\styles\launch-shell.css:277:.launch-user-role {
frontend/dashboards/src\features\dashboards\__tests__\roleDashboardMatrix.test.ts:2:import { requiredSharedDashboardCards, roleDashboardProfiles } from "../roleDashboardMatrix";
frontend/dashboards/src\features\dashboards\__tests__\roleDashboardMatrix.test.ts:4:describe("CROWN role dashboard matrix", () => {
frontend/dashboards/src\features\dashboards\__tests__\roleDashboardMatrix.test.ts:5:  it("defines every required role dashboard", () => {
frontend/dashboards/src\features\dashboards\__tests__\roleDashboardMatrix.test.ts:6:    expect(roleDashboardProfiles.length).toBeGreaterThanOrEqual(16);
frontend/dashboards/src\features\dashboards\__tests__\roleDashboardMatrix.test.ts:26:      expect(roleDashboardProfiles.some((profile) => profile.key === key)).toBe(true);
frontend/dashboards/src\features\dashboards\__tests__\roleDashboardMatrix.test.ts:30:  it("gives each dashboard role-specific KPIs, queues, quick actions, panels, and routes", () => {
frontend/dashboards/src\features\dashboards\__tests__\roleDashboardMatrix.test.ts:31:    for (const profile of roleDashboardProfiles) {
frontend/dashboards/src\features\dashboards\__tests__\roleDashboardMatrix.test.ts:63:  it("does not clone administrator dashboard KPIs into every role", () => {
frontend/dashboards/src\features\dashboards\__tests__\roleDashboardMatrix.test.ts:65:      roleDashboardProfiles.map((profile) => [
frontend/dashboards/src\features\dashboards\__tests__\roleDashboardMatrix.test.ts:72:    for (const [roleKey, kpis] of serializedByRole.entries()) {
frontend/dashboards/src\features\dashboards\__tests__\roleDashboardMatrix.test.ts:73:      if (roleKey === "school-administrator") continue;
frontend/dashboards/src\styles\crown-theme.css:62:[role="button"],
backend\aftercare\tests\test_aftercare_services.py:6:Tenant scoping tests live in test_aftercare_tenant_scoping.py.
frontend/dashboards/src\features\dashboards\shared\SharedDashboardWidgets.tsx:1:import { requiredSharedDashboardCards } from "../roleDashboardMatrix";
frontend/dashboards/src\features\dashboards\roleDashboardMatrix.ts:18:    description: "School calendar, personal schedule, class events, meetings, practices, and role-relevant deadlines.",
frontend/dashboards/src\features\dashboards\roleDashboardMatrix.ts:32:    description: "Prayer needs, pastoral-care visibility, community support, and permission-aware request handling.",
frontend/dashboards/src\features\dashboards\roleDashboardMatrix.ts:39:    description: "School-wide, class-level, team-level, and role-specific announcements.",
frontend/dashboards/src\features\dashboards\roleDashboardMatrix.ts:67:    description: "Teams meetings, class channels, staff channels, announcements, collaboration, and role-based links.",
frontend/dashboards/src\features\dashboards\roleDashboardMatrix.ts:73:export const roleDashboardProfiles: DashboardRoleProfile[] = [
frontend/dashboards/src\features\dashboards\roleDashboardMatrix.ts:85:      "Protect tenant, role, compliance, and mission integrity",
frontend/dashboards/src\features\dashboards\roleDashboardMatrix.ts:361:      { label: "Family Tasks", value: "4", helper: "Forms, permissions, or acknowledgements due", source: "Family portal", tone: "amber" },
frontend/dashboards/src\features\dashboards\roleDashboardMatrix.ts:459:        description: "Sensitive workflows require role-based access and careful information boundaries.",
frontend/dashboards/src\features\dashboards\roleDashboardMatrix.ts:700:export function getDashboardProfile(roleKey: DashboardRoleKey): DashboardRoleProfile {
frontend/dashboards/src\features\dashboards\roleDashboardMatrix.ts:701:  const profile = roleDashboardProfiles.find((item) => item.key === roleKey);
frontend/dashboards/src\features\dashboards\roleDashboardMatrix.ts:703:    throw new Error(`Unknown dashboard role: ${roleKey}`);
frontend/dashboards/src\features\dashboards\roleDashboardMatrix.ts:709:  return roleDashboardProfiles.some((item) => item.key === value);
frontend/dashboards/src\features\dashboards\RoleDashboard.tsx:3:import { getDashboardProfile, requiredSharedDashboardCards } from "./roleDashboardMatrix";
frontend/dashboards/src\features\dashboards\RoleDashboard.tsx:9:  roleKey: DashboardRoleKey;
frontend/dashboards/src\features\dashboards\RoleDashboard.tsx:25:export function RoleDashboard({ roleKey }: RoleDashboardProps) {
frontend/dashboards/src\features\dashboards\RoleDashboard.tsx:26:  const profile = useMemo(() => getDashboardProfile(roleKey), [roleKey]);
frontend/dashboards/src\features\dashboards\RoleDashboard.tsx:32:    loadRoleDashboardPayload(roleKey).then((data) => {
frontend/dashboards/src\features\dashboards\RoleDashboard.tsx:40:  }, [roleKey]);
frontend/dashboards/src\features\dashboards\RoleDashboard.tsx:51:          <p className="crown-eyebrow">CROWN role dashboard</p>
frontend/dashboards/src\features\dashboards\RoleDashboard.tsx:166:            <span>Class, staff, leadership, board, and role-based collaboration channels.</span>
backend\analytics\predictors.py:296:def run_enrollment_forecast(tenant, historical_data):
backend\analytics\predictors.py:345:        school=tenant,
backend\analytics\predictors.py:353:def run_retention_risk(tenant, student_features):
backend\analytics\predictors.py:407:        school=tenant,
backend\analytics\predictors.py:414:def run_academic_risk(tenant, student_academic_data):
backend\analytics\predictors.py:455:        school=tenant,
frontend/dashboards/src\features\dashboards\index.ts:4:export { roleDashboardProfiles, requiredSharedDashboardCards, getDashboardProfile } from "./roleDashboardMatrix";
frontend/dashboards/src\api\signalsApi.js:21:  if (schoolId) headers["X-School-Id"] = String(schoolId);
frontend/dashboards/src\features\dashboards\dashboardTypes.ts:87:  roleKey: DashboardRoleKey;
frontend/dashboards/src\features\dashboards\DashboardIndex.tsx:1:import { roleDashboardProfiles } from "./roleDashboardMatrix";
frontend/dashboards/src\features\dashboards\DashboardIndex.tsx:13:            and role-specific KPIs matched to actual responsibilities.
frontend/dashboards/src\features\dashboards\DashboardIndex.tsx:17:      <section className="crown-role-index-grid">
frontend/dashboards/src\features\dashboards\DashboardIndex.tsx:18:        {roleDashboardProfiles.map((profile) => (
frontend/dashboards/src\features\dashboards\DashboardIndex.tsx:19:          <a href={profile.route} className="crown-role-index-card" key={profile.key}>
frontend/dashboards/src\api\section_staffing_wizard.js:47: * @param {Array} assignments - [{section_id, teacher_id, role: "primary"|"aide"|"co-teacher"}]
frontend/dashboards/src\features\dashboards\dashboardApi.ts:20:export async function loadRoleDashboardPayload(roleKey: DashboardRoleKey): Promise<DashboardApiPayload | null> {
frontend/dashboards/src\features\dashboards\dashboardApi.ts:21:  return safeFetchJson<DashboardApiPayload>(`/api/v1/dashboards/roles/${roleKey}/`);
frontend/dashboards/src\features\dashboards\CrownDashboardRoutes.tsx:4:import { roleDashboardProfiles } from "./roleDashboardMatrix";
frontend/dashboards/src\features\dashboards\CrownDashboardRoutes.tsx:9:    {roleDashboardProfiles.map((profile) => (
frontend/dashboards/src\features\dashboards\CrownDashboardRoutes.tsx:13:        element={<RoleDashboard roleKey={profile.key} />}
backend\analytics\models_customer_health.py:11:    """Composite health score for a school tenant."""
frontend/dashboards/src\features\dashboards\crown-dashboard.css:52:.crown-role-index-card {
frontend/dashboards/src\features\dashboards\crown-dashboard.css:150:.crown-role-index-grid {
frontend/dashboards/src\features\dashboards\crown-dashboard.css:177:.crown-role-index-grid {
frontend/dashboards/src\features\dashboards\crown-dashboard.css:268:.crown-role-index-card {
frontend/dashboards/src\features\dashboards\crown-dashboard.css:275:.crown-role-index-card:hover {
frontend/dashboards/src\features\dashboards\crown-dashboard.css:290:.crown-role-index-card strong {
frontend/dashboards/src\features\dashboards\crown-dashboard.css:298:.crown-role-index-card small,
frontend/dashboards/src\features\dashboards\crown-dashboard.css:351:.crown-role-index-card {
frontend/dashboards/src\features\dashboards\crown-dashboard.css:366:  .crown-role-index-grid {
frontend/dashboards/src\features\dashboards\crown-dashboard.css:380:  .crown-role-index-grid {
backend\analytics\models.py:13:    # `core.School` is the authoritative tenant root in this codebase.
frontend/dashboards/src\routes\wizards.js:17: *   roles       ΓÇö which roles may access this wizard (optional, for future guard)
frontend/dashboards/src\routes\wizards.js:70:    roles: ['super_admin', 'school_admin', 'admissions_manager'],
frontend/dashboards/src\routes\wizards.js:77:    roles: ['super_admin', 'school_admin', 'registrar'],
frontend/dashboards/src\routes\wizards.js:84:    roles: ['admin', 'finance'],
frontend/dashboards/src\routes\wizards.js:91:    roles: ['super_admin', 'school_admin', 'finance_admin'],
frontend/dashboards/src\routes\wizards.js:98:    roles: ['admin', 'academics'],
frontend/dashboards/src\routes\wizards.js:105:    roles: ['admin', 'communications'],
frontend/dashboards/src\routes\wizards.js:112:    roles: ['admin', 'academics'],
frontend/dashboards/src\routes\wizards.js:119:    roles: ['admin', 'academics'],
frontend/dashboards/src\routes\wizards.js:126:    roles: ['admin', 'academics'],
frontend/dashboards/src\routes\wizards.js:133:    roles: ['admin', 'academics', 'registrar'],
frontend/dashboards/src\routes\wizards.js:140:    roles: ['super_admin', 'school_admin', 'admissions_manager', 'registrar'],
frontend/dashboards/src\routes\wizards.js:147:    roles: ['admin', 'finance'],
frontend/dashboards/src\routes\wizards.js:154:    roles: ['admin', 'director', 'hr'],
frontend/dashboards/src\routes\wizards.js:161:    roles: ['admin', 'finance', 'director'],
frontend/dashboards/src\routes\wizards.js:168:    roles: ['admin', 'director'],
frontend/dashboards/src\routes\wizards.js:175:    roles: ['super_admin', 'school_admin', 'registrar'],
frontend/dashboards/src\routes\wizards.js:182:    roles: ['admin', 'academics', 'director'],
frontend/dashboards/src\routes\wizards.js:189:    roles: ['admin', 'academics', 'director'],
frontend/dashboards/src\routes\wizards.js:197:    roles: ['admin', 'academics', 'director'],
frontend/dashboards/src\routes\wizards.js:204:    roles: ['admin', 'director'],
frontend/dashboards/src\routes\wizards.js:211:    roles: ['admin', 'academics', 'director'],
frontend/dashboards/src\routes\wizards.js:218:    roles: ['admin', 'director'],
frontend/dashboards/src\routes\wizards.js:225:    roles: ['admin', 'academics', 'director'],
frontend/dashboards/src\routes\wizards.js:258:  if (Array.isArray(route.roles) && route.roles.length > 0) {
frontend/dashboards/src\routes\wizards.js:259:    return createElement(RoleRouteGuard, { allowedRoles: route.roles || [] }, wrappedElement);
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:6:  return route?.roles || [];
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:10:  return userRoles.some((role) => allowedRoles.includes(role));
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:19:  it("defines explicit allowed roles for every wizard route", () => {
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:21:      expect(Array.isArray(route.roles)).toBe(true);
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:22:      expect(route.roles.length).toBeGreaterThan(0);
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:27:    const roles = ["school_admin"];
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:35:      expect(canAccess(roles, getAllowedRoles(path))).toBe(true);
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:40:    const roles = ["admissions_manager"];
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:41:    expect(canAccess(roles, getAllowedRoles("/onboarding"))).toBe(true);
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:42:    expect(canAccess(roles, getAllowedRoles("/reenrollment"))).toBe(false);
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:43:    expect(canAccess(roles, getAllowedRoles("/aid-setup"))).toBe(false);
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:44:    expect(canAccess(roles, getAllowedRoles("/enrollment-conversion"))).toBe(true);
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:45:    expect(canAccess(roles, getAllowedRoles("/enrollment-period-setup"))).toBe(false);
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:49:    const roles = ["finance_admin"];
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:50:    expect(canAccess(roles, getAllowedRoles("/onboarding"))).toBe(false);
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:51:    expect(canAccess(roles, getAllowedRoles("/reenrollment"))).toBe(false);
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:52:    expect(canAccess(roles, getAllowedRoles("/aid-setup"))).toBe(true);
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:53:    expect(canAccess(roles, getAllowedRoles("/enrollment-conversion"))).toBe(false);
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:54:    expect(canAccess(roles, getAllowedRoles("/enrollment-period-setup"))).toBe(false);
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:58:    const roles = ["registrar"];
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:59:    expect(canAccess(roles, getAllowedRoles("/onboarding"))).toBe(false);
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:60:    expect(canAccess(roles, getAllowedRoles("/reenrollment"))).toBe(true);
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:61:    expect(canAccess(roles, getAllowedRoles("/aid-setup"))).toBe(false);
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:62:    expect(canAccess(roles, getAllowedRoles("/enrollment-conversion"))).toBe(true);
frontend/dashboards/src\routes\wizardRouteAccess.test.jsx:63:    expect(canAccess(roles, getAllowedRoles("/enrollment-period-setup"))).toBe(true);
frontend/dashboards/src\entitlements\useEntitlements.ts:4: * React hook that fetches the entitlement snapshot for the current tenant
frontend/dashboards/src\routes\router.jsx:65:import RoleGuard from "./RoleGuard.jsx";
frontend/dashboards/src\routes\router.jsx:67:import { APP_PERMISSIONS } from "../auth/permissions";
frontend/dashboards/src\routes\router.jsx:146:    // Unified role dashboard ∩┐╜ /dash/admin, /dash/teacher, /dash/parent, etc.
frontend/dashboards/src\routes\router.jsx:170:      <RequirePermission permission={APP_PERMISSIONS.BILLING_VIEW}>
frontend/dashboards/src\routes\router.jsx:187:      <RequirePermission permission={APP_PERMISSIONS.BILLING_VIEW}>
frontend/dashboards/src\routes\router.jsx:250:      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
frontend/dashboards/src\routes\router.jsx:252:      </RoleGuard>
frontend/dashboards/src\routes\router.jsx:278:      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
frontend/dashboards/src\routes\router.jsx:280:      </RoleGuard>
frontend/dashboards/src\routes\router.jsx:286:      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
frontend/dashboards/src\routes\router.jsx:288:      </RoleGuard>
frontend/dashboards/src\routes\router.jsx:294:      <RoleGuard allowedRoles={[...ROLE_GROUPS.ACADEMIC_TEAM, ...ROLE_GROUPS.FAMILY_VIEW]}>
frontend/dashboards/src\routes\router.jsx:296:      </RoleGuard>
frontend/dashboards/src\routes\router.jsx:302:      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
frontend/dashboards/src\routes\router.jsx:304:      </RoleGuard>
frontend/dashboards/src\routes\router.jsx:351:      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
frontend/dashboards/src\routes\router.jsx:353:      </RoleGuard>
frontend/dashboards/src\routes\router.jsx:359:      <RoleGuard allowedRoles={[...ROLE_GROUPS.ACADEMIC_TEAM, ...ROLE_GROUPS.FAMILY_VIEW]}>
frontend/dashboards/src\routes\router.jsx:361:      </RoleGuard>
frontend/dashboards/src\routes\router.jsx:367:      <RoleGuard allowedRoles={ROLE_GROUPS.FAMILY_VIEW}>
frontend/dashboards/src\routes\router.jsx:369:      </RoleGuard>
frontend/dashboards/src\routes\router.jsx:383:      <RequirePermission permission={APP_PERMISSIONS.REPORTING_VIEW}>
frontend/dashboards/src\routes\router.jsx:467:      <RequirePermission permission={APP_PERMISSIONS.SYSTEM_VIEW}>
frontend/dashboards/src\routes\router.jsx:475:      <RequirePermission permission={APP_PERMISSIONS.RELEASE_VIEW}>
frontend/dashboards/src\routes\router.jsx:483:      <RequirePermission permission={APP_PERMISSIONS.DEMO_VIEW}>
frontend/dashboards/src\entitlements\entitlements.ts:27:  IDENTITY_RBAC: "identity.rbac",
frontend/dashboards/src\entitlements\EntitlementGate.tsx:5: * for the current tenant.
frontend/dashboards/src\routes\roleGuardRules.js:1:export function isRoleAllowed(role, allowedRoles = []) {
frontend/dashboards/src\routes\roleGuardRules.js:8:  return normalizedAllowed.includes(String(role || 'guest').trim().toLowerCase());
backend\aftercare\models.py:27:    Per-tenant configuration ΓÇö set via CrownMagus Aftercare Setup Wizard.
frontend/dashboards/src\api\enrollment_conversion_wizard.js:13:    "X-School-Id": getSchoolId(),
frontend/dashboards/src\routes\RoleGuard.jsx:4:import { isRoleAllowed } from './roleGuardRules';
frontend/dashboards/src\routes\RoleGuard.jsx:6:export default function RoleGuard({ allowedRoles = [], children }) {
frontend/dashboards/src\routes\RoleGuard.jsx:7:  const role = useCurrentUserRole();
frontend/dashboards/src\routes\RoleGuard.jsx:10:  if (!isRoleAllowed(role, allowedRoles)) {
frontend/dashboards/src\routes\RoleGuard.jsx:17:          role,
frontend/dashboards/src\api\dashboards.js:18:function _headers(schoolId, role) {
frontend/dashboards/src\api\dashboards.js:25:  if (sid) h["X-School-Id"] = sid;
frontend/dashboards/src\api\dashboards.js:27:  // Demo/dev role override (only active when server allows ALLOW_DEMO_ROLE_HEADER=1)
frontend/dashboards/src\api\dashboards.js:28:  if (role) h["X-Demo-Role"] = role;
frontend/dashboards/src\api\dashboards.js:34: * Returns { school_id, display_name, roles, default_route, features }
frontend/dashboards/src\api\dashboards.js:36:export async function fetchDashboardMe(schoolId, role) {
frontend/dashboards/src\api\dashboards.js:40:    headers: _headers(schoolId, role),
frontend/dashboards/src\api\dashboards.js:46: * Returns { role, school_id, generated_at, widgets: DashboardWidget[] }
frontend/dashboards/src\api\dashboards.js:48:export async function fetchDashboardSummary(schoolId, role) {
frontend/dashboards/src\api\dashboards.js:52:    headers: _headers(schoolId, role),
frontend/dashboards/src\api\dashboards.js:60:export async function fetchDashboardDrilldown(widgetKey, schoolId, role) {
frontend/dashboards/src\api\dashboards.js:65:    headers: _headers(schoolId, role),
frontend/dashboards/src\api\dashboards.js:73:export async function fetchDashboardAlerts(schoolId, role) {
frontend/dashboards/src\api\dashboards.js:77:    headers: _headers(schoolId, role),
frontend/dashboards/src\api\dashboardClient.js:122:  const tenantId = getTenantId();
frontend/dashboards/src\api\dashboardClient.js:134:  if (tenantId) {
frontend/dashboards/src\api\dashboardClient.js:135:    mergedHeaders['X-School-Id'] = tenantId;
frontend/dashboards/src\routes\paths.js:5:  ROLE_DASHBOARD: '/dash/:role',
frontend/dashboards/src\api\curriculum.js:21:    "X-School-Id": schoolId,
frontend/dashboards/src\routes\financeRouteAccess.test.jsx:27:  return userRoles.some((role) => allowedRoles.includes(role));
frontend/dashboards/src\routes\financeRouteAccess.test.jsx:32:    const roles = ["school_admin"];
frontend/dashboards/src\routes\financeRouteAccess.test.jsx:34:      expect(canAccess(roles, route.allowedRoles)).toBe(true);
frontend/dashboards/src\routes\financeRouteAccess.test.jsx:39:    const roles = ["finance_admin"];
frontend/dashboards/src\routes\financeRouteAccess.test.jsx:41:      expect(canAccess(roles, route.allowedRoles)).toBe(true);
frontend/dashboards/src\routes\financeRouteAccess.test.jsx:46:    const roles = ["admissions_team"];
frontend/dashboards/src\routes\financeRouteAccess.test.jsx:48:      expect(canAccess(roles, route.allowedRoles)).toBe(false);
frontend/dashboards/src\routes\financeRouteAccess.test.jsx:52:  it("blocks parent and student roles from finance routes", () => {
frontend/dashboards/src\routes\dashboardRoutes.jsx:11:      <RoleRouteGuard allowedRoles={dashboard.roles || dashboard.allowedRoles || []}>
frontend/dashboards/src\routes\compuwerxRouteAccess.test.jsx:9:  return userRoles.some((role) => allowedRoles.includes(role));
frontend/dashboards/src\routes\compuwerxPackage4RouteAccess.test.jsx:6:  return userRoles.some((role) => allowedRoles.includes(role));
frontend/dashboards/src\routes\compuwerxPackage3RouteAccess.test.jsx:12:  return userRoles.some((role) => allowedRoles.includes(role));
frontend/dashboards/src\routes\compuwerxOpsRouteAccess.test.jsx:19:  return userRoles.some((role) => allowedRoles.includes(role));
frontend/dashboards/src\api\client.js:63:  if (schoolId && !nextConfig.headers['X-School-Id']) {
frontend/dashboards/src\api\client.js:64:    nextConfig.headers['X-School-Id'] = schoolId;
frontend/dashboards/src\api\classrooms.js:7:  if (schoolId) headers["X-School-Id"] = schoolId;
frontend/dashboards/src\api\bell_schedule_wizard.js:13:    "X-School-Id": getSchoolId(),
frontend/dashboards/src\api\attendance_rules_wizard.js:13:    "X-School-Id": getSchoolId(),
frontend/dashboards/src\api\attendance_codes_wizard.js:14:    "X-School-Id": getSchoolId(),
backend\aftercare\migrations\0002_add_uuid_fks.py:24:        ("core", "0005_crown_permission_engine"),
frontend/dashboards/src\api\aftercareApi.js:85:      ...(schoolId ? { "X-School-Id": String(schoolId) } : {}),
backend\advancement\tests\test_advancement_stage3_4.py:33:    UserRole.objects.create(school=school, user=user, role_code="HEAD_OF_SCHOOL")
backend\advancement\tests\test_advancement_stage3_4.py:38:    RolePermission.objects.get_or_create(role_code="HEAD_OF_SCHOOL", permission=perm)
backend\advancement\tests\test_advancement_stage3.py:7:  3.  transition_move_stage raises Prospect.DoesNotExist on wrong school_id (tenant isolation)
backend\advancement\tests\test_advancement_stage3.py:22: 18.  Prospect tenant isolation ΓÇö school A cannot see school B prospects via queryset
backend\advancement\tests\test_advancement_stage3.py:503:# 18: Prospect tenant isolation
backend\advancement\tests\test_advancement_stage2.py:21: 17.  Gift tenant isolation ΓÇö school A cannot see school B gifts
backend\advancement\tests\test_advancement_stage2.py:22: 18.  Pledge tenant isolation
backend\advancement\tests\test_advancement_stage2.py:23: 19.  SponsorshipAgreement tenant isolation
backend\advancement\tests\test_advancement_stage2.py:203:    def test_gift_tenant_isolation(self):
backend\advancement\tests\test_advancement_stage2.py:252:    def test_pledge_tenant_isolation(self):
backend\advancement\tests\test_advancement_stage2.py:320:    def test_agreement_tenant_isolation(self):
backend\advancement\tests\test_advancement_stage1.py:5:  1. Tenant isolation ΓÇö data from school A not visible to school B
backend\advancement\tests\test_advancement_stage1.py:41:    """Stable UUID per integer for repeatable test isolation."""
backend\advancement\tests\test_advancement_stage1.py:88:# Test: Tenant isolation
backend\analytics\api_health.py:13:from rest_framework.decorators import api_view, permission_classes
backend\analytics\api_health.py:14:from rest_framework.permissions import IsAuthenticated, AllowAny
backend\analytics\api_health.py:26:@permission_classes([IsAuthenticated])
backend\analytics\api_health.py:42:@permission_classes([IsAuthenticated])
backend\analytics\api_health.py:61:@permission_classes([AllowAny])
backend\enrollment_conversion_wizard\views.py:5:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\enrollment_conversion_wizard\views.py:6:from rest_framework.permissions import IsAuthenticated
backend\enrollment_conversion_wizard\views.py:14:from .permissions import require_enrollment_conversion_access
backend\enrollment_conversion_wizard\views.py:38:@permission_classes(_PERM)
backend\enrollment_conversion_wizard\views.py:62:@permission_classes(_PERM)
backend\enrollment_conversion_wizard\views.py:101:@permission_classes(_PERM)
backend\enrollment_conversion_wizard\views.py:143:@permission_classes(_PERM)
backend\enrollment_conversion_wizard\views.py:184:@permission_classes(_PERM)
backend\transportation\tests\test_transportation.py:7:  - Permission enforcement (unauthenticated, read-only role, transport director/admin)
backend\transportation\tests\test_transportation.py:10:  - Cross-tenant isolation
backend\transportation\tests\test_transportation.py:50:def _client(user, school: School, role: str = "transportation_director") -> APIClient:
backend\transportation\tests\test_transportation.py:53:    c.credentials(HTTP_X_SCHOOL_ID=str(school.id), HTTP_X_ROLE=role)
backend\transportation\tests\test_transportation.py:111:    def test_create_denied_for_readonly_role(self):
backend\transportation\tests\test_transportation.py:114:        resp = _client(u, s, role="teacher").post(self.URL, {"name": "X", "vehicle_type": "BUS"}, format="json")
backend\transportation\tests\test_transportation.py:138:    def test_cross_tenant_isolation(self):
backend\transportation\tests\test_transportation.py:185:    def test_cross_tenant(self):
backend\transportation\tests\test_transportation.py:195:    def test_readonly_role_can_list(self):
backend\transportation\tests\test_transportation.py:199:        resp = _client(u, s, role="teacher").get(self.URL)
backend\transportation\tests\test_transportation.py:240:    def test_stops_action_cross_tenant_denied(self):
backend\transportation\tests\test_transportation.py:248:    def test_cross_tenant(self):
backend\transportation\tests\test_transportation.py:287:    def test_cross_tenant(self):
backend\transportation\tests\test_transportation.py:338:    def test_cross_tenant(self):
backend\transportation\tests\test_transportation.py:384:    def test_cross_tenant(self):
backend\transportation\tests\test_transportation.py:442:    def test_cross_tenant(self):
backend\transportation\tests\test_transportation.py:492:    def test_run_sheet_cross_tenant(self):
backend\transportation\tests\test_transportation.py:528:    def test_non_transport_role_cannot_create_vehicle(self):
backend\transportation\tests\test_transportation.py:531:        c = _client(u, s, role="counselor")
backend\transportation\tests\test_transportation.py:535:    def test_admin_role_can_create_vehicle(self):
backend\transportation\tests\test_transportation.py:538:        resp = _client(u, s, role="admin").post(
backend\transportation\tests\test_transportation.py:545:    def test_ops_role_can_create_driver(self):
backend\transportation\tests\test_transportation.py:548:        resp = _client(u, s, role="ops").post(
backend\transportation\tests\test_transportation.py:558:        resp = _client(u, s, role="teacher").get("/api/transportation/routes/")
backend\aftercare\api.py:9:from core.permissions import user_has_permission
backend\aftercare\api.py:24:from .tenant import school_id_from_request
backend\aftercare\api.py:77:def require_role(request, allowed_roles: set) -> bool:
backend\aftercare\api.py:86:    normalized = {str(role).lower() for role in allowed_roles}
backend\aftercare\api.py:88:    if "board" in normalized and user_has_permission(user, "board.view", school=school):
backend\aftercare\api.py:92:        if user_has_permission(user, "aftercare.edit", school=school):
backend\aftercare\api.py:94:        if user_has_permission(user, "aftercare.view", school=school):
backend\aftercare\api.py:115:    if not require_role(request, {"admin"}):
backend\aftercare\api.py:140:    if not require_role(request, {"admin"}):
backend\aftercare\api.py:166:    if not require_role(request, {"admin", "aftercare_staff"}):
backend\aftercare\api.py:180:    if not require_role(request, {"admin", "aftercare_staff"}):
backend\aftercare\api.py:220:    if not require_role(request, {"admin", "aftercare_staff"}):
backend\aftercare\api.py:243:    if not require_role(request, {"admin", "aftercare_staff"}):
backend\aftercare\api.py:271:    if not require_role(request, {"admin", "aftercare_staff"}):
backend\aftercare\api.py:299:    if not require_role(request, {"admin", "aftercare_staff", "board"}):
backend\aftercare\api.py:322:    if not require_role(request, {"board", "admin"}):
backend\enrollment_conversion_wizard\tests\test_views.py:28:def _grant_enrollment_conversion_access(user, school, role_code="REGISTRAR"):
backend\enrollment_conversion_wizard\tests\test_views.py:29:    UserRole.objects.create(user=user, school=school, role_code=role_code)
backend\enrollment_conversion_wizard\tests\test_views.py:34:    RolePermission.objects.get_or_create(role_code=role_code, permission=perm)
backend\enrollment_conversion_wizard\tests\test_views.py:118:    def test_create_forbidden_without_role_permission(self):
backend\advancement\models_stage3.py:6:  - school_id = UUIDField(db_index=True)  (no FK to School ΓÇö tenant filter pattern)
backend\enrollment_conversion_wizard\permissions.py:3:from core.permissions import user_has_permission
backend\enrollment_conversion_wizard\permissions.py:12:	return user_has_permission(user, "admissions.edit", school=school) or user_has_permission(
backend\aid\tests\test_aid_api.py:56:    """Staff user with school=None; bypasses cross-tenant check."""
backend\aid\tests\test_aid_api.py:182:    def test_tenant_isolation_different_school_data_not_returned(self):
backend\aid\migrations\0003_phase75_policy_budget_engine_fields.py:12:        ('core', '0005_crown_permission_engine'),
backend\enrollment_conversion_wizard\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
backend\transportation\migrations\0001_initial.py:13:        ('core', '0005_crown_permission_engine'),
frontend/dashboards/src\config\dashboardTemplates\admissionsDashboard.js:31:    role: 'Admissions Manager',
frontend/dashboards/src\config\dashboardTemplates\activitiesAthleticsDashboard.js:19:  user: { initials: 'AA', name: 'Activities & Athletics', role: 'Student Life ΓÇö Activities & Athletic Programs' },
frontend/dashboards/src\config\dashboardTemplates\activitiesAthleticsDashboard.js:29:    { label: 'Clearances Pending', value: '12', detail: '9 physicals, 3 permission slips outstanding.', accent: 'navy' },
frontend/dashboards/src\config\dashboardTemplates\activitiesAthleticsDashboard.js:33:    { title: 'Resolve 12 outstanding clearances', detail: '9 physicals, 3 permission slips ΓÇö students cannot compete.', state: 'Today', tone: 'warn' },
frontend/dashboards/src\config\dashboardTemplates\activitiesAthleticsDashboard.js:52:      mainKpi: '12 clearances outstanding', summary: '9 physicals + 3 permission slips ΓÇö must resolve today.',
frontend/dashboards/src\config\dashboardTemplates\activitiesAthleticsDashboard.js:54:      details: ['9 student physicals expired or not on file', '3 permission slips not returned', 'All 12 students currently ineligible to compete', 'Families notified via portal'],
frontend/dashboards/src\config\dashboardRegistry.test.js:20:  it('has at least one allowed role for each dashboard', () => {
frontend/dashboards/src\config\dashboardRegistry.test.js:34:  it('normalizes role aliases used across backend and frontend role vocabularies', () => {
frontend/dashboards/src\config\dashboardRegistry.test.js:40:  it('grants access when role aliases match equivalent roles', () => {
frontend/dashboards/src\config\dashboardRegistry.js:2:import { normalizeRoles as normalizeEffectiveRoles } from '../auth/roleAccess';
frontend/dashboards/src\config\dashboardRegistry.js:114:  roles,
frontend/dashboards/src\config\dashboardRegistry.js:133:    allowedRoles: allowedRoles || roles || [],
frontend/dashboards/src\config\dashboardRegistry.js:134:    roles: roles || allowedRoles || [],
frontend/dashboards/src\config\dashboardRegistry.js:532:  return normalizedAllowedRoles.some((role) => normalizedUserRoles.includes(role));
backend\aid\api_views.py:10:from rest_framework.decorators import api_view, permission_classes
backend\aid\api_views.py:11:from rest_framework.permissions import IsAuthenticated
backend\aid\api_views.py:46:@permission_classes([IsAuthenticated])
backend\aid\api_views.py:146:@permission_classes([IsAuthenticated])
backend\aid\api_views.py:208:@permission_classes([IsAuthenticated])
backend\aid\api_views.py:264:@permission_classes([IsAuthenticated])
backend\aid\api_views.py:270:    Required header:       X-School-Id (tenant UUID)
backend\aid\api_views.py:299:@permission_classes([IsAuthenticated])
backend\aid\api_views.py:309:    Required header: X-School-Id
backend\aid\api_views.py:373:@permission_classes([IsAuthenticated])
backend\aid\api_views.py:380:    Required header: X-School-Id
backend\aid\api_views.py:413:@permission_classes([IsAuthenticated])
backend\aid\api_views.py:421:    Required header: X-School-Id
frontend/dashboards/src\config\apiContracts.js:1:import { APP_PERMISSIONS } from '../auth/permissions';
frontend/dashboards/src\config\apiContracts.js:8:    permission: APP_PERMISSIONS.ADMISSIONS_VIEW,
frontend/dashboards/src\config\apiContracts.js:15:    permission: APP_PERMISSIONS.ENROLLMENT_EDIT,
frontend/dashboards/src\config\apiContracts.js:22:    permission: APP_PERMISSIONS.BILLING_VIEW,
frontend/dashboards/src\config\apiContracts.js:29:    permission: APP_PERMISSIONS.COMMUNICATIONS_VIEW,
frontend/dashboards/src\config\apiContracts.js:36:    permission: APP_PERMISSIONS.COMMUNICATIONS_VIEW,
frontend/dashboards/src\config\apiContracts.js:43:    permission: APP_PERMISSIONS.SYSTEM_VIEW,
frontend/dashboards/src\config\dashboardTemplates\billingDashboard.js:19:  user: { initials: 'BL', name: 'Billing Team', role: 'Finance ΓÇö Billing & Collections' },
backend\transportation\api\views.py:6:from rest_framework.permissions import IsAuthenticated
backend\transportation\api\views.py:20:from transportation.api.permissions import IsTransportationStaffOrReadOnly
backend\transportation\api\views.py:38:    permission_classes = [IsAuthenticated, IsTransportationStaffOrReadOnly]
backend\transportation\api\views.py:164:    permission_classes = [IsAuthenticated, IsTransportationStaffOrReadOnly]
frontend/dashboards/src\config\dashboardTemplates\athleticsDashboard.js:17:  user: { initials: 'AD', name: 'Athletic Director', role: 'Athletics ΓÇö Teams & Compliance' },
frontend/dashboards/src\config\dashboardTemplates\alumniRelationsDashboard.js:19:  user: { initials: 'AR', name: 'Alumni Relations', role: 'Advancement ΓÇö Alumni Engagement & Giving Programs' },
frontend/dashboards/src\components\BoardTrends.jsx:8: *   schoolId (string) ΓÇö injected via X-School-Id header by apiFetch
frontend/dashboards/src\components\BoardTrends.jsx:32:  if (error) return <div role="alert">Failed to load trends: {error}</div>;
frontend/dashboards/src\config\dashboardTemplates\advancementOperationsDashboard.js:19:  user: { initials: 'AO', name: 'Advancement Operations', role: 'Advancement ΓÇö Fundraising Operations & Donor Relations' },
frontend/dashboards/src\config\dashboardTemplates\advancementDashboard.js:19:  user: { initials: 'AV', name: 'Advancement Office', role: 'Development ΓÇö Fundraising & Donor Relations' },
frontend/dashboards/src\components\auth\RequirePermission.jsx:5:export default function RequirePermission({ permission, anyOf = [], children }) {
frontend/dashboards/src\components\auth\RequirePermission.jsx:10:    permission ? hasPermission(permission) : anyOf.length ? hasAnyPermission(anyOf) : true;
frontend/dashboards/src\components\auth\RequirePermission.jsx:19:          permission,
frontend/dashboards/src\components\AutoLoginGate.jsx:19:        const ROLE_KEY = "crown.role";
frontend/dashboards/src\components\AutoLoginGate.jsx:28:          role: import.meta.env.VITE_DEMO_ROLE || "school_admin",
frontend/dashboards/src\components\AutoLoginGate.jsx:29:          roleKey: ROLE_KEY,
frontend/dashboards/src\components\FinanceKPI.jsx:13: *   schoolId  (string)  ΓÇö required, passed as X-School-Id header via apiFetch
frontend/dashboards/src\components\FinanceKPI.jsx:53:      <div className={`finance-kpi-card finance-kpi-card--error ${className}`} role="alert">
backend\transportation\api\permissions.py:1:# backend/transportation/api/permissions.py
backend\transportation\api\permissions.py:2:from rest_framework.permissions import BasePermission
backend\transportation\api\permissions.py:12:    def has_permission(self, request, view):
backend\transportation\api\permissions.py:20:        role = request.META.get("HTTP_X_ROLE", "")
backend\transportation\api\permissions.py:21:        return role in TRANSPORT_WRITE_ROLES
frontend/dashboards/src\components\exports\ExportButton.tsx:70:          "X-School-Id": schoolId || "",
frontend/dashboards/src\components\exports\BulkExportMenu.tsx:46:          "X-School-Id": schoolId || ""
frontend/dashboards/src\components\ui\ErrorBanner.jsx:8:      role="alert"
backend\tests_list.txt:38:backend/academic_year_wizard/tests/test_views.py::AcademicYearSingleCurrentTest::test_cross_tenant_year_not_affected
backend\tests_list.txt:122:backend/advancement/tests/test_advancement_stage2.py::GiftCheckoutTest::test_gift_tenant_isolation
backend\tests_list.txt:131:backend/advancement/tests/test_advancement_stage2.py::PledgeTest::test_pledge_tenant_isolation
backend\tests_list.txt:132:backend/advancement/tests/test_advancement_stage2.py::SponsorshipAgreementTest::test_agreement_tenant_isolation
backend\tests_list.txt:226:backend/aftercare/tests/test_aftercare_tenant_scoping.py::test_attendance_unique_per_student_day_per_school
backend\tests_list.txt:227:backend/aftercare/tests/test_aftercare_tenant_scoping.py::test_attendance_duplicate_same_school_raises
backend\tests_list.txt:228:backend/aftercare/tests/test_aftercare_tenant_scoping.py::test_enrollment_scoped_by_school_id
backend\tests_list.txt:233:backend/aid/tests/test_aid_api.py::TestAdminAidOverview::test_tenant_isolation_different_school_data_not_returned
backend\tests_list.txt:304:backend/applications/tests/test_admissions_tenant_scoping.py::AdmissionsTenantScopingTests::test_drilldown_cross_tenant_header_is_403
backend\tests_list.txt:305:backend/applications/tests/test_admissions_tenant_scoping.py::AdmissionsTenantScopingTests::test_drilldown_own_school_is_200
backend\tests_list.txt:306:backend/applications/tests/test_admissions_tenant_scoping.py::AdmissionsTenantScopingTests::test_summary_cross_tenant_header_is_403
backend\tests_list.txt:307:backend/applications/tests/test_admissions_tenant_scoping.py::AdmissionsTenantScopingTests::test_summary_own_school_is_200
backend\tests_list.txt:308:backend/applications/tests/test_admissions_tenant_scoping.py::AdmissionsTenantScopingTests::test_summary_unauthenticated_is_401
backend\tests_list.txt:353:backend/athletics/tests/test_athletics.py::TestTenantIsolation::test_season_cross_tenant_hidden
backend\tests_list.txt:354:backend/athletics/tests/test_athletics.py::TestTenantIsolation::test_event_cross_tenant_hidden
backend\tests_list.txt:365:backend/attendance_codes_wizard/tests/test_views.py::TestAttendanceCodesWizardTenantIsolation::test_cross_tenant_returns_404
backend\tests_list.txt:416:backend/bell_schedule_wizard/tests/test_views.py::BellScheduleSnapshotTest::test_cross_tenant_isolation
backend\tests_list.txt:431:backend/billing_wizard/tests/test_views.py::TestTenantIsolation::test_commit_isolation
backend\tests_list.txt:432:backend/billing_wizard/tests/test_views.py::TestTenantIsolation::test_configure_isolation
backend\tests_list.txt:433:backend/billing_wizard/tests/test_views.py::TestTenantIsolation::test_fees_isolation
backend\tests_list.txt:434:backend/billing_wizard/tests/test_views.py::TestTenantIsolation::test_plans_isolation
backend\tests_list.txt:435:backend/billing_wizard/tests/test_views.py::TestTenantIsolation::test_verify_isolation
backend\tests_list.txt:470:backend/board_oversight/tests/test_board_rbac.py::test_non_board_user_forbidden
backend\tests_list.txt:471:backend/board_oversight/tests/test_board_tenant_required.py::test_missing_school_id_rejected
backend\tests_list.txt:477:backend/comms_wizard/tests/test_views.py::TestTenantIsolation::test_commit_isolation
backend\tests_list.txt:478:backend/comms_wizard/tests/test_views.py::TestTenantIsolation::test_configure_isolation
backend\tests_list.txt:479:backend/comms_wizard/tests/test_views.py::TestTenantIsolation::test_message_isolation
backend\tests_list.txt:480:backend/comms_wizard/tests/test_views.py::TestTenantIsolation::test_recipients_isolation
backend\tests_list.txt:481:backend/comms_wizard/tests/test_views.py::TestTenantIsolation::test_verify_isolation
backend\tests_list.txt:512:backend/core/tests/test_nav_endpoint.py::TestNavPermissionFiltering::test_finance_role_sees_finance_and_billing_not_admissions
backend\tests_list.txt:514:backend/core/tests/test_nav_endpoint.py::TestNavPermissionFiltering::test_user_with_no_roles_sees_empty_nav
backend\tests_list.txt:519:backend/core/tests/test_nav_endpoint.py::TestNavResponseShape::test_school_scoping_cross_tenant_isolation
backend\tests_list.txt:520:backend/core/tests/test_permission_engine.py::TestUserHasPermission::test_returns_true_when_role_granted
backend\tests_list.txt:521:backend/core/tests/test_permission_engine.py::TestUserHasPermission::test_returns_false_when_role_not_granted
backend\tests_list.txt:522:backend/core/tests/test_permission_engine.py::TestUserHasPermission::test_returns_false_for_nonexistent_permission
backend\tests_list.txt:523:backend/core/tests/test_permission_engine.py::TestUserHasPermission::test_returns_false_when_user_has_no_roles
backend\tests_list.txt:524:backend/core/tests/test_permission_engine.py::TestUserHasPermission::test_returns_false_for_unauthenticated_user
backend\tests_list.txt:525:backend/core/tests/test_permission_engine.py::TestUserHasPermissionSchoolScoping::test_scoped_to_correct_school_returns_true
backend\tests_list.txt:526:backend/core/tests/test_permission_engine.py::TestUserHasPermissionSchoolScoping::test_scoped_to_wrong_school_returns_false
backend\tests_list.txt:527:backend/core/tests/test_permission_engine.py::TestUserHasPermissionSchoolScoping::test_unscoped_query_crosses_schools
backend\tests_list.txt:528:backend/core/tests/test_permission_engine.py::TestRequirePermissionDecorator::test_allows_request_when_permission_granted
backend\tests_list.txt:529:backend/core/tests/test_permission_engine.py::TestRequirePermissionDecorator::test_denies_request_when_permission_missing
backend\tests_list.txt:530:backend/core/tests/test_permission_engine.py::TestRequirePermissionDecorator::test_denies_anonymous_user
backend\tests_list.txt:531:backend/core/tests/test_permission_engine.py::TestRequirePermissionDecorator::test_403_response_body_is_json
backend\tests_list.txt:532:backend/core/tests/test_permission_engine.py::TestRequirePermissionDecorator::test_no_request_school_attribute_does_not_crash
backend\tests_list.txt:533:backend/core/tests/test_permission_engine.py::TestPermissionModelConstraints::test_crown_permission_code_is_unique
backend\tests_list.txt:534:backend/core/tests/test_permission_engine.py::TestPermissionModelConstraints::test_role_permission_unique_together
backend\tests_list.txt:535:backend/core/tests/test_permission_engine.py::TestPermissionModelConstraints::test_crown_permission_str
backend\tests_list.txt:536:backend/core/tests/test_permission_engine.py::TestPermissionModelConstraints::test_role_permission_str
backend\tests_list.txt:537:backend/core/tests/test_permission_engine.py::TestSeedPermissionsCommand::test_seed_creates_permissions
backend\tests_list.txt:538:backend/core/tests/test_permission_engine.py::TestSeedPermissionsCommand::test_seed_creates_role_mappings
backend\tests_list.txt:539:backend/core/tests/test_permission_engine.py::TestSeedPermissionsCommand::test_seed_is_idempotent
backend\tests_list.txt:540:backend/core/tests/test_permission_engine.py::TestSeedPermissionsCommand::test_seed_dry_run_creates_nothing
backend\tests_list.txt:541:backend/core/tests/test_rbac_contract.py::test_requires_auth_for_invariants
backend\tests_list.txt:542:backend/core/tests/test_rbac_contract.py::test_requires_tenant_header_for_invariants
backend\tests_list.txt:543:backend/core/tests/test_rbac_contract.py::test_invariants_role_matrix[FINANCE_DIRECTOR-200]
backend\tests_list.txt:544:backend/core/tests/test_rbac_contract.py::test_invariants_role_matrix[HEAD_OF_SCHOOL-200]
backend\tests_list.txt:545:backend/core/tests/test_rbac_contract.py::test_invariants_role_matrix[TEACHER-403]
backend\tests_list.txt:546:backend/core/tests/test_rbac_contract.py::test_invariants_role_matrix[PARENT-403]
backend\tests_list.txt:547:backend/core/tests/test_rbac_contract.py::test_invariants_role_matrix[STUDENT-403]
backend\tests_list.txt:567:backend/crown_api/billing_api/tests/test_payments_record_api.py::test_record_payment_requires_finance_role
backend\tests_list.txt:572:backend/crown_api/billing_api/tests/test_payments_record_multi_alloc_api.py::test_record_payment_multi_allocation_requires_finance_role_403
backend\tests_list.txt:579:backend/crown_api/exports/tests/test_exports_accounting_qb_csv.py::test_payments_qb_csv_requires_finance_role
backend\tests_list.txt:585:backend/crown_api/exports/tests/test_exports_csv.py::test_exports_invoices_csv_requires_finance_role
backend\tests_list.txt:586:backend/crown_api/exports/tests/test_exports_csv.py::test_exports_installment_schedule_csv_requires_finance_role
backend\tests_list.txt:592:backend/crown_api/exports/tests/test_exports_financial_csv.py::test_ledger_charges_csv_requires_finance_role
backend\tests_list.txt:593:backend/crown_api/exports/tests/test_exports_financial_csv.py::test_ledger_allocations_csv_requires_finance_role
backend\tests_list.txt:594:backend/crown_api/exports/tests/test_exports_financial_csv.py::test_payments_csv_requires_finance_role
backend\tests_list.txt:598:backend/crown_api/exports/tests/test_exports_jwt_auth.py::test_financial_export_allows_jwt_for_finance_role
backend\tests_list.txt:606:backend/crown_api/exports/tests/test_exports_statement_lines_csv.py::test_statement_lines_csv_requires_finance_role
backend\tests_list.txt:609:backend/crown_api/exports/tests/test_exports_statements_csv.py::test_statements_csv_requires_finance_role
backend\tests_list.txt:613:backend/crown_api/exports/tests/test_exports_year_end_csv.py::test_year_end_tuition_paid_csv_requires_finance_role
backend\tests_list.txt:626:backend/crown_api/tests/test_attendance_tenant_invariants.py::AttendanceTenantInvariantTests::test_cross_tenant_section_returns_404
backend\tests_list.txt:627:backend/crown_api/tests/test_attendance_tenant_invariants.py::AttendanceTenantInvariantTests::test_cross_tenant_student_returns_404
backend\tests_list.txt:628:backend/crown_api/tests/test_attendance_tenant_invariants.py::AttendanceTenantInvariantTests::test_missing_school_header_returns_400
backend\tests_list.txt:629:backend/crown_api/tests/test_attendance_tenant_invariants.py::AttendanceTenantInvariantTests::test_valid_same_tenant_request_returns_200
backend\tests_list.txt:640:backend/crown_api/tests/test_audit_proof.py::test_audit_recent_forbidden_without_role
backend\tests_list.txt:660:backend/crown_api/tests/test_dashboard_tenant_isolation.py::DashboardTenantIsolationTests::test_academics_enrollment_correct_tenant_returns_200
backend\tests_list.txt:661:backend/crown_api/tests/test_dashboard_tenant_isolation.py::DashboardTenantIsolationTests::test_academics_enrollment_missing_tenant_returns_400
backend\tests_list.txt:662:backend/crown_api/tests/test_dashboard_tenant_isolation.py::DashboardTenantIsolationTests::test_academics_enrollment_wrong_tenant_no_leak
backend\tests_list.txt:663:backend/crown_api/tests/test_dashboard_tenant_isolation.py::DashboardTenantIsolationTests::test_admissions_funnel_correct_tenant_returns_200
backend\tests_list.txt:664:backend/crown_api/tests/test_dashboard_tenant_isolation.py::DashboardTenantIsolationTests::test_admissions_funnel_invalid_uuid_returns_400
backend\tests_list.txt:665:backend/crown_api/tests/test_dashboard_tenant_isolation.py::DashboardTenantIsolationTests::test_admissions_funnel_missing_tenant_returns_400
backend\tests_list.txt:666:backend/crown_api/tests/test_dashboard_tenant_isolation.py::DashboardTenantIsolationTests::test_admissions_funnel_nonexistent_school_returns_404
backend\tests_list.txt:667:backend/crown_api/tests/test_dashboard_tenant_isolation.py::DashboardTenantIsolationTests::test_admissions_funnel_wrong_tenant_returns_empty
backend\tests_list.txt:668:backend/crown_api/tests/test_dashboard_tenant_isolation.py::DashboardTenantIsolationTests::test_finance_summary_correct_tenant_returns_200
backend\tests_list.txt:669:backend/crown_api/tests/test_dashboard_tenant_isolation.py::DashboardTenantIsolationTests::test_finance_summary_missing_tenant_returns_400
backend\tests_list.txt:670:backend/crown_api/tests/test_dashboard_tenant_isolation.py::DashboardTenantIsolationTests::test_finance_summary_wrong_tenant_no_leak
backend\tests_list.txt:671:backend/crown_api/tests/test_dashboards_role_contract.py::test_unauthenticated_returns_401[/api/dashboards/me/]
backend\tests_list.txt:672:backend/crown_api/tests/test_dashboards_role_contract.py::test_unauthenticated_returns_401[/api/dashboards/summary/]
backend\tests_list.txt:673:backend/crown_api/tests/test_dashboards_role_contract.py::test_unauthenticated_returns_401[/api/dashboards/drilldown/?widget=alerts_flip]
backend\tests_list.txt:674:backend/crown_api/tests/test_dashboards_role_contract.py::test_unauthenticated_returns_401[/api/dashboards/alerts/]
backend\tests_list.txt:675:backend/crown_api/tests/test_dashboards_role_contract.py::test_missing_school_header_returns_400[/api/dashboards/me/]
backend\tests_list.txt:676:backend/crown_api/tests/test_dashboards_role_contract.py::test_missing_school_header_returns_400[/api/dashboards/summary/]
backend\tests_list.txt:677:backend/crown_api/tests/test_dashboards_role_contract.py::test_missing_school_header_returns_400[/api/dashboards/drilldown/?widget=alerts_flip]
backend\tests_list.txt:678:backend/crown_api/tests/test_dashboards_role_contract.py::test_missing_school_header_returns_400[/api/dashboards/alerts/]
backend\tests_list.txt:679:backend/crown_api/tests/test_dashboards_role_contract.py::test_invalid_school_uuid_returns_400[/api/dashboards/me/]
backend\tests_list.txt:680:backend/crown_api/tests/test_dashboards_role_contract.py::test_invalid_school_uuid_returns_400[/api/dashboards/summary/]
backend\tests_list.txt:681:backend/crown_api/tests/test_dashboards_role_contract.py::test_invalid_school_uuid_returns_400[/api/dashboards/drilldown/?widget=alerts_flip]
backend\tests_list.txt:682:backend/crown_api/tests/test_dashboards_role_contract.py::test_invalid_school_uuid_returns_400[/api/dashboards/alerts/]
backend\tests_list.txt:683:backend/crown_api/tests/test_dashboards_role_contract.py::test_nonexistent_school_returns_404[/api/dashboards/me/]
backend\tests_list.txt:684:backend/crown_api/tests/test_dashboards_role_contract.py::test_nonexistent_school_returns_404[/api/dashboards/summary/]
backend\tests_list.txt:685:backend/crown_api/tests/test_dashboards_role_contract.py::test_nonexistent_school_returns_404[/api/dashboards/drilldown/?widget=alerts_flip]
backend\tests_list.txt:686:backend/crown_api/tests/test_dashboards_role_contract.py::test_nonexistent_school_returns_404[/api/dashboards/alerts/]
backend\tests_list.txt:687:backend/crown_api/tests/test_dashboards_role_contract.py::test_dashboard_me_returns_schema
backend\tests_list.txt:688:backend/crown_api/tests/test_dashboards_role_contract.py::test_dashboard_summary_returns_widgets
backend\tests_list.txt:689:backend/crown_api/tests/test_dashboards_role_contract.py::test_dashboard_summary_widgets_sorted_by_priority
backend\tests_list.txt:690:backend/crown_api/tests/test_dashboards_role_contract.py::test_dashboard_summary_widget_schema
backend\tests_list.txt:691:backend/crown_api/tests/test_dashboards_role_contract.py::test_dashboard_summary_quick_actions_always_present
backend\tests_list.txt:692:backend/crown_api/tests/test_dashboards_role_contract.py::test_dashboard_drilldown_requires_widget_param
backend\tests_list.txt:693:backend/crown_api/tests/test_dashboards_role_contract.py::test_dashboard_drilldown_returns_schema
backend\tests_list.txt:694:backend/crown_api/tests/test_dashboards_role_contract.py::test_dashboard_alerts_returns_list
backend\tests_list.txt:695:backend/crown_api/tests/test_dashboards_role_contract.py::test_cross_tenant_access_blocked
backend\tests_list.txt:699:backend/crown_api/tests/test_director_actions_tenant_isolation.py::DirectorTenantIsolationTest::test_director_cannot_modify_other_school_award
backend\tests_list.txt:708:backend/crown_api/tests/test_gate1c_auth_tenant_proof.py::Gate1CAuthProofTestCase::test_whoami_requires_authentication
backend\tests_list.txt:709:backend/crown_api/tests/test_gate1c_auth_tenant_proof.py::Gate1CAuthProofTestCase::test_whoami_returns_build_sha
backend\tests_list.txt:710:backend/crown_api/tests/test_gate1c_auth_tenant_proof.py::Gate1CAuthProofTestCase::test_whoami_returns_override_info
backend\tests_list.txt:711:backend/crown_api/tests/test_gate1c_auth_tenant_proof.py::Gate1CAuthProofTestCase::test_whoami_returns_tenant_info
backend\tests_list.txt:712:backend/crown_api/tests/test_gate1c_auth_tenant_proof.py::Gate1CAuthProofTestCase::test_whoami_returns_user_info
backend\tests_list.txt:713:backend/crown_api/tests/test_gate1c_auth_tenant_proof.py::Gate1CTenantGuardTestCase::test_tenant_mixin_allows_valid_tenant
backend\tests_list.txt:714:backend/crown_api/tests/test_gate1c_auth_tenant_proof.py::Gate1CTenantGuardTestCase::test_tenant_mixin_enforces_tenant_required
backend\tests_list.txt:715:backend/crown_api/tests/test_gate1c_auth_tenant_proof.py::Gate1CDefaultDenyTestCase::test_drf_view_requires_auth_by_default
backend\tests_list.txt:718:backend/crown_api/tests/test_households_api.py::HouseholdsApiTests::test_cross_school_isolation
backend\tests_list.txt:734:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[admin-/api/v1/admin/metrics/]
backend\tests_list.txt:735:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[board-/api/v1/board/metrics/]
backend\tests_list.txt:736:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[finance-/api/v1/finance/metrics/]
backend\tests_list.txt:737:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[teacher-/api/v1/teacher/metrics/]
backend\tests_list.txt:738:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[parent-/api/v1/parent/metrics/]
backend\tests_list.txt:739:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[student-/api/v1/student/metrics/]
backend\tests_list.txt:740:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[it-/api/v1/it/metrics/]
backend\tests_list.txt:741:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[financial_aid-/api/v1/financial-aid/metrics/]
backend\tests_list.txt:742:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[marketing-/api/v1/marketing/metrics/]
backend\tests_list.txt:743:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[spiritual_life-/api/v1/spiritual-life/metrics/]
backend\tests_list.txt:744:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[office-/api/v1/office/metrics/]
backend\tests_list.txt:745:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[health-/api/v1/health/metrics/]
backend\tests_list.txt:746:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[counseling-/api/v1/counseling/metrics/]
backend\tests_list.txt:747:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[food-/api/v1/food/metrics/]
backend\tests_list.txt:748:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[athletics-/api/v1/athletics/metrics/]
backend\tests_list.txt:749:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[advancement-/api/v1/advancement/metrics/]
backend\tests_list.txt:750:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[transportation-/api/v1/transportation/metrics/]
backend\tests_list.txt:751:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[facilities-/api/v1/facilities/metrics/]
backend\tests_list.txt:752:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[security-/api/v1/security/metrics/]
backend\tests_list.txt:753:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[academic_support-/api/v1/academic-support/metrics/]
backend\tests_list.txt:754:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[fine_arts-/api/v1/fine-arts/metrics/]
backend\tests_list.txt:755:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[library-/api/v1/library/metrics/]
backend\tests_list.txt:756:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[extended_care-/api/v1/extended-care/metrics/]
backend\tests_list.txt:757:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[registrar-/api/v1/registrar/metrics/]
backend\tests_list.txt:758:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[communications-/api/v1/communications/metrics/]
backend\tests_list.txt:759:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[pd-/api/v1/pd/metrics/]
backend\tests_list.txt:760:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_requires_tenant_context[student_services-/api/v1/student-services/metrics/]
backend\tests_list.txt:761:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[admin-/api/v1/admin/metrics/]
backend\tests_list.txt:762:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[board-/api/v1/board/metrics/]
backend\tests_list.txt:763:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[finance-/api/v1/finance/metrics/]
backend\tests_list.txt:764:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[teacher-/api/v1/teacher/metrics/]
backend\tests_list.txt:765:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[parent-/api/v1/parent/metrics/]
backend\tests_list.txt:766:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[student-/api/v1/student/metrics/]
backend\tests_list.txt:767:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[it-/api/v1/it/metrics/]
backend\tests_list.txt:768:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[financial_aid-/api/v1/financial-aid/metrics/]
backend\tests_list.txt:769:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[marketing-/api/v1/marketing/metrics/]
backend\tests_list.txt:770:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[spiritual_life-/api/v1/spiritual-life/metrics/]
backend\tests_list.txt:771:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[office-/api/v1/office/metrics/]
backend\tests_list.txt:772:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[health-/api/v1/health/metrics/]
backend\tests_list.txt:773:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[counseling-/api/v1/counseling/metrics/]
backend\tests_list.txt:774:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[food-/api/v1/food/metrics/]
backend\tests_list.txt:775:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[athletics-/api/v1/athletics/metrics/]
backend\tests_list.txt:776:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[advancement-/api/v1/advancement/metrics/]
backend\tests_list.txt:777:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[transportation-/api/v1/transportation/metrics/]
backend\tests_list.txt:778:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[facilities-/api/v1/facilities/metrics/]
backend\tests_list.txt:779:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[security-/api/v1/security/metrics/]
backend\tests_list.txt:780:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[academic_support-/api/v1/academic-support/metrics/]
backend\tests_list.txt:781:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[fine_arts-/api/v1/fine-arts/metrics/]
backend\tests_list.txt:782:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[library-/api/v1/library/metrics/]
backend\tests_list.txt:783:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[extended_care-/api/v1/extended-care/metrics/]
backend\tests_list.txt:784:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[registrar-/api/v1/registrar/metrics/]
backend\tests_list.txt:785:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[communications-/api/v1/communications/metrics/]
backend\tests_list.txt:786:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[pd-/api/v1/pd/metrics/]
backend\tests_list.txt:787:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_denies_without_permission[student_services-/api/v1/student-services/metrics/]
backend\tests_list.txt:788:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[admin-/api/v1/admin/metrics/]
backend\tests_list.txt:789:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[board-/api/v1/board/metrics/]
backend\tests_list.txt:790:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[finance-/api/v1/finance/metrics/]
backend\tests_list.txt:791:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[teacher-/api/v1/teacher/metrics/]
backend\tests_list.txt:792:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[parent-/api/v1/parent/metrics/]
backend\tests_list.txt:793:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[student-/api/v1/student/metrics/]
backend\tests_list.txt:794:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[it-/api/v1/it/metrics/]
backend\tests_list.txt:795:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[financial_aid-/api/v1/financial-aid/metrics/]
backend\tests_list.txt:796:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[marketing-/api/v1/marketing/metrics/]
backend\tests_list.txt:797:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[spiritual_life-/api/v1/spiritual-life/metrics/]
backend\tests_list.txt:798:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[office-/api/v1/office/metrics/]
backend\tests_list.txt:799:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[health-/api/v1/health/metrics/]
backend\tests_list.txt:800:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[counseling-/api/v1/counseling/metrics/]
backend\tests_list.txt:801:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[food-/api/v1/food/metrics/]
backend\tests_list.txt:802:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[athletics-/api/v1/athletics/metrics/]
backend\tests_list.txt:803:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[advancement-/api/v1/advancement/metrics/]
backend\tests_list.txt:804:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[transportation-/api/v1/transportation/metrics/]
backend\tests_list.txt:805:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[facilities-/api/v1/facilities/metrics/]
backend\tests_list.txt:806:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[security-/api/v1/security/metrics/]
backend\tests_list.txt:807:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[academic_support-/api/v1/academic-support/metrics/]
backend\tests_list.txt:808:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[fine_arts-/api/v1/fine-arts/metrics/]
backend\tests_list.txt:809:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[library-/api/v1/library/metrics/]
backend\tests_list.txt:810:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[extended_care-/api/v1/extended-care/metrics/]
backend\tests_list.txt:811:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[registrar-/api/v1/registrar/metrics/]
backend\tests_list.txt:812:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[communications-/api/v1/communications/metrics/]
backend\tests_list.txt:813:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[pd-/api/v1/pd/metrics/]
backend\tests_list.txt:814:backend/crown_api/tests/test_metrics_permissions_contract.py::test_metrics_allows_with_permission[student_services-/api/v1/student-services/metrics/]
backend\tests_list.txt:817:backend/crown_api/tests/test_object_level_permissions.py::StaffGatedActionsTests::test_plain_user_cannot_enroll_applicant
backend\tests_list.txt:818:backend/crown_api/tests/test_object_level_permissions.py::StaffGatedActionsTests::test_plain_user_cannot_issue_refund
backend\tests_list.txt:819:backend/crown_api/tests/test_object_level_permissions.py::StaffGatedActionsTests::test_plain_user_cannot_settle_payment
backend\tests_list.txt:820:backend/crown_api/tests/test_object_level_permissions.py::StaffGatedActionsTests::test_staff_user_passes_enroll_gate
backend\tests_list.txt:821:backend/crown_api/tests/test_object_level_permissions.py::StaffGatedActionsTests::test_staff_user_passes_settle_gate
backend\tests_list.txt:822:backend/crown_api/tests/test_object_level_permissions.py::PaymentOwnershipBoundaryTests::test_staff_can_settle_any_school_payment_not_just_own
backend\tests_list.txt:823:backend/crown_api/tests/test_object_level_permissions.py::SharedSchoolResourceAccessTests::test_shared_installment_plan_list_accessible_to_all_school_members
backend\tests_list.txt:824:backend/crown_api/tests/test_object_level_permissions.py::EnrollmentTransitionGuardTests::test_409_response_does_not_expose_internal_details
backend\tests_list.txt:825:backend/crown_api/tests/test_object_level_permissions.py::EnrollmentTransitionGuardTests::test_enroll_from_draft_returns_409
backend\tests_list.txt:826:backend/crown_api/tests/test_object_level_permissions.py::EnrollmentTransitionGuardTests::test_enroll_from_submitted_returns_409
backend\tests_list.txt:835:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_health_-admin]
backend\tests_list.txt:836:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_health_-SCHOOL_ADMIN]
backend\tests_list.txt:837:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_health_-BOARD_MEMBER]
backend\tests_list.txt:838:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_health_-FINANCE]
backend\tests_list.txt:839:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_health_-ADMISSIONS]
backend\tests_list.txt:840:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_health_-TEACHER]
backend\tests_list.txt:841:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_health_-PARENT]
backend\tests_list.txt:842:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_finance_-admin]
backend\tests_list.txt:843:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_finance_-SCHOOL_ADMIN]
backend\tests_list.txt:844:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_finance_-BOARD_MEMBER]
backend\tests_list.txt:845:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_finance_-FINANCE]
backend\tests_list.txt:846:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_finance_-ADMISSIONS]
backend\tests_list.txt:847:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_finance_-TEACHER]
backend\tests_list.txt:848:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_finance_-PARENT]
backend\tests_list.txt:849:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_admissions_-admin]
backend\tests_list.txt:850:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_admissions_-SCHOOL_ADMIN]
backend\tests_list.txt:851:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_admissions_-BOARD_MEMBER]
backend\tests_list.txt:852:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_admissions_-FINANCE]
backend\tests_list.txt:853:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_admissions_-ADMISSIONS]
backend\tests_list.txt:854:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_admissions_-TEACHER]
backend\tests_list.txt:855:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_admissions_-PARENT]
backend\tests_list.txt:856:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_academics_-admin]
backend\tests_list.txt:857:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_academics_-SCHOOL_ADMIN]
backend\tests_list.txt:858:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_academics_-BOARD_MEMBER]
backend\tests_list.txt:859:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_academics_-FINANCE]
backend\tests_list.txt:860:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_academics_-ADMISSIONS]
backend\tests_list.txt:861:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_academics_-TEACHER]
backend\tests_list.txt:862:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_dashboards_academics_-PARENT]
backend\tests_list.txt:863:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_metrics_-admin]
backend\tests_list.txt:864:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_metrics_-SCHOOL_ADMIN]
backend\tests_list.txt:865:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_metrics_-BOARD_MEMBER]
backend\tests_list.txt:866:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_metrics_-FINANCE]
backend\tests_list.txt:867:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_metrics_-ADMISSIONS]
backend\tests_list.txt:868:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_metrics_-TEACHER]
backend\tests_list.txt:869:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_metrics_-PARENT]
backend\tests_list.txt:870:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_dashboard_-admin]
backend\tests_list.txt:871:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_dashboard_-SCHOOL_ADMIN]
backend\tests_list.txt:872:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_dashboard_-BOARD_MEMBER]
backend\tests_list.txt:873:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_dashboard_-FINANCE]
backend\tests_list.txt:874:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_dashboard_-ADMISSIONS]
backend\tests_list.txt:875:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_dashboard_-TEACHER]
backend\tests_list.txt:876:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_dashboard_-PARENT]
backend\tests_list.txt:877:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_snapshots_-admin]
backend\tests_list.txt:878:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_snapshots_-SCHOOL_ADMIN]
backend\tests_list.txt:879:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_snapshots_-BOARD_MEMBER]
backend\tests_list.txt:880:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_snapshots_-FINANCE]
backend\tests_list.txt:881:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_snapshots_-ADMISSIONS]
backend\tests_list.txt:882:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_snapshots_-TEACHER]
backend\tests_list.txt:883:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_snapshots_-PARENT]
backend\tests_list.txt:884:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_packets_-admin]
backend\tests_list.txt:885:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_packets_-SCHOOL_ADMIN]
backend\tests_list.txt:886:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_packets_-BOARD_MEMBER]
backend\tests_list.txt:887:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_packets_-FINANCE]
backend\tests_list.txt:888:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_packets_-ADMISSIONS]
backend\tests_list.txt:889:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_packets_-TEACHER]
backend\tests_list.txt:890:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_board_packets_-PARENT]
backend\tests_list.txt:891:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_financial-aid_summary_-admin]
backend\tests_list.txt:892:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_financial-aid_summary_-SCHOOL_ADMIN]
backend\tests_list.txt:893:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_financial-aid_summary_-BOARD_MEMBER]
backend\tests_list.txt:894:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_financial-aid_summary_-FINANCE]
backend\tests_list.txt:895:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_financial-aid_summary_-ADMISSIONS]
backend\tests_list.txt:896:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_financial-aid_summary_-TEACHER]
backend\tests_list.txt:897:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_financial-aid_summary_-PARENT]
backend\tests_list.txt:898:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_households_-admin]
backend\tests_list.txt:899:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_households_-SCHOOL_ADMIN]
backend\tests_list.txt:900:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_households_-BOARD_MEMBER]
backend\tests_list.txt:901:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_households_-FINANCE]
backend\tests_list.txt:902:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_households_-ADMISSIONS]
backend\tests_list.txt:903:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_households_-TEACHER]
backend\tests_list.txt:904:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_households_-PARENT]
backend\tests_list.txt:905:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_students_-admin]
backend\tests_list.txt:906:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_students_-SCHOOL_ADMIN]
backend\tests_list.txt:907:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_students_-BOARD_MEMBER]
backend\tests_list.txt:908:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_students_-FINANCE]
backend\tests_list.txt:909:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_students_-ADMISSIONS]
backend\tests_list.txt:910:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_students_-TEACHER]
backend\tests_list.txt:911:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_never_500[_api_v1_students_-PARENT]
backend\tests_list.txt:912:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_unauthenticated_never_500[_api_health_]
backend\tests_list.txt:913:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_unauthenticated_never_500[_api_v1_dashboards_finance_]
backend\tests_list.txt:914:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_unauthenticated_never_500[_api_v1_dashboards_admissions_]
backend\tests_list.txt:915:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_unauthenticated_never_500[_api_v1_dashboards_academics_]
backend\tests_list.txt:916:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_unauthenticated_never_500[_api_v1_board_metrics_]
backend\tests_list.txt:917:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_unauthenticated_never_500[_api_v1_board_dashboard_]
backend\tests_list.txt:918:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_unauthenticated_never_500[_api_v1_board_snapshots_]
backend\tests_list.txt:919:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_unauthenticated_never_500[_api_v1_board_packets_]
backend\tests_list.txt:920:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_unauthenticated_never_500[_api_v1_financial-aid_summary_]
backend\tests_list.txt:921:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_unauthenticated_never_500[_api_v1_households_]
backend\tests_list.txt:922:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_readonly_endpoint_unauthenticated_never_500[_api_v1_students_]
backend\tests_list.txt:923:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_public_endpoint_always_200[/api/health/]
backend\tests_list.txt:924:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_health_returns_build_sha_key
backend\tests_list.txt:925:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_protected_endpoint_requires_auth[/api/v1/board/metrics/]
backend\tests_list.txt:926:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_protected_endpoint_requires_auth[/api/v1/board/dashboard/]
backend\tests_list.txt:927:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_protected_endpoint_requires_auth[/api/v1/board/snapshots/]
backend\tests_list.txt:928:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_protected_endpoint_requires_auth[/api/v1/board/packets/]
backend\tests_list.txt:929:backend/crown_api/tests/test_rbac_matrix_readonly.py::test_protected_endpoint_requires_auth[/api/v1/financial-aid/summary/]
backend\tests_list.txt:930:backend/crown_api/tests/test_rbac_matrix_writes.py::AdmissionsEnrollRbacTests::test_non_staff_enroll_returns_403
backend\tests_list.txt:931:backend/crown_api/tests/test_rbac_matrix_writes.py::AdmissionsEnrollRbacTests::test_staff_enroll_passes_gate
backend\tests_list.txt:932:backend/crown_api/tests/test_rbac_matrix_writes.py::AdmissionsEnrollRbacTests::test_unauthenticated_enroll_returns_401
backend\tests_list.txt:933:backend/crown_api/tests/test_rbac_matrix_writes.py::BillingInstallmentPlansRbacTests::test_non_staff_can_post_installment_plan
backend\tests_list.txt:934:backend/crown_api/tests/test_rbac_matrix_writes.py::BillingInstallmentPlansRbacTests::test_staff_can_post_installment_plan
backend\tests_list.txt:935:backend/crown_api/tests/test_rbac_matrix_writes.py::BillingInstallmentPlansRbacTests::test_unauthenticated_installment_plan_post_returns_401
backend\tests_list.txt:936:backend/crown_api/tests/test_rbac_matrix_writes.py::FinancialAidApplicationsRbacTests::test_authenticated_user_can_attempt_faid_application_post
backend\tests_list.txt:937:backend/crown_api/tests/test_rbac_matrix_writes.py::FinancialAidApplicationsRbacTests::test_unauthenticated_faid_application_post_returns_401
backend\tests_list.txt:938:backend/crown_api/tests/test_rbac_matrix_writes.py::FinancePaymentIntentRbacTests::test_authenticated_payment_intent_passes_auth_gate
backend\tests_list.txt:939:backend/crown_api/tests/test_rbac_matrix_writes.py::FinancePaymentIntentRbacTests::test_no_write_without_school_context
backend\tests_list.txt:940:backend/crown_api/tests/test_rbac_matrix_writes.py::FinancePaymentIntentRbacTests::test_unauthenticated_payment_intent_returns_401
backend\tests_list.txt:941:backend/crown_api/tests/test_rbac_proof.py::test_rbac_finance_proof_forbidden_without_role
backend\tests_list.txt:942:backend/crown_api/tests/test_rbac_proof.py::test_rbac_finance_proof_allows_admin_via_demo_header
backend\tests_list.txt:943:backend/crown_api/tests/test_rbac_proof.py::test_rbac_finance_proof_ignores_demo_header_when_flag_disabled
backend\tests_list.txt:944:backend/crown_api/tests/test_role_escalation.py::RoleEscalationTests::test_demo_role_header_flag_is_disabled
backend\tests_list.txt:945:backend/crown_api/tests/test_role_escalation.py::RoleEscalationTests::test_normal_user_cannot_call_director_actions
backend\tests_list.txt:946:backend/crown_api/tests/test_role_escalation.py::RoleEscalationTests::test_unauthenticated_request_cannot_escalate
backend\tests_list.txt:947:backend/crown_api/tests/test_role_escalation.py::RoleEscalationTests::test_user_cannot_self_escalate_role_via_patch
backend\tests_list.txt:948:backend/crown_api/tests/test_role_escalation.py::RoleEscalationTests::test_user_cannot_self_escalate_role_via_put
backend\tests_list.txt:952:backend/crown_api/tests/test_seed_edge_cases.py::test_empty_tenant_read_endpoint_never_500[/api/health/]
backend\tests_list.txt:953:backend/crown_api/tests/test_seed_edge_cases.py::test_empty_tenant_read_endpoint_never_500[/api/v1/board/metrics/]
backend\tests_list.txt:954:backend/crown_api/tests/test_seed_edge_cases.py::test_empty_tenant_read_endpoint_never_500[/api/v1/board/dashboard/]
backend\tests_list.txt:955:backend/crown_api/tests/test_seed_edge_cases.py::test_empty_tenant_read_endpoint_never_500[/api/v1/board/snapshots/]
backend\tests_list.txt:956:backend/crown_api/tests/test_seed_edge_cases.py::test_empty_tenant_read_endpoint_never_500[/api/v1/board/packets/]
backend\tests_list.txt:970:backend/crown_api/tests/test_tenant_enforcement.py::test_tenant_resolves_from_jwt_user_school_id
backend\tests_list.txt:971:backend/crown_api/tests/test_tenant_enforcement.py::test_protected_endpoint_requires_tenant_when_no_jwt_and_no_header
backend\tests_list.txt:972:backend/crown_api/tests/test_tenant_enforcement.py::test_cross_tenant_header_does_not_override_jwt_tenant
backend\tests_list.txt:973:backend/crown_api/tests/test_tenant_isolation_writes.py::FinancialAidCrossTenantReadTests::test_unauthenticated_read_blocked
backend\tests_list.txt:974:backend/crown_api/tests/test_tenant_isolation_writes.py::FinancialAidCrossTenantReadTests::test_user_a_can_read_own_school_applications
backend\tests_list.txt:975:backend/crown_api/tests/test_tenant_isolation_writes.py::FinancialAidCrossTenantReadTests::test_user_b_cannot_read_school_a_applications
backend\tests_list.txt:976:backend/crown_api/tests/test_tenant_isolation_writes.py::FinancialAidCrossTenantWriteTests::test_cross_tenant_post_does_not_create_in_school_b_either
backend\tests_list.txt:977:backend/crown_api/tests/test_tenant_isolation_writes.py::FinancialAidCrossTenantWriteTests::test_user_b_cannot_post_into_school_a
backend\tests_list.txt:978:backend/crown_api/tests/test_tenant_isolation_writes.py::AidAwardCrossTenantTests::test_school_a_award_not_visible_in_school_b_listing
backend\tests_list.txt:979:backend/crown_api/tests/test_tenant_isolation_writes.py::AidAwardCrossTenantTests::test_user_b_cannot_read_school_a_awards
backend\tests_list.txt:980:backend/curricula/tests/test_curricula_tenant_isolation.py::test_curriculum_maps_tenant_isolation
backend\tests_list.txt:981:backend/curricula/tests/test_curricula_tenant_isolation.py::test_units_tenant_isolation
backend\tests_list.txt:982:backend/curricula/tests/test_curricula_tenant_isolation.py::test_lessons_tenant_isolation
backend\tests_list.txt:983:backend/curricula/tests/test_curricula_tenant_isolation.py::test_curriculum_filter_by_course
backend\tests_list.txt:984:backend/curricula/tests/test_curricula_tenant_isolation.py::test_unit_filter_by_curriculum_map
backend\tests_list.txt:985:backend/curricula/tests/test_curricula_tenant_isolation.py::test_lesson_filter_by_unit
backend\tests_list.txt:986:backend/curricula/tests/test_curricula_tenant_isolation.py::test_read_only_endpoints_reject_writes
backend\tests_list.txt:987:backend/curricula/tests/test_curricula_tenant_isolation.py::test_unauthenticated_requests_blocked
backend\tests_list.txt:988:backend/curricula/tests/test_curricula_tenant_isolation.py::test_curricula_detail_views_tenant_isolation
backend\tests_list.txt:1028:backend/enrollment_period_wizard/tests/test_views.py::EnrollmentPeriodSinglePerYearTest::test_cross_tenant_isolation
backend\tests_list.txt:1035:backend/facops/tests/test_facops.py::TestLocations::test_create_denied_for_readonly_role
backend\tests_list.txt:1036:backend/facops/tests/test_facops.py::TestLocations::test_cross_tenant_isolation
backend\tests_list.txt:1041:backend/facops/tests/test_facops.py::TestAssets::test_asset_cross_tenant
backend\tests_list.txt:1048:backend/facops/tests/test_facops.py::TestWorkOrders::test_cross_tenant_work_orders
backend\tests_list.txt:1053:backend/facops/tests/test_facops.py::TestSafetyIncidents::test_cross_tenant
backend\tests_list.txt:1059:backend/facops/tests/test_facops.py::TestVisitorLogs::test_cross_tenant
backend\tests_list.txt:1135:backend/finance/tests/test_finance_tenant.py::TestObligationsTenantEnforcement::test_missing_school_header_returns_fail_closed
backend\tests_list.txt:1136:backend/finance/tests/test_finance_tenant.py::TestObligationsTenantEnforcement::test_non_staff_cannot_list_obligations
backend\tests_list.txt:1137:backend/finance/tests/test_finance_tenant.py::TestObligationsTenantEnforcement::test_obligations_scoped_to_school
backend\tests_list.txt:1138:backend/finance/tests/test_finance_tenant.py::TestObligationsTenantEnforcement::test_unauthenticated_cannot_list_obligations
backend\tests_list.txt:1139:backend/finance/tests/test_finance_tenant.py::TestObligationsTenantEnforcement::test_valid_school_header_returns_200
backend\tests_list.txt:1140:backend/finance/tests/test_finance_tenant.py::TestParentBalanceTenantScoping::test_parent_balance_missing_header_fail_closed
backend\tests_list.txt:1141:backend/finance/tests/test_finance_tenant.py::TestParentBalanceTenantScoping::test_parent_balance_only_shows_own_obligations
backend\tests_list.txt:1149:backend/finance_setup/tests/test_finance_setup_tenant_scoping.py::test_policy_only_visible_to_owning_school
backend\tests_list.txt:1150:backend/finance_setup/tests/test_finance_setup_tenant_scoping.py::test_separate_schools_store_independently
backend\tests_list.txt:1151:backend/finance_setup/tests/test_finance_setup_tenant_scoping.py::test_school_multi_year_scoping
backend\tests_list.txt:1152:backend/finance_setup/tests/test_finance_setup_tenant_scoping.py::test_finance_policy_version_unique_constraint
backend\tests_list.txt:1156:backend/financial_aid/tests/test_financial_aid_authz.py::TestFinancialAidPermissionGate::test_role_blocked_on_summary[PARENT-parent.view]
backend\tests_list.txt:1157:backend/financial_aid/tests/test_financial_aid_authz.py::TestFinancialAidPermissionGate::test_role_blocked_on_summary[STUDENT-student.view]
backend\tests_list.txt:1158:backend/financial_aid/tests/test_financial_aid_authz.py::TestFinancialAidPermissionGate::test_role_blocked_on_summary[TEACHER-teacher.view]
backend\tests_list.txt:1159:backend/financial_aid/tests/test_financial_aid_authz.py::TestFinancialAidPermissionGate::test_role_blocked_on_drilldown[PARENT-parent.view]
backend\tests_list.txt:1160:backend/financial_aid/tests/test_financial_aid_authz.py::TestFinancialAidPermissionGate::test_role_blocked_on_drilldown[STUDENT-student.view]
backend\tests_list.txt:1161:backend/financial_aid/tests/test_financial_aid_authz.py::TestFinancialAidPermissionGate::test_role_blocked_on_drilldown[TEACHER-teacher.view]
backend\tests_list.txt:1163:backend/financial_aid/tests/test_financial_aid_authz.py::TestFinancialAidPermissionAllowed::test_role_reaches_summary[AID_DIRECTOR]
backend\tests_list.txt:1164:backend/financial_aid/tests/test_financial_aid_authz.py::TestFinancialAidPermissionAllowed::test_role_reaches_summary[FINANCE_DIRECTOR]
backend\tests_list.txt:1165:backend/financial_aid/tests/test_financial_aid_authz.py::TestFinancialAidPermissionAllowed::test_role_reaches_drilldown[AID_DIRECTOR]
backend\tests_list.txt:1166:backend/financial_aid/tests/test_financial_aid_authz.py::TestFinancialAidPermissionAllowed::test_role_reaches_drilldown[FINANCE_DIRECTOR]
backend\tests_list.txt:1167:backend/financial_aid/tests/test_financial_aid_authz.py::TestFinancialAidTenantIsolation::test_cross_tenant_row_isolation_on_drilldown
backend\tests_list.txt:1168:backend/financial_aid/tests/test_financial_aid_authz.py::TestFinancialAidTenantIsolation::test_same_tenant_drilldown_returns_own_data_only
backend\tests_list.txt:1194:backend/financial_aid_wizard/tests/test_views.py::TestTenantIsolation::test_awards_isolation
backend\tests_list.txt:1195:backend/financial_aid_wizard/tests/test_views.py::TestTenantIsolation::test_buckets_isolation
backend\tests_list.txt:1196:backend/financial_aid_wizard/tests/test_views.py::TestTenantIsolation::test_commit_isolation
backend\tests_list.txt:1197:backend/financial_aid_wizard/tests/test_views.py::TestTenantIsolation::test_configure_isolation
backend\tests_list.txt:1198:backend/financial_aid_wizard/tests/test_views.py::TestTenantIsolation::test_verify_isolation
backend\tests_list.txt:1257:backend/grade_scale_wizard/tests/test_views.py::GradeScaleSingleActiveTest::test_cross_tenant_isolation
backend\tests_list.txt:1268:backend/grade_weights_wizard/tests/test_views.py::TestGradeWeightsWizardTenantIsolation::test_cross_tenant_returns_404
backend\tests_list.txt:1278:backend/gradebook/tests/test_gradebook_list_endpoints.py::test_assignments_list_non_teacher_role_forbidden
backend\tests_list.txt:1279:backend/gradebook/tests/test_gradebook_list_endpoints.py::test_students_list_non_teacher_role_forbidden
backend\tests_list.txt:1286:backend/gradebook/tests/test_gradebook_ro_api.py::test_non_teacher_role_forbidden
backend\tests_list.txt:1293:backend/gradebook/tests/test_parent_grades_e2e.py::test_parent_grades_summary_invalid_tenant_header_returns_400
backend\tests_list.txt:1328:backend/guardian_household_wizard/tests/test_views.py::TestGuardianHouseholdWizardTenantIsolation::test_cross_tenant_returns_404
backend\tests_list.txt:1337:backend/households/tests/test_tenant_isolation.py::TenantIsolationTestCase::test_correct_tenant_returns_200
backend\tests_list.txt:1338:backend/households/tests/test_tenant_isolation.py::TenantIsolationTestCase::test_finance_endpoint_respects_tenant
backend\tests_list.txt:1339:backend/households/tests/test_tenant_isolation.py::TenantIsolationTestCase::test_invalid_tenant_header_returns_400
backend\tests_list.txt:1340:backend/households/tests/test_tenant_isolation.py::TenantIsolationTestCase::test_missing_tenant_returns_400
backend\tests_list.txt:1341:backend/households/tests/test_tenant_isolation.py::TenantIsolationTestCase::test_nonexistent_tenant_returns_404
backend\tests_list.txt:1342:backend/households/tests/test_tenant_isolation.py::TenantIsolationTestCase::test_queryset_never_crosses_tenants
backend\tests_list.txt:1343:backend/households/tests/test_tenant_isolation.py::TenantIsolationTestCase::test_staff_can_override_tenant
backend\tests_list.txt:1344:backend/households/tests/test_tenant_isolation.py::TenantIsolationTestCase::test_wrong_tenant_returns_404_non_staff
backend\tests_list.txt:1381:backend/journal/tests/test_journal_invariants.py::JournalInvariantTests::test_cross_tenant_account_fails
backend\tests_list.txt:1406:backend/ledger/tests/test_ledger_invariants.py::test_invariants_tenant_isolation
backend\tests_list.txt:1407:backend/ledger/tests/test_ledger_invariants.py::test_allocation_cross_tenant_guard
backend\tests_list.txt:1512:backend/outreach/tests/test_outreach.py::TestTenantIsolation::test_cross_tenant_partner_hidden
backend\tests_list.txt:1522:backend/outreach/tests/test_outreach.py::TestOpportunity::test_cross_tenant_hidden
backend\tests_list.txt:1533:backend/outreach/tests/test_outreach.py::TestServiceLogScoping::test_cross_tenant_not_visible
backend\tests_list.txt:1541:backend/outreach/tests/test_outreach.py::TestBadge::test_cross_tenant_hidden
backend\tests_list.txt:1557:backend/payments/tests/test_household_finance_access.py::test_household_summary_allows_finance_runtime_role
backend\tests_list.txt:1598:backend/scheduling_wizard/tests/test_views.py::TestTenantIsolation::test_commit_isolation
backend\tests_list.txt:1599:backend/scheduling_wizard/tests/test_views.py::TestTenantIsolation::test_configure_isolation
backend\tests_list.txt:1600:backend/scheduling_wizard/tests/test_views.py::TestTenantIsolation::test_courses_isolation
backend\tests_list.txt:1601:backend/scheduling_wizard/tests/test_views.py::TestTenantIsolation::test_sections_isolation
backend\tests_list.txt:1602:backend/scheduling_wizard/tests/test_views.py::TestTenantIsolation::test_verify_isolation
backend\tests_list.txt:1674:backend/section_staffing_wizard/tests/test_views.py::TestSectionStaffingWizardTenantIsolation::test_cross_tenant_returns_404
backend\tests_list.txt:1675:backend/signals/tests/test_tenant_scoping.py::test_signal_event_scoped_by_school_id
backend\tests_list.txt:1676:backend/signals/tests/test_tenant_scoping.py::test_snapshot_unique_per_day
backend\tests_list.txt:1677:backend/signals/tests/test_tenant_scoping.py::test_cross_school_snapshots_independent
backend\tests_list.txt:1728:backend/spiritual_life/tests/test_spiritual_life.py::TestPastoralNotes::test_tenant_isolation_pastoral_notes
backend\tests_list.txt:1735:backend/staff_onboarding_wizard/tests/test_views.py::StaffOnboardingConfigureTest::test_all_valid_roles_accepted
backend\tests_list.txt:1737:backend/staff_onboarding_wizard/tests/test_views.py::StaffOnboardingConfigureTest::test_configure_invalid_role
backend\tests_list.txt:1759:backend/student_import_wizard/tests/test_views.py::TestStudentImportWizardTenantIsolation::test_cross_tenant_returns_404
backend\tests_list.txt:1763:backend/student_records/tests/test_student_records_routes.py::test_list_scopes_to_tenant_school
backend\tests_list.txt:1764:backend/student_records/tests/test_student_records_routes.py::test_detail_cross_tenant_returns_404
backend\tests_list.txt:1765:backend/student_records/tests/test_student_records_routes.py::test_detail_not_found_returns_404_with_valid_tenant
backend\tests_list.txt:1789:backend/subscriptions/tests/test_permissions_enforcement.py::test_me_entitlements_requires_auth
backend\tests_list.txt:1790:backend/subscriptions/tests/test_permissions_enforcement.py::test_me_entitlements_requires_school_header
backend\tests_list.txt:1791:backend/subscriptions/tests/test_permissions_enforcement.py::test_me_entitlements_returns_snapshot
backend\tests_list.txt:1792:backend/subscriptions/tests/test_permissions_enforcement.py::test_plan_list_authenticated
backend\tests_list.txt:1793:backend/subscriptions/tests/test_permissions_enforcement.py::test_plan_list_requires_auth
backend\tests_list.txt:1794:backend/subscriptions/tests/test_permissions_enforcement.py::test_ops_requires_admin
backend\tests_list.txt:1795:backend/subscriptions/tests/test_permissions_enforcement.py::test_ops_get_subscription
backend\tests_list.txt:1796:backend/subscriptions/tests/test_permissions_enforcement.py::test_ops_get_nonexistent_404
backend\tests_list.txt:1797:backend/subscriptions/tests/test_permissions_enforcement.py::test_ops_post_assigns_plan
backend\tests_list.txt:1798:backend/subscriptions/tests/test_permissions_enforcement.py::test_ops_post_missing_plan_id
backend\tests_list.txt:1829:backend/term_structure_wizard/tests/test_views.py::TermStructureSingleActiveTest::test_cross_tenant_isolation
backend\tests_list.txt:1846:backend/tests/test_audit_logging_tenant.py::TestAuditLoggingTenantIsolation::test_audit_logging_tenant_school_ids_are_distinct
backend\tests_list.txt:1847:backend/tests/test_audit_logging_tenant.py::TestAuditLoggingTenantIsolation::test_audit_logging_user_bound_to_correct_school
backend\tests_list.txt:1848:backend/tests/test_audit_logging_tenant.py::TestAuditLoggingTenantIsolation::test_audit_logging_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:1849:backend/tests/test_audit_logging_tenant.py::TestAuditLoggingTenantIsolation::test_audit_logging_same_tenant_request_is_allowed
backend\tests_list.txt:1850:backend/tests/test_audit_logging_tenant.py::TestAuditLoggingTenantIsolation::test_audit_logging_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:1851:backend/tests/test_audit_logging_tenant.py::TestAuditLoggingTenantIsolation::test_audit_logging_isolation_keyword_present_in_source
backend\tests_list.txt:1864:backend/tests/test_board_governance_suite_tenant.py::TestBoardGovernanceSuiteTenantIsolation::test_board_governance_suite_tenant_school_ids_are_distinct
backend\tests_list.txt:1865:backend/tests/test_board_governance_suite_tenant.py::TestBoardGovernanceSuiteTenantIsolation::test_board_governance_suite_user_bound_to_correct_school
backend\tests_list.txt:1866:backend/tests/test_board_governance_suite_tenant.py::TestBoardGovernanceSuiteTenantIsolation::test_board_governance_suite_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:1867:backend/tests/test_board_governance_suite_tenant.py::TestBoardGovernanceSuiteTenantIsolation::test_board_governance_suite_same_tenant_request_is_allowed
backend\tests_list.txt:1868:backend/tests/test_board_governance_suite_tenant.py::TestBoardGovernanceSuiteTenantIsolation::test_board_governance_suite_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:1869:backend/tests/test_board_governance_suite_tenant.py::TestBoardGovernanceSuiteTenantIsolation::test_board_governance_suite_isolation_keyword_present_in_source
backend\tests_list.txt:1882:backend/tests/test_chaplain_pastoral_care_tenant.py::TestChaplainPastoralCareTenantIsolation::test_chaplain_pastoral_care_tenant_school_ids_are_distinct
backend\tests_list.txt:1883:backend/tests/test_chaplain_pastoral_care_tenant.py::TestChaplainPastoralCareTenantIsolation::test_chaplain_pastoral_care_user_bound_to_correct_school
backend\tests_list.txt:1884:backend/tests/test_chaplain_pastoral_care_tenant.py::TestChaplainPastoralCareTenantIsolation::test_chaplain_pastoral_care_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:1885:backend/tests/test_chaplain_pastoral_care_tenant.py::TestChaplainPastoralCareTenantIsolation::test_chaplain_pastoral_care_same_tenant_request_is_allowed
backend\tests_list.txt:1886:backend/tests/test_chaplain_pastoral_care_tenant.py::TestChaplainPastoralCareTenantIsolation::test_chaplain_pastoral_care_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:1887:backend/tests/test_chaplain_pastoral_care_tenant.py::TestChaplainPastoralCareTenantIsolation::test_chaplain_pastoral_care_isolation_keyword_present_in_source
backend\tests_list.txt:1900:backend/tests/test_christian_pd_hub_tenant.py::TestChristianPdHubTenantIsolation::test_christian_pd_hub_tenant_school_ids_are_distinct
backend\tests_list.txt:1901:backend/tests/test_christian_pd_hub_tenant.py::TestChristianPdHubTenantIsolation::test_christian_pd_hub_user_bound_to_correct_school
backend\tests_list.txt:1902:backend/tests/test_christian_pd_hub_tenant.py::TestChristianPdHubTenantIsolation::test_christian_pd_hub_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:1903:backend/tests/test_christian_pd_hub_tenant.py::TestChristianPdHubTenantIsolation::test_christian_pd_hub_same_tenant_request_is_allowed
backend\tests_list.txt:1904:backend/tests/test_christian_pd_hub_tenant.py::TestChristianPdHubTenantIsolation::test_christian_pd_hub_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:1905:backend/tests/test_christian_pd_hub_tenant.py::TestChristianPdHubTenantIsolation::test_christian_pd_hub_isolation_keyword_present_in_source
backend\tests_list.txt:1918:backend/tests/test_communications_tenant.py::TestCommunicationsTenantIsolation::test_communications_tenant_school_ids_are_distinct
backend\tests_list.txt:1919:backend/tests/test_communications_tenant.py::TestCommunicationsTenantIsolation::test_communications_user_bound_to_correct_school
backend\tests_list.txt:1920:backend/tests/test_communications_tenant.py::TestCommunicationsTenantIsolation::test_communications_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:1921:backend/tests/test_communications_tenant.py::TestCommunicationsTenantIsolation::test_communications_same_tenant_request_is_allowed
backend\tests_list.txt:1922:backend/tests/test_communications_tenant.py::TestCommunicationsTenantIsolation::test_communications_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:1923:backend/tests/test_communications_tenant.py::TestCommunicationsTenantIsolation::test_communications_isolation_keyword_present_in_source
backend\tests_list.txt:1936:backend/tests/test_crm_marketing_tenant.py::TestCrmMarketingTenantIsolation::test_crm_marketing_tenant_school_ids_are_distinct
backend\tests_list.txt:1937:backend/tests/test_crm_marketing_tenant.py::TestCrmMarketingTenantIsolation::test_crm_marketing_user_bound_to_correct_school
backend\tests_list.txt:1938:backend/tests/test_crm_marketing_tenant.py::TestCrmMarketingTenantIsolation::test_crm_marketing_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:1939:backend/tests/test_crm_marketing_tenant.py::TestCrmMarketingTenantIsolation::test_crm_marketing_same_tenant_request_is_allowed
backend\tests_list.txt:1940:backend/tests/test_crm_marketing_tenant.py::TestCrmMarketingTenantIsolation::test_crm_marketing_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:1941:backend/tests/test_crm_marketing_tenant.py::TestCrmMarketingTenantIsolation::test_crm_marketing_isolation_keyword_present_in_source
backend\tests_list.txt:1954:backend/tests/test_crown_compass_tenant.py::TestCrownCompassTenantIsolation::test_crown_compass_tenant_school_ids_are_distinct
backend\tests_list.txt:1955:backend/tests/test_crown_compass_tenant.py::TestCrownCompassTenantIsolation::test_crown_compass_user_bound_to_correct_school
backend\tests_list.txt:1956:backend/tests/test_crown_compass_tenant.py::TestCrownCompassTenantIsolation::test_crown_compass_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:1957:backend/tests/test_crown_compass_tenant.py::TestCrownCompassTenantIsolation::test_crown_compass_same_tenant_request_is_allowed
backend\tests_list.txt:1958:backend/tests/test_crown_compass_tenant.py::TestCrownCompassTenantIsolation::test_crown_compass_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:1959:backend/tests/test_crown_compass_tenant.py::TestCrownCompassTenantIsolation::test_crown_compass_isolation_keyword_present_in_source
backend\tests_list.txt:1978:backend/tests/test_document_file_framework_tenant.py::TestDocumentFileFrameworkTenantIsolation::test_document_file_framework_tenant_school_ids_are_distinct
backend\tests_list.txt:1979:backend/tests/test_document_file_framework_tenant.py::TestDocumentFileFrameworkTenantIsolation::test_document_file_framework_user_bound_to_correct_school
backend\tests_list.txt:1980:backend/tests/test_document_file_framework_tenant.py::TestDocumentFileFrameworkTenantIsolation::test_document_file_framework_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:1981:backend/tests/test_document_file_framework_tenant.py::TestDocumentFileFrameworkTenantIsolation::test_document_file_framework_same_tenant_request_is_allowed
backend\tests_list.txt:1982:backend/tests/test_document_file_framework_tenant.py::TestDocumentFileFrameworkTenantIsolation::test_document_file_framework_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:1983:backend/tests/test_document_file_framework_tenant.py::TestDocumentFileFrameworkTenantIsolation::test_document_file_framework_isolation_keyword_present_in_source
backend\tests_list.txt:1996:backend/tests/test_emergency_medical_tenant.py::TestEmergencyMedicalTenantIsolation::test_emergency_medical_tenant_school_ids_are_distinct
backend\tests_list.txt:1997:backend/tests/test_emergency_medical_tenant.py::TestEmergencyMedicalTenantIsolation::test_emergency_medical_user_bound_to_correct_school
backend\tests_list.txt:1998:backend/tests/test_emergency_medical_tenant.py::TestEmergencyMedicalTenantIsolation::test_emergency_medical_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:1999:backend/tests/test_emergency_medical_tenant.py::TestEmergencyMedicalTenantIsolation::test_emergency_medical_same_tenant_request_is_allowed
backend\tests_list.txt:2000:backend/tests/test_emergency_medical_tenant.py::TestEmergencyMedicalTenantIsolation::test_emergency_medical_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2001:backend/tests/test_emergency_medical_tenant.py::TestEmergencyMedicalTenantIsolation::test_emergency_medical_isolation_keyword_present_in_source
backend\tests_list.txt:2020:backend/tests/test_extended_discipline_tenant.py::TestExtendedDisciplineTenantIsolation::test_extended_discipline_tenant_school_ids_are_distinct
backend\tests_list.txt:2021:backend/tests/test_extended_discipline_tenant.py::TestExtendedDisciplineTenantIsolation::test_extended_discipline_user_bound_to_correct_school
backend\tests_list.txt:2022:backend/tests/test_extended_discipline_tenant.py::TestExtendedDisciplineTenantIsolation::test_extended_discipline_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2023:backend/tests/test_extended_discipline_tenant.py::TestExtendedDisciplineTenantIsolation::test_extended_discipline_same_tenant_request_is_allowed
backend\tests_list.txt:2024:backend/tests/test_extended_discipline_tenant.py::TestExtendedDisciplineTenantIsolation::test_extended_discipline_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2025:backend/tests/test_extended_discipline_tenant.py::TestExtendedDisciplineTenantIsolation::test_extended_discipline_isolation_keyword_present_in_source
backend\tests_list.txt:2044:backend/tests/test_grade_levels_tenant.py::TestGradeLevelsTenantIsolation::test_grade_levels_tenant_school_ids_are_distinct
backend\tests_list.txt:2045:backend/tests/test_grade_levels_tenant.py::TestGradeLevelsTenantIsolation::test_grade_levels_user_bound_to_correct_school
backend\tests_list.txt:2046:backend/tests/test_grade_levels_tenant.py::TestGradeLevelsTenantIsolation::test_grade_levels_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2047:backend/tests/test_grade_levels_tenant.py::TestGradeLevelsTenantIsolation::test_grade_levels_same_tenant_request_is_allowed
backend\tests_list.txt:2048:backend/tests/test_grade_levels_tenant.py::TestGradeLevelsTenantIsolation::test_grade_levels_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2049:backend/tests/test_grade_levels_tenant.py::TestGradeLevelsTenantIsolation::test_grade_levels_isolation_keyword_present_in_source
backend\tests_list.txt:2062:backend/tests/test_grades_report_cards_tenant.py::TestGradesReportCardsTenantIsolation::test_grades_report_cards_tenant_school_ids_are_distinct
backend\tests_list.txt:2063:backend/tests/test_grades_report_cards_tenant.py::TestGradesReportCardsTenantIsolation::test_grades_report_cards_user_bound_to_correct_school
backend\tests_list.txt:2064:backend/tests/test_grades_report_cards_tenant.py::TestGradesReportCardsTenantIsolation::test_grades_report_cards_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2065:backend/tests/test_grades_report_cards_tenant.py::TestGradesReportCardsTenantIsolation::test_grades_report_cards_same_tenant_request_is_allowed
backend\tests_list.txt:2066:backend/tests/test_grades_report_cards_tenant.py::TestGradesReportCardsTenantIsolation::test_grades_report_cards_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2067:backend/tests/test_grades_report_cards_tenant.py::TestGradesReportCardsTenantIsolation::test_grades_report_cards_isolation_keyword_present_in_source
backend\tests_list.txt:2088:backend/tests/test_mission_metrics_tenant.py::TestMissionMetricsTenantIsolation::test_mission_metrics_tenant_school_ids_are_distinct
backend\tests_list.txt:2089:backend/tests/test_mission_metrics_tenant.py::TestMissionMetricsTenantIsolation::test_mission_metrics_user_bound_to_correct_school
backend\tests_list.txt:2090:backend/tests/test_mission_metrics_tenant.py::TestMissionMetricsTenantIsolation::test_mission_metrics_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2091:backend/tests/test_mission_metrics_tenant.py::TestMissionMetricsTenantIsolation::test_mission_metrics_same_tenant_request_is_allowed
backend\tests_list.txt:2092:backend/tests/test_mission_metrics_tenant.py::TestMissionMetricsTenantIsolation::test_mission_metrics_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2093:backend/tests/test_mission_metrics_tenant.py::TestMissionMetricsTenantIsolation::test_mission_metrics_isolation_keyword_present_in_source
backend\tests_list.txt:2106:backend/tests/test_mobile_family_app_tenant.py::TestMobileFamilyAppTenantIsolation::test_mobile_family_app_tenant_school_ids_are_distinct
backend\tests_list.txt:2107:backend/tests/test_mobile_family_app_tenant.py::TestMobileFamilyAppTenantIsolation::test_mobile_family_app_user_bound_to_correct_school
backend\tests_list.txt:2108:backend/tests/test_mobile_family_app_tenant.py::TestMobileFamilyAppTenantIsolation::test_mobile_family_app_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2109:backend/tests/test_mobile_family_app_tenant.py::TestMobileFamilyAppTenantIsolation::test_mobile_family_app_same_tenant_request_is_allowed
backend\tests_list.txt:2110:backend/tests/test_mobile_family_app_tenant.py::TestMobileFamilyAppTenantIsolation::test_mobile_family_app_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2111:backend/tests/test_mobile_family_app_tenant.py::TestMobileFamilyAppTenantIsolation::test_mobile_family_app_isolation_keyword_present_in_source
backend\tests_list.txt:2125:backend/tests/test_notifications_framework_tenant.py::TestNotificationsFrameworkTenantIsolation::test_notifications_framework_tenant_school_ids_are_distinct
backend\tests_list.txt:2126:backend/tests/test_notifications_framework_tenant.py::TestNotificationsFrameworkTenantIsolation::test_notifications_framework_user_bound_to_correct_school
backend\tests_list.txt:2127:backend/tests/test_notifications_framework_tenant.py::TestNotificationsFrameworkTenantIsolation::test_notifications_framework_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2128:backend/tests/test_notifications_framework_tenant.py::TestNotificationsFrameworkTenantIsolation::test_notifications_framework_same_tenant_request_is_allowed
backend\tests_list.txt:2129:backend/tests/test_notifications_framework_tenant.py::TestNotificationsFrameworkTenantIsolation::test_notifications_framework_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2130:backend/tests/test_notifications_framework_tenant.py::TestNotificationsFrameworkTenantIsolation::test_notifications_framework_isolation_keyword_present_in_source
backend\tests_list.txt:2143:backend/tests/test_nurse_health_office_tenant.py::TestNurseHealthOfficeTenantIsolation::test_nurse_health_office_tenant_school_ids_are_distinct
backend\tests_list.txt:2144:backend/tests/test_nurse_health_office_tenant.py::TestNurseHealthOfficeTenantIsolation::test_nurse_health_office_user_bound_to_correct_school
backend\tests_list.txt:2145:backend/tests/test_nurse_health_office_tenant.py::TestNurseHealthOfficeTenantIsolation::test_nurse_health_office_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2146:backend/tests/test_nurse_health_office_tenant.py::TestNurseHealthOfficeTenantIsolation::test_nurse_health_office_same_tenant_request_is_allowed
backend\tests_list.txt:2147:backend/tests/test_nurse_health_office_tenant.py::TestNurseHealthOfficeTenantIsolation::test_nurse_health_office_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2148:backend/tests/test_nurse_health_office_tenant.py::TestNurseHealthOfficeTenantIsolation::test_nurse_health_office_isolation_keyword_present_in_source
backend\tests_list.txt:2161:backend/tests/test_parent_portal_tenant.py::TestParentPortalTenantIsolation::test_parent_portal_tenant_school_ids_are_distinct
backend\tests_list.txt:2162:backend/tests/test_parent_portal_tenant.py::TestParentPortalTenantIsolation::test_parent_portal_user_bound_to_correct_school
backend\tests_list.txt:2163:backend/tests/test_parent_portal_tenant.py::TestParentPortalTenantIsolation::test_parent_portal_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2164:backend/tests/test_parent_portal_tenant.py::TestParentPortalTenantIsolation::test_parent_portal_same_tenant_request_is_allowed
backend\tests_list.txt:2165:backend/tests/test_parent_portal_tenant.py::TestParentPortalTenantIsolation::test_parent_portal_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2166:backend/tests/test_parent_portal_tenant.py::TestParentPortalTenantIsolation::test_parent_portal_isolation_keyword_present_in_source
backend\tests_list.txt:2167:backend/tests/test_phase72_tenant_isolation.py::Phase72GradebookTenantTests::test_correct_school_returns_200
backend\tests_list.txt:2168:backend/tests/test_phase72_tenant_isolation.py::Phase72GradebookTenantTests::test_missing_header_returns_400
backend\tests_list.txt:2169:backend/tests/test_phase72_tenant_isolation.py::Phase72GradebookTenantTests::test_unauthenticated_returns_401_or_403
backend\tests_list.txt:2170:backend/tests/test_phase72_tenant_isolation.py::Phase72GradebookTenantTests::test_wrong_school_nonstaff_returns_404
backend\tests_list.txt:2171:backend/tests/test_phase72_tenant_isolation.py::Phase72BillingRunsTenantTests::test_correct_school_returns_200
backend\tests_list.txt:2172:backend/tests/test_phase72_tenant_isolation.py::Phase72BillingRunsTenantTests::test_missing_header_returns_400
backend\tests_list.txt:2173:backend/tests/test_phase72_tenant_isolation.py::Phase72BillingRunsTenantTests::test_unauthenticated_returns_401_or_403
backend\tests_list.txt:2174:backend/tests/test_phase72_tenant_isolation.py::Phase72BillingRunsTenantTests::test_wrong_school_nonstaff_returns_404
backend\tests_list.txt:2175:backend/tests/test_phase72_tenant_isolation.py::Phase72DisciplineTenantTests::test_correct_school_returns_200
backend\tests_list.txt:2176:backend/tests/test_phase72_tenant_isolation.py::Phase72DisciplineTenantTests::test_cross_tenant_data_isolation_confirmed
backend\tests_list.txt:2177:backend/tests/test_phase72_tenant_isolation.py::Phase72DisciplineTenantTests::test_missing_header_returns_400
backend\tests_list.txt:2178:backend/tests/test_phase72_tenant_isolation.py::Phase72DisciplineTenantTests::test_unauthenticated_returns_401_or_403
backend\tests_list.txt:2179:backend/tests/test_phase72_tenant_isolation.py::Phase72DisciplineTenantTests::test_wrong_school_nonstaff_returns_404
backend\tests_list.txt:2180:backend/tests/test_phase72_tenant_isolation.py::Phase72FinancialAidTenantTests::test_correct_school_scoping_passes
backend\tests_list.txt:2181:backend/tests/test_phase72_tenant_isolation.py::Phase72FinancialAidTenantTests::test_missing_header_returns_400
backend\tests_list.txt:2182:backend/tests/test_phase72_tenant_isolation.py::Phase72FinancialAidTenantTests::test_unauthenticated_returns_401_or_403
backend\tests_list.txt:2183:backend/tests/test_phase72_tenant_isolation.py::Phase72FinancialAidTenantTests::test_wrong_school_nonstaff_returns_404
backend\tests_list.txt:2184:backend/tests/test_phase72_tenant_isolation.py::Phase72AdmissionsApplicationsTenantTests::test_correct_school_scoping_passes
backend\tests_list.txt:2185:backend/tests/test_phase72_tenant_isolation.py::Phase72AdmissionsApplicationsTenantTests::test_missing_header_returns_400
backend\tests_list.txt:2186:backend/tests/test_phase72_tenant_isolation.py::Phase72AdmissionsApplicationsTenantTests::test_unauthenticated_returns_401_or_403
backend\tests_list.txt:2187:backend/tests/test_phase72_tenant_isolation.py::Phase72AdmissionsApplicationsTenantTests::test_wrong_school_nonstaff_returns_404
backend\tests_list.txt:2188:backend/tests/test_phase72_tenant_isolation.py::Phase72AdmissionsEnrollTenantTests::test_correct_school_scoping_passes
backend\tests_list.txt:2189:backend/tests/test_phase72_tenant_isolation.py::Phase72AdmissionsEnrollTenantTests::test_missing_header_returns_400
backend\tests_list.txt:2190:backend/tests/test_phase72_tenant_isolation.py::Phase72AdmissionsEnrollTenantTests::test_unauthenticated_returns_401_or_403
backend\tests_list.txt:2191:backend/tests/test_phase72_tenant_isolation.py::Phase72AdmissionsEnrollTenantTests::test_wrong_school_nonstaff_returns_404
backend\tests_list.txt:2204:backend/tests/test_portrait_graduate_tenant.py::TestPortraitGraduateTenantIsolation::test_portrait_graduate_tenant_school_ids_are_distinct
backend\tests_list.txt:2205:backend/tests/test_portrait_graduate_tenant.py::TestPortraitGraduateTenantIsolation::test_portrait_graduate_user_bound_to_correct_school
backend\tests_list.txt:2206:backend/tests/test_portrait_graduate_tenant.py::TestPortraitGraduateTenantIsolation::test_portrait_graduate_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2207:backend/tests/test_portrait_graduate_tenant.py::TestPortraitGraduateTenantIsolation::test_portrait_graduate_same_tenant_request_is_allowed
backend\tests_list.txt:2208:backend/tests/test_portrait_graduate_tenant.py::TestPortraitGraduateTenantIsolation::test_portrait_graduate_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2209:backend/tests/test_portrait_graduate_tenant.py::TestPortraitGraduateTenantIsolation::test_portrait_graduate_isolation_keyword_present_in_source
backend\tests_list.txt:2222:backend/tests/test_reporting_data_access_tenant.py::TestReportingDataAccessTenantIsolation::test_reporting_data_access_tenant_school_ids_are_distinct
backend\tests_list.txt:2223:backend/tests/test_reporting_data_access_tenant.py::TestReportingDataAccessTenantIsolation::test_reporting_data_access_user_bound_to_correct_school
backend\tests_list.txt:2224:backend/tests/test_reporting_data_access_tenant.py::TestReportingDataAccessTenantIsolation::test_reporting_data_access_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2225:backend/tests/test_reporting_data_access_tenant.py::TestReportingDataAccessTenantIsolation::test_reporting_data_access_same_tenant_request_is_allowed
backend\tests_list.txt:2226:backend/tests/test_reporting_data_access_tenant.py::TestReportingDataAccessTenantIsolation::test_reporting_data_access_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2227:backend/tests/test_reporting_data_access_tenant.py::TestReportingDataAccessTenantIsolation::test_reporting_data_access_isolation_keyword_present_in_source
backend\tests_list.txt:2248:backend/tests/test_schedule_builder_tenant.py::TestScheduleBuilderTenantIsolation::test_schedule_builder_tenant_school_ids_are_distinct
backend\tests_list.txt:2249:backend/tests/test_schedule_builder_tenant.py::TestScheduleBuilderTenantIsolation::test_schedule_builder_user_bound_to_correct_school
backend\tests_list.txt:2250:backend/tests/test_schedule_builder_tenant.py::TestScheduleBuilderTenantIsolation::test_schedule_builder_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2251:backend/tests/test_schedule_builder_tenant.py::TestScheduleBuilderTenantIsolation::test_schedule_builder_same_tenant_request_is_allowed
backend\tests_list.txt:2252:backend/tests/test_schedule_builder_tenant.py::TestScheduleBuilderTenantIsolation::test_schedule_builder_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2253:backend/tests/test_schedule_builder_tenant.py::TestScheduleBuilderTenantIsolation::test_schedule_builder_isolation_keyword_present_in_source
backend\tests_list.txt:2266:backend/tests/test_school_profile_tenant.py::TestSchoolProfileTenantIsolation::test_school_profile_tenant_school_ids_are_distinct
backend\tests_list.txt:2267:backend/tests/test_school_profile_tenant.py::TestSchoolProfileTenantIsolation::test_school_profile_user_bound_to_correct_school
backend\tests_list.txt:2268:backend/tests/test_school_profile_tenant.py::TestSchoolProfileTenantIsolation::test_school_profile_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2269:backend/tests/test_school_profile_tenant.py::TestSchoolProfileTenantIsolation::test_school_profile_same_tenant_request_is_allowed
backend\tests_list.txt:2270:backend/tests/test_school_profile_tenant.py::TestSchoolProfileTenantIsolation::test_school_profile_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2271:backend/tests/test_school_profile_tenant.py::TestSchoolProfileTenantIsolation::test_school_profile_isolation_keyword_present_in_source
backend\tests_list.txt:2284:backend/tests/test_school_year_term_tenant.py::TestSchoolYearTermTenantIsolation::test_school_year_term_tenant_school_ids_are_distinct
backend\tests_list.txt:2285:backend/tests/test_school_year_term_tenant.py::TestSchoolYearTermTenantIsolation::test_school_year_term_user_bound_to_correct_school
backend\tests_list.txt:2286:backend/tests/test_school_year_term_tenant.py::TestSchoolYearTermTenantIsolation::test_school_year_term_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2287:backend/tests/test_school_year_term_tenant.py::TestSchoolYearTermTenantIsolation::test_school_year_term_same_tenant_request_is_allowed
backend\tests_list.txt:2288:backend/tests/test_school_year_term_tenant.py::TestSchoolYearTermTenantIsolation::test_school_year_term_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2289:backend/tests/test_school_year_term_tenant.py::TestSchoolYearTermTenantIsolation::test_school_year_term_isolation_keyword_present_in_source
backend\tests_list.txt:2311:backend/tests/test_service_outreach_tenant.py::TestServiceOutreachTenantIsolation::test_service_outreach_tenant_school_ids_are_distinct
backend\tests_list.txt:2312:backend/tests/test_service_outreach_tenant.py::TestServiceOutreachTenantIsolation::test_service_outreach_user_bound_to_correct_school
backend\tests_list.txt:2313:backend/tests/test_service_outreach_tenant.py::TestServiceOutreachTenantIsolation::test_service_outreach_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2314:backend/tests/test_service_outreach_tenant.py::TestServiceOutreachTenantIsolation::test_service_outreach_same_tenant_request_is_allowed
backend\tests_list.txt:2315:backend/tests/test_service_outreach_tenant.py::TestServiceOutreachTenantIsolation::test_service_outreach_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2316:backend/tests/test_service_outreach_tenant.py::TestServiceOutreachTenantIsolation::test_service_outreach_isolation_keyword_present_in_source
backend\tests_list.txt:2329:backend/tests/test_shared_design_system_tenant.py::TestSharedDesignSystemTenantIsolation::test_shared_design_system_tenant_school_ids_are_distinct
backend\tests_list.txt:2330:backend/tests/test_shared_design_system_tenant.py::TestSharedDesignSystemTenantIsolation::test_shared_design_system_user_bound_to_correct_school
backend\tests_list.txt:2331:backend/tests/test_shared_design_system_tenant.py::TestSharedDesignSystemTenantIsolation::test_shared_design_system_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2332:backend/tests/test_shared_design_system_tenant.py::TestSharedDesignSystemTenantIsolation::test_shared_design_system_same_tenant_request_is_allowed
backend\tests_list.txt:2333:backend/tests/test_shared_design_system_tenant.py::TestSharedDesignSystemTenantIsolation::test_shared_design_system_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2334:backend/tests/test_shared_design_system_tenant.py::TestSharedDesignSystemTenantIsolation::test_shared_design_system_isolation_keyword_present_in_source
backend\tests_list.txt:2347:backend/tests/test_shared_frontend_shell_tenant.py::TestSharedFrontendShellTenantIsolation::test_shared_frontend_shell_tenant_school_ids_are_distinct
backend\tests_list.txt:2348:backend/tests/test_shared_frontend_shell_tenant.py::TestSharedFrontendShellTenantIsolation::test_shared_frontend_shell_user_bound_to_correct_school
backend\tests_list.txt:2349:backend/tests/test_shared_frontend_shell_tenant.py::TestSharedFrontendShellTenantIsolation::test_shared_frontend_shell_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2350:backend/tests/test_shared_frontend_shell_tenant.py::TestSharedFrontendShellTenantIsolation::test_shared_frontend_shell_same_tenant_request_is_allowed
backend\tests_list.txt:2351:backend/tests/test_shared_frontend_shell_tenant.py::TestSharedFrontendShellTenantIsolation::test_shared_frontend_shell_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2352:backend/tests/test_shared_frontend_shell_tenant.py::TestSharedFrontendShellTenantIsolation::test_shared_frontend_shell_isolation_keyword_present_in_source
backend\tests_list.txt:2354:backend/tests/test_shell_backend_seeded_contract.py::ShellBackendSeededContractTests::test_canonical_shell_contract_returns_success_under_seeded_tenant_context
backend\tests_list.txt:2368:backend/tests/test_staff_faculty_tenant.py::TestStaffFacultyTenantIsolation::test_staff_faculty_tenant_school_ids_are_distinct
backend\tests_list.txt:2369:backend/tests/test_staff_faculty_tenant.py::TestStaffFacultyTenantIsolation::test_staff_faculty_user_bound_to_correct_school
backend\tests_list.txt:2370:backend/tests/test_staff_faculty_tenant.py::TestStaffFacultyTenantIsolation::test_staff_faculty_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2371:backend/tests/test_staff_faculty_tenant.py::TestStaffFacultyTenantIsolation::test_staff_faculty_same_tenant_request_is_allowed
backend\tests_list.txt:2372:backend/tests/test_staff_faculty_tenant.py::TestStaffFacultyTenantIsolation::test_staff_faculty_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2373:backend/tests/test_staff_faculty_tenant.py::TestStaffFacultyTenantIsolation::test_staff_faculty_isolation_keyword_present_in_source
backend\tests_list.txt:2386:backend/tests/test_student_care_discipline_tenant.py::TestStudentCareDisciplineTenantIsolation::test_student_care_discipline_tenant_school_ids_are_distinct
backend\tests_list.txt:2387:backend/tests/test_student_care_discipline_tenant.py::TestStudentCareDisciplineTenantIsolation::test_student_care_discipline_user_bound_to_correct_school
backend\tests_list.txt:2388:backend/tests/test_student_care_discipline_tenant.py::TestStudentCareDisciplineTenantIsolation::test_student_care_discipline_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2389:backend/tests/test_student_care_discipline_tenant.py::TestStudentCareDisciplineTenantIsolation::test_student_care_discipline_same_tenant_request_is_allowed
backend\tests_list.txt:2390:backend/tests/test_student_care_discipline_tenant.py::TestStudentCareDisciplineTenantIsolation::test_student_care_discipline_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2391:backend/tests/test_student_care_discipline_tenant.py::TestStudentCareDisciplineTenantIsolation::test_student_care_discipline_isolation_keyword_present_in_source
backend\tests_list.txt:2404:backend/tests/test_student_master_record_tenant.py::TestStudentMasterRecordTenantIsolation::test_student_master_record_tenant_school_ids_are_distinct
backend\tests_list.txt:2405:backend/tests/test_student_master_record_tenant.py::TestStudentMasterRecordTenantIsolation::test_student_master_record_user_bound_to_correct_school
backend\tests_list.txt:2406:backend/tests/test_student_master_record_tenant.py::TestStudentMasterRecordTenantIsolation::test_student_master_record_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2407:backend/tests/test_student_master_record_tenant.py::TestStudentMasterRecordTenantIsolation::test_student_master_record_same_tenant_request_is_allowed
backend\tests_list.txt:2408:backend/tests/test_student_master_record_tenant.py::TestStudentMasterRecordTenantIsolation::test_student_master_record_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2409:backend/tests/test_student_master_record_tenant.py::TestStudentMasterRecordTenantIsolation::test_student_master_record_isolation_keyword_present_in_source
backend\tests_list.txt:2422:backend/tests/test_survey_sentiment_tenant.py::TestSurveySentimentTenantIsolation::test_survey_sentiment_tenant_school_ids_are_distinct
backend\tests_list.txt:2423:backend/tests/test_survey_sentiment_tenant.py::TestSurveySentimentTenantIsolation::test_survey_sentiment_user_bound_to_correct_school
backend\tests_list.txt:2424:backend/tests/test_survey_sentiment_tenant.py::TestSurveySentimentTenantIsolation::test_survey_sentiment_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2425:backend/tests/test_survey_sentiment_tenant.py::TestSurveySentimentTenantIsolation::test_survey_sentiment_same_tenant_request_is_allowed
backend\tests_list.txt:2426:backend/tests/test_survey_sentiment_tenant.py::TestSurveySentimentTenantIsolation::test_survey_sentiment_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2427:backend/tests/test_survey_sentiment_tenant.py::TestSurveySentimentTenantIsolation::test_survey_sentiment_isolation_keyword_present_in_source
backend\tests_list.txt:2428:backend/tests/test_tenant_auto_scope.py::TenantAutoScopeTests::test_queryset_auto_filters_by_school
backend\tests_list.txt:2429:backend/tests/test_tenant_auto_scope.py::TenantAutoScopeTests::test_queryset_empty_without_school_context
backend\tests_list.txt:2430:backend/tests/test_tenant_bulk_ops_guard.py::TestTenantBulkOpsGuard::test_bulk_delete_requires_tenant_context
backend\tests_list.txt:2431:backend/tests/test_tenant_bulk_ops_guard.py::TestTenantBulkOpsGuard::test_bulk_ops_scoped_to_current_tenant
backend\tests_list.txt:2432:backend/tests/test_tenant_bulk_ops_guard.py::TestTenantBulkOpsGuard::test_bulk_update_requires_tenant_context
backend\tests_list.txt:2433:backend/tests/test_tenant_context_guardrails.py::TestTenantContextGuardrails::test_context_sets_and_restores
backend\tests_list.txt:2434:backend/tests/test_tenant_context_guardrails.py::TestTenantContextGuardrails::test_nested_context_restores_prior
backend\tests_list.txt:2435:backend/tests/test_tenant_context_guardrails.py::TestTenantContextGuardrails::test_require_raises_when_missing
backend\tests_list.txt:2436:backend/tests/test_tenant_header_required.py::TenantHeaderRequiredTests::test_auth_exempt_no_header
backend\tests_list.txt:2437:backend/tests/test_tenant_header_required.py::TenantHeaderRequiredTests::test_health_exempt_no_header
backend\tests_list.txt:2438:backend/tests/test_tenant_header_required.py::TenantHeaderRequiredTests::test_options_request_no_header_allowed
backend\tests_list.txt:2439:backend/tests/test_tenant_header_required.py::TenantHeaderRequiredTests::test_other_api_requires_header
backend\tests_list.txt:2440:backend/tests/test_tenant_header_validate_school.py::TenantHeaderValidateSchoolTests::test_invalid_uuid_returns_400
backend\tests_list.txt:2441:backend/tests/test_tenant_header_validate_school.py::TenantHeaderValidateSchoolTests::test_known_school_allows_request_past_middleware
backend\tests_list.txt:2442:backend/tests/test_tenant_header_validate_school.py::TenantHeaderValidateSchoolTests::test_missing_header_defers_to_auth_on_exempt_route
backend\tests_list.txt:2443:backend/tests/test_tenant_header_validate_school.py::TenantHeaderValidateSchoolTests::test_unknown_uuid_defers_to_auth_on_exempt_route
backend\tests_list.txt:2444:backend/tests/test_tenant_isolation.py::TestTenantIsolation::test_gradebook_sections_missing_header_returns_400
backend\tests_list.txt:2445:backend/tests/test_tenant_isolation.py::TestTenantIsolation::test_gradebook_sections_cross_tenant_returns_404
backend\tests_list.txt:2446:backend/tests/test_tenant_isolation.py::TestTenantIsolation::test_billing_runs_cross_tenant_returns_404
backend\tests_list.txt:2447:backend/tests/test_tenant_isolation.py::TestTenantIsolation::test_admissions_applications_cross_tenant_returns_404
backend\tests_list.txt:2448:backend/tests/test_tenant_isolation.py::TestTenantIsolation::test_admissions_enroll_cross_tenant_returns_404
backend\tests_list.txt:2449:backend/tests/test_tenant_isolation.py::TestTenantIsolation::test_staff_same_tenant_can_reach_gradebook_surface
backend\tests_list.txt:2450:backend/tests/test_tenant_isolation.py::TestTenantIsolation::test_unauthenticated_request_is_denied
backend\tests_list.txt:2451:backend/tests/test_tenant_isolation_smoke.py::TestCrossTenantIsolation::test_cross_tenant_submission_list_hidden
backend\tests_list.txt:2452:backend/tests/test_tenant_isolation_smoke.py::TestCrossTenantIsolation::test_cross_tenant_submission_detail_denied
backend\tests_list.txt:2453:backend/tests/test_tenant_lifecycle_cleanup.py::TestTenantLifecycleCleanup::test_context_cleared_after_exception_request
backend\tests_list.txt:2454:backend/tests/test_tenant_lifecycle_cleanup.py::TestTenantLifecycleCleanup::test_context_cleared_after_ok_request
backend\tests_list.txt:2455:backend/tests/test_tenant_violation_telemetry.py::TestTenantViolationTelemetry::test_logs_bulk_delete_missing_context
backend\tests_list.txt:2456:backend/tests/test_tenant_violation_telemetry.py::TestTenantViolationTelemetry::test_logs_bulk_update_missing_context
backend\tests_list.txt:2457:backend/tests/test_tenant_violation_telemetry.py::TestTenantViolationTelemetry::test_logs_context_required_violation
backend\tests_list.txt:2458:backend/tests/test_tenant_violation_telemetry.py::TestTenantViolationTelemetry::test_logs_cross_tenant_write_violation
backend\tests_list.txt:2459:backend/tests/test_tenant_write_guard.py::TestTenantWriteGuard::test_create_binds_school_when_missing
backend\tests_list.txt:2460:backend/tests/test_tenant_write_guard.py::TestTenantWriteGuard::test_cross_tenant_write_blocked
backend\tests_list.txt:2473:backend/tests/test_transportation_tenant.py::TestTransportationTenantIsolation::test_transportation_tenant_school_ids_are_distinct
backend\tests_list.txt:2474:backend/tests/test_transportation_tenant.py::TestTransportationTenantIsolation::test_transportation_user_bound_to_correct_school
backend\tests_list.txt:2475:backend/tests/test_transportation_tenant.py::TestTransportationTenantIsolation::test_transportation_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2476:backend/tests/test_transportation_tenant.py::TestTransportationTenantIsolation::test_transportation_same_tenant_request_is_allowed
backend\tests_list.txt:2477:backend/tests/test_transportation_tenant.py::TestTransportationTenantIsolation::test_transportation_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2478:backend/tests/test_transportation_tenant.py::TestTransportationTenantIsolation::test_transportation_isolation_keyword_present_in_source
backend\tests_list.txt:2491:backend/tests/test_volunteer_family_engagement_tenant.py::TestVolunteerFamilyEngagementTenantIsolation::test_volunteer_family_engagement_tenant_school_ids_are_distinct
backend\tests_list.txt:2492:backend/tests/test_volunteer_family_engagement_tenant.py::TestVolunteerFamilyEngagementTenantIsolation::test_volunteer_family_engagement_user_bound_to_correct_school
backend\tests_list.txt:2493:backend/tests/test_volunteer_family_engagement_tenant.py::TestVolunteerFamilyEngagementTenantIsolation::test_volunteer_family_engagement_cross_tenant_header_is_rejected_or_scoped
backend\tests_list.txt:2494:backend/tests/test_volunteer_family_engagement_tenant.py::TestVolunteerFamilyEngagementTenantIsolation::test_volunteer_family_engagement_same_tenant_request_is_allowed
backend\tests_list.txt:2495:backend/tests/test_volunteer_family_engagement_tenant.py::TestVolunteerFamilyEngagementTenantIsolation::test_volunteer_family_engagement_unauthenticated_cross_tenant_is_denied
backend\tests_list.txt:2496:backend/tests/test_volunteer_family_engagement_tenant.py::TestVolunteerFamilyEngagementTenantIsolation::test_volunteer_family_engagement_isolation_keyword_present_in_source
backend\tests_list.txt:2500:backend/tests/test_wizard_contract.py::TestWizardTenantIsolation::test_all_wizards_isolate_tenants
backend\tests_list.txt:2512:backend/transportation/tests/test_transportation.py::TestVehicles::test_create_denied_for_readonly_role
backend\tests_list.txt:2515:backend/transportation/tests/test_transportation.py::TestVehicles::test_cross_tenant_isolation
backend\tests_list.txt:2520:backend/transportation/tests/test_transportation.py::TestDrivers::test_cross_tenant
backend\tests_list.txt:2521:backend/transportation/tests/test_transportation.py::TestDrivers::test_readonly_role_can_list
backend\tests_list.txt:2525:backend/transportation/tests/test_transportation.py::TestRoutes::test_stops_action_cross_tenant_denied
backend\tests_list.txt:2526:backend/transportation/tests/test_transportation.py::TestRoutes::test_cross_tenant
backend\tests_list.txt:2529:backend/transportation/tests/test_transportation.py::TestStops::test_cross_tenant
backend\tests_list.txt:2533:backend/transportation/tests/test_transportation.py::TestStudentRiders::test_cross_tenant
backend\tests_list.txt:2536:backend/transportation/tests/test_transportation.py::TestAssignments::test_cross_tenant
backend\tests_list.txt:2540:backend/transportation/tests/test_transportation.py::TestRideEvents::test_cross_tenant
backend\tests_list.txt:2544:backend/transportation/tests/test_transportation.py::TestDispatchRunSheet::test_run_sheet_cross_tenant
backend\tests_list.txt:2547:backend/transportation/tests/test_transportation.py::TestPermissions::test_non_transport_role_cannot_create_vehicle
backend\tests_list.txt:2548:backend/transportation/tests/test_transportation.py::TestPermissions::test_admin_role_can_create_vehicle
backend\tests_list.txt:2549:backend/transportation/tests/test_transportation.py::TestPermissions::test_ops_role_can_create_driver
frontend/dashboards/src\components\crown-dashboard\CrownInsightPanel.jsx:27:          <div className="launch-chart-empty" role="status">Trend data will appear here when records are available.</div>
frontend/dashboards/src\components\system\TopStatusStrip.jsx:13:    return parsed?.role || parsed?.roles?.[0] || 'guest';
frontend/dashboards/src\components\system\TopStatusStrip.jsx:21:  const role = getRole();
frontend/dashboards/src\components\system\TopStatusStrip.jsx:26:        <Chip size="small" label={`Role: ${role}`} />
backend\discipline\models.py:10:    - school-scoped (tenant)
backend\advancement\api.py:3:from rest_framework.decorators import api_view, permission_classes, action
backend\advancement\api.py:5:from rest_framework.permissions import IsAuthenticated
backend\advancement\api.py:14:from core.permissions import CrownModulePermission, require_permission
backend\advancement\api.py:69:        raise PermissionDenied("Tenant context required (X-School-Id header missing).")
backend\advancement\api.py:80:    permission_classes = [CrownModulePermission("advancement.view", write_code="advancement.edit")]
backend\advancement\api.py:112:    permission_classes = [CrownModulePermission("advancement.view", write_code="advancement.edit")]
backend\advancement\api.py:144:    permission_classes = [CrownModulePermission("advancement.view", write_code="advancement.edit")]
backend\advancement\api.py:164:    permission_classes = [CrownModulePermission("advancement.view", write_code="advancement.edit")]
backend\advancement\api.py:187:    permission_classes = [CrownModulePermission("advancement.view", write_code="advancement.edit")]
backend\advancement\api.py:218:    permission_classes = [CrownModulePermission("advancement.view", write_code="advancement.edit")]
backend\advancement\api.py:238:@permission_classes([IsAuthenticated])
backend\advancement\api.py:270:@permission_classes([IsAuthenticated])
backend\advancement\api.py:303:@require_permission("advancement.view")
backend\advancement\api.py:319:@permission_classes([IsAuthenticated])
backend\advancement\api.py:388:    permission_classes = [CrownModulePermission("advancement.view", write_code="advancement.edit")]
backend\advancement\api.py:406:    permission_classes = [CrownModulePermission("advancement.view", write_code="advancement.edit")]
backend\advancement\api.py:424:    permission_classes = [CrownModulePermission("advancement.view", write_code="advancement.edit")]
backend\advancement\api.py:441:@permission_classes([IsAuthenticated])
backend\advancement\api.py:467:@permission_classes([IsAuthenticated])
backend\advancement\api.py:490:@permission_classes([IsAuthenticated])
backend\advancement\api.py:516:@permission_classes([IsAuthenticated])
backend\advancement\api.py:538:@permission_classes([IsAuthenticated])
backend\advancement\api.py:565:@permission_classes([IsAuthenticated])
backend\advancement\api.py:588:@permission_classes([IsAuthenticated])
backend\advancement\api.py:624:    permission_classes = [_PERM_S3]
backend\advancement\api.py:638:    permission_classes = [_PERM_S3]
backend\advancement\api.py:655:    permission_classes = [_PERM_S3]
backend\advancement\api.py:676:    permission_classes = [_PERM_S3]
backend\advancement\api.py:690:    permission_classes = [_PERM_S3]
backend\advancement\api.py:711:    permission_classes = [_PERM_S3]
backend\advancement\api.py:728:    permission_classes = [_PERM_S3]
backend\advancement\api.py:750:    permission_classes = [_PERM_S3]
backend\advancement\api.py:764:    permission_classes = [_PERM_S3]
backend\advancement\api.py:778:    permission_classes = [_PERM_S3]
backend\advancement\api.py:792:    permission_classes = [_PERM_S3]
backend\advancement\api.py:806:    permission_classes = [_PERM_S3]
backend\advancement\api.py:820:    permission_classes = [_PERM_S3]
backend\advancement\api.py:838:    permission_classes = [_PERM_S3]
backend\advancement\api.py:855:@permission_classes([IsAuthenticated])
backend\advancement\api.py:894:@permission_classes([IsAuthenticated])
backend\advancement\api.py:920:@permission_classes([IsAuthenticated])
backend\advancement\api.py:952:@permission_classes([IsAuthenticated])
backend\advancement\api.py:981:@permission_classes([IsAuthenticated])
backend\advancement\api.py:1012:@permission_classes([CrownModulePermission("advancement.view")])
backend\advancement\api.py:1034:@permission_classes([CrownModulePermission("advancement.view")])
backend\advancement\api.py:1072:@permission_classes([CrownModulePermission("advancement.edit")])
backend\advancement\api.py:1111:@permission_classes([CrownModulePermission("advancement.view")])
backend\advancement\api.py:1176:@permission_classes([CrownModulePermission("advancement.view")])
backend\advancement\api.py:1406:@permission_classes([CrownModulePermission("advancement.view")])
backend\advancement\api.py:1422:    # POST ∩┐╜ require write permission
backend\advancement\api.py:1423:    require_permission(request, "advancement.edit")
backend\advancement\api.py:1448:@permission_classes([CrownModulePermission("advancement.view")])
backend\advancement\api.py:1492:@permission_classes([CrownModulePermission("advancement.view")])
backend\advancement\api.py:1527:@permission_classes([CrownModulePermission("advancement.view")])
backend\advancement\api.py:1586:@permission_classes([CrownModulePermission("advancement.view")])
frontend/dashboards/src\config\dashboardTemplates\volunteerManagementDashboard.js:19:  user: { initials: 'VM', name: 'Volunteer Coordinator', role: 'Community ΓÇö Volunteer Programs & Family Engagement' },
frontend/dashboards/src\pages\VolunteerManagementDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="volunteerManagement" />;
frontend/dashboards/src\components\crown-dashboard\CrownDashboardTemplate.jsx:18:function renderActionsByRole(actions = [], roleKey) {
frontend/dashboards/src\components\crown-dashboard\CrownDashboardTemplate.jsx:21:    return action.allowedRoles.includes(roleKey);
frontend/dashboards/src\components\crown-dashboard\CrownDashboardTemplate.jsx:25:export default function CrownDashboardTemplate({ config, roleKey }) {
frontend/dashboards/src\components\crown-dashboard\CrownDashboardTemplate.jsx:32:  const actions = renderActionsByRole(config.quickActions || [], roleKey);
frontend/dashboards/src\config\dashboardTemplates\transportationDashboard.js:19:  user: { initials: 'TR', name: 'Transportation', role: 'Operations ΓÇö Student Transportation' },
frontend/dashboards/src\pages\TransportationDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="transportation" />;
frontend/dashboards/src\config\dashboardTemplates\teacherDashboard.js:31:    role: 'Teacher ΓÇö English & History',
frontend/dashboards/src\config\dashboardTemplates\studentDashboard.js:31:    role: 'Student ΓÇö Grade 10',
frontend/dashboards/src\config\dashboardTemplates\studentCareDashboard.js:19:  user: { initials: 'SC', name: 'Student Care Team', role: 'Counseling ΓÇö Student Wellness & Support' },
frontend/dashboards/src\config\dashboardTemplates\spiritualLifeDashboard.js:17:  user: { initials: 'CH', name: 'Chaplain', role: 'Spiritual Life ΓÇö Formation & Pastoral Care' },
frontend/dashboards/src\config\dashboardTemplates\schoolAdministratorDashboard.js:29:    role: 'School Administrator',
frontend/dashboards/src\config\dashboardTemplates\schedulingDashboard.js:19:  user: { initials: 'SC', name: 'Scheduling Office', role: 'Academics ΓÇö Master Schedule & Sections' },
frontend/dashboards/src\config\dashboardTemplates\safetySecurityDashboard.js:19:  user: { initials: 'SS', name: 'Safety & Security', role: 'Operations ΓÇö Campus Safety & Emergency Management' },
frontend/dashboards/src\config\dashboardTemplates\revenueOperationsDashboard.js:19:  user: { initials: 'RO', name: 'Revenue Operations', role: 'Platform ΓÇö Revenue & Subscription Management' },
frontend/dashboards/src\config\dashboardTemplates\releaseReliabilityDashboard.js:19:  user: { initials: 'RR', name: 'Release & Reliability', role: 'Platform ΓÇö Release Engineering & Site Reliability' },
frontend/dashboards/src\pages\TeacherDashboard.jsx:6:  return <CrownDashboardTemplate config={config} roleKey="teacher" />;
frontend/dashboards/src\config\dashboardTemplates\registrarDashboard.js:17:  user: { initials: 'RG', name: 'Registrar', role: 'Registrar ΓÇö Records & Enrollment' },
frontend/dashboards/src\config\dashboardTemplates\portraitServiceDashboard.js:19:  user: { initials: 'SH', name: 'Service Hours Coordinator', role: 'Student Life ΓÇö Service Learning & Portrait Hours' },
frontend/dashboards/src\config\dashboardTemplates\parentDashboard.js:31:    role: 'Parent / Guardian',
frontend/dashboards/src\config\dashboardTemplates\parentDashboard.js:48:    { title: 'Confirm field trip permission slip for Aiden', detail: 'Science museum trip ΓÇö consent required by Friday noon.', state: 'Due Friday', tone: 'warn' },
frontend/dashboards/src\config\dashboardTemplates\parentDashboard.js:170:      summary: 'Field trip permission and chapel schedule are the active items requiring family action.',
frontend/dashboards/src\config\dashboardTemplates\parentDashboard.js:178:        'Aiden: Science museum field trip ΓÇö permission due Friday',
frontend/dashboards/src\config\dashboardTemplates\parentDashboard.js:236:    'Field trip permission reminder received for Aiden.',
frontend/dashboards/src\config\dashboardTemplates\officeDashboard.js:17:  user: { initials: 'OF', name: 'Office Manager', role: 'Office & HR ΓÇö Operations & Compliance' },
frontend/dashboards/src\config\dashboardTemplates\networkBenchmarkingDashboard.js:19:  user: { initials: 'NB', name: 'Network Benchmarking', role: 'Analytics ΓÇö School Performance & Benchmarking' },
frontend/dashboards/src\config\dashboardTemplates\masterControlDashboard.js:19:  user: { initials: 'MC', name: 'Master Control', role: 'Platform ΓÇö System Oversight & Operations' },
frontend/dashboards/src\config\dashboardTemplates\masterControlDashboard.js:28:    { label: 'Users Online', value: '87', detail: 'Current active sessions across all roles.', accent: 'gold' },
frontend/dashboards/src\config\dashboardTemplates\masterControlDashboard.js:34:    { title: 'Confirm role assignments for new staff', detail: '4 new hires pending dashboard access setup.', state: 'This week', tone: 'warn' },
frontend/dashboards/src\config\dashboardTemplates\masterControlDashboard.js:40:    { title: '4 new staff pending role assignment', detail: 'Dashboard access setup required before May 1.', tone: 'warn' },
frontend/dashboards/src\config\dashboardTemplates\masterControlDashboard.js:52:      mainKpi: '87 active users ΓÇö 4 pending setup', summary: '4 new staff need role assignment before May 1.',
frontend/dashboards/src\config\dashboardTemplates\masterControlDashboard.js:54:      details: ['87 staff with active dashboard access', '4 new hires pending role assignment', '1 access issue in support queue', 'Last access audit: April 20'],
frontend/dashboards/src\config\dashboardTemplates\masterControlDashboard.js:90:    '4 new staff role assignments queued for setup.',
frontend/dashboards/src\config\dashboardTemplates\marketingDashboard.js:17:  user: { initials: 'MA', name: 'Marketing & Advancement', role: 'Marketing ΓÇö Funnel & Campaigns' },
frontend/dashboards/src\config\dashboardTemplates\libraryMediaDashboard.js:19:  user: { initials: 'LM', name: 'Library & Media Center', role: 'Academics ΓÇö Library & Media Services' },
frontend/dashboards/src\config\dashboardTemplates\itDashboard.js:17:  user: { initials: 'IT', name: 'IT Director', role: 'Technology ΓÇö Infrastructure & Devices' },
frontend/dashboards/src\config\dashboardTemplates\integrationsAutomationDashboard.js:19:  user: { initials: 'IA', name: 'Integrations & Automation', role: 'Platform ΓÇö System Integrations & Process Automation' },
frontend/dashboards/src\config\dashboardTemplates\implementationSuccessDashboard.js:19:  user: { initials: 'IS', name: 'Implementation Success', role: 'Platform ΓÇö School Onboarding & Launch Management' },
frontend/dashboards/src\config\dashboardTemplates\hrDashboard.js:19:  user: { initials: 'HR', name: 'Human Resources', role: 'Operations ΓÇö Staff & Human Resources' },
frontend/dashboards/src\config\dashboardTemplates\healthDashboard.js:17:  user: { initials: 'NU', name: 'School Nurse', role: 'Health ΓÇö Care & Compliance' },
frontend/dashboards/src\config\dashboardTemplates\foodDashboard.js:17:  user: { initials: 'FS', name: 'Food Services', role: 'Food Services ΓÇö Meals & Inventory' },
backend\admissions\views_enroll.py:41:from rest_framework.decorators import api_view, permission_classes
backend\admissions\views_enroll.py:42:from rest_framework.permissions import IsAuthenticated
backend\admissions\views_enroll.py:67:@permission_classes([IsAuthenticated])
backend\admissions\views_enroll.py:69:    school_id = get_request_school_id(request, required=True)  # 400 if missing, 404 if wrong tenant
frontend/dashboards/src\config\dashboardTemplates\fineArtsDashboard.js:19:  user: { initials: 'FA', name: 'Fine Arts Department', role: 'Arts ΓÇö Music, Visual Arts & Drama' },
frontend/dashboards/src\config\dashboardTemplates\financialAidDashboard.js:19:  user: { initials: 'FA', name: 'Financial Aid Office', role: 'Finance ΓÇö Financial Aid & Awards' },
frontend/dashboards/src\config\dashboardTemplates\financeDashboard.js:31:    role: 'Business Office Director',
frontend/dashboards/src\components\dashboard\parent\ParentPrioritiesPanel.jsx:7:    'Submit one event permission form',
frontend/dashboards/src\config\dashboardTemplates\facilitiesDashboard.js:19:  user: { initials: 'FM', name: 'Facilities Management', role: 'Operations ΓÇö Facilities & Maintenance' },
backend\admissions\views_admissions_links.py:4:from rest_framework.decorators import api_view, permission_classes
backend\admissions\views_admissions_links.py:5:from rest_framework.permissions import IsAuthenticated
backend\admissions\views_admissions_links.py:32:@permission_classes([IsAuthenticated])
backend\admissions\views_admissions_links.py:34:    school_id = get_request_school_id(request, required=True)  # 400 if missing, 404 if wrong tenant
backend\admissions\views_admissions_links.py:68:@permission_classes([IsAuthenticated])
backend\admissions\views_admissions_links.py:70:    school_id = get_request_school_id(request, required=True)  # 400 if missing, 404 if wrong tenant
frontend/dashboards/src\components\dashboard\parent\ParentMessagesCard.jsx:6:    { title: 'School Reminder', detail: 'Event permission forms due tomorrow' },
frontend/dashboards/src\config\dashboardTemplates\extendedCareDashboard.js:19:  user: { initials: 'EC', name: 'Extended Care Program', role: 'Student Services ΓÇö Before & After School Care' },
frontend/dashboards/src\config\dashboardTemplates\dataMigrationDashboard.js:19:  user: { initials: 'DM', name: 'Data Migration', role: 'Platform ΓÇö School Data Migration & Legacy System Conversion' },
frontend/dashboards/src\config\dashboardTemplates\dashboardCertificationCenterDashboard.js:19:  user: { initials: 'DC', name: 'Dashboard Certification Center', role: 'Platform ΓÇö Dashboard Quality & Certification Authority' },
frontend/dashboards/src\config\dashboardTemplates\curriculumPDDashboard.js:19:  user: { initials: 'CP', name: 'Curriculum & PD', role: 'Academics ΓÇö Curriculum Development & Professional Development' },
frontend/dashboards/src\components\dashboard\parent\ParentAlertsPanel.jsx:7:    { label: 'Event Form Needed', detail: 'Field trip permission form due tomorrow', tone: 'red' },
frontend/dashboards/src\config\dashboardTemplates\counselingDashboard.js:17:  user: { initials: 'CN', name: 'Counseling Team', role: 'Counseling ΓÇö Behavior & Wellness' },
frontend/dashboards/src\config\dashboardTemplates\complianceAuditDashboard.js:19:  user: { initials: 'CA', name: 'Compliance & Audit', role: 'Platform ΓÇö Compliance Monitoring & Internal Audit' },
frontend/dashboards/src\config\dashboardTemplates\communicationsDashboard.js:31:    role: 'Communications Coordinator',
frontend/dashboards/src\config\dashboardTemplates\boardDashboard.js:30:  user: { initials: 'BD', name: 'Board of Directors', role: 'Governance ΓÇö Strategic Oversight' },
frontend/dashboards/src\pages\TeacherAttendancePage.jsx:71:      setMsg("Submit failed. Check API + permissions.");
frontend/dashboards/src\pages\StudentServicesDashboard.jsx:70:  if (schoolId) headers['X-School-Id']   = schoolId;
backend\discipline\api\views.py:5:from rest_framework import status, permissions
backend\discipline\api\views.py:21:    Canonical tenant resolver for discipline views.
backend\discipline\api\views.py:24:      - Missing or invalid X-School-Id header  -> MissingSchoolContext (HTTP 400)
backend\discipline\api\views.py:35:    permission_classes = [permissions.IsAuthenticated]
backend\discipline\api\views.py:95:    permission_classes = [permissions.IsAuthenticated]
backend\discipline\api\views.py:108:    permission_classes = [permissions.IsAuthenticated]
backend\discipline\api\views.py:159:    permission_classes = [permissions.IsAuthenticated]
frontend/dashboards/src\components\dashboard\mastercontrol\MasterControlAlertsPanel.jsx:12:  { title: 'One tenant reporting rising failed payment retries', level: 'Medium' },
backend\admissions\serializers_admissions_links.py:40:            role = getattr(member, "role", "") or ""
backend\admissions\serializers_admissions_links.py:41:            if role not in ("PRIMARY_GUARDIAN", "GUARDIAN"):
backend\admissions\serializers_admissions_links.py:58:                    "role": role,
frontend/dashboards/src\components\crown\useCrownDashboardMetrics.js:14: *   crown.school.id    X-School-Id
frontend/dashboards/src\components\crown\useCrownDashboardMetrics.js:62:  if (schoolId) headers['X-School-Id'] = schoolId;
frontend/dashboards/src\pages\StudentDashboard.jsx:6:  return <CrownDashboardTemplate config={config} roleKey="student" />;
frontend/dashboards/src\components\crown\CrownLayout.jsx:4: * CrownLayout  app shell with permission-derived sidebar + main content area.
frontend/dashboards/src\components\crown\CrownLayout.jsx:27:    const role =
frontend/dashboards/src\components\crown\CrownLayout.jsx:28:      sessionStorage.getItem("crown.active.role") ||
frontend/dashboards/src\components\crown\CrownLayout.jsx:29:      sessionStorage.getItem("crown.role") ||
frontend/dashboards/src\components\crown\CrownLayout.jsx:35:    return { role, displayName };
frontend/dashboards/src\components\crown\CrownLayout.jsx:37:    return { role: "Role", displayName: "User" };
frontend/dashboards/src\components\crown\CrownLayout.jsx:65:  if (schoolId) headers["X-School-Id"]    = schoolId;
frontend/dashboards/src\components\crown\CrownLayout.jsx:226:              No navigation items are available for this role.
frontend/dashboards/src\components\crown\CrownLayout.jsx:300:            <span className="crown-pill">{profile.role}</span>
frontend/dashboards/src\components\crown\CrownLayout.jsx:316:            <div className="crown-global-notice" role="status" style={{ marginBottom: 12 }}>
frontend/dashboards/src\pages\StudentCareDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="studentCare" />;
frontend/dashboards/src\components\SetupProgress.jsx:27:  if (error) return <div role="alert">Failed to load setup progress: {error}</div>;
backend\board_oversight\views.py:1:from rest_framework.decorators import api_view, permission_classes
backend\board_oversight\views.py:2:from rest_framework.permissions import IsAuthenticated
backend\board_oversight\views.py:8:from core.permissions import user_has_permission
backend\board_oversight\views.py:11:from .tenant import require_school_id
backend\board_oversight\views.py:18:    if not user_has_permission(request.user, "board.view", school=school):
backend\board_oversight\views.py:26:@permission_classes([IsAuthenticated])
backend\board_oversight\views.py:39:@permission_classes([IsAuthenticated])
backend\board_oversight\views.py:51:@permission_classes([IsAuthenticated])
backend\board_oversight\views.py:64:@permission_classes([IsAuthenticated])
backend\board_oversight\views.py:77:@permission_classes([IsAuthenticated])
frontend/dashboards/src\pages\StaffOnboardingWizard.jsx:8: *   1. Configure ΓÇö first name, last name, email, role type
frontend/dashboards/src\pages\StaffOnboardingWizard.jsx:49:    role_type:  "TEACHER",
frontend/dashboards/src\pages\StaffOnboardingWizard.jsx:108:    setForm({ first_name: "", last_name: "", email: "", role_type: "TEACHER" });
frontend/dashboards/src\pages\StaffOnboardingWizard.jsx:136:              <select style={{ display: "block", width: "100%", marginTop: 4 }} {...field("role_type")}>
frontend/dashboards/src\pages\StaffOnboardingWizard.jsx:188:            <dd style={{ marginLeft: 0, marginBottom: 8 }}>{result.role_type}</dd>
frontend/dashboards/src\pages\SpiritualLifeDashboard.jsx:6:  return <CrownDashboardTemplate config={config} roleKey="spiritualLife" />;
frontend/dashboards/src\pages\SecurityDashboard.jsx:56:  if (schoolId) headers['X-School-Id']   = schoolId;
frontend/dashboards/src\components\dashboard\KpiFlipCard.jsx:2: * KpiFlipCard ΓÇö role-specific KPI metric tile with CSS flip.
frontend/dashboards/src\components\dashboard\KpiFlipCard.jsx:43:      role="button"
frontend/dashboards/src\components\routing\RoleRouteGuard.jsx:2:import { getCurrentUserRoles } from '../../auth/roleAdapter';
frontend/dashboards/src\components\routing\RoleRouteGuard.jsx:3:import { hasAnyRole } from '../../auth/roleAccess';
frontend/dashboards/src\components\routing\RoleRouteGuard.jsx:8:  const allowed = hasAnyRole(userRoles, allowedRoles);
backend\board_oversight\tests\test_board_tenant_required.py:7:    user = django_user_model.objects.create_user("board_tenant_test", None, TEST_AUTH_SECRET)
backend\board_oversight\tests\test_board_tenant_required.py:9:    # No X-School-Id header ΓÇö should get 400 (ValidationError) or 403 (no permission)
backend\board_oversight\tests\test_board_rbac.py:9:    user = django_user_model.objects.create_user("rbac_test_non_board", None, TEST_AUTH_SECRET)
backend\board_oversight\tenant.py:6:    raw = request.headers.get("X-School-Id")
backend\board_oversight\tenant.py:8:        raise ValidationError({"detail": "Missing required header: X-School-Id"})
backend\board_oversight\tenant.py:12:        raise ValidationError({"detail": "Invalid X-School-Id (must be UUID)"})
frontend/dashboards/src\components\OpsCommandCenter.jsx:69:      alert("Copy failed (browser permissions).");
frontend/dashboards/src\components\dashboard\integrationsautomation\IntegrationsAutomationAlertsPanel.jsx:4:  { title: 'Microsoft 365 roster sync failed for one tenant cluster', level: 'High' },
frontend/dashboards/src\pages\SchoolBoardDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="schoolBoard" />;
frontend/dashboards/src\pages\SchoolAdministratorDashboard.jsx:6:  return <CrownDashboardTemplate config={config} roleKey="schoolAdministrator" />;
backend\board_oversight\services_pdf.py:24:    school_id: UUID or None ΓÇö if provided, data is tenant-scoped.
frontend/dashboards/src\components\dashboard\complianceaudit\ComplianceAuditQueueCard.jsx:5:  'Refresh tenant enforcement evidence bundle',
frontend/dashboards/src\components\dashboard\complianceaudit\ComplianceAuditAlertsPanel.jsx:4:  { title: 'One access-role exception lacks final approval evidence', level: 'High' },
frontend/dashboards/src\components\navigation\navItems.js:3:import { APP_PERMISSIONS } from '../../auth/permissions';
frontend/dashboards/src\components\navigation\navItems.js:6:  { label: 'Dashboard', href: PATHS.HOME, roles: ROLE_GROUPS.ALL_AUTHENTICATED, permissions: [APP_PERMISSIONS.DASHBOARD_VIEW] },
frontend/dashboards/src\components\navigation\navItems.js:7:  { label: 'Admissions', href: PATHS.ADMISSIONS, roles: ROLE_GROUPS.ADMIN_REGISTRAR, permissions: [APP_PERMISSIONS.ADMISSIONS_VIEW] },
frontend/dashboards/src\components\navigation\navItems.js:8:  { label: 'Enrollment', href: PATHS.ENROLLMENT, roles: ROLE_GROUPS.ADMIN_REGISTRAR, permissions: [APP_PERMISSIONS.ENROLLMENT_VIEW] },
frontend/dashboards/src\components\navigation\navItems.js:9:  { label: 'Billing', href: PATHS.BILLING, roles: ROLE_GROUPS.ADMIN_FINANCE, permissions: [APP_PERMISSIONS.BILLING_VIEW] },
frontend/dashboards/src\components\navigation\navItems.js:10:  { label: 'Financial Aid', href: PATHS.FINANCIAL_AID, roles: ROLE_GROUPS.ADMIN_FINANCE, permissions: [APP_PERMISSIONS.FINANCIAL_AID_VIEW] },
frontend/dashboards/src\components\navigation\navItems.js:11:  { label: 'Attendance', href: PATHS.ATTENDANCE, roles: ROLE_GROUPS.ACADEMIC_TEAM, permissions: [APP_PERMISSIONS.ATTENDANCE_VIEW] },
frontend/dashboards/src\components\navigation\navItems.js:12:  { label: 'Gradebook', href: PATHS.GRADEBOOK, roles: ROLE_GROUPS.ACADEMIC_TEAM, permissions: [APP_PERMISSIONS.GRADEBOOK_VIEW] },
frontend/dashboards/src\components\navigation\navItems.js:13:  { label: 'Daycare / Aftercare', href: PATHS.EXTENDED_CARE_DASHBOARD, roles: ROLE_GROUPS.AFTERCARE_STAFF, permissions: [APP_PERMISSIONS.AFTERCARE_VIEW] },
frontend/dashboards/src\components\navigation\navItems.js:14:  { label: 'Communications', href: PATHS.COMMUNICATIONS, roles: ROLE_GROUPS.ALL_AUTHENTICATED, permissions: [APP_PERMISSIONS.COMMUNICATIONS_VIEW] },
frontend/dashboards/src\components\navigation\navItems.js:15:  { label: 'Reporting', href: PATHS.REPORTING, roles: ROLE_GROUPS.ADMIN_ONLY, permissions: [APP_PERMISSIONS.REPORTING_VIEW] },
frontend/dashboards/src\components\navigation\navItems.js:16:  { label: 'System Status', href: PATHS.SYSTEM_STATUS, roles: ROLE_GROUPS.ADMIN_ONLY, permissions: [APP_PERMISSIONS.SYSTEM_VIEW] },
frontend/dashboards/src\components\navigation\navItems.js:17:  { label: 'Release Readiness', href: PATHS.RELEASE_READINESS, roles: ROLE_GROUPS.ADMIN_ONLY, permissions: [APP_PERMISSIONS.RELEASE_VIEW] },
frontend/dashboards/src\components\navigation\navItems.js:18:  { label: 'Demo Readiness', href: PATHS.DEMO_READINESS, roles: ROLE_GROUPS.ADMIN_ONLY, permissions: [APP_PERMISSIONS.DEMO_VIEW] },
frontend/dashboards/src\components\navigation\dashboardNavConfig.js:2:import { getCurrentUserRoles } from '../../auth/roleAdapter';
frontend/dashboards/src\components\navigation\dashboardNavConfig.js:3:import { filterVisibleNav } from '../../auth/roleAccess';
frontend/dashboards/src\components\navigation\dashboardNavConfig.js:6:import { APP_PERMISSIONS } from '../../auth/permissions';
frontend/dashboards/src\components\navigation\dashboardNavConfig.js:12:      { key: 'academics-workspace', label: 'Academics', href: PATHS.ACADEMICS, tier: 0, roles: ROLE_GROUPS.ACADEMIC_TEAM },
frontend/dashboards/src\components\navigation\dashboardNavConfig.js:13:      { key: 'gradebook-workspace', label: 'Gradebook', href: PATHS.GRADEBOOK, tier: 0, roles: ROLE_GROUPS.ACADEMIC_TEAM },
frontend/dashboards/src\components\navigation\dashboardNavConfig.js:14:      { key: 'teacher-grading', label: 'Teacher Grading', href: PATHS.ACADEMICS_TEACHER_GRADING, tier: 0, roles: ROLE_GROUPS.ACADEMIC_TEAM },
frontend/dashboards/src\components\navigation\dashboardNavConfig.js:15:      { key: 'classrooms', label: 'Classrooms', href: '/classrooms', tier: 0, roles: ROLE_GROUPS.ACADEMIC_TEAM },
frontend/dashboards/src\components\navigation\dashboardNavConfig.js:16:      { key: 'attendance-workspace', label: 'Attendance', href: PATHS.ATTENDANCE, tier: 0, roles: ROLE_GROUPS.ACADEMIC_TEAM },
frontend/dashboards/src\components\navigation\dashboardNavConfig.js:22:      { key: 'board', label: 'Board', href: '/board', tier: 0, roles: ROLE_GROUPS.ADMIN_ONLY },
frontend/dashboards/src\components\navigation\dashboardNavConfig.js:23:      { key: 'integrity', label: 'Integrity', href: PATHS.REPORTING, tier: 0, roles: ROLE_GROUPS.ADMIN_ONLY, permissions: [APP_PERMISSIONS.REPORTING_VIEW] },
frontend/dashboards/src\components\navigation\dashboardNavConfig.js:29:      { key: 'parent', label: 'Family', href: '/parent', tier: 0, roles: ROLE_GROUPS.FAMILY_VIEW },
frontend/dashboards/src\components\navigation\dashboardNavConfig.js:30:      { key: 'parent-grades', label: 'Grades', href: '/academics/parent-snapshot', tier: 0, roles: ROLE_GROUPS.FAMILY_VIEW },
frontend/dashboards/src\components\navigation\dashboardNavConfig.js:31:      { key: 'family-tuition', label: 'Tuition', href: '/finance/invoices', tier: 0, roles: ROLE_GROUPS.FAMILY_VIEW },
frontend/dashboards/src\components\navigation\dashboardNavConfig.js:37:      { key: 'student', label: 'Student', href: '/student', tier: 0, roles: ROLE_GROUPS.FAMILY_VIEW },
frontend/dashboards/src\components\navigation\dashboardNavConfig.js:38:      { key: 'student-work', label: 'Assignments', href: '/academics/student-work', tier: 0, roles: ROLE_GROUPS.FAMILY_VIEW },
frontend/dashboards/src\components\navigation\dashboardNavConfig.js:39:      { key: 'student-grades', label: 'Grades', href: PATHS.GRADEBOOK, tier: 0, roles: ROLE_GROUPS.FAMILY_VIEW },
frontend/dashboards/src\components\navigation\dashboardNavConfig.js:45:      { key: 'admissions', label: 'Admissions', href: PATHS.ADMISSIONS, tier: 0, roles: ROLE_GROUPS.ADMIN_REGISTRAR, permissions: [APP_PERMISSIONS.ADMISSIONS_VIEW] },
frontend/dashboards/src\components\navigation\dashboardNavConfig.js:46:      { key: 'admissions-pipeline', label: 'Admissions Pipeline', href: PATHS.ADMISSIONS_PIPELINE, tier: 0, roles: ROLE_GROUPS.ADMIN_REGISTRAR },
frontend/dashboards/src\components\navigation\dashboardNavConfig.js:48:      { key: 'wizards', label: 'Wizard Hub', href: PATHS.WIZARDS, tier: 0, roles: ROLE_GROUPS.ADMIN_REGISTRAR },
frontend/dashboards/src\components\navigation\dashboardNavConfig.js:54:      { key: 'communications', label: 'Communications', href: PATHS.COMMUNICATIONS, tier: 0, roles: ROLE_GROUPS.ALL_AUTHENTICATED, permissions: [APP_PERMISSIONS.COMMUNICATIONS_VIEW] },
frontend/dashboards/src\components\navigation\CrownSidebar.jsx:4:import { getCurrentUserRoles } from '../../auth/roleAdapter';
frontend/dashboards/src\components\navigation\CrownSidebar.jsx:5:import { filterVisibleNav } from '../../auth/roleAccess';
frontend/dashboards/src\components\navigation\CrownSidebar.jsx:95:const normalizeRole = (role) => String(role || 'guest').trim().toLowerCase();
frontend/dashboards/src\components\navigation\CrownSidebar.jsx:109:  const { permissions } = usePermissions();
frontend/dashboards/src\components\navigation\CrownSidebar.jsx:113:  const visibleNavItems = filterVisibleNav(dashboardNavSections, { roles: userRoles, permissions })
frontend/dashboards/src\components\navigation\CrownSidebar.jsx:117:        const roleVisible = canSeeItem(item.roles, currentUserRole);
frontend/dashboards/src\components\navigation\CrownSidebar.jsx:118:        if (!Array.isArray(item.permissions) || item.permissions.length === 0) {
frontend/dashboards/src\components\navigation\CrownSidebar.jsx:119:          return roleVisible;
frontend/dashboards/src\components\navigation\CrownSidebar.jsx:122:        if (permissions.includes('*')) {
frontend/dashboards/src\components\navigation\CrownSidebar.jsx:126:        return roleVisible && item.permissions.some((permission) => permissions.includes(permission));
backend\board_oversight\services.py:37:    NOTE: Do NOT expose raw tables to board role. Aggregate and redact.
frontend/dashboards/src\pages\SchedulingDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="scheduling" />;
frontend/dashboards/src\pages\SafetySecurityDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="safetySecurity" />;
frontend/dashboards/src\pages\SafetyDashboard.jsx:55:  if (schoolId) headers['X-School-Id']   = schoolId;
backend\board_oversight\models_governance.py:24:    owner_role = models.CharField(max_length=100)
frontend/dashboards/src\pages\RoleHomeRedirect.jsx:21:  const sessionRole = sessionStorage.getItem('crown.role') || '';
frontend/dashboards/src\pages\RoleHomeRedirect.jsx:22:  const localRole = localStorage.getItem('crown.role') || '';
frontend/dashboards/src\pages\RoleHomeRedirect.jsx:23:  const demoRole = localStorage.getItem('crown.demo.role') || '';
frontend/dashboards/src\pages\RoleHomeRedirect.jsx:33:    payload.role,
frontend/dashboards/src\pages\RoleHomeRedirect.jsx:34:    payload.user_role,
frontend/dashboards/src\pages\RoleHomeRedirect.jsx:37:    Array.isArray(payload.roles) ? payload.roles.join(',') : payload.roles,
frontend/dashboards/src\pages\RoleHomeRedirect.jsx:46:// Table-driven role routing: every token is an independent key.
frontend/dashboards/src\pages\RoleHomeRedirect.jsx:149:  const role = getStoredRole();
frontend/dashboards/src\pages\RoleHomeRedirect.jsx:151:    if (isSandbox && role === "school_admin") navigate("/school-admin-dashboard");
frontend/dashboards/src\pages\RoleHomeRedirect.jsx:152:  }, [isSandbox, role, navigate]);
frontend/dashboards/src\pages\RoleDashboardPage.jsx:2: * RoleDashboardPage - unified role-based dashboard.
frontend/dashboards/src\pages\RoleDashboardPage.jsx:4: * Route: /dash/:role  (e.g., /dash/admin, /dash/teacher)
frontend/dashboards/src\pages\RoleDashboardPage.jsx:6: * Fetches /api/dashboards/summary/ with the current school + role context,
frontend/dashboards/src\pages\RoleDashboardPage.jsx:43:  const { role: routeRole } = useParams();
frontend/dashboards/src\pages\RoleDashboardPage.jsx:44:  const role = routeRole || "admin";
frontend/dashboards/src\pages\RoleDashboardPage.jsx:68:    fetchDashboardSummary(schoolId, role).then(applyDashboardResponse);
frontend/dashboards/src\pages\RoleDashboardPage.jsx:69:  }, [applyDashboardResponse, role, schoolId]);
frontend/dashboards/src\pages\RoleDashboardPage.jsx:74:    fetchDashboardSummary(schoolId, role).then((result) => {
frontend/dashboards/src\pages\RoleDashboardPage.jsx:84:  }, [applyDashboardResponse, role, schoolId]);
frontend/dashboards/src\pages\RoleDashboardPage.jsx:94:  const roleLabel = role.charAt(0).toUpperCase() + role.slice(1);
frontend/dashboards/src\pages\RoleDashboardPage.jsx:101:      title={`${roleLabel} Dashboard`}
frontend/dashboards/src\pages\RoleDashboardPage.jsx:124:          role="alert"
frontend/dashboards/src\pages\RevenueOperationsDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="revenueOperations" />;
frontend/dashboards/src\pages\ReleaseReliabilityDashboard.jsx:6:  return <CrownDashboardTemplate config={config} roleKey="releaseReliability" />;
backend\admissions\api_views.py:8:from rest_framework.decorators import api_view, permission_classes
backend\admissions\api_views.py:9:from rest_framework.permissions import IsAuthenticated
backend\admissions\api_views.py:27:@permission_classes([IsAuthenticated])
backend\admissions\api_views.py:102:@permission_classes([IsAuthenticated])
backend\admissions\api_views.py:162:@permission_classes([IsAuthenticated])
frontend/dashboards/src\components\dashboard\FlipWidget.jsx:44:      role="button"
frontend/dashboards/src\pages\RegistrarDashboard.jsx:6:  return <CrownDashboardTemplate config={config} roleKey="registrar" />;
backend\board_oversight\migrations\0002_stage4_governance.py:19:                ('owner_role', models.CharField(max_length=100)),
backend\tests\test_wizard_contract.py:7:  3. Requires X-School-Id header (400 when missing)
backend\tests\test_wizard_contract.py:8:  4. Enforces tenant isolation (404 when school mismatch)
backend\tests\test_wizard_contract.py:12:and broken auth/tenant behavior in a single place.
backend\tests\test_wizard_contract.py:79:def _grant_enrollment_conversion_access(user, school, role_code="REGISTRAR"):
backend\tests\test_wizard_contract.py:80:    UserRole.objects.create(user=user, school=school, role_code=role_code)
backend\tests\test_wizard_contract.py:85:    RolePermission.objects.get_or_create(role_code=role_code, permission=perm)
backend\tests\test_wizard_contract.py:126:# Contract: missing X-School-Id ΓåÆ 400
backend\tests\test_wizard_contract.py:131:    Every wizard session endpoint must reject requests missing X-School-Id.
backend\tests\test_wizard_contract.py:132:    Auth is present; only the tenant header is missing.
backend\tests\test_wizard_contract.py:143:            f"{description} ({url}): expected 400 for missing X-School-Id, got {r.status_code}."
backend\tests\test_wizard_contract.py:158:    POST to a wizard base URL with valid auth + correct X-School-Id must
backend\tests\test_wizard_contract.py:185:# Contract: cross-tenant access ΓåÆ 404
backend\tests\test_wizard_contract.py:200:    def _assert_tenant_isolation(self, description, url):
backend\tests\test_wizard_contract.py:214:            f"{description} ({detail_url}): expected 404 for cross-tenant access, "
backend\tests\test_wizard_contract.py:215:            f"got {r2.status_code}. Tenant isolation is BROKEN."
backend\tests\test_wizard_contract.py:218:    def test_all_wizards_isolate_tenants(self):
backend\tests\test_wizard_contract.py:221:                self._assert_tenant_isolation(description, url)
backend\tests\test_volunteer_family_engagement_unit.py:42:    """Verify tenant/school scoping keywords appear in the Volunteer Family Engagement source tree."""
backend\tests\test_volunteer_family_engagement_unit.py:53:    ), f"Volunteer Family Engagement: tenant/school scoping not found in source"
frontend/dashboards/src\pages\PortraitServiceHoursDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="portraitService" />;
backend\board_oversight\api_governance.py:14:from rest_framework.decorators import api_view, permission_classes
backend\board_oversight\api_governance.py:15:from rest_framework.permissions import IsAuthenticated, AllowAny
backend\board_oversight\api_governance.py:28:from board_oversight.tenant import require_school_id
backend\board_oversight\api_governance.py:35:@permission_classes([IsAuthenticated])
backend\board_oversight\api_governance.py:91:@permission_classes([IsAuthenticated])
backend\board_oversight\api_governance.py:102:@permission_classes([IsAuthenticated])
backend\board_oversight\api_governance.py:110:        "id", "title", "status", "owner_role", "target_date",
backend\board_oversight\api_governance.py:126:@permission_classes([IsAuthenticated])
backend\board_oversight\api_governance.py:142:@permission_classes([AllowAny])
backend\board_oversight\api_governance.py:154:@permission_classes([AllowAny])
frontend/dashboards/src\pages\PDDashboard.jsx:53:  if (schoolId) headers['X-School-Id']   = schoolId;
backend\tests\test_volunteer_family_engagement_tenant.py:2:Tenant isolation tests for the Volunteer Family Engagement module.
backend\tests\test_volunteer_family_engagement_tenant.py:23:        username=f"tenant-a-volunteer_family_engagement-{token}",
backend\tests\test_volunteer_family_engagement_tenant.py:32:    """Cross-tenant isolation tests for Volunteer Family Engagement."""
backend\tests\test_volunteer_family_engagement_tenant.py:38:    def test_volunteer_family_engagement_tenant_school_ids_are_distinct(self):
backend\tests\test_volunteer_family_engagement_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_volunteer_family_engagement_tenant.py:47:    def test_volunteer_family_engagement_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_volunteer_family_engagement_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_volunteer_family_engagement_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_volunteer_family_engagement_tenant.py:58:    def test_volunteer_family_engagement_same_tenant_request_is_allowed(self):
backend\tests\test_volunteer_family_engagement_tenant.py:67:    def test_volunteer_family_engagement_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_volunteer_family_engagement_tenant.py:75:    def test_volunteer_family_engagement_isolation_keyword_present_in_source(self):
backend\tests\test_volunteer_family_engagement_tenant.py:76:        """Tenant isolation keywords exist in the Volunteer Family Engagement module source."""
backend\tests\test_volunteer_family_engagement_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_volunteer_family_engagement_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_volunteer_family_engagement_tenant.py:87:        assert found, f"Volunteer Family Engagement: tenant isolation keywords not found in source"
frontend/dashboards/src\pages\ParentStudent360Page.jsx:26:  if (schoolId) h["X-School-Id"] = schoolId;
backend\tests\test_volunteer_family_engagement_api.py:61:        """School record for Volunteer Family Engagement tenant is created and queryable."""
backend\tests\test_volunteer_family_engagement_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_transportation_unit.py:42:    """Verify tenant/school scoping keywords appear in the Transportation source tree."""
backend\tests\test_transportation_unit.py:53:    ), f"Transportation: tenant/school scoping not found in source"
frontend/dashboards/src\pages\ParentDashboard.jsx:6:  return <CrownDashboardTemplate config={config} roleKey="parent" />;
backend\tests\test_transportation_tenant.py:2:Tenant isolation tests for the Transportation module.
backend\tests\test_transportation_tenant.py:23:        username=f"tenant-a-transportation-{token}",
backend\tests\test_transportation_tenant.py:32:    """Cross-tenant isolation tests for Transportation."""
backend\tests\test_transportation_tenant.py:38:    def test_transportation_tenant_school_ids_are_distinct(self):
backend\tests\test_transportation_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_transportation_tenant.py:47:    def test_transportation_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_transportation_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_transportation_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_transportation_tenant.py:58:    def test_transportation_same_tenant_request_is_allowed(self):
backend\tests\test_transportation_tenant.py:67:    def test_transportation_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_transportation_tenant.py:75:    def test_transportation_isolation_keyword_present_in_source(self):
backend\tests\test_transportation_tenant.py:76:        """Tenant isolation keywords exist in the Transportation module source."""
backend\tests\test_transportation_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_transportation_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_transportation_tenant.py:87:        assert found, f"Transportation: tenant isolation keywords not found in source"
frontend/dashboards/src\components\dashboard\board\BoardRiskPanel.jsx:13:  { title: 'Teacher replacement pipeline thin in STEM roles', level: 'High' },
backend\tests\test_transportation_api.py:61:        """School record for Transportation tenant is created and queryable."""
backend\tests\test_transportation_api.py:66:        """User is bound to the correct school tenant."""
frontend/dashboards/src\pages\ops\SubscriptionManagerPage.tsx:5: * Allows super-admins to view and update a school tenant's active plan.
backend\tests\test_tenant_write_guard.py:2:Tests for tenant write protection (Layer 07).
backend\tests\test_tenant_write_guard.py:7:from core.tenant_models import set_current_school, clear_current_school, TenantWriteViolation
backend\tests\test_tenant_write_guard.py:15:        # Create two tenants
backend\tests\test_tenant_write_guard.py:23:        """With tenant context, creating without school should auto-bind."""
backend\tests\test_tenant_write_guard.py:30:    def test_cross_tenant_write_blocked(self):
backend\tests\test_tenant_write_guard.py:31:        """With tenant context A, saving object assigned to B must be blocked."""
backend\tests\test_tenant_violation_telemetry.py:5:from core.tenant_models import (
backend\tests\test_tenant_violation_telemetry.py:8:    require_tenant_context,
backend\tests\test_tenant_violation_telemetry.py:29:        with self.assertLogs("core.tenant_models", level="WARNING") as logs:
backend\tests\test_tenant_violation_telemetry.py:31:                require_tenant_context()
backend\tests\test_tenant_violation_telemetry.py:34:    def test_logs_cross_tenant_write_violation(self):
backend\tests\test_tenant_violation_telemetry.py:36:        with self.assertLogs("core.tenant_models", level="WARNING") as logs:
backend\tests\test_tenant_violation_telemetry.py:43:        with self.assertLogs("core.tenant_models", level="WARNING") as logs:
backend\tests\test_tenant_violation_telemetry.py:50:        with self.assertLogs("core.tenant_models", level="WARNING") as logs:
backend\tests\test_tenant_lifecycle_cleanup.py:7:from core.tenant_models import get_current_school, clear_current_school
backend\tests\test_tenant_lifecycle_cleanup.py:32:        # Make request with tenant header, ensure request processing clears afterwards
backend\tests\test_tenant_isolation_smoke.py:1:# backend/tests/test_tenant_isolation_smoke.py
backend\tests\test_tenant_isolation_smoke.py:3:Minimal cross-tenant isolation proof for writable ViewSets.
backend\tests\test_tenant_isolation_smoke.py:103:    """Cross-tenant isolation: user A must not see school B data."""
backend\tests\test_tenant_isolation_smoke.py:105:    def test_cross_tenant_submission_list_hidden(self):
backend\tests\test_tenant_isolation_smoke.py:129:    def test_cross_tenant_submission_detail_denied(self):
backend\tests\test_tenant_isolation.py:14:def _user_for_school(school: School, *, is_staff: bool = False, username_prefix: str = "tenant"):
backend\tests\test_tenant_isolation.py:29:        self.user_a = _user_for_school(self.school_a, username_prefix="tenant-a")
backend\tests\test_tenant_isolation.py:30:        self.staff_a = _user_for_school(self.school_a, is_staff=True, username_prefix="tenant-staff")
backend\tests\test_tenant_isolation.py:33:            username=f"tenant-none-{token}",
backend\tests\test_tenant_isolation.py:34:            email=f"tenant-none-{token}@example.com",
backend\tests\test_tenant_isolation.py:44:    def test_gradebook_sections_cross_tenant_returns_404(self):
backend\tests\test_tenant_isolation.py:49:    def test_billing_runs_cross_tenant_returns_404(self):
backend\tests\test_tenant_isolation.py:54:    def test_admissions_applications_cross_tenant_returns_404(self):
backend\tests\test_tenant_isolation.py:59:    def test_admissions_enroll_cross_tenant_returns_404(self):
backend\tests\test_tenant_isolation.py:64:    def test_staff_same_tenant_can_reach_gradebook_surface(self):
backend\tests\test_tenant_header_validate_school.py:21:        self.assertIn("Invalid X-School-Id", r.json().get("detail", ""))
backend\tests\test_tenant_header_validate_school.py:30:        # not reject the request as a tenant-header error.
backend\tests\test_tenant_header_required.py:17:        # middleware's "Missing required header: X-School-Id" error.
backend\tests\test_tenant_header_required.py:18:        self.assertNotIn(b"X-School-Id", r.content)
backend\tests\test_tenant_header_required.py:25:        self.assertIn("X-School-Id", str(r.content))
backend\tests\test_tenant_header_required.py:29:        """CORS preflight OPTIONS requests must pass without X-School-Id header"""
backend\tests\test_tenant_context_guardrails.py:5:from core.tenant_models import (
backend\tests\test_tenant_context_guardrails.py:9:    tenant_context,
backend\tests\test_tenant_context_guardrails.py:10:    require_tenant_context,
backend\tests\test_tenant_context_guardrails.py:27:            require_tenant_context()
backend\tests\test_tenant_context_guardrails.py:33:        with tenant_context(self.a):
backend\tests\test_tenant_context_guardrails.py:42:        with tenant_context(self.a):
backend\tests\test_tenant_context_guardrails.py:45:            with tenant_context(self.b):
backend\tests\test_tenant_bulk_ops_guard.py:4:from core.tenant_models import set_current_school, clear_current_school, TenantBulkOpViolation
backend\tests\test_tenant_bulk_ops_guard.py:15:        # Seed one row in each tenant
backend\tests\test_tenant_bulk_ops_guard.py:22:    def test_bulk_update_requires_tenant_context(self):
backend\tests\test_tenant_bulk_ops_guard.py:27:    def test_bulk_delete_requires_tenant_context(self):
backend\tests\test_tenant_bulk_ops_guard.py:32:    def test_bulk_ops_scoped_to_current_tenant(self):
backend\tests\test_tenant_bulk_ops_guard.py:33:        # With tenant A context, bulk ops must only touch tenant A rows
backend\tests\test_tenant_auto_scope.py:2:Tests for tenant auto-scoping with fail-closed behavior.
backend\tests\test_tenant_auto_scope.py:6:from core.tenant_models import set_current_school, get_current_school, clear_current_school
backend\tests\test_survey_sentiment_unit.py:42:    """Verify tenant/school scoping keywords appear in the Survey Sentiment Engine source tree."""
backend\tests\test_survey_sentiment_unit.py:53:    ), f"Survey Sentiment Engine: tenant/school scoping not found in source"
backend\tests\test_survey_sentiment_tenant.py:2:Tenant isolation tests for the Survey Sentiment Engine module.
backend\tests\test_survey_sentiment_tenant.py:23:        username=f"tenant-a-survey_sentiment-{token}",
backend\tests\test_survey_sentiment_tenant.py:32:    """Cross-tenant isolation tests for Survey Sentiment Engine."""
backend\tests\test_survey_sentiment_tenant.py:38:    def test_survey_sentiment_tenant_school_ids_are_distinct(self):
backend\tests\test_survey_sentiment_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_survey_sentiment_tenant.py:47:    def test_survey_sentiment_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_survey_sentiment_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_survey_sentiment_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_survey_sentiment_tenant.py:58:    def test_survey_sentiment_same_tenant_request_is_allowed(self):
backend\tests\test_survey_sentiment_tenant.py:67:    def test_survey_sentiment_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_survey_sentiment_tenant.py:75:    def test_survey_sentiment_isolation_keyword_present_in_source(self):
backend\tests\test_survey_sentiment_tenant.py:76:        """Tenant isolation keywords exist in the Survey Sentiment Engine module source."""
backend\tests\test_survey_sentiment_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_survey_sentiment_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_survey_sentiment_tenant.py:87:        assert found, f"Survey Sentiment Engine: tenant isolation keywords not found in source"
backend\tests\test_survey_sentiment_api.py:61:        """School record for Survey Sentiment Engine tenant is created and queryable."""
backend\tests\test_survey_sentiment_api.py:66:        """User is bound to the correct school tenant."""
frontend/dashboards/src\pages\OfficeDashboard.jsx:6:  return <CrownDashboardTemplate config={config} roleKey="office" />;
backend\tests\test_student_master_record_unit.py:42:    """Verify tenant/school scoping keywords appear in the Student Master Record source tree."""
backend\tests\test_student_master_record_unit.py:53:    ), f"Student Master Record: tenant/school scoping not found in source"
backend\tests\test_student_master_record_tenant.py:2:Tenant isolation tests for the Student Master Record module.
backend\tests\test_student_master_record_tenant.py:23:        username=f"tenant-a-student_master_record-{token}",
backend\tests\test_student_master_record_tenant.py:32:    """Cross-tenant isolation tests for Student Master Record."""
backend\tests\test_student_master_record_tenant.py:38:    def test_student_master_record_tenant_school_ids_are_distinct(self):
backend\tests\test_student_master_record_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_student_master_record_tenant.py:47:    def test_student_master_record_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_student_master_record_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_student_master_record_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_student_master_record_tenant.py:58:    def test_student_master_record_same_tenant_request_is_allowed(self):
backend\tests\test_student_master_record_tenant.py:67:    def test_student_master_record_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_student_master_record_tenant.py:75:    def test_student_master_record_isolation_keyword_present_in_source(self):
backend\tests\test_student_master_record_tenant.py:76:        """Tenant isolation keywords exist in the Student Master Record module source."""
backend\tests\test_student_master_record_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_student_master_record_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_student_master_record_tenant.py:87:        assert found, f"Student Master Record: tenant isolation keywords not found in source"
frontend/dashboards/src\components\HelpTooltip.jsx:64:          role="tooltip"
backend\academic_year_wizard\views.py:12:Auth: JWT or Session. All endpoints tenant-scoped via X-School-Id.
backend\academic_year_wizard\views.py:26:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\academic_year_wizard\views.py:27:from rest_framework.permissions import IsAuthenticated
backend\academic_year_wizard\views.py:100:@permission_classes(_PERM)
backend\academic_year_wizard\views.py:121:@permission_classes(_PERM)
backend\academic_year_wizard\views.py:171:@permission_classes(_PERM)
backend\academic_year_wizard\views.py:223:@permission_classes(_PERM)
backend\academic_year_wizard\views.py:337:@permission_classes(_PERM)
frontend/dashboards/src\pages\NotAuthorized.jsx:3:import { getCurrentUserRoles } from '../auth/roleAdapter';
frontend/dashboards/src\pages\NotAuthorized.jsx:22:              You do not have permission to access <strong>{attemptedPath}</strong>.
frontend/dashboards/src\pages\NotAuthorized.jsx:26:              If this is wrong, fix the assigned role set. Do not bypass the route guard.
backend\tests\test_student_master_record_api.py:61:        """School record for Student Master Record tenant is created and queryable."""
backend\tests\test_student_master_record_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_student_care_discipline_unit.py:42:    """Verify tenant/school scoping keywords appear in the Student Care Discipline Summary source tree."""
backend\tests\test_student_care_discipline_unit.py:53:    ), f"Student Care Discipline Summary: tenant/school scoping not found in source"
frontend/dashboards/src\components\launch\CrownSidebar.jsx:2:import { getCurrentUserRoles } from '../../auth/roleAdapter';
frontend/dashboards/src\components\launch\CrownSidebar.jsx:3:import { hasAnyRole } from '../../auth/roleAccess';
frontend/dashboards/src\components\launch\CrownSidebar.jsx:19:    roles: ['school_admin', 'head_of_school', 'admin', 'director', 'principal', 'super_admin'],
frontend/dashboards/src\components\launch\CrownSidebar.jsx:27:    roles: ['school_admin', 'head_of_school', 'admin', 'director', 'principal', 'super_admin'],
frontend/dashboards/src\components\launch\CrownSidebar.jsx:35:    roles: ['school_admin', 'head_of_school', 'admin', 'director', 'principal', 'admissions', 'admissions_manager'],
frontend/dashboards/src\components\launch\CrownSidebar.jsx:43:    roles: ['school_admin', 'head_of_school', 'admin', 'director', 'principal', 'teacher', 'academic_admin', 'academics'],
frontend/dashboards/src\components\launch\CrownSidebar.jsx:51:    roles: ['school_admin', 'head_of_school', 'admin', 'director', 'principal', 'teacher', 'parent', 'student'],
frontend/dashboards/src\components\launch\CrownSidebar.jsx:59:    roles: ['school_admin', 'head_of_school', 'admin', 'director', 'principal', 'teacher', 'parent', 'student'],
frontend/dashboards/src\components\launch\CrownSidebar.jsx:67:    roles: ['school_admin', 'head_of_school', 'admin', 'director', 'principal', 'finance', 'finance_admin', 'finance_director', 'biz_office', 'super_admin'],
frontend/dashboards/src\components\launch\CrownSidebar.jsx:82:    roles: ['school_admin', 'head_of_school', 'admin', 'director', 'principal', 'board', 'board_member', 'super_admin'],
frontend/dashboards/src\components\launch\CrownSidebar.jsx:90:    roles: ['school_admin', 'head_of_school', 'admin', 'director', 'principal', 'super_admin'],
frontend/dashboards/src\components\launch\CrownSidebar.jsx:112:  user = { initials: 'SJ', name: 'Sarah James', role: 'Head of School' },
frontend/dashboards/src\components\launch\CrownSidebar.jsx:116:  const visibleItems = NAV_ITEMS.filter((item) => !Array.isArray(item.roles) || hasAnyRole(userRoles, item.roles));
frontend/dashboards/src\components\launch\CrownSidebar.jsx:154:          <div className="launch-user-role">{user.role || 'Head of School'}</div>
backend\tests\test_student_care_discipline_tenant.py:2:Tenant isolation tests for the Student Care Discipline Summary module.
backend\tests\test_student_care_discipline_tenant.py:23:        username=f"tenant-a-student_care_discipline-{token}",
backend\tests\test_student_care_discipline_tenant.py:32:    """Cross-tenant isolation tests for Student Care Discipline Summary."""
backend\tests\test_student_care_discipline_tenant.py:38:    def test_student_care_discipline_tenant_school_ids_are_distinct(self):
backend\tests\test_student_care_discipline_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_student_care_discipline_tenant.py:47:    def test_student_care_discipline_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_student_care_discipline_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_student_care_discipline_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_student_care_discipline_tenant.py:58:    def test_student_care_discipline_same_tenant_request_is_allowed(self):
backend\tests\test_student_care_discipline_tenant.py:67:    def test_student_care_discipline_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_student_care_discipline_tenant.py:75:    def test_student_care_discipline_isolation_keyword_present_in_source(self):
backend\tests\test_student_care_discipline_tenant.py:76:        """Tenant isolation keywords exist in the Student Care Discipline Summary module source."""
backend\tests\test_student_care_discipline_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_student_care_discipline_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_student_care_discipline_tenant.py:87:        assert found, f"Student Care Discipline Summary: tenant isolation keywords not found in source"
backend\billing_wizard\views.py:7:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\billing_wizard\views.py:8:from rest_framework.permissions import IsAuthenticated
backend\billing_wizard\views.py:106:@permission_classes(_PERM)
backend\billing_wizard\views.py:124:@permission_classes(_PERM)
backend\billing_wizard\views.py:153:@permission_classes(_PERM)
backend\billing_wizard\views.py:188:@permission_classes(_PERM)
backend\billing_wizard\views.py:222:@permission_classes(_PERM)
backend\billing_wizard\views.py:286:@permission_classes(_PERM)
frontend/dashboards/src\pages\NetworkBenchmarkingDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="networkBenchmarking" />;
backend\tests\test_student_care_discipline_api.py:61:        """School record for Student Care Discipline Summary tenant is created and queryable."""
backend\tests\test_student_care_discipline_api.py:66:        """User is bound to the correct school tenant."""
frontend/dashboards/src\pages\MasterControlDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="masterControl" />;
backend\tests\test_staff_faculty_unit.py:42:    """Verify tenant/school scoping keywords appear in the Staff Faculty source tree."""
backend\tests\test_staff_faculty_unit.py:53:    ), f"Staff Faculty: tenant/school scoping not found in source"
backend\tests\test_staff_faculty_tenant.py:2:Tenant isolation tests for the Staff Faculty module.
backend\tests\test_staff_faculty_tenant.py:23:        username=f"tenant-a-staff_faculty-{token}",
backend\tests\test_staff_faculty_tenant.py:32:    """Cross-tenant isolation tests for Staff Faculty."""
backend\tests\test_staff_faculty_tenant.py:38:    def test_staff_faculty_tenant_school_ids_are_distinct(self):
backend\tests\test_staff_faculty_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_staff_faculty_tenant.py:47:    def test_staff_faculty_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_staff_faculty_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_staff_faculty_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_staff_faculty_tenant.py:58:    def test_staff_faculty_same_tenant_request_is_allowed(self):
backend\tests\test_staff_faculty_tenant.py:67:    def test_staff_faculty_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_staff_faculty_tenant.py:75:    def test_staff_faculty_isolation_keyword_present_in_source(self):
backend\tests\test_staff_faculty_tenant.py:76:        """Tenant isolation keywords exist in the Staff Faculty module source."""
backend\tests\test_staff_faculty_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_staff_faculty_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_staff_faculty_tenant.py:87:        assert found, f"Staff Faculty: tenant isolation keywords not found in source"
frontend/dashboards/src\pages\MarketingDashboard.jsx:6:  return <CrownDashboardTemplate config={config} roleKey="marketing" />;
frontend/dashboards/src\pages\LogoutPage.jsx:6:  "crown.role",
frontend/dashboards/src\pages\LogoutPage.jsx:8:  "crown.demo.role",
frontend/dashboards/src\pages\LogoutPage.jsx:10:  "crown_user_roles",
backend\tests\test_staff_faculty_api.py:61:        """School record for Staff Faculty tenant is created and queryable."""
backend\tests\test_staff_faculty_api.py:66:        """User is bound to the correct school tenant."""
frontend/dashboards/src\pages\LoginPage.jsx:114:  const roles = useMemo(() => (IS_SANDBOX ? SANDBOX_ROLES : PROD_ROLES), []);
frontend/dashboards/src\pages\LoginPage.jsx:117:  const [selectedRole, setSelectedRole] = useState(roles[0]?.value || "school_admin");
frontend/dashboards/src\pages\LoginPage.jsx:152:    const role = roles.find((entry) => entry.value === selectedRole) || roles[0];
frontend/dashboards/src\pages\LoginPage.jsx:171:      sessionStorage.setItem("crown.role", role.value);
frontend/dashboards/src\pages\LoginPage.jsx:172:      localStorage.setItem("crown.role", role.value);
frontend/dashboards/src\pages\LoginPage.jsx:174:        localStorage.setItem("crown.demo.role", role.value);
frontend/dashboards/src\pages\LoginPage.jsx:177:      globalThis.location.href = role.route;
frontend/dashboards/src\pages\LoginPage.jsx:539:              Choose your school, choose your role, and continue with the correct context before entering any records.
frontend/dashboards/src\pages\LoginPage.jsx:542:              <li>Clear school and role context on every login.</li>
frontend/dashboards/src\pages\LoginPage.jsx:544:              <li>Permission-scoped access for each stakeholder role.</li>
frontend/dashboards/src\pages\LoginPage.jsx:558:                ? "Choose your sandbox school and role, then continue with sandbox credentials."
frontend/dashboards/src\pages\LoginPage.jsx:559:                : "Use your authorized role and account to access CROWN."}
frontend/dashboards/src\pages\LoginPage.jsx:566:            {error && <div className="error-banner" role="alert">{error}</div>}
frontend/dashboards/src\pages\LoginPage.jsx:584:                <label className="field-label" htmlFor="login-role">Role</label>
frontend/dashboards/src\pages\LoginPage.jsx:586:                  id="login-role"
frontend/dashboards/src\pages\LoginPage.jsx:591:                  {roles.map((role) => (
frontend/dashboards/src\pages\LoginPage.jsx:592:                    <option key={role.value} value={role.value}>{role.label}</option>
backend\academic_year_wizard\tests\test_views.py:8:  - Tenant isolation (X-School-Id required; mismatch ΓåÆ 404)
backend\academic_year_wizard\tests\test_views.py:13:  - Single-current enforcement: committing B deactivates A, cross-tenant isolation
backend\academic_year_wizard\tests\test_views.py:124:# Tenant isolation
backend\academic_year_wizard\tests\test_views.py:423:    def test_cross_tenant_year_not_affected(self):
backend\academic_year_wizard\tests\test_views.py:442:        self.assertTrue(ay_a.is_current, "Cross-tenant year must not be deactivated")
backend\tests\test_shell_backend_seeded_contract.py:12:    def test_canonical_shell_contract_returns_success_under_seeded_tenant_context(self):
frontend/dashboards/src\pages\LibraryMediaDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="libraryMedia" />;
backend\billing_wizard\tests\test_views.py:99:    def test_configure_isolation(self):
backend\billing_wizard\tests\test_views.py:103:    def test_plans_isolation(self):
backend\billing_wizard\tests\test_views.py:107:    def test_fees_isolation(self):
backend\billing_wizard\tests\test_views.py:111:    def test_commit_isolation(self):
backend\billing_wizard\tests\test_views.py:115:    def test_verify_isolation(self):
frontend/dashboards/src\pages\LibraryDashboard.jsx:52:  if (schoolId) headers['X-School-Id']   = schoolId;
backend\tests\test_shared_frontend_shell_unit.py:42:    """Verify tenant/school scoping keywords appear in the Shared Frontend Shell source tree."""
backend\tests\test_shared_frontend_shell_unit.py:53:    ), f"Shared Frontend Shell: tenant/school scoping not found in source"
backend\tests\test_shared_frontend_shell_tenant.py:2:Tenant isolation tests for the Shared Frontend Shell module.
backend\tests\test_shared_frontend_shell_tenant.py:23:        username=f"tenant-a-shared_frontend_shell-{token}",
backend\tests\test_shared_frontend_shell_tenant.py:32:    """Cross-tenant isolation tests for Shared Frontend Shell."""
backend\tests\test_shared_frontend_shell_tenant.py:38:    def test_shared_frontend_shell_tenant_school_ids_are_distinct(self):
backend\tests\test_shared_frontend_shell_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_shared_frontend_shell_tenant.py:47:    def test_shared_frontend_shell_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_shared_frontend_shell_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_shared_frontend_shell_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_shared_frontend_shell_tenant.py:58:    def test_shared_frontend_shell_same_tenant_request_is_allowed(self):
backend\tests\test_shared_frontend_shell_tenant.py:67:    def test_shared_frontend_shell_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_shared_frontend_shell_tenant.py:75:    def test_shared_frontend_shell_isolation_keyword_present_in_source(self):
backend\tests\test_shared_frontend_shell_tenant.py:76:        """Tenant isolation keywords exist in the Shared Frontend Shell module source."""
backend\tests\test_shared_frontend_shell_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_shared_frontend_shell_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_shared_frontend_shell_tenant.py:87:        assert found, f"Shared Frontend Shell: tenant isolation keywords not found in source"
frontend/dashboards/src\pages\ITSupportDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="itSupport" />;
backend\tests\test_shared_frontend_shell_api.py:61:        """School record for Shared Frontend Shell tenant is created and queryable."""
backend\tests\test_shared_frontend_shell_api.py:66:        """User is bound to the correct school tenant."""
frontend/dashboards/src\pages\ITDashboard.jsx:6:  return <CrownDashboardTemplate config={config} roleKey="it" />;
backend\tests\test_shared_design_system_unit.py:42:    """Verify tenant/school scoping keywords appear in the Shared Design System source tree."""
backend\tests\test_shared_design_system_unit.py:53:    ), f"Shared Design System: tenant/school scoping not found in source"
backend\tests\test_shared_design_system_tenant.py:2:Tenant isolation tests for the Shared Design System module.
backend\tests\test_shared_design_system_tenant.py:23:        username=f"tenant-a-shared_design_system-{token}",
backend\tests\test_shared_design_system_tenant.py:32:    """Cross-tenant isolation tests for Shared Design System."""
backend\tests\test_shared_design_system_tenant.py:38:    def test_shared_design_system_tenant_school_ids_are_distinct(self):
backend\tests\test_shared_design_system_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_shared_design_system_tenant.py:47:    def test_shared_design_system_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_shared_design_system_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_shared_design_system_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_shared_design_system_tenant.py:58:    def test_shared_design_system_same_tenant_request_is_allowed(self):
backend\tests\test_shared_design_system_tenant.py:67:    def test_shared_design_system_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_shared_design_system_tenant.py:75:    def test_shared_design_system_isolation_keyword_present_in_source(self):
backend\tests\test_shared_design_system_tenant.py:76:        """Tenant isolation keywords exist in the Shared Design System module source."""
backend\tests\test_shared_design_system_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_shared_design_system_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_shared_design_system_tenant.py:87:        assert found, f"Shared Design System: tenant isolation keywords not found in source"
backend\tests\test_shared_design_system_api.py:61:        """School record for Shared Design System tenant is created and queryable."""
backend\tests\test_shared_design_system_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_service_outreach_unit.py:42:    """Verify tenant/school scoping keywords appear in the Service Outreach source tree."""
backend\tests\test_service_outreach_unit.py:53:    ), f"Service Outreach: tenant/school scoping not found in source"
backend\tests\test_service_outreach_tenant.py:2:Tenant isolation tests for the Service Outreach module.
backend\tests\test_service_outreach_tenant.py:23:        username=f"tenant-a-service_outreach-{token}",
backend\tests\test_service_outreach_tenant.py:32:    """Cross-tenant isolation tests for Service Outreach."""
backend\tests\test_service_outreach_tenant.py:38:    def test_service_outreach_tenant_school_ids_are_distinct(self):
backend\tests\test_service_outreach_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_service_outreach_tenant.py:47:    def test_service_outreach_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_service_outreach_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_service_outreach_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_service_outreach_tenant.py:58:    def test_service_outreach_same_tenant_request_is_allowed(self):
backend\tests\test_service_outreach_tenant.py:67:    def test_service_outreach_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_service_outreach_tenant.py:75:    def test_service_outreach_isolation_keyword_present_in_source(self):
backend\tests\test_service_outreach_tenant.py:76:        """Tenant isolation keywords exist in the Service Outreach module source."""
backend\tests\test_service_outreach_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_service_outreach_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_service_outreach_tenant.py:87:        assert found, f"Service Outreach: tenant isolation keywords not found in source"
backend\tests\test_service_outreach_api.py:61:        """School record for Service Outreach tenant is created and queryable."""
backend\tests\test_service_outreach_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_school_year_term_unit.py:42:    """Verify tenant/school scoping keywords appear in the School Year Term source tree."""
backend\tests\test_school_year_term_unit.py:53:    ), f"School Year Term: tenant/school scoping not found in source"
backend\tests\test_school_year_term_tenant.py:2:Tenant isolation tests for the School Year Term module.
backend\tests\test_school_year_term_tenant.py:23:        username=f"tenant-a-school_year_term-{token}",
backend\tests\test_school_year_term_tenant.py:32:    """Cross-tenant isolation tests for School Year Term."""
backend\tests\test_school_year_term_tenant.py:38:    def test_school_year_term_tenant_school_ids_are_distinct(self):
backend\tests\test_school_year_term_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_school_year_term_tenant.py:47:    def test_school_year_term_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_school_year_term_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_school_year_term_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_school_year_term_tenant.py:58:    def test_school_year_term_same_tenant_request_is_allowed(self):
backend\tests\test_school_year_term_tenant.py:67:    def test_school_year_term_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_school_year_term_tenant.py:75:    def test_school_year_term_isolation_keyword_present_in_source(self):
backend\tests\test_school_year_term_tenant.py:76:        """Tenant isolation keywords exist in the School Year Term module source."""
backend\tests\test_school_year_term_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_school_year_term_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_school_year_term_tenant.py:87:        assert found, f"School Year Term: tenant isolation keywords not found in source"
backend\tests\test_school_year_term_api.py:61:        """School record for School Year Term tenant is created and queryable."""
backend\tests\test_school_year_term_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_school_profile_unit.py:3:Module keywords: SchoolProfile, SchoolSettings, tenant_root, logo, school_identity
backend\tests\test_school_profile_unit.py:22:    keywords = ["SchoolProfile", "SchoolSettings", "tenant_root", "logo", "school_identity"]
backend\tests\test_school_profile_unit.py:42:    """Verify tenant/school scoping keywords appear in the School Profile source tree."""
backend\tests\test_school_profile_unit.py:53:    ), f"School Profile: tenant/school scoping not found in source"
backend\tests\test_school_profile_tenant.py:2:Tenant isolation tests for the School Profile module.
backend\tests\test_school_profile_tenant.py:3:Module keywords: SchoolProfile, SchoolSettings, tenant_root, logo, school_identity
backend\tests\test_school_profile_tenant.py:23:        username=f"tenant-a-school_profile-{token}",
backend\tests\test_school_profile_tenant.py:32:    """Cross-tenant isolation tests for School Profile."""
backend\tests\test_school_profile_tenant.py:38:    def test_school_profile_tenant_school_ids_are_distinct(self):
backend\tests\test_school_profile_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_school_profile_tenant.py:47:    def test_school_profile_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_school_profile_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_school_profile_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_school_profile_tenant.py:58:    def test_school_profile_same_tenant_request_is_allowed(self):
backend\tests\test_school_profile_tenant.py:67:    def test_school_profile_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_school_profile_tenant.py:75:    def test_school_profile_isolation_keyword_present_in_source(self):
backend\tests\test_school_profile_tenant.py:76:        """Tenant isolation keywords exist in the School Profile module source."""
backend\tests\test_school_profile_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_school_profile_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_school_profile_tenant.py:87:        assert found, f"School Profile: tenant isolation keywords not found in source"
backend\tests\test_school_profile_negative.py:3:Module keywords: SchoolProfile, SchoolSettings, tenant_root, logo, school_identity
backend\tests\test_school_profile_api.py:3:Module keywords: SchoolProfile, SchoolSettings, tenant_root, logo, school_identity
backend\tests\test_school_profile_api.py:61:        """School record for School Profile tenant is created and queryable."""
backend\tests\test_school_profile_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_schedule_builder_unit.py:42:    """Verify tenant/school scoping keywords appear in the Standalone Schedule Builder source tree."""
backend\tests\test_schedule_builder_unit.py:53:    ), f"Standalone Schedule Builder: tenant/school scoping not found in source"
backend\tests\test_schedule_builder_tenant.py:2:Tenant isolation tests for the Standalone Schedule Builder module.
backend\tests\test_schedule_builder_tenant.py:23:        username=f"tenant-a-schedule_builder-{token}",
backend\tests\test_schedule_builder_tenant.py:32:    """Cross-tenant isolation tests for Standalone Schedule Builder."""
backend\tests\test_schedule_builder_tenant.py:38:    def test_schedule_builder_tenant_school_ids_are_distinct(self):
backend\tests\test_schedule_builder_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_schedule_builder_tenant.py:47:    def test_schedule_builder_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_schedule_builder_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_schedule_builder_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_schedule_builder_tenant.py:58:    def test_schedule_builder_same_tenant_request_is_allowed(self):
backend\tests\test_schedule_builder_tenant.py:67:    def test_schedule_builder_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_schedule_builder_tenant.py:75:    def test_schedule_builder_isolation_keyword_present_in_source(self):
backend\tests\test_schedule_builder_tenant.py:76:        """Tenant isolation keywords exist in the Standalone Schedule Builder module source."""
backend\tests\test_schedule_builder_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_schedule_builder_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_schedule_builder_tenant.py:87:        assert found, f"Standalone Schedule Builder: tenant isolation keywords not found in source"
backend\academic_year_wizard\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
frontend/dashboards/src\pages\IntegrationsAutomationDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="integrationsAutomation" />;
backend\tests\test_schedule_builder_api.py:61:        """School record for Standalone Schedule Builder tenant is created and queryable."""
backend\tests\test_schedule_builder_api.py:66:        """User is bound to the correct school tenant."""
frontend/dashboards/src\pages\ImplementationSuccessDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="implementationSuccess" />;
frontend/dashboards/src\pages\HumanResources.jsx:35:    { id: '1', first_name: 'Jane',  last_name: 'Smith',  role: 'Head of School',      department: 'Administration', active: true },
frontend/dashboards/src\pages\HumanResources.jsx:36:    { id: '2', first_name: 'Mark',  last_name: 'Torres', role: 'Dean of Academics',   department: 'Academics',      active: true },
frontend/dashboards/src\pages\HumanResources.jsx:37:    { id: '3', first_name: 'Linda', last_name: 'Park',   role: 'Director of Finance', department: 'Finance',        active: true },
frontend/dashboards/src\pages\HumanResources.jsx:38:    { id: '4', first_name: 'Brian', last_name: 'Hayes',  role: 'IT Coordinator',      department: 'Technology',     active: true },
frontend/dashboards/src\pages\HumanResources.jsx:39:    { id: '5', first_name: 'Sara',  last_name: 'Cole',   role: 'Registrar',           department: 'Administration', active: false },
frontend/dashboards/src\pages\HumanResources.jsx:47:  if (schoolId) headers['X-School-Id']   = schoolId;
frontend/dashboards/src\pages\HumanResources.jsx:153:                      <td style={{ padding: '6px 8px', color: 'var(--crown-ink)' }}>{e.role}</td>
backend\tests\test_reporting_data_access_unit.py:42:    """Verify tenant/school scoping keywords appear in the Reporting Data Access Standards source tree."""
backend\tests\test_reporting_data_access_unit.py:53:    ), f"Reporting Data Access Standards: tenant/school scoping not found in source"
backend\tests\test_reporting_data_access_tenant.py:2:Tenant isolation tests for the Reporting Data Access Standards module.
backend\tests\test_reporting_data_access_tenant.py:23:        username=f"tenant-a-reporting_data_access-{token}",
backend\tests\test_reporting_data_access_tenant.py:32:    """Cross-tenant isolation tests for Reporting Data Access Standards."""
backend\tests\test_reporting_data_access_tenant.py:38:    def test_reporting_data_access_tenant_school_ids_are_distinct(self):
backend\tests\test_reporting_data_access_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_reporting_data_access_tenant.py:47:    def test_reporting_data_access_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_reporting_data_access_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_reporting_data_access_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_reporting_data_access_tenant.py:58:    def test_reporting_data_access_same_tenant_request_is_allowed(self):
backend\tests\test_reporting_data_access_tenant.py:67:    def test_reporting_data_access_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_reporting_data_access_tenant.py:75:    def test_reporting_data_access_isolation_keyword_present_in_source(self):
backend\tests\test_reporting_data_access_tenant.py:76:        """Tenant isolation keywords exist in the Reporting Data Access Standards module source."""
backend\tests\test_reporting_data_access_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_reporting_data_access_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_reporting_data_access_tenant.py:87:        assert found, f"Reporting Data Access Standards: tenant isolation keywords not found in source"
frontend/dashboards/src\pages\HRDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="hr" />;
backend\billing_wizard\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
backend\tests\test_reporting_data_access_api.py:61:        """School record for Reporting Data Access Standards tenant is created and queryable."""
backend\tests\test_reporting_data_access_api.py:66:        """User is bound to the correct school tenant."""
frontend/dashboards/src\pages\HealthOfficeDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="healthOffice" />;
backend\tests\test_portrait_graduate_unit.py:42:    """Verify tenant/school scoping keywords appear in the Portrait of the Graduate source tree."""
backend\tests\test_portrait_graduate_unit.py:53:    ), f"Portrait of the Graduate: tenant/school scoping not found in source"
backend\tests\test_portrait_graduate_tenant.py:2:Tenant isolation tests for the Portrait of the Graduate module.
backend\tests\test_portrait_graduate_tenant.py:23:        username=f"tenant-a-portrait_graduate-{token}",
backend\tests\test_portrait_graduate_tenant.py:32:    """Cross-tenant isolation tests for Portrait of the Graduate."""
backend\tests\test_portrait_graduate_tenant.py:38:    def test_portrait_graduate_tenant_school_ids_are_distinct(self):
backend\tests\test_portrait_graduate_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_portrait_graduate_tenant.py:47:    def test_portrait_graduate_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_portrait_graduate_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_portrait_graduate_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_portrait_graduate_tenant.py:58:    def test_portrait_graduate_same_tenant_request_is_allowed(self):
backend\tests\test_portrait_graduate_tenant.py:67:    def test_portrait_graduate_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_portrait_graduate_tenant.py:75:    def test_portrait_graduate_isolation_keyword_present_in_source(self):
backend\tests\test_portrait_graduate_tenant.py:76:        """Tenant isolation keywords exist in the Portrait of the Graduate module source."""
backend\tests\test_portrait_graduate_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_portrait_graduate_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_portrait_graduate_tenant.py:87:        assert found, f"Portrait of the Graduate: tenant isolation keywords not found in source"
frontend/dashboards/src\pages\HealthDashboard.jsx:6:  return <CrownDashboardTemplate config={config} roleKey="health" />;
backend\tests\test_portrait_graduate_api.py:61:        """School record for Portrait of the Graduate tenant is created and queryable."""
backend\tests\test_portrait_graduate_api.py:66:        """User is bound to the correct school tenant."""
backend\curriculum\views.py:9:from rest_framework.permissions import IsAuthenticated
backend\curriculum\views.py:22:    permission_classes = [IsAuthenticated]
backend\curriculum\views.py:67:        School-scoped via X-School-Id.
backend\tests\test_platform_provisioning.py:26:    from tenants.models import TenantProfile
backend\tests\test_platform_provisioning.py:65:    from tenants.models import TenantProfile
backend\tests\test_phase72_tenant_isolation.py:5:Verifies tenant-scoping enforcement across the six major live API surfaces,
backend\tests\test_phase72_tenant_isolation.py:10:    ├óΓÇáΓÇÖ non-staff cross-tenant request ├óΓÇáΓÇÖ HTTP 404
backend\tests\test_phase72_tenant_isolation.py:14:    ├óΓÇáΓÇÖ cross-tenant request ├óΓÇáΓÇÖ HTTP 200 with empty/school-B-only data
backend\tests\test_phase72_tenant_isolation.py:15:    ├óΓÇáΓÇÖ school-A data MUST NOT appear (ORM-level isolation confirmed)
backend\tests\test_phase72_tenant_isolation.py:18:  1. Missing X-School-Id header  ├óΓÇáΓÇÖ 400
backend\tests\test_phase72_tenant_isolation.py:23:Branch: phase/7.2-tenant-isolation-audit
backend\tests\test_phase72_tenant_isolation.py:46:        # Non-staff user ├óΓé¼ΓÇ¥ used for cross-tenant (wrong school) tests.
backend\tests\test_phase72_tenant_isolation.py:53:        # Staff user ├óΓé¼ΓÇ¥ bypasses role checks; used for correct-school 200 tests.
backend\tests\test_phase72_tenant_isolation.py:68:        # tenant resolver finds no header and no user.school_id -> None -> 400.
backend\tests\test_phase72_tenant_isolation.py:88:    Mechanism: resolve_tenant_school_id detects header_present + user.school_id mismatch.
backend\tests\test_phase72_tenant_isolation.py:95:        No X-School-Id header -> MissingSchoolContext (HTTP 400).
backend\tests\test_phase72_tenant_isolation.py:96:        Must use user_noschool (no school_id attribute) so tenant resolver
backend\tests\test_phase72_tenant_isolation.py:106:        Non-staff users without a gradebook role get 403 from _sections_for_gradebook().
backend\tests\test_phase72_tenant_isolation.py:108:        the tenant guard firing.
backend\tests\test_phase72_tenant_isolation.py:118:        Canonical cross-tenant prevention confirmed.
backend\tests\test_phase72_tenant_isolation.py:140:      missing header ├óΓÇáΓÇÖ 400, wrong tenant ├óΓÇáΓÇÖ 404.
backend\tests\test_phase72_tenant_isolation.py:147:        No X-School-Id -> MissingSchoolContext (HTTP 400).
backend\tests\test_phase72_tenant_isolation.py:148:        Must use user_noschool (no school_id attribute) so tenant resolver
backend\tests\test_phase72_tenant_isolation.py:166:        Canonical cross-tenant prevention confirmed for billing module.
backend\tests\test_phase72_tenant_isolation.py:192:    Wrong-tenant non-staff requests now return HTTP 404 (was 200 before remediation).
backend\tests\test_phase72_tenant_isolation.py:199:        No X-School-Id header -> MissingSchoolContext (HTTP 400).
backend\tests\test_phase72_tenant_isolation.py:217:        get_request_school_id() enforces the cross-tenant guard.
backend\tests\test_phase72_tenant_isolation.py:223:    def test_cross_tenant_data_isolation_confirmed(self):
backend\tests\test_phase72_tenant_isolation.py:225:        Cross-tenant request blocked at the scoping layer (404).
backend\tests\test_phase72_tenant_isolation.py:247:    Scoping now fires before permission check; wrong-tenant -> 404.
backend\tests\test_phase72_tenant_isolation.py:253:        """No X-School-Id -> MissingSchoolContext (HTTP 400). Uses user_noschool."""
backend\tests\test_phase72_tenant_isolation.py:259:        """Correct school header -> scoping passes (200 or 403 from permission check)."""
backend\tests\test_phase72_tenant_isolation.py:265:        """Non-staff user_a with school_b header -> 404 (canonical cross-tenant guard)."""
backend\tests\test_phase72_tenant_isolation.py:282:#    canonical pattern; scoping fires before staff/permission checks in all three.
backend\tests\test_phase72_tenant_isolation.py:288:    Scoping fires before staff check; wrong-tenant -> 404, missing header -> 400.
backend\tests\test_phase72_tenant_isolation.py:294:        """No X-School-Id -> MissingSchoolContext (HTTP 400). Uses user_noschool."""
backend\tests\test_phase72_tenant_isolation.py:306:        """Non-staff user_a with school_b header -> 404 (canonical cross-tenant guard)."""
backend\tests\test_phase72_tenant_isolation.py:326:        """No X-School-Id -> MissingSchoolContext (HTTP 400). Scoping fires before body parse."""
backend\tests\test_phase72_tenant_isolation.py:341:        """Non-staff user_a with school_b header -> 404 (canonical cross-tenant guard)."""
backend\tests\test_parent_portal_unit.py:42:    """Verify tenant/school scoping keywords appear in the Parent Portal source tree."""
backend\tests\test_parent_portal_unit.py:53:    ), f"Parent Portal: tenant/school scoping not found in source"
backend\tests\test_parent_portal_tenant.py:2:Tenant isolation tests for the Parent Portal module.
backend\tests\test_parent_portal_tenant.py:23:        username=f"tenant-a-parent_portal-{token}",
backend\tests\test_parent_portal_tenant.py:32:    """Cross-tenant isolation tests for Parent Portal."""
backend\tests\test_parent_portal_tenant.py:38:    def test_parent_portal_tenant_school_ids_are_distinct(self):
backend\tests\test_parent_portal_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_parent_portal_tenant.py:47:    def test_parent_portal_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_parent_portal_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_parent_portal_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_parent_portal_tenant.py:58:    def test_parent_portal_same_tenant_request_is_allowed(self):
backend\tests\test_parent_portal_tenant.py:67:    def test_parent_portal_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_parent_portal_tenant.py:75:    def test_parent_portal_isolation_keyword_present_in_source(self):
backend\tests\test_parent_portal_tenant.py:76:        """Tenant isolation keywords exist in the Parent Portal module source."""
backend\tests\test_parent_portal_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_parent_portal_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_parent_portal_tenant.py:87:        assert found, f"Parent Portal: tenant isolation keywords not found in source"
backend\curriculum\utils.py:11:    require X-School-Id and resolve core.School.
backend\curriculum\utils.py:13:    raw = request.headers.get("X-School-Id") or request.META.get("HTTP_X_SCHOOL_ID")
backend\curriculum\utils.py:15:        raise ValidationError({"detail": "CTX_MISSING_SCHOOL_ID: X-School-Id header is required."})
backend\curriculum\utils.py:19:        raise ValidationError({"detail": f"CTX_INVALID_SCHOOL_ID: no school found for X-School-Id={raw}."})
backend\tests\test_parent_portal_api.py:61:        """School record for Parent Portal tenant is created and queryable."""
backend\tests\test_parent_portal_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_nurse_health_office_unit.py:42:    """Verify tenant/school scoping keywords appear in the Nurse Health Office source tree."""
backend\tests\test_nurse_health_office_unit.py:53:    ), f"Nurse Health Office: tenant/school scoping not found in source"
backend\tests\test_nurse_health_office_tenant.py:2:Tenant isolation tests for the Nurse Health Office module.
backend\tests\test_nurse_health_office_tenant.py:23:        username=f"tenant-a-nurse_health_office-{token}",
backend\tests\test_nurse_health_office_tenant.py:32:    """Cross-tenant isolation tests for Nurse Health Office."""
backend\tests\test_nurse_health_office_tenant.py:38:    def test_nurse_health_office_tenant_school_ids_are_distinct(self):
backend\tests\test_nurse_health_office_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_nurse_health_office_tenant.py:47:    def test_nurse_health_office_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_nurse_health_office_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_nurse_health_office_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_nurse_health_office_tenant.py:58:    def test_nurse_health_office_same_tenant_request_is_allowed(self):
backend\tests\test_nurse_health_office_tenant.py:67:    def test_nurse_health_office_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_nurse_health_office_tenant.py:75:    def test_nurse_health_office_isolation_keyword_present_in_source(self):
backend\tests\test_nurse_health_office_tenant.py:76:        """Tenant isolation keywords exist in the Nurse Health Office module source."""
backend\tests\test_nurse_health_office_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_nurse_health_office_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_nurse_health_office_tenant.py:87:        assert found, f"Nurse Health Office: tenant isolation keywords not found in source"
backend\tests\test_nurse_health_office_api.py:61:        """School record for Nurse Health Office tenant is created and queryable."""
backend\tests\test_nurse_health_office_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_notifications_framework_unit.py:42:    """Verify tenant/school scoping keywords appear in the Notifications Framework source tree."""
backend\tests\test_notifications_framework_unit.py:53:    ), f"Notifications Framework: tenant/school scoping not found in source"
backend\tests\test_notifications_framework_tenant.py:2:Tenant isolation tests for the Notifications Framework module.
backend\tests\test_notifications_framework_tenant.py:23:        username=f"tenant-a-notifications_framework-{token}",
backend\tests\test_notifications_framework_tenant.py:32:    """Cross-tenant isolation tests for Notifications Framework."""
backend\tests\test_notifications_framework_tenant.py:38:    def test_notifications_framework_tenant_school_ids_are_distinct(self):
backend\tests\test_notifications_framework_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_notifications_framework_tenant.py:47:    def test_notifications_framework_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_notifications_framework_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_notifications_framework_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_notifications_framework_tenant.py:58:    def test_notifications_framework_same_tenant_request_is_allowed(self):
backend\tests\test_notifications_framework_tenant.py:67:    def test_notifications_framework_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_notifications_framework_tenant.py:75:    def test_notifications_framework_isolation_keyword_present_in_source(self):
backend\tests\test_notifications_framework_tenant.py:76:        """Tenant isolation keywords exist in the Notifications Framework module source."""
backend\tests\test_notifications_framework_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_notifications_framework_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_notifications_framework_tenant.py:87:        assert found, f"Notifications Framework: tenant isolation keywords not found in source"
backend\tests\test_notifications_framework_api.py:61:        """School record for Notifications Framework tenant is created and queryable."""
backend\tests\test_notifications_framework_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_mobile_family_app_unit.py:42:    """Verify tenant/school scoping keywords appear in the Mobile Family App source tree."""
backend\tests\test_mobile_family_app_unit.py:53:    ), f"Mobile Family App: tenant/school scoping not found in source"
backend\tests\test_mobile_family_app_tenant.py:2:Tenant isolation tests for the Mobile Family App module.
backend\tests\test_mobile_family_app_tenant.py:23:        username=f"tenant-a-mobile_family_app-{token}",
backend\tests\test_mobile_family_app_tenant.py:32:    """Cross-tenant isolation tests for Mobile Family App."""
backend\tests\test_mobile_family_app_tenant.py:38:    def test_mobile_family_app_tenant_school_ids_are_distinct(self):
backend\tests\test_mobile_family_app_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_mobile_family_app_tenant.py:47:    def test_mobile_family_app_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_mobile_family_app_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_mobile_family_app_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_mobile_family_app_tenant.py:58:    def test_mobile_family_app_same_tenant_request_is_allowed(self):
backend\tests\test_mobile_family_app_tenant.py:67:    def test_mobile_family_app_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_mobile_family_app_tenant.py:75:    def test_mobile_family_app_isolation_keyword_present_in_source(self):
backend\tests\test_mobile_family_app_tenant.py:76:        """Tenant isolation keywords exist in the Mobile Family App module source."""
backend\tests\test_mobile_family_app_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_mobile_family_app_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_mobile_family_app_tenant.py:87:        assert found, f"Mobile Family App: tenant isolation keywords not found in source"
frontend/dashboards/src\pages\GradebookRO.jsx:279:  // Probe write permissions once after assignments load
frontend/dashboards/src\pages\GradebookRO.jsx:378:  // Probe write permissions once on load
backend\tests\test_mobile_family_app_api.py:61:        """School record for Mobile Family App tenant is created and queryable."""
backend\tests\test_mobile_family_app_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_mission_metrics_unit.py:42:    """Verify tenant/school scoping keywords appear in the Mission Metrics source tree."""
backend\tests\test_mission_metrics_unit.py:53:    ), f"Mission Metrics: tenant/school scoping not found in source"
frontend/dashboards/src\pages\GradebookDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="gradebook" />;
backend\tests\test_mission_metrics_tenant.py:2:Tenant isolation tests for the Mission Metrics module.
backend\tests\test_mission_metrics_tenant.py:23:        username=f"tenant-a-mission_metrics-{token}",
backend\tests\test_mission_metrics_tenant.py:32:    """Cross-tenant isolation tests for Mission Metrics."""
backend\tests\test_mission_metrics_tenant.py:38:    def test_mission_metrics_tenant_school_ids_are_distinct(self):
backend\tests\test_mission_metrics_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_mission_metrics_tenant.py:47:    def test_mission_metrics_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_mission_metrics_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_mission_metrics_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_mission_metrics_tenant.py:58:    def test_mission_metrics_same_tenant_request_is_allowed(self):
backend\tests\test_mission_metrics_tenant.py:67:    def test_mission_metrics_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_mission_metrics_tenant.py:75:    def test_mission_metrics_isolation_keyword_present_in_source(self):
backend\tests\test_mission_metrics_tenant.py:76:        """Tenant isolation keywords exist in the Mission Metrics module source."""
backend\tests\test_mission_metrics_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_mission_metrics_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_mission_metrics_tenant.py:87:        assert found, f"Mission Metrics: tenant isolation keywords not found in source"
frontend/dashboards/src\pages\ForbiddenPage.jsx:10:  const role = state.role || 'unknown';
frontend/dashboards/src\pages\ForbiddenPage.jsx:22:            Your current role does not have access to this page.
frontend/dashboards/src\pages\ForbiddenPage.jsx:26:            Role: <strong>{role}</strong>
frontend/dashboards/src\pages\FoodServiceDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="foodService" />;
backend\tests\test_mission_metrics_api.py:61:        """School record for Mission Metrics tenant is created and queryable."""
backend\tests\test_mission_metrics_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_microsoft_integration_readiness.py:31:    monkeypatch.setenv("AZURE_TENANT_ID", "tenant-123")
backend\tests\test_microsoft_integration_readiness.py:54:    assert calls[0]["url"].startswith("https://login.microsoftonline.com/tenant-123/")
backend\course_catalog_wizard\views.py:7:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\course_catalog_wizard\views.py:8:from rest_framework.permissions import IsAuthenticated
backend\course_catalog_wizard\views.py:29:@permission_classes(_PERM)
backend\course_catalog_wizard\views.py:40:@permission_classes(_PERM)
backend\course_catalog_wizard\views.py:76:@permission_classes(_PERM)
backend\course_catalog_wizard\views.py:111:@permission_classes(_PERM)
backend\tests\test_graduation_audit_v1.py:6:from core.tenant_models import clear_current_school, set_current_school
backend\tests\test_grade_levels_unit.py:42:    """Verify tenant/school scoping keywords appear in the Grade Levels source tree."""
backend\tests\test_grade_levels_unit.py:53:    ), f"Grade Levels: tenant/school scoping not found in source"
backend\tests\test_grade_levels_tenant.py:2:Tenant isolation tests for the Grade Levels module.
backend\tests\test_grade_levels_tenant.py:23:        username=f"tenant-a-grade_levels-{token}",
backend\tests\test_grade_levels_tenant.py:32:    """Cross-tenant isolation tests for Grade Levels."""
backend\tests\test_grade_levels_tenant.py:38:    def test_grade_levels_tenant_school_ids_are_distinct(self):
backend\tests\test_grade_levels_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_grade_levels_tenant.py:47:    def test_grade_levels_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_grade_levels_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_grade_levels_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_grade_levels_tenant.py:58:    def test_grade_levels_same_tenant_request_is_allowed(self):
backend\tests\test_grade_levels_tenant.py:67:    def test_grade_levels_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_grade_levels_tenant.py:75:    def test_grade_levels_isolation_keyword_present_in_source(self):
backend\tests\test_grade_levels_tenant.py:76:        """Tenant isolation keywords exist in the Grade Levels module source."""
backend\tests\test_grade_levels_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_grade_levels_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_grade_levels_tenant.py:87:        assert found, f"Grade Levels: tenant isolation keywords not found in source"
backend\academics_ro\views.py:16:    role = (
backend\academics_ro\views.py:17:        getattr(request, "crown_role", None) 
backend\academics_ro\views.py:19:        or request.headers.get("x-role") 
backend\academics_ro\views.py:32:        or request.headers.get("X-School-Id") 
backend\academics_ro\views.py:37:    return (role, user_id, school_id)
backend\academics_ro\views.py:48:    permission_classes = []
backend\academics_ro\views.py:51:        role, user_id, school_id = _get_user_context(request)
backend\academics_ro\views.py:56:                {"detail": "Missing school context (X-School-Id header required)."},
backend\academics_ro\views.py:68:        if not role or role not in ALLOWED_ROLES:
backend\academics_ro\views.py:70:                {"detail": f"Invalid or missing role. X-Role header must be one of: {', '.join(ALLOWED_ROLES)}."},
frontend/dashboards/src\pages\FoodDashboard.jsx:6:  return <CrownDashboardTemplate config={config} roleKey="food" />;
backend\tests\test_grade_levels_api.py:61:        """School record for Grade Levels tenant is created and queryable."""
backend\tests\test_grade_levels_api.py:66:        """User is bound to the correct school tenant."""
frontend/dashboards/src\pages\FineArtsDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="fineArts" />;
backend\tests\test_grades_report_cards_unit.py:42:    """Verify tenant/school scoping keywords appear in the Grades Report Cards source tree."""
backend\tests\test_grades_report_cards_unit.py:53:    ), f"Grades Report Cards: tenant/school scoping not found in source"
backend\tests\test_grades_report_cards_tenant.py:2:Tenant isolation tests for the Grades Report Cards module.
backend\tests\test_grades_report_cards_tenant.py:23:        username=f"tenant-a-grades_report_cards-{token}",
backend\tests\test_grades_report_cards_tenant.py:32:    """Cross-tenant isolation tests for Grades Report Cards."""
backend\tests\test_grades_report_cards_tenant.py:38:    def test_grades_report_cards_tenant_school_ids_are_distinct(self):
backend\tests\test_grades_report_cards_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_grades_report_cards_tenant.py:47:    def test_grades_report_cards_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_grades_report_cards_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_grades_report_cards_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_grades_report_cards_tenant.py:58:    def test_grades_report_cards_same_tenant_request_is_allowed(self):
backend\tests\test_grades_report_cards_tenant.py:67:    def test_grades_report_cards_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_grades_report_cards_tenant.py:75:    def test_grades_report_cards_isolation_keyword_present_in_source(self):
backend\tests\test_grades_report_cards_tenant.py:76:        """Tenant isolation keywords exist in the Grades Report Cards module source."""
backend\tests\test_grades_report_cards_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_grades_report_cards_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_grades_report_cards_tenant.py:87:        assert found, f"Grades Report Cards: tenant isolation keywords not found in source"
backend\tests\test_grades_report_cards_api.py:61:        """School record for Grades Report Cards tenant is created and queryable."""
backend\tests\test_grades_report_cards_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_golden_path.py:40:    RolePermission.objects.get_or_create(role_code="REGISTRAR", permission=perm)
backend\tests\test_golden_path.py:41:    UserRole.objects.get_or_create(user=user, school=school, role_code="REGISTRAR")
backend\tests\test_golden_path.py:172:    UserRole.objects.create(user=user, school=school, role_code="HEAD_OF_SCHOOL")
backend\tests\test_extended_discipline_unit.py:42:    """Verify tenant/school scoping keywords appear in the Extended Discipline Workflows source tree."""
backend\tests\test_extended_discipline_unit.py:53:    ), f"Extended Discipline Workflows: tenant/school scoping not found in source"
backend\tests\test_extended_discipline_tenant.py:2:Tenant isolation tests for the Extended Discipline Workflows module.
backend\tests\test_extended_discipline_tenant.py:23:        username=f"tenant-a-extended_discipline-{token}",
backend\tests\test_extended_discipline_tenant.py:32:    """Cross-tenant isolation tests for Extended Discipline Workflows."""
backend\tests\test_extended_discipline_tenant.py:38:    def test_extended_discipline_tenant_school_ids_are_distinct(self):
backend\tests\test_extended_discipline_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_extended_discipline_tenant.py:47:    def test_extended_discipline_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_extended_discipline_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_extended_discipline_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_extended_discipline_tenant.py:58:    def test_extended_discipline_same_tenant_request_is_allowed(self):
backend\tests\test_extended_discipline_tenant.py:67:    def test_extended_discipline_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_extended_discipline_tenant.py:75:    def test_extended_discipline_isolation_keyword_present_in_source(self):
backend\tests\test_extended_discipline_tenant.py:76:        """Tenant isolation keywords exist in the Extended Discipline Workflows module source."""
backend\tests\test_extended_discipline_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_extended_discipline_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_extended_discipline_tenant.py:87:        assert found, f"Extended Discipline Workflows: tenant isolation keywords not found in source"
backend\tests\test_extended_discipline_api.py:61:        """School record for Extended Discipline Workflows tenant is created and queryable."""
backend\tests\test_extended_discipline_api.py:66:        """User is bound to the correct school tenant."""
backend\billing\api.py:12:from rest_framework.decorators import api_view, permission_classes
backend\billing\api.py:13:from rest_framework.permissions import IsAuthenticated
backend\billing\api.py:22:from crown_api.billing_api.permissions import has_finance_runtime_role
backend\billing\api.py:47:@permission_classes([IsAuthenticated])
backend\billing\api.py:154:@permission_classes([IsAuthenticated])
backend\billing\api.py:209:@permission_classes([IsAuthenticated])
backend\billing\api.py:272:@permission_classes([IsAuthenticated])
backend\billing\api.py:289:@permission_classes([IsAuthenticated])
backend\billing\api.py:296:    if not has_finance_runtime_role(request.user):
backend\billing\api.py:298:            {"detail": "You do not have permission to view school-wide invoices."},
backend\tests\test_emergency_medical_unit.py:42:    """Verify tenant/school scoping keywords appear in the Emergency Medical Essentials source tree."""
backend\tests\test_emergency_medical_unit.py:53:    ), f"Emergency Medical Essentials: tenant/school scoping not found in source"
backend\tests\test_emergency_medical_tenant.py:2:Tenant isolation tests for the Emergency Medical Essentials module.
backend\tests\test_emergency_medical_tenant.py:23:        username=f"tenant-a-emergency_medical-{token}",
backend\tests\test_emergency_medical_tenant.py:32:    """Cross-tenant isolation tests for Emergency Medical Essentials."""
backend\tests\test_emergency_medical_tenant.py:38:    def test_emergency_medical_tenant_school_ids_are_distinct(self):
backend\tests\test_emergency_medical_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_emergency_medical_tenant.py:47:    def test_emergency_medical_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_emergency_medical_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_emergency_medical_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_emergency_medical_tenant.py:58:    def test_emergency_medical_same_tenant_request_is_allowed(self):
backend\tests\test_emergency_medical_tenant.py:67:    def test_emergency_medical_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_emergency_medical_tenant.py:75:    def test_emergency_medical_isolation_keyword_present_in_source(self):
backend\tests\test_emergency_medical_tenant.py:76:        """Tenant isolation keywords exist in the Emergency Medical Essentials module source."""
backend\tests\test_emergency_medical_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_emergency_medical_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_emergency_medical_tenant.py:87:        assert found, f"Emergency Medical Essentials: tenant isolation keywords not found in source"
backend\tests\test_emergency_medical_api.py:61:        """School record for Emergency Medical Essentials tenant is created and queryable."""
backend\tests\test_emergency_medical_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_document_file_framework_unit.py:42:    """Verify tenant/school scoping keywords appear in the Document File Framework source tree."""
backend\tests\test_document_file_framework_unit.py:53:    ), f"Document File Framework: tenant/school scoping not found in source"
backend\tests\test_document_file_framework_tenant.py:2:Tenant isolation tests for the Document File Framework module.
backend\tests\test_document_file_framework_tenant.py:23:        username=f"tenant-a-document_file_framework-{token}",
backend\tests\test_document_file_framework_tenant.py:32:    """Cross-tenant isolation tests for Document File Framework."""
backend\tests\test_document_file_framework_tenant.py:38:    def test_document_file_framework_tenant_school_ids_are_distinct(self):
backend\tests\test_document_file_framework_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_document_file_framework_tenant.py:47:    def test_document_file_framework_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_document_file_framework_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_document_file_framework_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_document_file_framework_tenant.py:58:    def test_document_file_framework_same_tenant_request_is_allowed(self):
backend\tests\test_document_file_framework_tenant.py:67:    def test_document_file_framework_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_document_file_framework_tenant.py:75:    def test_document_file_framework_isolation_keyword_present_in_source(self):
backend\tests\test_document_file_framework_tenant.py:76:        """Tenant isolation keywords exist in the Document File Framework module source."""
backend\tests\test_document_file_framework_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_document_file_framework_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_document_file_framework_tenant.py:87:        assert found, f"Document File Framework: tenant isolation keywords not found in source"
backend\tests\test_document_file_framework_api.py:61:        """School record for Document File Framework tenant is created and queryable."""
backend\tests\test_document_file_framework_api.py:66:        """User is bound to the correct school tenant."""
backend\curricula\views.py:3:from rest_framework.decorators import api_view, permission_classes
backend\curricula\views.py:4:from rest_framework.permissions import IsAuthenticated
backend\curricula\views.py:22:    permission_classes = [IsAuthenticated]
backend\curricula\views.py:43:    permission_classes = [IsAuthenticated]
backend\curricula\views.py:64:    permission_classes = [IsAuthenticated]
backend\tests\test_curriculum_pacing.py:19:    - Respects school scoping via X-School-Id header
backend\tests\test_crown_compass_unit.py:42:    """Verify tenant/school scoping keywords appear in the Crown Compass source tree."""
backend\tests\test_crown_compass_unit.py:53:    ), f"Crown Compass: tenant/school scoping not found in source"
backend\tests\test_crown_compass_tenant.py:2:Tenant isolation tests for the Crown Compass module.
backend\tests\test_crown_compass_tenant.py:23:        username=f"tenant-a-crown_compass-{token}",
backend\tests\test_crown_compass_tenant.py:32:    """Cross-tenant isolation tests for Crown Compass."""
backend\tests\test_crown_compass_tenant.py:38:    def test_crown_compass_tenant_school_ids_are_distinct(self):
backend\tests\test_crown_compass_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_crown_compass_tenant.py:47:    def test_crown_compass_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_crown_compass_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_crown_compass_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_crown_compass_tenant.py:58:    def test_crown_compass_same_tenant_request_is_allowed(self):
backend\tests\test_crown_compass_tenant.py:67:    def test_crown_compass_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_crown_compass_tenant.py:75:    def test_crown_compass_isolation_keyword_present_in_source(self):
backend\tests\test_crown_compass_tenant.py:76:        """Tenant isolation keywords exist in the Crown Compass module source."""
backend\tests\test_crown_compass_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_crown_compass_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_crown_compass_tenant.py:87:        assert found, f"Crown Compass: tenant isolation keywords not found in source"
frontend/dashboards/src\pages\FinancialAidDashboard.jsx:12:  return <CrownDashboardTemplate config={config} roleKey="financialAid" />;
backend\tests\test_crown_compass_api.py:61:        """School record for Crown Compass tenant is created and queryable."""
backend\tests\test_crown_compass_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_crm_marketing_unit.py:42:    """Verify tenant/school scoping keywords appear in the CRM Marketing Suite source tree."""
backend\tests\test_crm_marketing_unit.py:53:    ), f"CRM Marketing Suite: tenant/school scoping not found in source"
backend\tests\test_crm_marketing_tenant.py:2:Tenant isolation tests for the CRM Marketing Suite module.
backend\tests\test_crm_marketing_tenant.py:23:        username=f"tenant-a-crm_marketing-{token}",
backend\tests\test_crm_marketing_tenant.py:32:    """Cross-tenant isolation tests for CRM Marketing Suite."""
backend\tests\test_crm_marketing_tenant.py:38:    def test_crm_marketing_tenant_school_ids_are_distinct(self):
backend\tests\test_crm_marketing_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_crm_marketing_tenant.py:47:    def test_crm_marketing_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_crm_marketing_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_crm_marketing_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_crm_marketing_tenant.py:58:    def test_crm_marketing_same_tenant_request_is_allowed(self):
backend\tests\test_crm_marketing_tenant.py:67:    def test_crm_marketing_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_crm_marketing_tenant.py:75:    def test_crm_marketing_isolation_keyword_present_in_source(self):
backend\tests\test_crm_marketing_tenant.py:76:        """Tenant isolation keywords exist in the CRM Marketing Suite module source."""
backend\tests\test_crm_marketing_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_crm_marketing_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_crm_marketing_tenant.py:87:        assert found, f"CRM Marketing Suite: tenant isolation keywords not found in source"
backend\tests\test_crm_marketing_api.py:61:        """School record for CRM Marketing Suite tenant is created and queryable."""
backend\tests\test_crm_marketing_api.py:66:        """User is bound to the correct school tenant."""
backend\course_catalog_wizard\migrations\0001_initial.py:13:        ('core', '0005_crown_permission_engine'),
backend\tests\TEST_CONVENTIONS.md:6:API tests must satisfy tenant context explicitly, or they will fail early by design before permission/view logic executes.
backend\tests\TEST_CONVENTIONS.md:12:3. For tests expecting tenant errors, assert the explicit tenant failure contract (`missing_tenant`, `invalid_tenant_header`, etc.) rather than generic auth failures.
backend\tests\TEST_CONVENTIONS.md:13:4. Only exempt endpoints listed by tenant middleware policy should omit tenant context.
backend\tests\TEST_CONVENTIONS.md:39:Tests that omit tenant context can fail with 400 before hitting endpoint permissions/logic, which masks true intent of auth/business assertions.
backend\tests\test_communications_unit.py:42:    """Verify tenant/school scoping keywords appear in the Communications source tree."""
backend\tests\test_communications_unit.py:53:    ), f"Communications: tenant/school scoping not found in source"
backend\tests\test_communications_tenant.py:2:Tenant isolation tests for the Communications module.
backend\tests\test_communications_tenant.py:23:        username=f"tenant-a-communications-{token}",
backend\tests\test_communications_tenant.py:32:    """Cross-tenant isolation tests for Communications."""
backend\tests\test_communications_tenant.py:38:    def test_communications_tenant_school_ids_are_distinct(self):
backend\tests\test_communications_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_communications_tenant.py:47:    def test_communications_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_communications_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_communications_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_communications_tenant.py:58:    def test_communications_same_tenant_request_is_allowed(self):
backend\tests\test_communications_tenant.py:67:    def test_communications_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_communications_tenant.py:75:    def test_communications_isolation_keyword_present_in_source(self):
backend\tests\test_communications_tenant.py:76:        """Tenant isolation keywords exist in the Communications module source."""
backend\tests\test_communications_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_communications_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_communications_tenant.py:87:        assert found, f"Communications: tenant isolation keywords not found in source"
backend\curricula\tests\test_curricula_tenant_isolation.py:2:Tenant isolation tests for curricula API.
backend\curricula\tests\test_curricula_tenant_isolation.py:101:def test_curriculum_maps_tenant_isolation(two_schools_with_curricula):
backend\curricula\tests\test_curricula_tenant_isolation.py:118:def test_units_tenant_isolation(two_schools_with_curricula):
backend\curricula\tests\test_curricula_tenant_isolation.py:135:def test_lessons_tenant_isolation(two_schools_with_curricula):
backend\curricula\tests\test_curricula_tenant_isolation.py:153:    """Verify filtering by course respects tenant isolation."""
backend\curricula\tests\test_curricula_tenant_isolation.py:165:    # Try to filter by school B's course - should see nothing (tenant boundary)
backend\curricula\tests\test_curricula_tenant_isolation.py:172:    """Verify filtering by curriculum map respects tenant isolation."""
backend\curricula\tests\test_curricula_tenant_isolation.py:191:    """Verify filtering by unit respects tenant isolation."""
backend\curricula\tests\test_curricula_tenant_isolation.py:265:def test_curricula_detail_views_tenant_isolation(two_schools_with_curricula):
backend\curricula\tests\test_curricula_tenant_isolation.py:266:    """Verify detail endpoints respect tenant boundaries."""
backend\tests\test_communications_api.py:61:        """School record for Communications tenant is created and queryable."""
backend\tests\test_communications_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_christian_pd_hub_unit.py:42:    """Verify tenant/school scoping keywords appear in the Christian PD Hub source tree."""
backend\tests\test_christian_pd_hub_unit.py:53:    ), f"Christian PD Hub: tenant/school scoping not found in source"
backend\tests\test_christian_pd_hub_tenant.py:2:Tenant isolation tests for the Christian PD Hub module.
backend\tests\test_christian_pd_hub_tenant.py:23:        username=f"tenant-a-christian_pd_hub-{token}",
backend\tests\test_christian_pd_hub_tenant.py:32:    """Cross-tenant isolation tests for Christian PD Hub."""
backend\tests\test_christian_pd_hub_tenant.py:38:    def test_christian_pd_hub_tenant_school_ids_are_distinct(self):
backend\tests\test_christian_pd_hub_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_christian_pd_hub_tenant.py:47:    def test_christian_pd_hub_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_christian_pd_hub_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_christian_pd_hub_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_christian_pd_hub_tenant.py:58:    def test_christian_pd_hub_same_tenant_request_is_allowed(self):
backend\tests\test_christian_pd_hub_tenant.py:67:    def test_christian_pd_hub_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_christian_pd_hub_tenant.py:75:    def test_christian_pd_hub_isolation_keyword_present_in_source(self):
backend\tests\test_christian_pd_hub_tenant.py:76:        """Tenant isolation keywords exist in the Christian PD Hub module source."""
backend\tests\test_christian_pd_hub_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_christian_pd_hub_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_christian_pd_hub_tenant.py:87:        assert found, f"Christian PD Hub: tenant isolation keywords not found in source"
backend\tests\test_christian_pd_hub_api.py:61:        """School record for Christian PD Hub tenant is created and queryable."""
backend\tests\test_christian_pd_hub_api.py:66:        """User is bound to the correct school tenant."""
frontend/dashboards/src\pages\FacilitiesDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="facilities" />;
backend\tests\test_chaplain_pastoral_care_unit.py:42:    """Verify tenant/school scoping keywords appear in the Chaplain Pastoral Care source tree."""
backend\tests\test_chaplain_pastoral_care_unit.py:53:    ), f"Chaplain Pastoral Care: tenant/school scoping not found in source"
backend\tests\test_chaplain_pastoral_care_tenant.py:2:Tenant isolation tests for the Chaplain Pastoral Care module.
backend\tests\test_chaplain_pastoral_care_tenant.py:23:        username=f"tenant-a-chaplain_pastoral_care-{token}",
backend\tests\test_chaplain_pastoral_care_tenant.py:32:    """Cross-tenant isolation tests for Chaplain Pastoral Care."""
backend\tests\test_chaplain_pastoral_care_tenant.py:38:    def test_chaplain_pastoral_care_tenant_school_ids_are_distinct(self):
backend\tests\test_chaplain_pastoral_care_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_chaplain_pastoral_care_tenant.py:47:    def test_chaplain_pastoral_care_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_chaplain_pastoral_care_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_chaplain_pastoral_care_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_chaplain_pastoral_care_tenant.py:58:    def test_chaplain_pastoral_care_same_tenant_request_is_allowed(self):
backend\tests\test_chaplain_pastoral_care_tenant.py:67:    def test_chaplain_pastoral_care_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_chaplain_pastoral_care_tenant.py:75:    def test_chaplain_pastoral_care_isolation_keyword_present_in_source(self):
backend\tests\test_chaplain_pastoral_care_tenant.py:76:        """Tenant isolation keywords exist in the Chaplain Pastoral Care module source."""
backend\tests\test_chaplain_pastoral_care_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_chaplain_pastoral_care_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_chaplain_pastoral_care_tenant.py:87:        assert found, f"Chaplain Pastoral Care: tenant isolation keywords not found in source"
frontend/dashboards/src\pages\ExtendedCareDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="extendedCare" />;
backend\tests\test_chaplain_pastoral_care_api.py:61:        """School record for Chaplain Pastoral Care tenant is created and queryable."""
backend\tests\test_chaplain_pastoral_care_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_board_governance_suite_unit.py:42:    """Verify tenant/school scoping keywords appear in the Board Governance Suite source tree."""
backend\tests\test_board_governance_suite_unit.py:53:    ), f"Board Governance Suite: tenant/school scoping not found in source"
backend\tests\test_board_governance_suite_tenant.py:2:Tenant isolation tests for the Board Governance Suite module.
backend\tests\test_board_governance_suite_tenant.py:23:        username=f"tenant-a-board_governance_suite-{token}",
backend\tests\test_board_governance_suite_tenant.py:32:    """Cross-tenant isolation tests for Board Governance Suite."""
backend\tests\test_board_governance_suite_tenant.py:38:    def test_board_governance_suite_tenant_school_ids_are_distinct(self):
backend\tests\test_board_governance_suite_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_board_governance_suite_tenant.py:47:    def test_board_governance_suite_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_board_governance_suite_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_board_governance_suite_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_board_governance_suite_tenant.py:58:    def test_board_governance_suite_same_tenant_request_is_allowed(self):
backend\tests\test_board_governance_suite_tenant.py:67:    def test_board_governance_suite_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_board_governance_suite_tenant.py:75:    def test_board_governance_suite_isolation_keyword_present_in_source(self):
backend\tests\test_board_governance_suite_tenant.py:76:        """Tenant isolation keywords exist in the Board Governance Suite module source."""
backend\tests\test_board_governance_suite_tenant.py:85:        isolation_keywords = ["school_id", "TenantScoped", "tenant", "X-School-ID", "403", "404"]
backend\tests\test_board_governance_suite_tenant.py:86:        found = any(kw in source_text for kw in isolation_keywords)
backend\tests\test_board_governance_suite_tenant.py:87:        assert found, f"Board Governance Suite: tenant isolation keywords not found in source"
backend\tests\test_board_governance_suite_api.py:61:        """School record for Board Governance Suite tenant is created and queryable."""
backend\tests\test_board_governance_suite_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_audit_logging_unit.py:42:    """Verify tenant/school scoping keywords appear in the Audit Logging source tree."""
backend\tests\test_audit_logging_unit.py:53:    ), f"Audit Logging: tenant/school scoping not found in source"
backend\tests\test_audit_logging_tenant.py:2:Tenant isolation tests for the Audit Logging module.
backend\tests\test_audit_logging_tenant.py:23:        username=f"tenant-a-audit_logging-{token}",
backend\tests\test_audit_logging_tenant.py:32:    """Cross-tenant isolation tests for Audit Logging."""
backend\tests\test_audit_logging_tenant.py:38:    def test_audit_logging_tenant_school_ids_are_distinct(self):
backend\tests\test_audit_logging_tenant.py:39:        """Two tenant schools have distinct IDs ├óΓé¼ΓÇ¥ no data bleed possible."""
backend\tests\test_audit_logging_tenant.py:47:    def test_audit_logging_cross_tenant_header_is_rejected_or_scoped(self):
backend\tests\test_audit_logging_tenant.py:48:        """User from school A cannot freely access school B resources (cross-tenant 403/404)."""
backend\tests\test_audit_logging_tenant.py:55:        # cross-tenant isolation: result must not be an unguarded 200 serving school B data
backend\tests\test_audit_logging_tenant.py:58:    def test_audit_logging_same_tenant_request_is_allowed(self):
backend\tests\test_audit_logging_tenant.py:67:    def test_audit_logging_unauthenticated_cross_tenant_is_denied(self):
backend\tests\test_audit_logging_tenant.py:75:    def test_audit_logging_isolation_keyword_present_in_source(self):
backend\tests\test_audit_logging_tenant.py:76:        """Tenant isolation keywords exist in the Audit Logging module source."""
backend\tests\test_audit_logging_api.py:61:        """School record for Audit Logging tenant is created and queryable."""
backend\tests\test_audit_logging_api.py:66:        """User is bound to the correct school tenant."""
backend\tests\test_51x51_evidence_51_standalone_schedule_builder.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_51_standalone_schedule_builder.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_51_standalone_schedule_builder.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_51_standalone_schedule_builder.py:45:# tenant
backend\tests\test_51x51_evidence_51_standalone_schedule_builder.py:46:# cross-tenant
backend\tests\test_51x51_evidence_51_standalone_schedule_builder.py:48:# isolation
backend\bell_schedule_wizard\views.py:8:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\bell_schedule_wizard\views.py:9:from rest_framework.permissions import IsAuthenticated
backend\bell_schedule_wizard\views.py:156:@permission_classes(_PERM)
backend\bell_schedule_wizard\views.py:175:@permission_classes(_PERM)
backend\bell_schedule_wizard\views.py:224:@permission_classes(_PERM)
backend\bell_schedule_wizard\views.py:310:@permission_classes(_PERM)
backend\bell_schedule_wizard\views.py:431:@permission_classes(_PERM)
backend\tests\test_51x51_evidence_49_survey___sentiment_engine.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_49_survey___sentiment_engine.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_49_survey___sentiment_engine.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_49_survey___sentiment_engine.py:45:# tenant
backend\tests\test_51x51_evidence_49_survey___sentiment_engine.py:46:# cross-tenant
backend\tests\test_51x51_evidence_49_survey___sentiment_engine.py:48:# isolation
backend\tests\test_51x51_evidence_48_mobile_app___family_app.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_48_mobile_app___family_app.py:13:MODULE_TEXT = 'Mobile App / Family App\nProvides mobile access to family, student, teacher, alerts, calendar, and school-life workflows.\nMobile login | Push alerts | Family view | Calendar | Messages\nAuthenticate mobile user | Send push | Show scoped records | Support tasks | Respect permissions\nmobile active users | push delivery | crash rate | task completion | mobile login success\nauth | parent portal | communications | calendar | notifications\nProduct + Dev 4\nLater Add-on'
backend\tests\test_51x51_evidence_48_mobile_app___family_app.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_48_mobile_app___family_app.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_48_mobile_app___family_app.py:38:# Authenticate mobile user | Send push | Show scoped records | Support tasks | Respect permissions
backend\tests\test_51x51_evidence_48_mobile_app___family_app.py:45:# tenant
backend\tests\test_51x51_evidence_48_mobile_app___family_app.py:46:# cross-tenant
backend\tests\test_51x51_evidence_48_mobile_app___family_app.py:48:# isolation
backend\tests\test_51x51_evidence_47_crm___marketing_suite.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_47_crm___marketing_suite.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_47_crm___marketing_suite.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_47_crm___marketing_suite.py:45:# tenant
backend\tests\test_51x51_evidence_47_crm___marketing_suite.py:46:# cross-tenant
backend\tests\test_51x51_evidence_47_crm___marketing_suite.py:48:# isolation
backend\tests\test_51x51_evidence_46_mission_metrics.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_46_mission_metrics.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_46_mission_metrics.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_46_mission_metrics.py:45:# tenant
backend\tests\test_51x51_evidence_46_mission_metrics.py:46:# cross-tenant
backend\tests\test_51x51_evidence_46_mission_metrics.py:48:# isolation
backend\tests\test_51x51_evidence_45_portrait_of_the_graduate.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_45_portrait_of_the_graduate.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_45_portrait_of_the_graduate.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_45_portrait_of_the_graduate.py:45:# tenant
backend\tests\test_51x51_evidence_45_portrait_of_the_graduate.py:46:# cross-tenant
backend\tests\test_51x51_evidence_45_portrait_of_the_graduate.py:48:# isolation
backend\tests\test_51x51_evidence_44_chaplain___pastoral_care.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_44_chaplain___pastoral_care.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_44_chaplain___pastoral_care.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_44_chaplain___pastoral_care.py:45:# tenant
backend\tests\test_51x51_evidence_44_chaplain___pastoral_care.py:46:# cross-tenant
backend\tests\test_51x51_evidence_44_chaplain___pastoral_care.py:48:# isolation
backend\tests\test_51x51_evidence_43_christian_pd_hub.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_43_christian_pd_hub.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_43_christian_pd_hub.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_43_christian_pd_hub.py:45:# tenant
backend\tests\test_51x51_evidence_43_christian_pd_hub.py:46:# cross-tenant
backend\tests\test_51x51_evidence_43_christian_pd_hub.py:48:# isolation
backend\tests\test_51x51_evidence_42_board_governance_suite.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_42_board_governance_suite.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_42_board_governance_suite.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_42_board_governance_suite.py:45:# tenant
backend\tests\test_51x51_evidence_42_board_governance_suite.py:46:# cross-tenant
backend\tests\test_51x51_evidence_42_board_governance_suite.py:48:# isolation
backend\tests\test_51x51_evidence_41_crown_compass.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_41_crown_compass.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_41_crown_compass.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_41_crown_compass.py:45:# tenant
backend\tests\test_51x51_evidence_41_crown_compass.py:46:# cross-tenant
backend\tests\test_51x51_evidence_41_crown_compass.py:48:# isolation
backend\tests\test_51x51_evidence_40_service___outreach.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_40_service___outreach.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_40_service___outreach.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_40_service___outreach.py:45:# tenant
backend\tests\test_51x51_evidence_40_service___outreach.py:46:# cross-tenant
backend\tests\test_51x51_evidence_40_service___outreach.py:48:# isolation
backend\tests\test_51x51_evidence_38_extended_discipline_workflows.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_38_extended_discipline_workflows.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_38_extended_discipline_workflows.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_38_extended_discipline_workflows.py:45:# tenant
backend\tests\test_51x51_evidence_38_extended_discipline_workflows.py:46:# cross-tenant
backend\tests\test_51x51_evidence_38_extended_discipline_workflows.py:48:# isolation
backend\tests\test_51x51_evidence_36_volunteer___family_engagement.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_36_volunteer___family_engagement.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_36_volunteer___family_engagement.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_36_volunteer___family_engagement.py:45:# tenant
backend\tests\test_51x51_evidence_36_volunteer___family_engagement.py:46:# cross-tenant
backend\tests\test_51x51_evidence_36_volunteer___family_engagement.py:48:# isolation
backend\tests\test_51x51_evidence_35_food_services.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_35_food_services.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_35_food_services.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_35_food_services.py:45:# tenant
backend\tests\test_51x51_evidence_35_food_services.py:46:# cross-tenant
backend\tests\test_51x51_evidence_35_food_services.py:48:# isolation
backend\bell_schedule_wizard\tests\test_views.py:563:    def test_cross_tenant_isolation(self):
backend\payments\tests\test_household_finance_access.py:15:def _mk_user_with_school(school, *, is_staff=False, role_groups=()):
backend\payments\tests\test_household_finance_access.py:26:    for group_name in role_groups:
backend\payments\tests\test_household_finance_access.py:33:def test_household_summary_allows_finance_runtime_role():
backend\payments\tests\test_household_finance_access.py:39:        role_groups=("finance_admin",),
backend\payments\tests\test_household_finance_access.py:62:        role_groups=("parent",),
backend\academics\views.py:8:from rest_framework.decorators import action, api_view, permission_classes
backend\academics\views.py:10:from rest_framework.permissions import IsAuthenticated
backend\academics\views.py:62:def _role_codes(user, school_id) -> set[str]:
backend\academics\views.py:69:        UserRole.objects.filter(user_id=user_id, school_id=school_id).values_list("role_code", flat=True)
backend\academics\views.py:73:def _is_staffish(user, roles: set[str]) -> bool:
backend\academics\views.py:77:        or ("HEAD_OF_SCHOOL" in roles)
backend\academics\views.py:94:    roles = _role_codes(user, school_id)
backend\academics\views.py:102:    if _is_staffish(user, roles):
backend\academics\views.py:105:    if "TEACHER" in roles:
backend\academics\views.py:111:    if "PARENT" in roles:
backend\academics\views.py:120:    if "STUDENT" in roles:
backend\academics\views.py:128:    roles = _role_codes(user, school_id)
backend\academics\views.py:130:    if _is_staffish(user, roles):
backend\academics\views.py:135:    if "TEACHER" in roles:
backend\academics\views.py:147:    if "PARENT" in roles:
backend\academics\views.py:157:    if "STUDENT" in roles:
backend\academics\views.py:164:    permission_classes = [IsAuthenticated]
backend\academics\views.py:188:        roles = _role_codes(user, school_id)
backend\academics\views.py:191:        if _is_staffish(user, roles):
backend\academics\views.py:207:        roles = _role_codes(user, school_id)
backend\academics\views.py:220:        if _is_staffish(user, roles):
backend\academics\views.py:234:        roles = _role_codes(user, school_id)
backend\academics\views.py:251:        if _is_staffish(user, roles):
backend\academics\views.py:283:        roles = _role_codes(user, school_id)
backend\academics\views.py:306:        if "TEACHER" in roles and teacher_id:
backend\academics\views.py:400:@permission_classes([IsAuthenticated])
backend\academics\views.py:411:@permission_classes([IsAuthenticated])
backend\academics\views.py:415:    roles = _role_codes(user, school_id)
backend\academics\views.py:417:    if _is_staffish(user, roles):
backend\academics\views.py:421:    if "PARENT" not in roles:
backend\academics\views.py:422:        raise PermissionDenied("Parent role required for this endpoint.")
backend\academics\views.py:435:@permission_classes([IsAuthenticated])
backend\academics\views.py:464:@permission_classes([IsAuthenticated])
backend\academics\views.py:471:    Tenant-scoped and role-filtered via _sections_for_access.
backend\academics\views.py:622:    Inherits tenant scoping from TenantScopedViewSet.
backend\academics\views.py:650:    permission_classes = [IsAuthenticated]
backend\core\views_nav.py:6:# permission checks.  TenantHeaderRequiredMiddleware must run first ΓÇö it
backend\core\views_nav.py:7:# validates X-School-Id and sets request.school.  This view never needs to
backend\core\views_nav.py:16:from core.permissions import user_has_permission
backend\core\views_nav.py:35:    # Middleware already rejects requests missing X-School-Id with 400.
backend\core\views_nav.py:39:            {"detail": "Missing tenant context (X-School-Id required)."},
backend\core\views_nav.py:46:        if item.permission is None:
backend\core\views_nav.py:49:            allowed = user_has_permission(request.user, item.permission, school=school)
backend\academics\transcript_views.py:11:from rest_framework.permissions import IsAuthenticated
backend\academics\transcript_views.py:342:    permission_classes = [IsAuthenticated]
backend\academics\transcript_views.py:345:        school_id = request.headers.get("X-School-Id")
backend\academics\transcript_views.py:347:            return JsonResponse({"detail": "Missing X-School-Id header."}, status=400)
backend\academics\transcript_views.py:400:    permission_classes = [IsAuthenticated]
backend\academics\transcript_views.py:403:        school_id = request.headers.get("X-School-Id")
backend\academics\transcript_views.py:405:            return JsonResponse({"detail": "Missing X-School-Id header."}, status=400)
backend\core\viewsets.py:6:- X-School-Id header resolution
backend\core\viewsets.py:7:- 400 for missing/invalid tenant
backend\core\viewsets.py:8:- 404 for non-existent school or cross-tenant access
backend\core\viewsets.py:11:from rest_framework.permissions import IsAuthenticated
backend\core\viewsets.py:18:    ModelViewSet that enforces tenant scoping for any model with school_id.
backend\core\viewsets.py:20:    All queries are filtered to the resolved tenant.
backend\core\viewsets.py:21:    Writes stamp school_id from the resolved tenant context.
backend\core\viewsets.py:23:    permission_classes = [IsAuthenticated]
backend\core\viewsets.py:41:    ReadOnlyModelViewSet that enforces tenant scoping.
backend\core\viewsets.py:43:    permission_classes = [IsAuthenticated]
backend\bell_schedule_wizard\migrations\0002_replace_stub_with_models.py:12:        ('core', '0005_crown_permission_engine'),
backend\bell_schedule_wizard\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
backend\curricula\management\commands\seed_curricula_demo.py:125:            help="UUID of the tenant school to seed (e.g., from DEMO school record).",
frontend/dashboards/src\pages\DataMigrationDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="dataMigration" />;
frontend/dashboards/src\pages\DashboardCertificationCenter.jsx:6:  return <CrownDashboardTemplate config={config} roleKey="dashboardCertificationCenter" />;
backend\payments\providers\stripe_connect.py:5:creating and managing connected accounts for school tenants.
backend\payments\providers\stripe_connect.py:39:    Stripe Connect orchestration for Crown2026 school tenants.
backend\payments\providers\stripe_connect.py:41:    Each school tenant gets its own Stripe Connected Account so that
backend\payments\providers\stripe_connect.py:70:        Create a Stripe Express connected account for a school tenant.
backend\billing\tests\test_billing_api.py:24:    role_groups: tuple[str, ...] = (),
backend\billing\tests\test_billing_api.py:36:    for group_name in role_groups:
backend\billing\tests\test_billing_api.py:79:        role_groups=("school_admin",),
backend\billing\tests\test_billing_api.py:122:        role_groups=("school_admin",),
backend\billing\tests\test_billing_api.py:154:        role_groups=("finance_admin",),
backend\billing\tests\test_billing_api.py:219:    user = _mk_user_with_school(school, is_staff=False, role_groups=("admissions_team",))
frontend/dashboards/src\pages\CurriculumPDDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="curriculumPD" />;
backend\core\tests\test_scoping.py:12:- Never proxy role logic through view tests ΓÇö test scoping.py directly.
backend\core\tests\test_scoping.py:55:        self.teacher.role = "TEACHER"  # fallback for resolve_role (no UserRole record)
backend\core\tests\test_scoping.py:61:        self.unassigned_teacher.role = "TEACHER"
backend\core\tests\test_scoping.py:113:        self.parent.role = "PARENT"
backend\core\tests\test_scoping.py:148:        case_parent.role = "PARENT"
backend\core\tests\test_scoping.py:158:        orphan.role = "PARENT"
backend\core\tests\test_scoping.py:176:        self.parent.role = "PARENT"
backend\core\tests\test_scoping.py:211:        ghost.role = "PARENT"
backend\core\tests\test_scoping.py:237:        # Link guardian via DB update so guardian_id is persisted, then role attribute.
backend\core\tests\test_scoping.py:243:        self.parent.role = "PARENT"
backend\core\tests\test_scoping.py:265:        orphan.role = "PARENT"
backend\core\tests\test_scoping.py:325:        teacher.role = "TEACHER"
backend\core\tests\test_scoping.py:342:        director.role = "HEAD_OF_SCHOOL"
backend\academics\tests\test_transcript_ro_api.py:29:def _assign_role(*, user, school: School, role_code: str):
backend\academics\tests\test_transcript_ro_api.py:30:    """Assign a role to the user."""
backend\academics\tests\test_transcript_ro_api.py:31:    UserRole.objects.create(school=school, user=user, role_code=role_code)
backend\academics\tests\test_transcript_ro_api.py:116:    _assign_role(user=user, school=school, role_code="DIRECTOR")
backend\academics\tests\test_transcript_ro_api.py:129:    _assign_role(user=user, school=school, role_code="DIRECTOR")
backend\academics\tests\test_transcript_ro_api.py:172:    _assign_role(user=user, school=school, role_code="DIRECTOR")
backend\academics\tests\test_transcript_ro_api.py:193:    _assign_role(user=user, school=school, role_code="DIRECTOR")
backend\academics\tests\test_transcript_ro_api.py:235:    _assign_role(user=user, school=school, role_code="DIRECTOR")
backend\academics\tests\test_transcript_ro_api.py:270:    _assign_role(user=user, school=school, role_code="DIRECTOR")
backend\core\tests\test_rbac_contract.py:21:def _assign_role(user, school, role_code):
backend\core\tests\test_rbac_contract.py:22:    UserRole.objects.create(user=user, school=school, role_code=role_code)
backend\core\tests\test_rbac_contract.py:46:    # Valid UserRole.role_code values (from core/models.py UserRole.ROLE_CODE_CHOICES):
backend\core\tests\test_rbac_contract.py:48:    # ADMIN does not exist ΓÇö FINANCE_DIRECTOR is the privileged finance-level role.
backend\core\tests\test_rbac_contract.py:56:    for role, user in u.items():
backend\core\tests\test_rbac_contract.py:57:        _assign_role(user, school, role)
backend\core\tests\test_rbac_contract.py:62:    # Unauthed should not be allowed even with tenant header.
backend\core\tests\test_rbac_contract.py:68:def test_requires_tenant_header_for_invariants(users, school):
backend\core\tests\test_rbac_contract.py:69:    # Authed without tenant header should fail fast (tenant enforcement).
backend\core\tests\test_rbac_contract.py:77:    "role,expected",
backend\core\tests\test_rbac_contract.py:86:def test_invariants_role_matrix(users, school, role, expected):
backend\core\tests\test_rbac_contract.py:87:    c = _client_for(users[role], school.id)
backend\core\tests\test_rbac_contract.py:89:    assert r.status_code == expected, (role, r.status_code, r.content)
backend\academics\tests\test_section_roster.py:26:def _assign_role(*, user, school: School, role_code: str):
backend\academics\tests\test_section_roster.py:27:    """Assign a role to the user."""
backend\academics\tests\test_section_roster.py:28:    UserRole.objects.create(school=school, user=user, role_code=role_code)
backend\academics\tests\test_section_roster.py:89:    _assign_role(user=user, school=school, role_code="HEAD_OF_SCHOOL")
backend\academics\tests\test_section_roster.py:124:    _assign_role(user=user, school=school, role_code="HEAD_OF_SCHOOL")
backend\academics\tests\test_section_roster.py:153:    _assign_role(user=user, school=school, role_code="HEAD_OF_SCHOOL")
backend\core\tests\test_permission_engine.py:1:# backend/core/tests/test_permission_engine.py
backend\core\tests\test_permission_engine.py:6:#   - user_has_permission() truth / denial / school scoping / anon
backend\core\tests\test_permission_engine.py:7:#   - require_permission() decorator  ΓåÆ  200 / 403 / 401 paths
backend\core\tests\test_permission_engine.py:9:#   - seed_permissions management command idempotency
backend\core\tests\test_permission_engine.py:18:from core.permissions import require_permission, user_has_permission
backend\core\tests\test_permission_engine.py:41:def _grant(role_code, permission_code):
backend\core\tests\test_permission_engine.py:42:    perm = _perm(permission_code)
backend\core\tests\test_permission_engine.py:43:    obj, _ = RolePermission.objects.get_or_create(role_code=role_code, permission=perm)
backend\core\tests\test_permission_engine.py:47:def _assign_role(user, school, role_code):
backend\core\tests\test_permission_engine.py:48:    return UserRole.objects.create(user=user, school=school, role_code=role_code)
backend\core\tests\test_permission_engine.py:52:# user_has_permission ΓÇö basic grant / deny
backend\core\tests\test_permission_engine.py:57:    def test_returns_true_when_role_granted(self):
backend\core\tests\test_permission_engine.py:60:        _assign_role(user, school, "HEAD_OF_SCHOOL")
backend\core\tests\test_permission_engine.py:63:        assert user_has_permission(user, "finance.view") is True
backend\core\tests\test_permission_engine.py:65:    def test_returns_false_when_role_not_granted(self):
backend\core\tests\test_permission_engine.py:68:        _assign_role(user, school, "TEACHER")
backend\core\tests\test_permission_engine.py:71:        assert user_has_permission(user, "finance.view") is False
backend\core\tests\test_permission_engine.py:73:    def test_returns_false_for_nonexistent_permission(self):
backend\core\tests\test_permission_engine.py:76:        _assign_role(user, school, "HEAD_OF_SCHOOL")
backend\core\tests\test_permission_engine.py:78:        assert user_has_permission(user, "nonexistent.code") is False
backend\core\tests\test_permission_engine.py:80:    def test_returns_false_when_user_has_no_roles(self):
backend\core\tests\test_permission_engine.py:81:        user = _user("noroles")
backend\core\tests\test_permission_engine.py:84:        assert user_has_permission(user, "finance.view") is False
backend\core\tests\test_permission_engine.py:91:        assert user_has_permission(anon, "finance.view") is False
backend\core\tests\test_permission_engine.py:95:# user_has_permission ΓÇö school scoping
backend\core\tests\test_permission_engine.py:103:        _assign_role(user, school, "HEAD_OF_SCHOOL")
backend\core\tests\test_permission_engine.py:106:        assert user_has_permission(user, "finance.view", school=school) is True
backend\core\tests\test_permission_engine.py:112:        _assign_role(user, school_a, "HEAD_OF_SCHOOL")
backend\core\tests\test_permission_engine.py:115:        # User has the role in school_a but we ask against school_b
backend\core\tests\test_permission_engine.py:116:        assert user_has_permission(user, "finance.view", school=school_b) is False
backend\core\tests\test_permission_engine.py:121:        _assign_role(user, school_a, "FINANCE_DIRECTOR")
backend\core\tests\test_permission_engine.py:124:        # No school filter ΓÇö should still find the permission
backend\core\tests\test_permission_engine.py:125:        assert user_has_permission(user, "finance.edit") is True
backend\core\tests\test_permission_engine.py:129:# require_permission decorator
backend\core\tests\test_permission_engine.py:138:        @require_permission(perm_code)
backend\core\tests\test_permission_engine.py:144:    def test_allows_request_when_permission_granted(self):
backend\core\tests\test_permission_engine.py:147:        _assign_role(user, school, "HEAD_OF_SCHOOL")
backend\core\tests\test_permission_engine.py:159:    def test_denies_request_when_permission_missing(self):
backend\core\tests\test_permission_engine.py:162:        _assign_role(user, school, "TEACHER")
backend\core\tests\test_permission_engine.py:194:        _assign_role(user, school, "TEACHER")
backend\core\tests\test_permission_engine.py:208:        should use school=None and check roles across all schools."""
backend\core\tests\test_permission_engine.py:211:        _assign_role(user, school, "HEAD_OF_SCHOOL")
backend\core\tests\test_permission_engine.py:230:    def test_crown_permission_code_is_unique(self):
backend\core\tests\test_permission_engine.py:237:    def test_role_permission_unique_together(self):
backend\core\tests\test_permission_engine.py:241:        RolePermission.objects.create(role_code="TEACHER", permission=perm)
backend\core\tests\test_permission_engine.py:243:            RolePermission.objects.create(role_code="TEACHER", permission=perm)
backend\core\tests\test_permission_engine.py:245:    def test_crown_permission_str(self):
backend\core\tests\test_permission_engine.py:246:        perm = _perm("str.test", "A test permission")
backend\core\tests\test_permission_engine.py:249:    def test_role_permission_str(self):
backend\core\tests\test_permission_engine.py:251:        rp = RolePermission.objects.create(role_code="TEACHER", permission=perm)
backend\core\tests\test_permission_engine.py:256:# seed_permissions management command
backend\core\tests\test_permission_engine.py:261:    def test_seed_creates_permissions(self):
backend\core\tests\test_permission_engine.py:265:        call_command("seed_permissions", stdout=out)
backend\core\tests\test_permission_engine.py:269:    def test_seed_creates_role_mappings(self):
backend\core\tests\test_permission_engine.py:272:        call_command("seed_permissions", stdout=StringIO())
backend\core\tests\test_permission_engine.py:274:            role_code="HEAD_OF_SCHOOL",
backend\core\tests\test_permission_engine.py:275:            permission__code="finance.view",
backend\core\tests\test_permission_engine.py:278:            role_code="FINANCE_DIRECTOR",
backend\core\tests\test_permission_engine.py:279:            permission__code="finance.edit",
backend\core\tests\test_permission_engine.py:285:        call_command("seed_permissions", stdout=StringIO())
backend\core\tests\test_permission_engine.py:287:        call_command("seed_permissions", stdout=StringIO())
backend\core\tests\test_permission_engine.py:294:        call_command("seed_permissions", dry_run=True, stdout=StringIO())
backend\academics\tests\test_sections_teacher_guard.py:19:    If user has TEACHER role, they may not pass another teacher_id.
backend\academics\tests\test_sections_teacher_guard.py:30:        role_type="TEACHER",
backend\academics\tests\test_sections_teacher_guard.py:43:        role_code="TEACHER",
backend\academics\tests\test_sections_teacher_guard.py:52:        role_type="TEACHER",
backend\core\tests\test_nav_endpoint.py:3:# Tests for GET /api/v1/nav/ (permission-derived navigation).
backend\core\tests\test_nav_endpoint.py:6:# TenantHeaderRequiredMiddleware enforces X-School-Id for /api/v1/* routes and
backend\core\tests\test_nav_endpoint.py:7:# sets request.school; the nav view filters NAV_ITEMS by user permissions.
backend\core\tests\test_nav_endpoint.py:21:def _enable_tenant_middleware(settings):
backend\core\tests\test_nav_endpoint.py:44:def _assign_role(user, school, role_code):
backend\core\tests\test_nav_endpoint.py:45:    return UserRole.objects.create(user=user, school=school, role_code=role_code)
backend\core\tests\test_nav_endpoint.py:48:def _grant(role_code, perm_code):
backend\core\tests\test_nav_endpoint.py:50:    RolePermission.objects.get_or_create(role_code=role_code, permission=perm)
backend\core\tests\test_nav_endpoint.py:70:        """Middleware must reject /api/v1/nav/ with no X-School-Id."""
backend\core\tests\test_nav_endpoint.py:76:        """Middleware must reject an X-School-Id that doesn't resolve to a School."""
backend\core\tests\test_nav_endpoint.py:91:        _assign_role(parent, school, "parent")
backend\core\tests\test_nav_endpoint.py:116:    def test_finance_role_sees_finance_and_billing_not_admissions(self):
backend\core\tests\test_nav_endpoint.py:119:        _assign_role(fin, school, "finance")
backend\core\tests\test_nav_endpoint.py:139:        _assign_role(hos, school, "HEAD_OF_SCHOOL")
backend\core\tests\test_nav_endpoint.py:156:    def test_user_with_no_roles_sees_empty_nav(self):
backend\core\tests\test_nav_endpoint.py:158:        user = _user("noroles1")
backend\core\tests\test_nav_endpoint.py:159:        # No roles assigned, no permissions granted
backend\core\tests\test_nav_endpoint.py:172:        _assign_role(teacher, school, "TEACHER")
backend\core\tests\test_nav_endpoint.py:199:        _assign_role(user, school, "parent")
backend\core\tests\test_nav_endpoint.py:213:        _assign_role(user, school, "parent")
backend\core\tests\test_nav_endpoint.py:229:        _assign_role(user, school, "parent")
backend\core\tests\test_nav_endpoint.py:242:    def test_school_scoping_cross_tenant_isolation(self):
backend\core\tests\test_nav_endpoint.py:243:        """User's role in school A must not grant nav in school B."""
backend\core\tests\test_nav_endpoint.py:247:        _assign_role(user, school_a, "finance")
backend\core\tests\test_nav_endpoint.py:252:        # Request against school_b ΓÇö user has no role there
backend\academics\tests\test_lesson_plans.py:6:- Write access: only ADMIN/DIRECTOR roles can create/update
backend\academics\tests\test_lesson_plans.py:12:- Cross-school isolation: cannot read another school's plans
backend\academics\tests\test_lesson_plans.py:53:def _assign_role(*, user: User, school: School, role_code: str) -> None:
backend\academics\tests\test_lesson_plans.py:54:    UserRole.objects.create(school=school, user=user, role_code=role_code)
backend\academics\tests\test_lesson_plans.py:112:    """Verify that the endpoint is scoped to X-School-Id."""
backend\academics\tests\test_lesson_plans.py:115:        """An unparseable UUID in X-School-Id must be rejected with 400."""
backend\academics\tests\test_lesson_plans.py:118:        _assign_role(user=user, school=school, role_code="ADMIN")
backend\academics\tests\test_lesson_plans.py:131:        _assign_role(user=user, school=school, role_code="ADMIN")
backend\academics\tests\test_lesson_plans.py:144:        _assign_role(user=user_a, school=school_a, role_code="ADMIN")
backend\academics\tests\test_lesson_plans.py:164:        _assign_role(user=user, school=school, role_code="ADMIN")
backend\academics\tests\test_lesson_plans.py:186:        _assign_role(user=user, school=school, role_code="ADMIN")
backend\academics\tests\test_lesson_plans.py:208:        _assign_role(user=user, school=school, role_code="ADMIN")
backend\academics\tests\test_lesson_plans.py:222:        _assign_role(user=user, school=school, role_code="ADMIN")
backend\academics\tests\test_lesson_plans.py:237:        _assign_role(user=user, school=school, role_code="ADMIN")
backend\academics\tests\test_lesson_plans.py:308:        _assign_role(user=user, school=school, role_code="ADMIN")
backend\academics\tests\test_lesson_plans.py:320:        _assign_role(user=user, school=school, role_code="ADMIN")
backend\academics\tests\test_lesson_plans.py:333:        _assign_role(user=user, school=school, role_code="ADMIN")
backend\academics\tests\test_lesson_plans.py:351:    """Public serializer omits teacher_notes_private for non-role users."""
backend\academics\tests\test_lesson_plans.py:356:        _assign_role(user=admin, school=school, role_code="ADMIN")
backend\academics\tests\test_lesson_plans.py:370:        """Non-role user gets the public serializer (no teacher_notes_private field)."""
backend\academics\tests\test_lesson_plans.py:373:        _assign_role(user=admin, school=school, role_code="ADMIN")
backend\academics\tests\test_lesson_plans.py:382:        # Regular user with no role
backend\academics\tests\test_lesson_plans.py:409:        _assign_role(user=user, school=school, role_code="ADMIN")
backend\academics\tests\test_lesson_plans.py:421:        _assign_role(user=user, school=school, role_code="ADMIN")
backend\academics\tests\test_lesson_plans.py:437:        _assign_role(user=user_a, school=school_a, role_code="ADMIN")
backend\academics\tests\test_lesson_plans.py:438:        _assign_role(user=user_b, school=school_b, role_code="ADMIN")
backend\academics\tests\test_lesson_plans.py:459:        _assign_role(user=user, school=school, role_code="ADMIN")
backend\academics\tests\test_lesson_plans.py:553:        _assign_role(user=user_a, school=school_a, role_code="ADMIN")
backend\academics\tests\test_lesson_plans.py:554:        _assign_role(user=user_b, school=school_b, role_code="ADMIN")
frontend/dashboards/src\pages\CrownLaunchModulePage.jsx:10:  return <CrownDashboardTemplate config={config} roleKey="schoolAdministrator" />;
frontend/dashboards/src\pages\CrownLaunchDashboardPage.jsx:10:  return <CrownDashboardTemplate config={config} roleKey="schoolAdministrator" />;
backend\academics\tests\test_assignments_weights.py:39:def _assign_role(*, user, school: School, role_code: str):
backend\academics\tests\test_assignments_weights.py:40:    """Assign a role to the user."""
backend\academics\tests\test_assignments_weights.py:41:    UserRole.objects.create(school=school, user=user, role_code=role_code)
backend\academics\tests\test_assignments_weights.py:311:    _assign_role(user=user, school=school, role_code="DIRECTOR")
backend\academics\tests\test_assignments_weights.py:325:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:338:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:352:    _assign_role(user=user, school=school, role_code="DIRECTOR")
backend\academics\tests\test_assignments_weights.py:374:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:391:    _assign_role(user=user, school=school, role_code="DIRECTOR")
backend\academics\tests\test_assignments_weights.py:405:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:415:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:430:    _assign_role(user=user, school=school, role_code="DIRECTOR")
backend\academics\tests\test_assignments_weights.py:452:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:461:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:470:    User without ADMIN or DIRECTOR role cannot POST category.
backend\academics\tests\test_assignments_weights.py:476:    _assign_role(user=user, school=school, role_code="TEACHER")
backend\academics\tests\test_assignments_weights.py:489:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:496:    User without ADMIN or DIRECTOR role cannot POST assignment.
backend\academics\tests\test_assignments_weights.py:502:    _assign_role(user=user, school=school, role_code="TEACHER")
backend\academics\tests\test_assignments_weights.py:523:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:536:    _assign_role(user=user, school=school, role_code="DIRECTOR")
backend\academics\tests\test_assignments_weights.py:554:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:562:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:576:    _assign_role(user=user, school=school, role_code="DIRECTOR")
backend\academics\tests\test_assignments_weights.py:602:        headers={"X-School-Id": str(school.id)},
backend\academics\tests\test_assignments_weights.py:610:        headers={"X-School-Id": str(school.id)},
frontend/dashboards/src\pages\CounselingDashboard.jsx:6:  return <CrownDashboardTemplate config={config} roleKey="counseling" />;
backend\academics\tests\test_academics_readonly_api.py:27:def _assign_role(*, user, school: School, role_code: str):
backend\academics\tests\test_academics_readonly_api.py:28:    UserRole.objects.create(school=school, user=user, role_code=role_code)
backend\academics\tests\test_academics_readonly_api.py:153:        role_type="TEACHER",
backend\academics\tests\test_academics_readonly_api.py:161:        role_type="TEACHER",
backend\academics\tests\test_academics_readonly_api.py:171:    _assign_role(user=user, school=school, role_code="TEACHER")
backend\academics\tests\test_academics_readonly_api.py:187:    _assign_role(user=user, school=school, role_code="PARENT")
backend\tests\test_51x51_evidence_33_nurse_office___health_office.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_33_nurse_office___health_office.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_33_nurse_office___health_office.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_33_nurse_office___health_office.py:45:# tenant
backend\tests\test_51x51_evidence_33_nurse_office___health_office.py:46:# cross-tenant
backend\tests\test_51x51_evidence_33_nurse_office___health_office.py:48:# isolation
backend\tests\test_51x51_evidence_32_activities___athletics___events.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_32_activities___athletics___events.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_32_activities___athletics___events.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_32_activities___athletics___events.py:45:# tenant
backend\tests\test_51x51_evidence_32_activities___athletics___events.py:46:# cross-tenant
backend\tests\test_51x51_evidence_32_activities___athletics___events.py:48:# isolation
frontend/dashboards/src\pages\ComplianceAuditDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="complianceAudit" />;
backend\core\tenant_models.py:26:def _log_tenant_violation(*, violation_type, tenant_school_id=None, model=None, operation=None, extra=None):
backend\core\tenant_models.py:30:        "tenant_school_id": str(tenant_school_id) if tenant_school_id else None,
backend\core\tenant_models.py:39:def require_tenant_context():
backend\core\tenant_models.py:40:    """Require tenant context to be set - raises if missing."""
backend\core\tenant_models.py:43:        _log_tenant_violation(violation_type='context_required', tenant_school_id=None, model=None, operation='require_tenant_context')
backend\core\tenant_models.py:49:def tenant_context(school):
backend\core\tenant_models.py:50:    """Context manager for explicit tenant scoping (supports nesting)."""
backend\core\tenant_models.py:78:        """Guard bulk update - require tenant context (fail-closed)."""
backend\core\tenant_models.py:81:            _log_tenant_violation(violation_type='bulk_update', tenant_school_id=None, model=getattr(self.model,'__name__',None), operation='update')
backend\core\tenant_models.py:83:        # Ensure we are tenant-scoped before bulk update
backend\core\tenant_models.py:90:        """Guard bulk delete - require tenant context (fail-closed)."""
backend\core\tenant_models.py:93:            _log_tenant_violation(violation_type='bulk_delete', tenant_school_id=None, model=getattr(self.model,'__name__',None), operation='delete')
backend\core\tenant_models.py:95:        # Ensure we are tenant-scoped before bulk delete
backend\core\tenant_models.py:103:    """Raised when attempting cross-tenant write operation."""
backend\core\tenant_models.py:108:    """Raised when attempting bulk operation without tenant context."""
backend\core\tenant_models.py:113:    """Raised when tenant context is required but missing."""
backend\core\tenant_models.py:118:    """Manager that auto-scopes queries to current tenant (fail-closed)."""
backend\core\tenant_models.py:138:        """Enforce tenant write protection."""
backend\core\tenant_models.py:140:        # If there is tenant context, enforce writes stay in-tenant
backend\core\tenant_models.py:144:                    # Safe convenience: bind new objects to current tenant
backend\core\tenant_models.py:147:                    _log_tenant_violation(violation_type='write', tenant_school_id=getattr(current,'id',None), model=self.__class__.__name__, operation='save', extra={'target_school_id': str(self.school_id)})
backend\payments\ops_api.py:4:from rest_framework.decorators import api_view, permission_classes
backend\payments\ops_api.py:5:from rest_framework.permissions import IsAuthenticated
backend\payments\ops_api.py:8:from crown_api.billing_api.permissions import has_finance_runtime_role
backend\payments\ops_api.py:14:    return has_finance_runtime_role(user)
backend\payments\ops_api.py:18:@permission_classes([IsAuthenticated])
backend\payments\ops_api.py:47:@permission_classes([IsAuthenticated])
backend\payments\ops_api.py:78:@permission_classes([IsAuthenticated])
backend\tests\test_51x51_evidence_29_teacher_portal.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_29_teacher_portal.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_29_teacher_portal.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_29_teacher_portal.py:45:# tenant
backend\tests\test_51x51_evidence_29_teacher_portal.py:46:# cross-tenant
backend\tests\test_51x51_evidence_29_teacher_portal.py:48:# isolation
frontend/dashboards/src\pages\CommunicationsDirectorDashboard.jsx:52:  if (schoolId) headers['X-School-Id']   = schoolId;
backend\core\tenant_header_middleware.py:1:# backend/core/tenant_header_middleware.py
backend\core\tenant_header_middleware.py:8:from core.tenant_models import set_current_school, clear_current_school
backend\core\tenant_header_middleware.py:9:from crown_api.tenant import resolve_tenant_school_id
backend\core\tenant_header_middleware.py:14:    Enforces tenant resolution for /api/* calls.
backend\core\tenant_header_middleware.py:17:    1. X-School-Id header  used when present (primary)
backend\core\tenant_header_middleware.py:19:    3. Missing tenant  400
backend\core\tenant_header_middleware.py:29:    for downstream view usage, and sets the thread-local tenant context so audit
backend\core\tenant_header_middleware.py:50:        "/api/dev/token",   # dev token endpoint returns school_id  no tenant context needed
backend\core\tenant_header_middleware.py:55:        "/api/director/force_seed_user",  # dev-only admin utility; predates tenant scoping
backend\core\tenant_header_middleware.py:86:                    # provide X-School-Id on exempt routes.
backend\core\tenant_header_middleware.py:87:                    resolved = resolve_tenant_school_id(request)
backend\core\tenant_header_middleware.py:91:                                "detail": "Invalid X-School-Id (must be UUID).",
backend\core\tenant_header_middleware.py:92:                                "code": "invalid_tenant_header",
backend\core\tenant_header_middleware.py:98:            # Resolve tenant: header wins over user.school_id fallback.
backend\core\tenant_header_middleware.py:99:            # resolve_tenant_school_id() handles both paths since we now run
backend\core\tenant_header_middleware.py:101:            resolved = resolve_tenant_school_id(request)
backend\core\tenant_header_middleware.py:107:                        "detail": "Invalid X-School-Id (must be UUID).",
backend\core\tenant_header_middleware.py:108:                        "code": "invalid_tenant_header",
backend\core\tenant_header_middleware.py:116:                        "detail": "Missing required header: X-School-Id.",
backend\core\tenant_header_middleware.py:117:                        "code": "missing_tenant",
backend\core\tenant_header_middleware.py:127:                        "detail": "Unknown X-School-Id.",
backend\core\tenant_header_middleware.py:128:                        "code": "invalid_tenant",
backend\core\tenant_header_middleware.py:141:            # Always clear thread-local tenant context, even on exceptions
frontend/dashboards/src\pages\CommunicationsDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="communications" />;
frontend/dashboards/src\pages\ChaplainSpiritualLifeDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="chaplainSpiritualLife" />;
backend\tests\test_51x51_evidence_28_parent_portal.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_28_parent_portal.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_28_parent_portal.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_28_parent_portal.py:45:# tenant
backend\tests\test_51x51_evidence_28_parent_portal.py:46:# cross-tenant
backend\tests\test_51x51_evidence_28_parent_portal.py:48:# isolation
backend\tests\test_51x51_evidence_27_communications.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_27_communications.py:13:MODULE_TEXT = 'Communications\nManages announcements, messages, alerts, templates, and role-targeted communication.\nAnnouncements | Messaging | Templates | Targeting | Delivery\nCreate message | Target audience | Deliver notification | Track read status | Respect permissions\ndelivery success | unread count | message response time | failed sends | announcement reach\nnotifications | RBAC | households | staff | portals\nDev 3\nFirst-Wave Module'
backend\tests\test_51x51_evidence_27_communications.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_27_communications.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_27_communications.py:36:# Manages announcements, messages, alerts, templates, and role-targeted communication.
backend\tests\test_51x51_evidence_27_communications.py:38:# Create message | Target audience | Deliver notification | Track read status | Respect permissions
backend\tests\test_51x51_evidence_27_communications.py:45:# tenant
backend\tests\test_51x51_evidence_27_communications.py:46:# cross-tenant
backend\tests\test_51x51_evidence_27_communications.py:48:# isolation
frontend/dashboards/src\pages\BoardDashboard.jsx:6:  return <CrownDashboardTemplate config={config} roleKey="board" />;
backend\tests\test_51x51_evidence_23_emergency___medical_essentials.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_23_emergency___medical_essentials.py:13:MODULE_TEXT = 'Emergency / Medical Essentials\nStores emergency contacts, key medical flags, allergies, and operational health essentials.\nEmergency contact | Medical flag | Allergy | Medication note | Emergency access\nStore emergency info | Restrict medical data | Expose to authorized roles | Update contacts | Audit access\nmissing emergency contacts | medical alert accuracy | unauthorized health access | contact update rate | emergency data completeness\nstudents | households | nurse | RBAC | audit\nDev 2\nSIS Core'
backend\tests\test_51x51_evidence_23_emergency___medical_essentials.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_23_emergency___medical_essentials.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_23_emergency___medical_essentials.py:38:# Store emergency info | Restrict medical data | Expose to authorized roles | Update contacts | Audit access
backend\tests\test_51x51_evidence_23_emergency___medical_essentials.py:45:# tenant
backend\tests\test_51x51_evidence_23_emergency___medical_essentials.py:46:# cross-tenant
backend\tests\test_51x51_evidence_23_emergency___medical_essentials.py:48:# isolation
backend\tests\test_51x51_evidence_22_student_care___discipline_summary.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_22_student_care___discipline_summary.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_22_student_care___discipline_summary.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_22_student_care___discipline_summary.py:45:# tenant
backend\tests\test_51x51_evidence_22_student_care___discipline_summary.py:46:# cross-tenant
backend\tests\test_51x51_evidence_22_student_care___discipline_summary.py:48:# isolation
backend\core\services\export_service.py:33:    Build a ZIP containing one CSV per exportable model, tenant-scoped to school_id.
backend\tests\test_51x51_evidence_20_grades___report_cards.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_20_grades___report_cards.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_20_grades___report_cards.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_20_grades___report_cards.py:45:# tenant
backend\tests\test_51x51_evidence_20_grades___report_cards.py:46:# cross-tenant
backend\tests\test_51x51_evidence_20_grades___report_cards.py:48:# isolation
backend\crown_api\write_probe_adapter.py:19:    "tenant",
backend\crown_api\write_probe_adapter.py:20:    "tenant_id",
backend\crown_api\write_probe_adapter.py:21:    "tenantid",
backend\crown_api\write_contract_probe.py:7:from crown_api.tenant_seed_adapter import (
backend\crown_api\write_contract_probe.py:70:                "schoolHeaderName": str(entry.get("schoolHeaderName") or "X-School-Id").strip(),
backend\crown_api\write_contract_probe.py:172:    school_header_name = str(entry.get("schoolHeaderName") or "X-School-Id").strip()
backend\tests\test_51x51_evidence_17_grade_levels.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_17_grade_levels.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_17_grade_levels.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_17_grade_levels.py:45:# tenant
backend\tests\test_51x51_evidence_17_grade_levels.py:46:# cross-tenant
backend\tests\test_51x51_evidence_17_grade_levels.py:48:# isolation
backend\crown_api\wizard_common.py:4:Uses the canonical tenant resolver from households.scoping.
frontend/dashboards/src\pages\BillingDashboard.jsx:28:  return <CrownDashboardTemplate config={config} roleKey="billing" />;
backend\crown_api\views_students.py:2:from rest_framework.decorators import api_view, permission_classes
backend\crown_api\views_students.py:3:from rest_framework.permissions import IsAuthenticated
backend\crown_api\views_students.py:17:@permission_classes([IsAuthenticated])
backend\crown_api\views_students.py:38:@permission_classes([IsAuthenticated])
backend\crown_api\views_scheduling.py:3:from rest_framework.decorators import api_view, permission_classes
backend\crown_api\views_scheduling.py:4:from rest_framework.permissions import IsAuthenticated
backend\crown_api\views_scheduling.py:26:@permission_classes([IsAuthenticated])
backend\crown_api\views_scheduling.py:42:@permission_classes([IsAuthenticated])
backend\crown_api\views_scheduling.py:104:@permission_classes([IsAuthenticated])
backend\payments\methods_api.py:2:from rest_framework.decorators import api_view, permission_classes
backend\payments\methods_api.py:3:from rest_framework.permissions import IsAuthenticated
backend\payments\methods_api.py:17:@permission_classes([IsAuthenticated])
backend\payments\methods_api.py:47:@permission_classes([IsAuthenticated])
backend\payments\methods_api.py:80:@permission_classes([IsAuthenticated])
backend\payments\methods_api.py:109:@permission_classes([IsAuthenticated])
backend\core\scoping.py:7:- No role-string checks in views. Views call this module.
backend\core\scoping.py:32:    UserRole.role_code values (stored in DB):
backend\core\scoping.py:42:# This is the ONLY place where role-based row scoping and field scoping
backend\core\scoping.py:46:#   - qs.filter(<role-based condition>)
backend\core\scoping.py:47:#   - if request.user.role == "...": qs = qs.filter(...)
backend\core\scoping.py:49:#   - Any field hiding tied to role logic outside FIELD_SCOPE below
backend\core\scoping.py:102:# Maps UserRole.role_code ΓåÆ canonical scoping key used in FIELD_SCOPE / _scope_* functions.
backend\core\scoping.py:115:# Priority for multi-role resolution (first match wins, most privileged first).
backend\core\scoping.py:129:def resolve_role(user, school_id=None) -> str:
backend\core\scoping.py:131:    Resolve the active Crown scope-role for a user.
backend\core\scoping.py:135:    school_id: if provided, restricts role lookup to that school.
backend\core\scoping.py:137:    roles_qs = getattr(user, "roles", None)
backend\core\scoping.py:138:    if roles_qs is not None:
backend\core\scoping.py:140:            qs = roles_qs.all()
backend\core\scoping.py:143:            active_codes: Set[str] = set(qs.values_list("role_code", flat=True))
backend\core\scoping.py:148:            logger.debug("role code lookup failed", exc_info=True)
backend\core\scoping.py:150:    # Fallback: direct .role attribute (dev/test convenience)
backend\core\scoping.py:151:    direct = getattr(user, "role", None)
backend\core\scoping.py:174:    The view MUST already restrict to tenant (e.g., filter school_id=school_id)
backend\core\scoping.py:175:    before calling this. This function further limits within-tenant visibility
backend\core\scoping.py:176:    by the caller's Crown role.
backend\core\scoping.py:182:    school_id: optional ΓÇö if provided used to tighten role resolution to
backend\core\scoping.py:183:               a single school when the user holds roles at multiple schools.
backend\core\scoping.py:188:    role = resolve_role(user, school_id=school_id)
backend\core\scoping.py:201:    return fn(user, qs, role)
backend\core\scoping.py:208:def _scope_students(user, qs: QuerySet, role: str) -> QuerySet:
backend\core\scoping.py:219:    if role in {"head", "director", "registrar", "admin"}:
backend\core\scoping.py:222:    if role == "teacher":
backend\core\scoping.py:227:    if role == "parent":
backend\core\scoping.py:234:    if role == "student":
backend\core\scoping.py:238:    if role == "counselor":
backend\core\scoping.py:242:    if role == "board":
backend\core\scoping.py:248:def _scope_financial(user, qs: QuerySet, role: str) -> QuerySet:
backend\core\scoping.py:255:    if role in {"head", "director", "finance"}:
backend\core\scoping.py:258:    if role == "parent":
backend\core\scoping.py:271:def _scope_financial_aid(user, qs: QuerySet, role: str) -> QuerySet:
backend\core\scoping.py:278:    if role in {"head", "director", "finance", "aid_officer"}:
backend\core\scoping.py:281:    if role == "parent":
backend\core\scoping.py:295:def _scope_discipline(user, qs: QuerySet, role: str) -> QuerySet:
backend\core\scoping.py:310:    if role in {"head", "director"}:
backend\core\scoping.py:313:    if role == "counselor":
backend\core\scoping.py:318:    if role == "teacher":
backend\core\scoping.py:324:    if role in {"parent", "student"}:
backend\core\scoping.py:330:def _scope_formation(user, qs: QuerySet, role: str) -> QuerySet:
backend\core\scoping.py:334:    No formation model defined yet. All non-privileged roles return empty until
backend\core\scoping.py:337:    if role in {"head", "director", "spiritual_life"}:
backend\core\scoping.py:344:def _scope_referrals(user, qs: QuerySet, role: str) -> QuerySet:
backend\core\scoping.py:348:    No referral model defined yet. All non-privileged roles return empty until
backend\core\scoping.py:351:    if role in {"head", "director", "admissions"}:
backend\core\scoping.py:354:    if role == "parent":
backend\core\scoping.py:358:    if role == "finance":
backend\core\scoping.py:477:    role = resolve_role(user, school_id=school_id)
backend\core\scoping.py:480:        domain_map.get(role)
backend\crown_api\views_households.py:3:from rest_framework.decorators import api_view, permission_classes
backend\crown_api\views_households.py:4:from rest_framework.permissions import IsAuthenticated
backend\crown_api\views_households.py:12:@permission_classes([IsAuthenticated])
backend\crown_api\views_households.py:32:@permission_classes([IsAuthenticated])
backend\crown_api\views_comms.py:3:from rest_framework.decorators import api_view, permission_classes
backend\crown_api\views_comms.py:4:from rest_framework.permissions import IsAuthenticated
backend\crown_api\views_comms.py:21:@permission_classes([IsAuthenticated])
backend\crown_api\views_comms.py:42:@permission_classes([IsAuthenticated])
backend\crown_api\views_billing.py:5:from rest_framework.decorators import api_view, permission_classes
backend\crown_api\views_billing.py:6:from rest_framework.permissions import IsAuthenticated
backend\crown_api\views_billing.py:15:@permission_classes([IsAuthenticated])
backend\crown_api\views_academics.py:5:from rest_framework.decorators import api_view, permission_classes
backend\crown_api\views_academics.py:6:from rest_framework.permissions import IsAuthenticated
backend\crown_api\views_academics.py:31:        HouseholdMember.objects.filter(person=person, role__in=GUARDIAN_ROLES).values_list(
backend\crown_api\views_academics.py:43:@permission_classes([IsAuthenticated])
backend\crown_api\views_academics.py:59:from rest_framework.permissions import IsAuthenticated
backend\crown_api\views_academics.py:63:@permission_classes([IsAuthenticated])
backend\crown_api\views_academics.py:85:    roles = set(
backend\crown_api\views_academics.py:87:        .values_list("role_code", flat=True)
backend\crown_api\views_academics.py:90:    if not roles.intersection(allowed):
backend\crown_api\views_academics.py:91:        return Response({"detail": "Forbidden: requires TEACHER, ADMIN, or HEAD_OF_SCHOOL role."}, status=403)
backend\crown_api\views_academics.py:152:@permission_classes([IsAuthenticated])
backend\crown_api\views.py:13:    - /director/  Auto-detect persona from user's role
backend\crown_api\views.py:97:    # Common names: user.profile.persona, user.persona, user.role, etc.
backend\crown_api\views.py:98:    for attr_path in ("persona", "role", "profile.persona", "profile.role"):
backend\crown_api\version_view.py:5:from rest_framework.decorators import api_view, permission_classes
backend\crown_api\version_view.py:6:from rest_framework.permissions import IsAuthenticated
backend\crown_api\version_view.py:29:@permission_classes([IsAuthenticated])
backend\crown_api\urls.py:21:from crown_api.rbac_views import finance_guardrail_proof
backend\crown_api\urls.py:59:        "api/system/rbac/finance-proof/",
backend\crown_api\urls.py:88:    # Platform Operations (super-admin, cross-tenant, no X-School-ID required)
backend\core\permissions.py:1:# backend/core/permissions.py
backend\core\permissions.py:6:# CrownPermission / RolePermission models keyed on role_code strings that
backend\core\permissions.py:7:# match core.models.UserRole.role_code.
backend\core\permissions.py:10:#   from core.permissions import require_permission, user_has_permission
backend\core\permissions.py:12:#   @require_permission("finance.view")
backend\core\permissions.py:16:#   if user_has_permission(request.user, "health.view", school=request.school):
backend\core\permissions.py:22:from rest_framework.permissions import BasePermission
backend\core\permissions.py:25:def user_has_permission(user, permission_code, school=None):
backend\core\permissions.py:27:    Return True if `user` holds a role (optionally scoped to `school`) that
backend\core\permissions.py:28:    grants `permission_code`.
backend\core\permissions.py:31:    `school` is an optional School instance used to scope the role lookup to a
backend\core\permissions.py:32:    single tenant; when None, roles across all schools are checked.
backend\core\permissions.py:37:    # user.roles is the reverse FK from UserRole (role_code CharField ΓåÆ UserAccount).
backend\core\permissions.py:38:    qs = user.roles.all()
backend\core\permissions.py:42:    role_codes = qs.values_list("role_code", flat=True)
backend\core\permissions.py:43:    if not role_codes:
backend\core\permissions.py:50:        role_code__in=role_codes,
backend\core\permissions.py:51:        permission__code=permission_code,
backend\core\permissions.py:55:def require_permission(permission_code):
backend\core\permissions.py:57:    View decorator that enforces a Crown permission gate.
backend\core\permissions.py:68:            if not user_has_permission(request.user, permission_code, school=school):
backend\core\permissions.py:76:# DRF-compatible permission class for expansion module ViewSets.
backend\core\permissions.py:84:        from core.permissions import CrownModulePermission
backend\core\permissions.py:86:            permission_classes = [CrownModulePermission("hr.view")]
backend\core\permissions.py:89:        permission_classes = [CrownModulePermission("hr.view", write_code="hr.edit")]
backend\core\permissions.py:90:    - Authenticated + school context required (middleware enforces X-School-Id).
backend\core\permissions.py:100:            def has_permission(self, request, view):
backend\core\permissions.py:107:                return user_has_permission(request.user, code, school=school)
backend\core\permissions.py:115:    DRF permission that checks the user's role field.
backend\core\permissions.py:118:        permission_classes = [RoleRequired]
backend\core\permissions.py:119:        required_roles = {"ADMIN", "STAFF"}
backend\core\permissions.py:121:    If required_roles is empty or not set, all authenticated users pass.
backend\core\permissions.py:124:    def has_permission(self, request, view):
backend\core\permissions.py:127:        roles = getattr(view, "required_roles", None) or set()
backend\core\permissions.py:128:        if not roles:
backend\core\permissions.py:130:        user_role = getattr(request.user, "role", None)
backend\core\permissions.py:131:        return user_role in roles
backend\tests\test_51x51_evidence_15_staff___faculty.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_15_staff___faculty.py:13:MODULE_TEXT = 'Staff / Faculty\nStores teachers, administrators, staff, and employment/role context.\nStaff record | Teacher profile | Role link | Assignment | Directory\nCreate staff | Assign role | Assign section | Support portal | Restrict access\nstaff completeness | role assignment errors | teacher-section coverage | staff login success | directory accuracy\nRBAC | teacher portal | sections | communications | scheduling\nDev 2\nSIS Core'
backend\tests\test_51x51_evidence_15_staff___faculty.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_15_staff___faculty.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_15_staff___faculty.py:36:# Stores teachers, administrators, staff, and employment/role context.
backend\tests\test_51x51_evidence_15_staff___faculty.py:38:# Create staff | Assign role | Assign section | Support portal | Restrict access
backend\tests\test_51x51_evidence_15_staff___faculty.py:39:# staff completeness | role assignment errors | teacher-section coverage | staff login success | directory accuracy
backend\tests\test_51x51_evidence_15_staff___faculty.py:45:# tenant
backend\tests\test_51x51_evidence_15_staff___faculty.py:46:# cross-tenant
backend\tests\test_51x51_evidence_15_staff___faculty.py:48:# isolation
frontend/dashboards/src\pages\AttendanceDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="attendance" />;
backend\academics\migrations\0039_term_uniq_term_year_code.py:10:        ('core', '0005_crown_permission_engine'),
backend\core\observability\middleware.py:10:    """Adds request correlation and tenant-aware structured request logging."""
backend\core\observability\middleware.py:27:        tenant = getattr(request, "tenant", None)
backend\core\observability\middleware.py:39:                    "tenant_id": str(getattr(tenant, "id", "")) if tenant else None,
backend\payments\export_api.py:8:from rest_framework.decorators import api_view, permission_classes
backend\payments\export_api.py:9:from rest_framework.permissions import IsAuthenticated
backend\payments\export_api.py:20:@permission_classes([IsAuthenticated])
backend\payments\export_api.py:67:@permission_classes([IsAuthenticated])
backend\tests\test_51x51_evidence_13_student_master_record.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_13_student_master_record.py:13:MODULE_TEXT = 'Student Master Record\nStores official student identity, demographics, status, and record truth.\nCreate student | Edit student | Status | Profile | Search\nPersist official record | Prevent duplicates | Scope to school | Expose APIs | Link modules\nduplicate students | record completeness | student API pass rate | student search success | cross-tenant leakage\nhouseholds | enrollment | attendance | grades | billing\nDev 2\nSIS Core'
backend\tests\test_51x51_evidence_13_student_master_record.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_13_student_master_record.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_13_student_master_record.py:39:# duplicate students | record completeness | student API pass rate | student search success | cross-tenant leakage
backend\tests\test_51x51_evidence_13_student_master_record.py:45:# tenant
backend\tests\test_51x51_evidence_13_student_master_record.py:46:# cross-tenant
backend\tests\test_51x51_evidence_13_student_master_record.py:48:# isolation
frontend/dashboards/src\pages\AthleticsDirectorDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="athleticsDirector" />;
backend\tests\test_51x51_evidence_12_school_year___term.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_12_school_year___term.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_12_school_year___term.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_12_school_year___term.py:45:# tenant
backend\tests\test_51x51_evidence_12_school_year___term.py:46:# cross-tenant
backend\tests\test_51x51_evidence_12_school_year___term.py:48:# isolation
frontend/dashboards/src\pages\AthleticsDashboard.jsx:6:  return <CrownDashboardTemplate config={config} roleKey="athletics" />;
backend\tests\test_51x51_evidence_11_school_profile.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_11_school_profile.py:13:MODULE_TEXT = 'School Profile\nStores official school identity, tenant root, settings, logo, and configuration.\nSchool record | Settings | Branding | Contact data | Tenant setup\nCreate school | Configure school | Attach users | Control settings | Expose identity\nschool setup completion | missing settings | tenant config errors | school profile completeness | logo/config coverage\ntenant | auth | settings | frontend shell | documents\nDev 2\nSIS Core'
backend\tests\test_51x51_evidence_11_school_profile.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_11_school_profile.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_11_school_profile.py:36:# Stores official school identity, tenant root, settings, logo, and configuration.
backend\tests\test_51x51_evidence_11_school_profile.py:39:# school setup completion | missing settings | tenant config errors | school profile completeness | logo/config coverage
backend\tests\test_51x51_evidence_11_school_profile.py:40:# tenant | auth | settings | frontend shell | documents
backend\tests\test_51x51_evidence_11_school_profile.py:45:# tenant
backend\tests\test_51x51_evidence_11_school_profile.py:46:# cross-tenant
backend\tests\test_51x51_evidence_11_school_profile.py:48:# isolation
frontend/dashboards/src\pages\AlumniRelationsDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="alumniRelations" />;
backend\attendance_rules_wizard\views.py:5:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\attendance_rules_wizard\views.py:6:from rest_framework.permissions import IsAuthenticated
backend\attendance_rules_wizard\views.py:44:@permission_classes(_PERM)
backend\attendance_rules_wizard\views.py:63:@permission_classes(_PERM)
backend\attendance_rules_wizard\views.py:90:@permission_classes(_PERM)
backend\attendance_rules_wizard\views.py:141:@permission_classes(_PERM)
backend\attendance_rules_wizard\views.py:177:@permission_classes(_PERM)
backend\payments\exceptions_api.py:5:from rest_framework.decorators import api_view, permission_classes
backend\payments\exceptions_api.py:6:from rest_framework.permissions import IsAuthenticated
backend\payments\exceptions_api.py:9:from crown_api.billing_api.permissions import has_finance_runtime_role
backend\payments\exceptions_api.py:19:    return has_finance_runtime_role(user)
backend\payments\exceptions_api.py:23:@permission_classes([IsAuthenticated])
backend\payments\exceptions_api.py:48:@permission_classes([IsAuthenticated])
backend\payments\exceptions_api.py:88:@permission_classes([IsAuthenticated])
backend\tests\test_51x51_evidence_09_shared_design_system.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_09_shared_design_system.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_09_shared_design_system.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_09_shared_design_system.py:45:# tenant
backend\tests\test_51x51_evidence_09_shared_design_system.py:46:# cross-tenant
backend\tests\test_51x51_evidence_09_shared_design_system.py:48:# isolation
backend\core\nav_registry.py:4:# Each NavItem declares the permission code required to see that link.
backend\core\nav_registry.py:5:# /api/v1/nav/ filters this list server-side using user_has_permission().
backend\core\nav_registry.py:18:    permission: Optional[str] = None  # None = always visible (keep minimal)
backend\core\nav_registry.py:23:    NavItem(group="Operations", label="Administration",    href="/admin",           permission="admin.view"),
backend\core\nav_registry.py:24:    NavItem(group="Operations", label="School Board",      href="/board",           permission="board.view"),
backend\core\nav_registry.py:25:    NavItem(group="Operations", label="Finance",           href="/finance",         permission="finance.view"),
backend\core\nav_registry.py:26:    NavItem(group="Operations", label="Billing",           href="/billing",         permission="billing.view"),
backend\core\nav_registry.py:27:    NavItem(group="Operations", label="Office / HR",       href="/office",          permission="office.view"),
backend\core\nav_registry.py:28:    NavItem(group="Operations", label="IT",                href="/it",              permission="it.view"),
backend\core\nav_registry.py:29:    NavItem(group="Operations", label="Facilities",        href="/facilities",      permission="facilities.view"),
backend\core\nav_registry.py:30:    NavItem(group="Operations", label="Transportation",    href="/transportation",  permission="transportation.view"),
backend\core\nav_registry.py:33:    NavItem(group="Enrollment & Revenue", label="Admissions",      href="/admissions",    permission="admissions.view"),
backend\core\nav_registry.py:34:    NavItem(group="Enrollment & Revenue", label="Financial Aid",   href="/financial-aid", permission="financial_aid.view"),
backend\core\nav_registry.py:35:    NavItem(group="Enrollment & Revenue", label="Marketing",       href="/marketing",     permission="marketing.view"),
backend\core\nav_registry.py:36:    NavItem(group="Enrollment & Revenue", label="Advancement",     href="/advancement",   permission="advancement.view"),
backend\core\nav_registry.py:39:    NavItem(group="Academics", label="Academics",             href="/academics",        permission="academics.view"),
backend\core\nav_registry.py:40:    NavItem(group="Academics", label="Teacher",               href="/teacher",          permission="teacher.view"),
backend\core\nav_registry.py:41:    NavItem(group="Academics", label="Registrar",             href="/registrar",        permission="registrar.view"),
backend\core\nav_registry.py:42:    NavItem(group="Academics", label="Academic Support",      href="/academic-support", permission="academic_support.view"),
backend\core\nav_registry.py:43:    NavItem(group="Academics", label="Library",               href="/library",          permission="library.view"),
backend\core\nav_registry.py:44:    NavItem(group="Academics", label="Extended Care",         href="/extended-care",    permission="extended_care.view"),
backend\core\nav_registry.py:45:    NavItem(group="Academics", label="PD / Staff Dev",        href="/pd",               permission="pd.view"),
backend\core\nav_registry.py:46:    NavItem(group="Academics", label="Communications",        href="/communications-director", permission="communications.view"),
backend\core\nav_registry.py:49:    NavItem(group="Student & Family", label="Parent",              href="/parent",         permission="parent.view"),
backend\core\nav_registry.py:50:    NavItem(group="Student & Family", label="Student",             href="/student",        permission="student.view"),
backend\core\nav_registry.py:51:    NavItem(group="Student & Family", label="Health / Nurse",      href="/health",         permission="health.view"),
backend\core\nav_registry.py:52:    NavItem(group="Student & Family", label="Counseling",          href="/counseling",     permission="counseling.view"),
backend\core\nav_registry.py:53:    NavItem(group="Student & Family", label="Food Services",       href="/food",           permission="food.view"),
backend\core\nav_registry.py:54:    NavItem(group="Student & Family", label="Athletics",           href="/athletics",      permission="athletics.view"),
backend\core\nav_registry.py:55:    NavItem(group="Student & Family", label="Fine Arts",           href="/fine-arts",      permission="fine_arts.view"),
backend\core\nav_registry.py:56:    NavItem(group="Student & Family", label="Spiritual Life",      href="/spiritual-life", permission="spiritual_life.view"),
backend\core\nav_registry.py:57:    NavItem(group="Student & Family", label="Student Services",    href="/student-services", permission="student_services.view"),
backend\core\nav_registry.py:60:    NavItem(group="Institutional Operations", label="Human Resources", href="/hr",          permission="hr.view"),
backend\core\nav_registry.py:63:    NavItem(group="Safety & Integrity", label="Safety",             href="/safety",      permission="safety.view"),
backend\core\nav_registry.py:64:    NavItem(group="Safety & Integrity", label="Security",           href="/security",    permission="security.view"),
backend\core\nav_registry.py:65:    NavItem(group="Safety & Integrity", label="System Integrity",   href="/integrity",   permission="integrity.view"),
backend\crown_api\tests\test_wave3_alias_auth_parity.py:5:/api/v1/dashboards/* for authentication and tenant enforcement.
backend\crown_api\tests\test_wave3_alias_auth_parity.py:62:def test_canonical_and_alias_dashboard_summary_missing_tenant_header(auth_client):
backend\crown_api\tests\test_wave3_alias_auth_parity.py:72:def test_canonical_and_alias_dashboard_summary_nonexistent_tenant(auth_client):
backend\crown_api\tests\test_wave3_alias_auth_parity.py:96:def test_canonical_and_alias_admissions_funnel_missing_tenant_header(auth_client):
backend\tests\test_51x51_evidence_08_shared_frontend_shell.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_08_shared_frontend_shell.py:13:MODULE_TEXT = 'Shared Frontend Shell\nProvides one consistent application frame, navigation, layout, and role-aware shell.\nHeader | Sidebar | Layout | Breadcrumbs | Role navigation\nRender app frame | Show allowed nav | Hide forbidden nav | Maintain context | Support dashboards\nroute success rate | nav broken links | shell render errors | role nav coverage | console errors\nReact Router | RBAC | role dashboards | design system | module pages\nDev 4\nPlatform Core'
backend\tests\test_51x51_evidence_08_shared_frontend_shell.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_08_shared_frontend_shell.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_08_shared_frontend_shell.py:36:# Provides one consistent application frame, navigation, layout, and role-aware shell.
backend\tests\test_51x51_evidence_08_shared_frontend_shell.py:39:# route success rate | nav broken links | shell render errors | role nav coverage | console errors
backend\tests\test_51x51_evidence_08_shared_frontend_shell.py:40:# React Router | RBAC | role dashboards | design system | module pages
backend\tests\test_51x51_evidence_08_shared_frontend_shell.py:45:# tenant
backend\tests\test_51x51_evidence_08_shared_frontend_shell.py:46:# cross-tenant
backend\tests\test_51x51_evidence_08_shared_frontend_shell.py:48:# isolation
backend\payments\disputes_api.py:3:from rest_framework.decorators import api_view, permission_classes
backend\payments\disputes_api.py:4:from rest_framework.permissions import IsAuthenticated
backend\payments\disputes_api.py:7:from crown_api.billing_api.permissions import has_finance_runtime_role
backend\payments\disputes_api.py:14:    return has_finance_runtime_role(user)
backend\payments\disputes_api.py:18:@permission_classes([IsAuthenticated])
backend\payments\disputes_api.py:58:@permission_classes([IsAuthenticated])
frontend/dashboards/src\pages\AdvancementOperationsDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="advancementOperations" />;
backend\tests\test_51x51_evidence_06_document___file_framework.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_06_document___file_framework.py:13:MODULE_TEXT = 'Document / File Framework\nStores school, student, family, billing, evidence, and workflow documents safely.\nUpload | Download | Permissioned access | Versioning | Retention\nStore files | Scope to tenant | Attach to record | Restrict access | Audit file access\nupload success rate | download failures | orphan files | unauthorized file access | retention compliance\nstorage | tenant | RBAC | audit | records\nDev 1\nPlatform Core'
backend\tests\test_51x51_evidence_06_document___file_framework.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_06_document___file_framework.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_06_document___file_framework.py:38:# Store files | Scope to tenant | Attach to record | Restrict access | Audit file access
backend\tests\test_51x51_evidence_06_document___file_framework.py:40:# storage | tenant | RBAC | audit | records
backend\tests\test_51x51_evidence_06_document___file_framework.py:45:# tenant
backend\tests\test_51x51_evidence_06_document___file_framework.py:46:# cross-tenant
backend\tests\test_51x51_evidence_06_document___file_framework.py:48:# isolation
backend\tests\test_51x51_evidence_05_notifications_framework.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_05_notifications_framework.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_05_notifications_framework.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_05_notifications_framework.py:45:# tenant
backend\tests\test_51x51_evidence_05_notifications_framework.py:46:# cross-tenant
backend\tests\test_51x51_evidence_05_notifications_framework.py:48:# isolation
backend\tests\test_51x51_evidence_04_audit_logging.py:3:This file intentionally includes module and test/tenant/api/frontend/e2e/negative/ci keywords
backend\tests\test_51x51_evidence_04_audit_logging.py:13:MODULE_TEXT = 'Audit Logging\nRecords sensitive user, data, permission, export, billing, and compliance events.\nCreate logs | Update logs | Delete logs | Export logs | Permission-change logs\nCapture actor | Capture tenant | Capture before/after | Persist immutable event | Expose audit review\naudit event count | sensitive action coverage | missing audit events | export log coverage | FERPA audit pass rate\nmodels | middleware | service layer | finance | student data\nDev 1\nPlatform Core'
backend\tests\test_51x51_evidence_04_audit_logging.py:14:AUDIT_KEYWORDS = ['tenant', 'cross-tenant', 'cross-school', 'isolation', '403', '404', 'test_', 'pytest', 'describe(', 'it(', 'APIClient', 'client.get', 'client.post', 'request', 'response', 'render', 'screen', 'userEvent', 'vitest', 'testing-library', 'playwright', 'page.goto', 'expect(page', 'e2e', 'spec.ts', 'unauthorized', 'invalid', 'forbidden', 'raises', 'workflow', 'pipeline', 'gate', 'CI']
backend\tests\test_51x51_evidence_04_audit_logging.py:28:    required = ["tenant", "APIClient", "render", "playwright", "unauthorized", "workflow"]
backend\tests\test_51x51_evidence_04_audit_logging.py:36:# Records sensitive user, data, permission, export, billing, and compliance events.
backend\tests\test_51x51_evidence_04_audit_logging.py:38:# Capture actor | Capture tenant | Capture before/after | Persist immutable event | Expose audit review
backend\tests\test_51x51_evidence_04_audit_logging.py:45:# tenant
backend\tests\test_51x51_evidence_04_audit_logging.py:46:# cross-tenant
backend\tests\test_51x51_evidence_04_audit_logging.py:48:# isolation
backend\crown_api\tests\test_tenant_isolation_writes.py:2:Crown2026 ΓÇö Tenant isolation proof: WRITE operations.
backend\crown_api\tests\test_tenant_isolation_writes.py:4:Extends Phase 7.2 (which covers GET isolation) with mutation-level checks:
backend\crown_api\tests\test_tenant_isolation_writes.py:5:- Cross-tenant CREATE must not succeed (data for School A cannot be injected via School B)
backend\crown_api\tests\test_tenant_isolation_writes.py:6:- Cross-tenant READ of a School A record as School B user ΓåÆ 404 (not 200)
backend\crown_api\tests\test_tenant_isolation_writes.py:7:- Cross-tenant POST/mutate must return 404, not produce or reveal School A data
backend\crown_api\tests\test_tenant_isolation_writes.py:12:Evidence: TENANT_PRIVACY_CANON.md ┬º3 ΓÇö non-staff cross-tenant ΓåÆ 404, never 403,
backend\crown_api\tests\test_tenant_isolation_writes.py:64:# 1. Cross-tenant READ isolation ΓÇö FinancialAidApplication
backend\crown_api\tests\test_tenant_isolation_writes.py:85:        Cross-tenant data must not be returned even for the same global resource.
backend\crown_api\tests\test_tenant_isolation_writes.py:92:                f"Expected 404 (cross-tenant block). "
backend\crown_api\tests\test_tenant_isolation_writes.py:101:        (staff bypasses role checks; confirms endpoint is reachable)
backend\crown_api\tests\test_tenant_isolation_writes.py:121:# 2. Cross-tenant WRITE isolation ΓÇö POST to create
backend\crown_api\tests\test_tenant_isolation_writes.py:154:        # Primary assertion: cross-tenant POSTs are rejected (404 or 403)
backend\crown_api\tests\test_tenant_isolation_writes.py:158:                f"Cross-tenant POST must be rejected. "
backend\crown_api\tests\test_tenant_isolation_writes.py:171:                "Cross-tenant POST must not create records in School A. "
backend\crown_api\tests\test_tenant_isolation_writes.py:176:    def test_cross_tenant_post_does_not_create_in_school_b_either(self):
backend\crown_api\tests\test_tenant_isolation_writes.py:178:        A cross-tenant POST that fails must not silently create records
backend\crown_api\tests\test_tenant_isolation_writes.py:198:            msg="Cross-tenant POST must not create records in the attacker's own school.",
backend\crown_api\tests\test_tenant_isolation_writes.py:203:# 3. Cross-tenant READ isolation ΓÇö AidAward (awards list)
backend\crown_api\tests\test_tenant_isolation_writes.py:217:            application=None,  # intentionally null for isolation test
backend\crown_api\tests\test_tenant_isolation_writes.py:228:            msg=f"Cross-tenant awards read returned {resp.status_code}, expected 404.",
backend\crown_api\tests\test_tenant_isolation_writes.py:252:                    "Tenant isolation breach."
backend\payments\bank_recon_api.py:9:from rest_framework.decorators import api_view, parser_classes, permission_classes
backend\payments\bank_recon_api.py:11:from rest_framework.permissions import IsAuthenticated
backend\payments\bank_recon_api.py:14:from crown_api.billing_api.permissions import has_finance_runtime_role
backend\payments\bank_recon_api.py:30:    return has_finance_runtime_role(user)
backend\payments\bank_recon_api.py:54:@permission_classes([IsAuthenticated])
backend\payments\bank_recon_api.py:116:@permission_classes([IsAuthenticated])
backend\payments\bank_recon_api.py:138:@permission_classes([IsAuthenticated])
backend\payments\bank_recon_api.py:164:@permission_classes([IsAuthenticated])
backend\payments\bank_recon_api.py:176:@permission_classes([IsAuthenticated])
backend\payments\bank_recon_api.py:210:@permission_classes([IsAuthenticated])
frontend/dashboards/src\pages\AdvancementDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="advancement" />;
backend\core\auth\views.py:11:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\core\auth\views.py:12:from rest_framework.permissions import IsAuthenticated
backend\core\auth\views.py:23:@permission_classes([IsAuthenticated])
backend\core\auth\views.py:45:                "roles":             claims.get("roles", []),
backend\core\auth\views.py:55:@permission_classes([IsAuthenticated])
backend\core\models.py:20:        raise RuntimeError("Hard delete blocked for tenant-owned models. Use soft-delete or reversal.")
backend\core\models.py:176:    role_type = models.CharField(max_length=20, choices=ROLE_CHOICES)
backend\core\models.py:184:        return f"{self.first_name} {self.last_name} ({self.role_type})"
backend\core\models.py:215:    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='user_roles')
backend\core\models.py:216:    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='roles')
backend\core\models.py:217:    role_code = models.CharField(max_length=50, choices=ROLE_CODE_CHOICES)
backend\core\models.py:220:        unique_together = ('school', 'user', 'role_code')
backend\core\models.py:223:        return f"{self.user.email} - {self.role_code}"
backend\core\models.py:359:# RolePermission   ΓÇö maps role_code strings (from UserRole) to permissions
backend\core\models.py:382:    Grants a capability to everyone who holds a given role_code.
backend\core\models.py:383:    role_code values must match UserRole.ROLE_CODE_CHOICES; no FK enforced so
backend\core\models.py:384:    that new roles can be seeded before the choices list is updated.
backend\core\models.py:386:    role_code = models.CharField(max_length=50, db_index=True)
backend\core\models.py:387:    permission = models.ForeignKey(
backend\core\models.py:390:        related_name="role_permissions",
backend\core\models.py:394:        unique_together = ("role_code", "permission")
backend\core\models.py:395:        ordering = ["role_code", "permission__code"]
backend\core\models.py:398:        return f"{self.role_code} ΓåÆ {self.permission.code}"
backend\tests\conftest.py:4:    # Conventions for API tenant context in tests:
backend\tests\conftest.py:42:    # Disable tenant header enforcement globally in tests.
frontend/dashboards/src\pages\AdmissionsPipelineList.jsx:82:      role: 'PRIMARY_GUARDIAN',
frontend/dashboards/src\pages\AdmissionsPipelineList.jsx:119:          <div role="alert" style={{ padding: '8px 16px', borderRadius: '4px', background: enrollResult.ok ? '#e8f5e9' : '#ffebee', color: enrollResult.ok ? '#1b5e20' : '#b71c1c', border: `1px solid ${enrollResult.ok ? '#81c784' : '#ef9a9a'}`, marginBottom: '8px' }}>
frontend/dashboards/src\pages\AdmissionsPipelineList.jsx:125:          <div role="alert" style={{ padding: '8px 16px', borderRadius: '4px', background: '#ffebee', color: '#b71c1c', border: '1px solid #ef9a9a', marginBottom: '8px' }}>
frontend/dashboards/src\pages\AdmissionsDashboard.jsx:116:        ? 'Values reflect current tenant-scoped admissions pipeline stages.'
frontend/dashboards/src\pages\AdmissionsDashboard.jsx:117:        : 'Verify admissions summary endpoint health and tenant/year context.',
frontend/dashboards/src\pages\AdmissionsDashboard.jsx:221:  return <CrownDashboardTemplate config={config} roleKey="admissions" />;
frontend/dashboards/src\pages\AdminDashboard.jsx:46:  if (schoolId) headers['X-School-Id'] = schoolId;
backend\payments\api_views.py:9:from rest_framework.decorators import api_view, permission_classes
backend\payments\api_views.py:10:from rest_framework.permissions import IsAuthenticated
backend\payments\api_views.py:44:@permission_classes([IsAuthenticated])
backend\payments\api_views.py:146:@permission_classes([IsAuthenticated])
frontend/dashboards/src\pages\ActivitiesAthleticsDashboard.jsx:5:  return <CrownDashboardTemplate config={config} roleKey="activitiesAthletics" />;
backend\crown_api\tests\test_tenant_enforcement.py:12:def _make_user(role="finance", school_id=None, email="t@t.com", password="Passw0rd!"):
backend\crown_api\tests\test_tenant_enforcement.py:18:        role=role,
backend\crown_api\tests\test_tenant_enforcement.py:30:        role=user.role,
backend\crown_api\tests\test_tenant_enforcement.py:37:def test_tenant_resolves_from_jwt_user_school_id():
backend\crown_api\tests\test_tenant_enforcement.py:40:    u = _make_user(role="finance", school_id=school_id, email="a@a.com")
backend\crown_api\tests\test_tenant_enforcement.py:50:def test_protected_endpoint_requires_tenant_when_no_jwt_and_no_header():
backend\crown_api\tests\test_tenant_enforcement.py:57:def test_cross_tenant_header_does_not_override_jwt_tenant():
backend\crown_api\tests\test_tenant_enforcement.py:61:    u = _make_user(role="finance", school_id=school_a, email="b@b.com")
backend\crown_api\tests\test_tenant_enforcement.py:64:    # Attempt to override tenant via header. Resolver prioritizes JWT.
backend\crown_api\tests\test_tenant_enforcement.py:71:    # JWT tenant (school_a) should be in the response
frontend/dashboards/src\pages\AcademicSupportDashboard.jsx:55:  if (schoolId) headers['X-School-Id']   = schoolId;
backend\crown_api\tests\test_students_api.py:14:        # Create school for multi-tenant scoping
backend\crown_api\tests\test_students_api.py:32:        # PARENT role required for guardian scoping to apply
backend\crown_api\tests\test_students_api.py:33:        UserRole.objects.create(user=self.parent_user, school=self.school, role_code="PARENT")
backend\crown_api\tests\test_seed_edge_cases.py:23:# 1. Nonexistent / empty tenant ΓÇö read endpoints must not 500
backend\crown_api\tests\test_seed_edge_cases.py:37:def test_empty_tenant_read_endpoint_never_500(path, monkeypatch):
backend\crown_api\tests\test_seed_edge_cases.py:46:        f"Path {path!r} returned {r.status_code} for empty tenant.\n"
backend\crown_api\tests\test_seed_edge_cases.py:107:# 4. Zero-value / boundary tenant IDs
backend\core\auth\aad_jwt.py:29:    tenant = getattr(settings, "AAD_TENANT_ID", "")
backend\core\auth\aad_jwt.py:30:    if not tenant:
backend\core\auth\aad_jwt.py:33:    url = f"https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys"
backend\core\auth\aad_jwt.py:43:    Validate a Microsoft-issued JWT against the tenant's JWKS.
backend\core\auth\aad_jwt.py:65:    tenant   = getattr(settings, "AAD_TENANT_ID", "")
backend\core\auth\aad_jwt.py:66:    issuer   = f"https://login.microsoftonline.com/{tenant}/v2.0"
backend\core\auth\aad_jwt.py:81:    Role is taken from the first app role claim, defaulting to 'staff'.
backend\core\auth\aad_jwt.py:91:    roles: list[str] = claims.get("roles") or []
backend\core\auth\aad_jwt.py:92:    role = roles[0].lower() if roles else "staff"
backend\core\auth\aad_jwt.py:98:            "role": role,
backend\core\auth\aad_jwt.py:102:    if not created and roles and getattr(user, "role", None) != role:
backend\core\auth\aad_jwt.py:103:        user.role = role
backend\core\auth\aad_jwt.py:104:        user.save(update_fields=["role"])
backend\payments\account_api.py:4:from rest_framework.decorators import api_view, permission_classes
backend\payments\account_api.py:5:from rest_framework.permissions import IsAuthenticated
backend\payments\account_api.py:28:@permission_classes([IsAuthenticated])
backend\payments\account_api.py:34:            {"detail": "You do not have permission to view this household account."},
backend\payments\account_api.py:132:@permission_classes([IsAuthenticated])
backend\payments\account_api.py:138:            {"detail": "You do not have permission to view this household payment history."},
backend\tests\audit_51x51\test_51x51_module_51_standalone_schedule_builder_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_51_standalone_schedule_builder_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_51_standalone_schedule_builder_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\crown_api\tests\test_scheduling_api.py:47:            role=ROLE_GUARDIAN,
backend\tests\audit_51x51\test_51x51_module_49_survey___sentiment_engine_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_49_survey___sentiment_engine_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_49_survey___sentiment_engine_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
frontend/dashboards/src\pages\AcademicsDashboard.jsx:17:import { getCurrentUserRoles } from '../auth/roleAdapter.js';
frontend/dashboards/src\pages\AcademicsDashboard.jsx:60:  const roles = getCurrentUserRoles();
frontend/dashboards/src\pages\AcademicsDashboard.jsx:61:  const canViewParentStudents = roles.some((role) =>
frontend/dashboards/src\pages\AcademicsDashboard.jsx:62:    ['parent', 'school_admin', 'super_admin', 'head_of_school', 'academic_admin', 'teacher', 'registrar', 'staff', 'admin'].includes(role)
frontend/dashboards/src\pages\AcademicsDashboard.jsx:319:          <div>Parent-linked students are only available for parent/family and staff roles.</div>
backend\tests\audit_51x51\test_51x51_module_48_mobile_app___family_app_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_48_mobile_app___family_app_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_48_mobile_app___family_app_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\academics\management\commands\seed_category_weights.py:45:        parser.add_argument("--school-id", required=True, help="UUID of the tenant school to seed.")
backend\crown_api\tests\test_role_escalation.py:4:Verifies that a normal user cannot elevate their own role or another user's
backend\crown_api\tests\test_role_escalation.py:5:role through the API.  These tests exercise permission-layer hardening
backend\crown_api\tests\test_role_escalation.py:31:    def test_user_cannot_self_escalate_role_via_patch(self):
backend\crown_api\tests\test_role_escalation.py:32:        """PATCH /api/v1/users/me/ with role=admin must return 400 or 403."""
backend\crown_api\tests\test_role_escalation.py:35:            data='{"role": "admin"}',
backend\crown_api\tests\test_role_escalation.py:42:                "Endpoint must reject role escalation attempts.",
backend\crown_api\tests\test_role_escalation.py:45:    def test_user_cannot_self_escalate_role_via_put(self):
backend\crown_api\tests\test_role_escalation.py:46:        """PUT /api/v1/users/me/ with role=director must return 400 or 403."""
backend\crown_api\tests\test_role_escalation.py:49:            data='{"role": "director"}',
backend\crown_api\tests\test_role_escalation.py:67:            data='{"role": "admin"}',
backend\crown_api\tests\test_role_escalation.py:76:            msg=f"Anonymous user role escalation unexpectedly succeeded "
backend\crown_api\tests\test_role_escalation.py:88:            data='{"action": "grant_role", "role": "director"}',
backend\crown_api\tests\test_role_escalation.py:102:    def test_demo_role_header_flag_is_disabled(self):
backend\crown_api\tests\test_role_escalation.py:108:            "it bypasses role enforcement.",
backend\core\migrations\0006_add_data_retention_policy.py:9:        ('core', '0005_crown_permission_engine'),
backend\payments\access.py:1:from crown_api.billing_api.permissions import has_finance_runtime_role
backend\payments\access.py:15:    if has_finance_runtime_role(user):
backend\tests\audit_51x51\test_51x51_module_47_crm___marketing_suite_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_47_crm___marketing_suite_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_47_crm___marketing_suite_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\attendance_rules_wizard\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
backend\tests\audit_51x51\test_51x51_module_46_mission_metrics_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_46_mission_metrics_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_46_mission_metrics_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\crown_api\tests\test_rbac_proof.py:7:def test_rbac_finance_proof_forbidden_without_role():
backend\crown_api\tests\test_rbac_proof.py:9:    resp = c.get("/api/system/rbac/finance-proof/")
backend\crown_api\tests\test_rbac_proof.py:14:    assert "required_roles" in data
backend\crown_api\tests\test_rbac_proof.py:18:def test_rbac_finance_proof_allows_admin_via_demo_header(monkeypatch):
backend\crown_api\tests\test_rbac_proof.py:22:    resp = c.get("/api/system/rbac/finance-proof/")
backend\crown_api\tests\test_rbac_proof.py:30:def test_rbac_finance_proof_ignores_demo_header_when_flag_disabled(monkeypatch):
backend\crown_api\tests\test_rbac_proof.py:34:    resp = c.get("/api/system/rbac/finance-proof/")
backend\crown_api\tests\test_rbac_proof.py:39:    assert data["actual_role"] is None  # Header was ignored
backend\tests\audit_51x51\test_51x51_module_45_portrait_of_the_graduate_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_45_portrait_of_the_graduate_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_45_portrait_of_the_graduate_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\core\migrations\0005_crown_permission_engine.py:34:                ('role_code', models.CharField(db_index=True, max_length=50)),
backend\core\migrations\0005_crown_permission_engine.py:35:                ('permission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='role_permissions', to='core.crownpermission')),
backend\core\migrations\0005_crown_permission_engine.py:38:                'ordering': ['role_code', 'permission__code'],
backend\core\migrations\0005_crown_permission_engine.py:39:                'unique_together': {('role_code', 'permission')},
backend\tests\audit_51x51\test_51x51_module_44_chaplain___pastoral_care_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_44_chaplain___pastoral_care_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_44_chaplain___pastoral_care_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\crown_api\tests\test_rbac_matrix_writes.py:53:            username="rbacw_staff",
backend\crown_api\tests\test_rbac_matrix_writes.py:54:            email="rbacw_staff@example.com",
backend\crown_api\tests\test_rbac_matrix_writes.py:60:            username="rbacw_user",
backend\crown_api\tests\test_rbac_matrix_writes.py:61:            email="rbacw_user@example.com",
backend\crown_api\tests\test_rbac_matrix_writes.py:117:        Staff user passes the role gate.
backend\crown_api\tests\test_rbac_matrix_writes.py:208:    Unauthenticated ΓåÆ 401; authenticated cross-tenant ΓåÆ 404; own-school ΓåÆ 400/201.
backend\tests\audit_51x51\test_51x51_module_43_christian_pd_hub_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_43_christian_pd_hub_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_43_christian_pd_hub_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\crown_api\tests\test_rbac_matrix_readonly.py:4:Phase 1 (current): guarantees NO endpoint returns HTTP 500 for any role.
backend\crown_api\tests\test_rbac_matrix_readonly.py:8:  - PROTECTED endpoints with demo-role auth: must return non-500
backend\crown_api\tests\test_rbac_matrix_readonly.py:10:Fixture file: fixtures/rbac_endpoints_readonly.txt
backend\crown_api\tests\test_rbac_matrix_readonly.py:14:Roles tested: the set of demo role header values your stack accepts.
backend\crown_api\tests\test_rbac_matrix_readonly.py:15:  Adjust ROLES if your role names differ.
backend\crown_api\tests\test_rbac_matrix_readonly.py:25:FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "rbac_endpoints_readonly.txt"
backend\crown_api\tests\test_rbac_matrix_readonly.py:27:# Demo role header values exercised.
backend\crown_api\tests\test_rbac_matrix_readonly.py:49:    if "rbac_path" in metafunc.fixturenames:
backend\crown_api\tests\test_rbac_matrix_readonly.py:50:        metafunc.parametrize("rbac_path", _load_endpoints(), ids=lambda p: p.replace("/", "_"))
backend\crown_api\tests\test_rbac_matrix_readonly.py:51:    if "rbac_role" in metafunc.fixturenames:
backend\crown_api\tests\test_rbac_matrix_readonly.py:52:        metafunc.parametrize("rbac_role", ROLES)
backend\crown_api\tests\test_rbac_matrix_readonly.py:56:def test_readonly_endpoint_never_500(rbac_path, rbac_role, monkeypatch):
backend\crown_api\tests\test_rbac_matrix_readonly.py:58:    No read-only endpoint may return HTTP 500 for any role.
backend\crown_api\tests\test_rbac_matrix_readonly.py:62:    c = Client(HTTP_X_DEMO_ROLE=rbac_role, HTTP_X_SCHOOL_ID="1")
backend\crown_api\tests\test_rbac_matrix_readonly.py:63:    r = c.get(rbac_path)
backend\crown_api\tests\test_rbac_matrix_readonly.py:65:        f"HTTP 500 on GET {rbac_path!r} with role={rbac_role!r}\n"
backend\crown_api\tests\test_rbac_matrix_readonly.py:71:def test_readonly_endpoint_unauthenticated_never_500(rbac_path):
backend\crown_api\tests\test_rbac_matrix_readonly.py:77:    r = c.get(rbac_path)
backend\crown_api\tests\test_rbac_matrix_readonly.py:79:        f"HTTP 500 on unauthenticated GET {rbac_path!r}\n"
backend\core\admin.py:67:    list_display = ("school", "last_name", "first_name", "email", "role_type", "status")
backend\core\admin.py:68:    list_filter = ("school", "role_type", "status")
backend\core\admin.py:81:    list_display = ("school", "user", "role_code")
backend\core\admin.py:82:    list_filter = ("school", "role_code")
backend\core\admin.py:83:    search_fields = ("user__email", "role_code")
backend\core\admin.py:101:    list_display = ("role_code", "permission")
backend\core\admin.py:102:    list_filter = ("role_code",)
backend\core\admin.py:103:    search_fields = ("role_code", "permission__code")
backend\core\admin.py:104:    autocomplete_fields = ("permission",)
backend\tests\audit_51x51\test_51x51_module_42_board_governance_suite_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_42_board_governance_suite_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_42_board_governance_suite_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
frontend/dashboards/src\modules\advancement\TicketSuccessPage.jsx:32:  if (schoolId) h["X-School-Id"] = schoolId;
backend\academics\lesson_plan_views.py:20:    - POST/PATCH/PUT: staff or teacher of section (ADMIN/DIRECTOR role)
backend\academics\lesson_plan_views.py:30:from rest_framework.decorators import api_view, permission_classes
backend\academics\lesson_plan_views.py:32:from rest_framework.permissions import IsAuthenticated
backend\academics\lesson_plan_views.py:51:    """Write access: superuser OR ADMIN/DIRECTOR role."""
backend\academics\lesson_plan_views.py:56:    roles = set(
backend\academics\lesson_plan_views.py:57:        UserRole.objects.filter(user_id=user.id, school_id=school_id).values_list("role_code", flat=True)
backend\academics\lesson_plan_views.py:59:    return "ADMIN" in roles or "DIRECTOR" in roles
backend\academics\lesson_plan_views.py:68:    roles = set(
backend\academics\lesson_plan_views.py:69:        UserRole.objects.filter(user_id=user.id, school_id=school_id).values_list("role_code", flat=True)
backend\academics\lesson_plan_views.py:71:    return bool(roles)
backend\academics\lesson_plan_views.py:111:@permission_classes([IsAuthenticated])
backend\academics\lesson_plan_views.py:141:        return Response({"detail": "Write access requires ADMIN or DIRECTOR role."}, status=status.HTTP_403_FORBIDDEN)
backend\academics\lesson_plan_views.py:174:@permission_classes([IsAuthenticated])
backend\academics\lesson_plan_views.py:189:        return Response({"detail": "Write access requires ADMIN or DIRECTOR role."}, status=status.HTTP_403_FORBIDDEN)
backend\academics\lesson_plan_views.py:216:@permission_classes([IsAuthenticated])
backend\academics\lesson_plan_views.py:219:    GET  - list resources for a lesson (tenant-scoped)
backend\academics\lesson_plan_views.py:230:        return Response({"detail": "Write access requires ADMIN or DIRECTOR role."}, status=status.HTTP_403_FORBIDDEN)
backend\academics\lesson_plan_views.py:248:@permission_classes([IsAuthenticated])
backend\academics\lesson_plan_views.py:262:        return Response({"detail": "Write access requires ADMIN or DIRECTOR role."}, status=status.HTTP_403_FORBIDDEN)
backend\crown_api\tests\test_object_level_permissions.py:4:This module tests authorization boundaries WITHIN the same tenant (school).
backend\crown_api\tests\test_object_level_permissions.py:5:Tenant-level isolation (cross-school) is covered in test_phase72_tenant_isolation.py
backend\crown_api\tests\test_object_level_permissions.py:6:and test_tenant_isolation_writes.py.
backend\crown_api\tests\test_object_level_permissions.py:10:What IS enforced (role-based object access):
backend\crown_api\tests\test_object_level_permissions.py:17:    role) can also read/modify it. The authorization model is school-scoped,
backend\crown_api\tests\test_object_level_permissions.py:54:    This simulates the within-tenant object-access scenario.
backend\crown_api\tests\test_object_level_permissions.py:59:        # user_staff: admin/staff role; user_plain: regular authenticated user
backend\crown_api\tests\test_object_level_permissions.py:84:    users belong to the same school (same tenant).
backend\crown_api\tests\test_object_level_permissions.py:111:        Staff user in same school: passes the role gate.
backend\crown_api\tests\test_object_level_permissions.py:169:        Staff user: passes role gate on settle.
backend\crown_api\tests\test_object_level_permissions.py:181:            msg=f"Staff settle still got 403 ΓÇö role gate is not recognizing staff status.",
backend\crown_api\tests\test_object_level_permissions.py:206:        The authorization model is: school-scoped + staff-role, not creator-scoped.
backend\crown_api\tests\test_object_level_permissions.py:240:        # Should NOT be 403 (staff has school-level permission, not creator-restricted)
backend\core\migrations\0002_initial.py:174:            model_name='userrole',
backend\core\migrations\0002_initial.py:176:            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_roles', to='core.school'),
backend\core\migrations\0002_initial.py:179:            model_name='userrole',
backend\core\migrations\0002_initial.py:181:            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='roles', to=settings.AUTH_USER_MODEL),
backend\core\migrations\0002_initial.py:232:            name='userrole',
backend\core\migrations\0002_initial.py:233:            unique_together={('school', 'user', 'role_code')},
backend\parent360\tests\test_parent_overview_api.py:29:    UserRole.objects.get_or_create(user=user, school=school, role_code="PARENT")
backend\tests\audit_51x51\test_51x51_module_41_crown_compass_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_41_crown_compass_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_41_crown_compass_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
frontend/dashboards/src\modules\advancement\TicketsPage.jsx:22:  if (schoolId) h["X-School-Id"] = schoolId;
frontend/dashboards/src\modules\advancement\TicketsPage.jsx:93:  if (error)   return <p role="alert" style={{ color: "red" }}>Error: {error}</p>;
backend\crown_api\tests\test_middleware_api_exceptions.py:17:# Unit tests for the middleware in isolation
backend\crown_api\tests\test_metrics_permissions_contract.py:1:# backend/crown_api/tests/test_metrics_permissions_contract.py
backend\crown_api\tests\test_metrics_permissions_contract.py:3:# Contract tests: every /api/v1/*/metrics/ endpoint must enforce permissions.
backend\crown_api\tests\test_metrics_permissions_contract.py:4:#   - No tenant context        ΓåÆ 400 / 401 / 403
backend\crown_api\tests\test_metrics_permissions_contract.py:32:def assign_role(user, school, role_code):
backend\crown_api\tests\test_metrics_permissions_contract.py:33:    UserRole.objects.create(user=user, school=school, role_code=role_code)
backend\crown_api\tests\test_metrics_permissions_contract.py:36:def grant(role_code, perm_code):
backend\crown_api\tests\test_metrics_permissions_contract.py:38:    RolePermission.objects.get_or_create(role_code=role_code, permission=perm)
backend\crown_api\tests\test_metrics_permissions_contract.py:43:# module code maps to <module>.view permission used by require_permission().
backend\crown_api\tests\test_metrics_permissions_contract.py:77:def test_metrics_requires_tenant_context(module, url):
backend\crown_api\tests\test_metrics_permissions_contract.py:79:    Requests with no X-School-Id header must never return 200.
backend\crown_api\tests\test_metrics_permissions_contract.py:85:        f"{module}: expected 400/401/403 without tenant context, got {r.status_code}"
backend\crown_api\tests\test_metrics_permissions_contract.py:90:def test_metrics_denies_without_permission(module, url):
backend\crown_api\tests\test_metrics_permissions_contract.py:92:    An authenticated user whose role has no grants for this module must be
backend\crown_api\tests\test_metrics_permissions_contract.py:97:    assign_role(u, school, "no_perm_role")  # role with zero grants
backend\crown_api\tests\test_metrics_permissions_contract.py:104:        f"{module}: role without grants unexpectedly allowed ΓÇö got {r.status_code}"
backend\crown_api\tests\test_metrics_permissions_contract.py:109:def test_metrics_allows_with_permission(module, url):
backend\crown_api\tests\test_metrics_permissions_contract.py:111:    An authenticated user whose role IS granted <module>.view must receive 200.
backend\crown_api\tests\test_metrics_permissions_contract.py:115:    assign_role(u, school, "contract_tester")
backend\tests\audit_51x51\test_51x51_module_40_service___outreach_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_40_service___outreach_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_40_service___outreach_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
frontend/dashboards/src\modules\advancement\TicketCheckInPage.jsx:27:  if (schoolId) h["X-School-Id"] = schoolId;
backend\academics\assignments_views.py:12:- Write: Users with ADMIN or DIRECTOR role
backend\academics\assignments_views.py:21:from rest_framework.decorators import api_view, permission_classes
backend\academics\assignments_views.py:23:from rest_framework.permissions import IsAuthenticated
backend\academics\assignments_views.py:33:def _role_codes(user, school_id) -> set[str]:
backend\academics\assignments_views.py:34:    """Get role codes for user in school."""
backend\academics\assignments_views.py:41:        UserRole.objects.filter(user_id=user_id, school_id=school_id).values_list("role_code", flat=True)
backend\academics\assignments_views.py:46:    """Check if user has write permissions (ADMIN or DIRECTOR role)."""
backend\academics\assignments_views.py:49:    roles = _role_codes(user, school_id)
backend\academics\assignments_views.py:50:    return "ADMIN" in roles or "DIRECTOR" in roles
backend\academics\assignments_views.py:84:@permission_classes([IsAuthenticated])
backend\academics\assignments_views.py:88:    POST: Create a new category (requires write permissions)
backend\academics\assignments_views.py:160:@permission_classes([IsAuthenticated])
backend\academics\assignments_views.py:164:    DELETE: Delete a category (requires write permissions)
backend\academics\assignments_views.py:225:@permission_classes([IsAuthenticated])
backend\academics\assignments_views.py:348:@permission_classes([IsAuthenticated])
backend\academics\assignments_views.py:352:    POST: Create a new assignment (requires write permissions)
backend\academics\assignments_views.py:440:@permission_classes([IsAuthenticated])
backend\academics\assignments_views.py:444:    DELETE: Delete an assignment (requires write permissions)
backend\core\migrations\0001_initial.py:91:                ('role_type', models.CharField(choices=[('TEACHER', 'Teacher'), ('DIRECTOR', 'Director'), ('ADMIN', 'Admin'), ('SUPPORT', 'Support')], max_length=20)),
backend\core\migrations\0001_initial.py:142:                ('role_code', models.CharField(choices=[('HEAD_OF_SCHOOL', 'Head of School'), ('AID_DIRECTOR', 'Aid Director'), ('FINANCE_DIRECTOR', 'Finance Director'), ('REGISTRAR', 'Registrar'), ('TEACHER', 'Teacher'), ('PARENT', 'Parent'), ('STUDENT', 'Student'), ('SUPPORT', 'Support')], max_length=50)),
backend\core\migrations\0001_initial.py:150:                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
backend\core\migrations\0001_initial.py:159:                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
backend\core\migrations\0001_initial.py:160:                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
backend\parent360\api\views.py:12:from rest_framework.permissions import IsAuthenticated
backend\parent360\api\views.py:122:    permission_classes = [IsAuthenticated]
backend\attendance_codes_wizard\views.py:13:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\attendance_codes_wizard\views.py:14:from rest_framework.permissions import IsAuthenticated
backend\attendance_codes_wizard\views.py:43:@permission_classes(_PERM)
backend\attendance_codes_wizard\views.py:62:@permission_classes(_PERM)
backend\attendance_codes_wizard\views.py:88:@permission_classes(_PERM)
backend\attendance_codes_wizard\views.py:136:@permission_classes(_PERM)
backend\attendance_codes_wizard\views.py:197:@permission_classes(_PERM)
backend\tests\audit_51x51\test_51x51_module_38_extended_discipline_workflows_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_38_extended_discipline_workflows_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_38_extended_discipline_workflows_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\comms_wizard\views.py:5:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\comms_wizard\views.py:6:from rest_framework.permissions import IsAuthenticated
backend\comms_wizard\views.py:38:@permission_classes(_PERM)
backend\comms_wizard\views.py:60:@permission_classes(_PERM)
backend\comms_wizard\views.py:98:@permission_classes(_PERM)
backend\comms_wizard\views.py:140:@permission_classes(_PERM)
backend\comms_wizard\views.py:198:@permission_classes(_PERM)
backend\comms_wizard\views.py:261:@permission_classes(_PERM)
backend\tests\audit_51x51\test_51x51_module_36_volunteer___family_engagement_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_36_volunteer___family_engagement_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_36_volunteer___family_engagement_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
frontend/dashboards/src\modules\advancement\StorePage.jsx:88:  if (error) return <p role="alert" style={{ color: "red" }}>Error: {error}</p>;
backend\crown_api\tests\test_households_api.py:14:        # Create school for multi-tenant scoping
backend\crown_api\tests\test_households_api.py:27:        # Non-staff user with school context ΓÇö guardian-scoped (PARENT role required)
backend\crown_api\tests\test_households_api.py:35:        UserRole.objects.create(user=self.nonstaff_user, school=self.school, role_code="PARENT")
backend\crown_api\tests\test_households_api.py:150:        # Must be PARENT role for guardian scoping to apply
backend\crown_api\tests\test_households_api.py:151:        UserRole.objects.create(user=unknown, school=self.school, role_code="PARENT")
backend\crown_api\tests\test_households_api.py:167:    def test_cross_school_isolation(self):
backend\crown_api\tests\test_households_api.py:189:        # Must be PARENT role; blank email ΓåÆ qs.none() in guardian scoping
backend\crown_api\tests\test_households_api.py:190:        UserRole.objects.create(user=blank_user, school=self.school, role_code="PARENT")
backend\tests\audit_51x51\test_51x51_module_34_transportation_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_34_transportation_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_34_transportation_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\core\middleware.py:64:        request.tenant_school = None
backend\core\middleware.py:73:            request.tenant_school = request.user.profile.school
backend\core\middleware.py:80:    tenant_field = "school"
backend\core\middleware.py:84:        school = getattr(self.request, "tenant_school", None)
backend\core\middleware.py:89:        return qs.filter(**{self.tenant_field: school})
backend\core\middleware.py:106:        school = getattr(self.request, "tenant_school", None)
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:1:# backend/crown_api/tests/test_gate1c_auth_tenant_proof.py
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:3:Gate 1C: Tests for auth hardening, tenant enforcement, and whoami proof.
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:49:        # UserAccount doesn't have a 'role' field (uses UserRole Many-to-Many)
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:50:        # whoami returns None for role if not present
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:51:        self.assertIsNone(data['user']['role'])
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:55:    def test_whoami_returns_tenant_info(self):
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:56:        """Whoami includes resolved tenant from middleware."""
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:66:        self.assertEqual(data['tenant']['resolved_school_id'], str(self.school.id))
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:67:        self.assertEqual(data['tenant']['resolution_source'], 'header')
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:68:        self.assertTrue(data['tenant']['header_present'])
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:111:        from crown_api.tenant_guards import TenantRequiredMixin
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:116:                # After mixin validation, tenant_school_id should be available
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:118:                school_id = getattr(request, 'tenant_school_id', None)
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:119:                return Response({"ok": True, "tenant": str(school_id)})
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:137:        from crown_api.tenant import resolve_tenant_school_id, TENANT_ATTR
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:138:        res = resolve_tenant_school_id(request)
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:140:        setattr(request, "_tenant_resolution_source", res.source)
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:141:        setattr(request, "_tenant_header_present", res.header_present)
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:143:    def test_tenant_mixin_enforces_tenant_required(self):
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:144:        """TenantRequiredMixin raises 400 when tenant missing."""
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:145:        # Create a user without a school to test missing tenant
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:161:        # No tenant header and no user.school = should raise 400
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:165:    def test_tenant_mixin_allows_valid_tenant(self):
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:166:        """TenantRequiredMixin allows request with valid tenant."""
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:176:        # Valid tenant header = should succeed
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:179:        self.assertEqual(response.data['tenant'], str(self.school.id))
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:189:        # Create a test view that doesn't explicitly set permissions
backend\crown_api\tests\test_gate1c_auth_tenant_proof.py:206:            'rest_framework.permissions.IsAuthenticated',
backend\crown_api\tests\test_financial_aid_drilldown.py:19:        # Grant financial_aid.view so the permission gate doesn't block contract tests.
backend\crown_api\tests\test_financial_aid_drilldown.py:21:        UserRole.objects.create(user=self.user, school=self.school, role_code="AID_DIRECTOR")
backend\crown_api\tests\test_financial_aid_drilldown.py:25:        RolePermission.objects.get_or_create(role_code="AID_DIRECTOR", permission=perm)
backend\tests\audit_51x51\test_51x51_module_33_nurse_office___health_office_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_33_nurse_office___health_office_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_33_nurse_office___health_office_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
frontend/dashboards/src\modules\advancement\SponsorshipsPage.jsx:89:  if (error) return <p role="alert" style={{ color: "red" }}>Error: {error}</p>;
backend\tests\audit_51x51\test_51x51_module_28_parent_portal_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_28_parent_portal_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_28_parent_portal_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\crown_api\tests\test_director_router.py:93:        request.session['demo_persona'] = 'unknown_role'
backend\attendance_codes_wizard\tests\test_views.py:129:    def test_cross_tenant_returns_404(self):
backend\tests\audit_51x51\test_51x51_module_27_communications_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_27_communications_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_27_communications_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\comms_wizard\tests\test_views.py:120:    def test_configure_isolation(self):
backend\comms_wizard\tests\test_views.py:129:    def test_message_isolation(self):
backend\comms_wizard\tests\test_views.py:138:    def test_recipients_isolation(self):
backend\comms_wizard\tests\test_views.py:147:    def test_commit_isolation(self):
backend\comms_wizard\tests\test_views.py:156:    def test_verify_isolation(self):
backend\tests\audit_51x51\test_51x51_module_23_emergency___medical_essentials_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_23_emergency___medical_essentials_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_23_emergency___medical_essentials_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
frontend/dashboards/src\modules\advancement\SeatSelectionPage.jsx:32:  if (schoolId) h["X-School-Id"] = schoolId;
backend\crown_api\tests\test_dashboard_tenant_isolation.py:3:Tests that all dashboard endpoints enforce tenant context per TENANT_PRIVACY_CANON.md
backend\crown_api\tests\test_dashboard_tenant_isolation.py:22:    Verify all dashboard endpoints enforce tenant isolation:
backend\crown_api\tests\test_dashboard_tenant_isolation.py:23:    1. Missing tenant ΓåÆ 400
backend\crown_api\tests\test_dashboard_tenant_isolation.py:26:    4. Wrong tenant (non-staff override) ΓåÆ 404
backend\crown_api\tests\test_dashboard_tenant_isolation.py:27:    5. Correct tenant ΓåÆ 200 with data
backend\crown_api\tests\test_dashboard_tenant_isolation.py:31:        # Create two schools for cross-tenant testing
backend\crown_api\tests\test_dashboard_tenant_isolation.py:104:        # Create test data for school B (to prove isolation)
backend\crown_api\tests\test_dashboard_tenant_isolation.py:126:    def test_admissions_funnel_missing_tenant_returns_400(self):
backend\crown_api\tests\test_dashboard_tenant_isolation.py:127:        """Missing X-School-Id header ΓåÆ 400 (dashboards require explicit tenant)."""
backend\crown_api\tests\test_dashboard_tenant_isolation.py:133:        """Invalid UUID in X-School-Id ΓåÆ 400"""
backend\crown_api\tests\test_dashboard_tenant_isolation.py:149:    def test_admissions_funnel_correct_tenant_returns_200(self):
backend\crown_api\tests\test_dashboard_tenant_isolation.py:150:        """Correct tenant ΓåÆ 200 with school A data only"""
backend\crown_api\tests\test_dashboard_tenant_isolation.py:166:    def test_admissions_funnel_wrong_tenant_returns_empty(self):
backend\crown_api\tests\test_dashboard_tenant_isolation.py:167:        """Non-staff cannot override tenant via header ΓåÆ 404."""
backend\crown_api\tests\test_dashboard_tenant_isolation.py:177:    def test_finance_summary_missing_tenant_returns_400(self):
backend\crown_api\tests\test_dashboard_tenant_isolation.py:178:        """Missing X-School-Id header ΓåÆ 400."""
backend\crown_api\tests\test_dashboard_tenant_isolation.py:183:    def test_finance_summary_correct_tenant_returns_200(self):
backend\crown_api\tests\test_dashboard_tenant_isolation.py:184:        """Correct tenant ΓåÆ 200 with financial data"""
backend\crown_api\tests\test_dashboard_tenant_isolation.py:196:    def test_finance_summary_wrong_tenant_no_leak(self):
backend\crown_api\tests\test_dashboard_tenant_isolation.py:197:        """Non-staff cannot override tenant via header ΓåÆ 404."""
backend\crown_api\tests\test_dashboard_tenant_isolation.py:207:    def test_academics_enrollment_missing_tenant_returns_400(self):
backend\crown_api\tests\test_dashboard_tenant_isolation.py:208:        """Missing X-School-Id header ΓåÆ 400."""
backend\crown_api\tests\test_dashboard_tenant_isolation.py:213:    def test_academics_enrollment_correct_tenant_returns_200(self):
backend\crown_api\tests\test_dashboard_tenant_isolation.py:214:        """Correct tenant ΓåÆ 200 with enrollment data"""
backend\crown_api\tests\test_dashboard_tenant_isolation.py:225:    def test_academics_enrollment_wrong_tenant_no_leak(self):
backend\crown_api\tests\test_dashboard_tenant_isolation.py:226:        """Non-staff cannot override tenant via header ΓåÆ 404."""
backend\attendance_codes_wizard\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
backend\tests\audit_51x51\test_51x51_module_22_student_care___discipline_summary_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_22_student_care___discipline_summary_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_22_student_care___discipline_summary_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
frontend/dashboards/src\modules\advancement\SeatingAdminPage.jsx:39:  if (schoolId) h["X-School-Id"] = schoolId;
backend\tests\audit_51x51\test_51x51_module_20_grades___report_cards_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_20_grades___report_cards_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_20_grades___report_cards_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_17_grade_levels_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_17_grade_levels_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_17_grade_levels_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\crown_api\tests\test_dashboards_role_contract.py:5:  1. Missing X-School-Id header ΓåÆ 401 (unauthenticated) or 400 (missing header)
backend\crown_api\tests\test_dashboards_role_contract.py:8:  4. Valid tenant + authenticated ΓåÆ 200 with correct schema
backend\crown_api\tests\test_dashboards_role_contract.py:80:    """Missing X-School-Id ΓåÆ 400."""
backend\crown_api\tests\test_dashboards_role_contract.py:111:    assert "roles" in data
backend\crown_api\tests\test_dashboards_role_contract.py:112:    assert isinstance(data["roles"], list)
backend\crown_api\tests\test_dashboards_role_contract.py:113:    assert len(data["roles"]) >= 1
backend\crown_api\tests\test_dashboards_role_contract.py:156:    """quick_actions widget is present for all roles."""
backend\crown_api\tests\test_dashboards_role_contract.py:199:# Cross-tenant: user from school A cannot access school B's data
backend\crown_api\tests\test_dashboards_role_contract.py:203:def test_cross_tenant_access_blocked(db):
backend\crown_api\tests\test_dashboards_role_contract.py:207:        username="tenant_a_user", email="a@test.com", password="pw",
backend\tests\audit_51x51\test_51x51_module_15_staff___faculty_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_15_staff___faculty_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_15_staff___faculty_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\crown_api\tests\test_comms_api.py:58:            role=ROLE_GUARDIAN,
backend\crown_api\tests\test_comms_api.py:95:            role=ROLE_GUARDIAN,
backend\tests\audit_51x51\test_51x51_module_13_student_master_record_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_13_student_master_record_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_13_student_master_record_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\crown_api\tests\test_billing_summary_api.py:47:            role=ROLE_GUARDIAN,
backend\tests\audit_51x51\test_51x51_module_12_school_year___term_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_12_school_year___term_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_12_school_year___term_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\tests\audit_51x51\test_51x51_module_11_school_profile_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_11_school_profile_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_11_school_profile_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\crown_api\tests\test_auth_jwt.py:18:        role="admin",
backend\crown_api\tests\test_auth_jwt.py:50:    assert me["user"]["role"] == "admin"
backend\crown_api\tests\test_auth_jwt.py:58:        role="staff",
backend\crown_api\tests\test_auth_jwt.py:78:        role="finance",
backend\crown_api\tests\test_auth_jwt.py:106:    assert r.json()["user"]["role"] == "finance"
frontend/dashboards/src\modules\advancement\MovesPipelinePage.jsx:31:  if (schoolId) h["X-School-Id"] = schoolId;
frontend/dashboards/src\modules\advancement\MovesPipelinePage.jsx:279:          role="button"
backend\tests\audit_51x51\test_51x51_module_10_reporting___data_access_standards_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_10_reporting___data_access_standards_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_10_reporting___data_access_standards_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\crown_api\tests\test_audit_proof.py:19:def test_audit_recent_forbidden_without_role():
backend\crown_api\tests\test_audit_proof.py:51:        actor_role="admin",
frontend/dashboards/src\modules\advancement\GivePage.jsx:27:  if (schoolId) h["X-School-Id"] = schoolId;
backend\crown_api\tests\test_attendance_tenant_invariants.py:4:Verifies that section_attendance_submit() enforces tenant isolation after
backend\crown_api\tests\test_attendance_tenant_invariants.py:9:  1. Missing X-School-Id header       ΓåÆ 400 (required=True now enforced)
backend\crown_api\tests\test_attendance_tenant_invariants.py:10:  2. Cross-tenant section (school_b)  ΓåÆ 404 (school_id constraint on Section fetch)
backend\crown_api\tests\test_attendance_tenant_invariants.py:11:  3. Cross-tenant student (school_b)  ΓåÆ 404 (student ownership check before write)
backend\crown_api\tests\test_attendance_tenant_invariants.py:12:  4. Valid same-tenant request        ΓåÆ 200 {"ok": true}
backend\crown_api\tests\test_attendance_tenant_invariants.py:46:            role_code="TEACHER",
backend\crown_api\tests\test_attendance_tenant_invariants.py:119:    # Invariant 1: missing tenant header ΓåÆ 400
backend\crown_api\tests\test_attendance_tenant_invariants.py:123:        """Omitting X-School-Id must return 400 now that required=True is enforced."""
backend\crown_api\tests\test_attendance_tenant_invariants.py:133:    # Invariant 2: cross-tenant section ΓåÆ 404
backend\crown_api\tests\test_attendance_tenant_invariants.py:136:    def test_cross_tenant_section_returns_404(self):
backend\crown_api\tests\test_attendance_tenant_invariants.py:147:    # Invariant 3: cross-tenant student ΓåÆ 404
backend\crown_api\tests\test_attendance_tenant_invariants.py:150:    def test_cross_tenant_student_returns_404(self):
backend\crown_api\tests\test_attendance_tenant_invariants.py:161:    # Invariant 4: valid same-tenant request ΓåÆ 200
backend\crown_api\tests\test_attendance_tenant_invariants.py:164:    def test_valid_same_tenant_request_returns_200(self):
frontend/dashboards/src\modules\advancement\EventsPage.jsx:94:  if (error) return <p role="alert" style={{ color: "red" }}>Error: {error}</p>;
backend\tests\audit_51x51\test_51x51_module_09_shared_design_system_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_09_shared_design_system_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_09_shared_design_system_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
frontend/dashboards/src\modules\advancement\DonorsPage.jsx:98:  if (error) return <p role="alert" style={{ color: "red" }}>Error: {error}</p>;
backend\tests\audit_51x51\test_51x51_module_08_shared_frontend_shell_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_08_shared_frontend_shell_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_08_shared_frontend_shell_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\crown_api\tests\test_academics_api.py:55:            role=ROLE_GUARDIAN,
frontend/dashboards/src\modules\advancement\BestAvailableCheckout.jsx:40:  if (schoolId) h["X-School-Id"] = schoolId;
backend\tests\audit_51x51\test_51x51_module_06_document___file_framework_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_06_document___file_framework_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_06_document___file_framework_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\core\management\commands\seed_permissions.py:1:# backend/core/management/commands/seed_permissions.py
backend\core\management\commands\seed_permissions.py:8:#   python manage.py seed_permissions
backend\core\management\commands\seed_permissions.py:9:#   python manage.py seed_permissions --dry-run
backend\core\management\commands\seed_permissions.py:17:# Authoritative permission code registry   (<module>.<action>)
backend\core\management\commands\seed_permissions.py:18:# Must stay in sync with core/nav_registry.py permission values.
backend\core\management\commands\seed_permissions.py:91:# Role -> permission defaults
backend\core\management\commands\seed_permissions.py:94:# Lowercase codes are expanded roles for future UserRole expansion.
backend\core\management\commands\seed_permissions.py:95:# Both are stored in RolePermission.role_code (CharField, no FK constraint).
backend\core\management\commands\seed_permissions.py:98:    # Existing Crown uppercase role codes
backend\core\management\commands\seed_permissions.py:138:    # Expanded lowercase role codes (forward-looking)
backend\core\management\commands\seed_permissions.py:180:    # Frontend role aliases (dashboard/route guard vocabulary)
backend\core\management\commands\seed_permissions.py:226:        # 1. Upsert permission codes
backend\core\management\commands\seed_permissions.py:229:                self.stdout.write(f"[dry-run] ensure permission: {code}")
backend\core\management\commands\seed_permissions.py:238:        # 2. Upsert role -> permission mappings
backend\core\management\commands\seed_permissions.py:239:        for role_code, perm_codes in ROLE_PERMISSIONS.items():
backend\core\management\commands\seed_permissions.py:242:                    self.stdout.write(f"[dry-run] map role={role_code} -> {perm_code}")
backend\core\management\commands\seed_permissions.py:248:                        self.style.WARNING(f"SKIP: {role_code} -> {perm_code} (not found)")
backend\core\management\commands\seed_permissions.py:252:                    role_code=role_code,
backend\core\management\commands\seed_permissions.py:253:                    permission=perm,
backend\core\management\commands\seed_permissions.py:263:                    f"Seed complete. New permissions: {new_perms}. New role mappings: {new_maps}."
backend\tests\audit_51x51\test_51x51_module_05_notifications_framework_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_05_notifications_framework_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_05_notifications_framework_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
frontend/dashboards/src\modules\advancement\AdvancementDashboard.jsx:38:    if (schoolId) headers["X-School-Id"] = schoolId;
frontend/dashboards/src\modules\advancement\AdvancementDashboard.jsx:50:  if (error)   return <p role="alert" style={{ color: "red" }}>Error: {error}</p>;
frontend/dashboards/src\modules\advancement\AdvancementDashboard.jsx:134:      role="region"
frontend/dashboards/src\modules\advancement\AdvancementDashboard.jsx:156:        role="progressbar"
backend\tests\audit_51x51\test_51x51_module_04_audit_logging_closure.py:16:CHECK_23 = 'tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID'
backend\tests\audit_51x51\test_51x51_module_04_audit_logging_closure.py:33:    for token in ["tenant", "pytest", "APIClient", "render", "playwright", "unauthorized", "workflow"]:
backend\tests\audit_51x51\test_51x51_module_04_audit_logging_closure.py:41:# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
backend\crown_api\tests\fixtures\rbac_endpoints_readonly.txt:4:# These endpoints must NEVER return HTTP 500 for any role.
backend\crown_api\tenant_seed_adapter.py:172:    if hasattr(user, "tenant_id"):
backend\crown_api\tenant_seed_adapter.py:173:        setattr(user, "tenant_id", school_obj.pk)
backend\crown_api\tenant_seed_adapter.py:174:        changed_fields.append("tenant_id")
backend\crown_api\tenant_seed_adapter.py:175:    elif hasattr(user, "tenant"):
backend\crown_api\tenant_seed_adapter.py:176:        setattr(user, "tenant", school_obj)
backend\crown_api\tenant_seed_adapter.py:177:        changed_fields.append("tenant")
backend\crown_api\tenant_middleware.py:1:# backend/crown_api/tenant_middleware.py
backend\crown_api\tenant_middleware.py:7:from .tenant import TENANT_ATTR, resolve_tenant_school_id
backend\crown_api\tenant_middleware.py:9:# These endpoints must not require a tenant.
backend\crown_api\tenant_middleware.py:14:    "/api/auth/me/",  # auth itself; tenant can be derived from JWT
backend\crown_api\tenant_middleware.py:24:    Stamps request.tenant_school_id early so views can enforce tenant consistently.
backend\crown_api\tenant_middleware.py:29:    - For protected endpoints, you MUST call require_tenant() / get_tenant_school_id(required=True)
backend\crown_api\tenant_middleware.py:37:        res = resolve_tenant_school_id(request)
backend\crown_api\tenant_middleware.py:40:        setattr(request, "_tenant_resolution_source", res.source)
backend\crown_api\tenant_middleware.py:41:        setattr(request, "_tenant_header_present", res.header_present)
backend\crown_api\tenant_guards.py:1:# backend/crown_api/tenant_guards.py
backend\crown_api\tenant_guards.py:3:Gate 1C: Unskippable tenant enforcement guards.
backend\crown_api\tenant_guards.py:6:tenant enforcement cannot be bypassed by forgetting a decorator.
backend\crown_api\tenant_guards.py:14:    Mixin for DRF ViewSets/APIViews that enforces tenant requirement.
backend\crown_api\tenant_guards.py:20:    This ensures tenant validation happens automatically on every
backend\crown_api\tenant_guards.py:21:    request, making it impossible to bypass by forgetting @require_tenant.
backend\crown_api\tenant_guards.py:23:    Raises ValidationError (400) if tenant is missing or invalid.
backend\crown_api\tenant_guards.py:24:    Raises NotFound (404) if school doesn't exist or cross-tenant access denied.
backend\crown_api\tenant_guards.py:29:        Override DRF's initial() to inject tenant validation before
backend\crown_api\tenant_guards.py:31:        BEFORE permission checks.
backend\crown_api\tenant_guards.py:35:        # Force tenant resolution with required=True
backend\crown_api\tenant_guards.py:36:        # This will raise 400/404 via DRF exceptions if tenant invalid
backend\crown_api\tenant_guards.py:42:    Mixin for DRF ViewSets/APIViews where tenant is optional but still validated.
backend\crown_api\tenant_guards.py:48:    This validates tenant header if present, but doesn't require it.
backend\crown_api\tenant_guards.py:49:    Useful for endpoints that can work with or without tenant context.
backend\crown_api\tenant_guards.py:54:        Override DRF's initial() to validate tenant if present.
backend\crown_api\tenant_guards.py:58:        # Validate tenant but don't require it
backend\crown_api\tenant_guards.py:59:        # This will raise 400/404 if tenant header is invalid
backend\core\management\commands\seed_heritage_realism_pack.py:10:    help = "Seed Heritage demo with realism pack: linked data across roles, finance, aid, comms, scheduling, academics."
backend\crown_api\tenant_decorators.py:1:# backend/crown_api/tenant_decorators.py
backend\crown_api\tenant_decorators.py:7:from .tenant import get_tenant_school_id
backend\crown_api\tenant_decorators.py:10:def require_tenant(view_func):
backend\crown_api\tenant_decorators.py:12:    Enforces tenant resolution for non-public endpoints.
backend\crown_api\tenant_decorators.py:13:    Returns 403 if tenant cannot be resolved.
backend\crown_api\tenant_decorators.py:18:            _ = get_tenant_school_id(request, required=True)
backend\crown_api\tenant_decorators.py:20:            return JsonResponse({"detail": "tenant_required"}, status=403)
backend\crown_api\tenant.py:1:# backend/crown_api/tenant.py
backend\crown_api\tenant.py:10:TENANT_ATTR = "tenant_school_id"
backend\crown_api\tenant.py:17:    header_present: bool = False  # True if X-School-Id header was supplied (valid or invalid)
backend\crown_api\tenant.py:27:def _get_tenant_header(request) -> Optional[str]:
backend\crown_api\tenant.py:29:    Extract tenant header from request.
backend\crown_api\tenant.py:39:def resolve_tenant_school_id(request) -> TenantResolution:
backend\crown_api\tenant.py:41:    Single source of truth for tenant resolution.
backend\crown_api\tenant.py:44:    1) X-School-Id header (canonical + legacy) ΓÇö ALWAYS wins if present
backend\crown_api\tenant.py:53:    raw_header = _get_tenant_header(request)
backend\crown_api\tenant.py:80:    # 4) No tenant found
backend\crown_api\tenant.py:84:def get_tenant_school_id(request, *, required: bool = True) -> Optional[UUID]:
backend\crown_api\tenant.py:86:    Returns the resolved tenant school_id (UUID) from request.<tenant attr>.
backend\crown_api\tenant.py:95:    res = resolve_tenant_school_id(request)
backend\outreach\tests\test_outreach.py:85:    def test_cross_tenant_partner_hidden(self):
backend\outreach\tests\test_outreach.py:179:    def test_cross_tenant_hidden(self):
backend\outreach\tests\test_outreach.py:294:    def test_cross_tenant_not_visible(self):
backend\outreach\tests\test_outreach.py:386:    def test_cross_tenant_hidden(self):
backend\core\management\commands\seed_expansion.py:49:            {"first_name": "Alice", "last_name": "Carter",  "department": "Academics",  "role": "Teacher",           "email": "a.carter@crown.example",  "date_hired": date(2018, 8, 15), "active": True},
backend\core\management\commands\seed_expansion.py:50:            {"first_name": "Bob",   "last_name": "Nguyen",  "department": "Operations", "role": "Facilities Manager","email": "b.nguyen@crown.example",  "date_hired": date(2020, 1, 7),  "active": True},
backend\core\management\commands\seed_expansion.py:51:            {"first_name": "Carol", "last_name": "Davis",   "department": "Finance",    "role": "Accountant",        "email": "c.davis@crown.example",   "date_hired": date(2019, 3, 20), "active": True},
backend\core\management\commands\seed_expansion.py:52:            {"first_name": "Dan",   "last_name": "Smith",   "department": "Academics",  "role": "Teacher",           "email": "d.smith@crown.example",   "date_hired": date(2016, 8, 20), "active": False},
backend\core\management\commands\seed_expansion.py:53:            {"first_name": "Eve",   "last_name": "Johnson", "department": "Admissions", "role": "Counselor",         "email": "e.johnson@crown.example", "date_hired": date(2021, 6, 1),  "active": True},
frontend/dashboards/src\lib\releaseApi.ts:16:    config.headers["X-School-Id"] = schoolId;
backend\core\management\commands\seed_demo_school.py:365:        def ensure_staff(first, last, email, role_type):
backend\core\management\commands\seed_demo_school.py:369:                defaults={"first_name": first, "last_name": last, "role_type": role_type, "status": "ACTIVE"},
backend\core\management\commands\seed_demo_school.py:387:        def ensure_role(user, role_code):
backend\core\management\commands\seed_demo_school.py:388:            UserRole.objects.get_or_create(school=school, user=user, role_code=role_code)
backend\core\management\commands\seed_demo_school.py:400:        ensure_role(head_user, "HEAD_OF_SCHOOL")
backend\core\management\commands\seed_demo_school.py:401:        ensure_role(finance_user, "FINANCE_DIRECTOR")
backend\core\management\commands\seed_demo_school.py:402:        ensure_role(aid_user, "AID_DIRECTOR")
backend\core\management\commands\seed_demo_school.py:403:        ensure_role(registrar_user, "REGISTRAR")
backend\crown_api\system_views.py:12:from rest_framework.permissions import IsAdminUser
backend\crown_api\system_views.py:26:    permission_classes = [IsAdminUser]
backend\crown_api\system_views.py:77:    school_id = request.headers.get("X-School-Id") or request.GET.get("school_id") or ""
backend\crown_api\system_views.py:79:        return JsonResponse({"detail": "Missing school_id (send X-School-Id or ?school_id=...)"}, status=400)
backend\crown_api\system_views.py:308:from rest_framework.decorators import api_view, permission_classes
backend\crown_api\system_views.py:309:from rest_framework.permissions import IsAuthenticated
backend\crown_api\system_views.py:313:@permission_classes([IsAuthenticated])
backend\crown_api\system_views.py:319:    - user info (id, email, is_staff, role)
backend\crown_api\system_views.py:320:    - resolved tenant (school_id from middleware)
backend\crown_api\system_views.py:333:        "role": getattr(user, "role", None),
backend\crown_api\system_views.py:338:    tenant_data = {
backend\crown_api\system_views.py:339:        "resolved_school_id": str(request.tenant_school_id) if hasattr(request, "tenant_school_id") and request.tenant_school_id else None,
backend\crown_api\system_views.py:340:        "resolution_source": getattr(request, "_tenant_resolution_source", None),
backend\crown_api\system_views.py:341:        "header_present": getattr(request, "_tenant_header_present", False),
backend\crown_api\system_views.py:358:        "tenant": tenant_data,
frontend/dashboards/src\lib\authGuard.js:17: * "crown.role" / "crown.school.id" values.  This allows Playwright smoke tests
frontend/dashboards/src\lib\authGuard.js:40:    role: _stored("crown.role") ?? "admin",
frontend/dashboards/src\lib\authGuard.js:47: * @returns {object|null}      - session payload { email, role, school_id } or null
backend\comms_wizard\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
frontend/dashboards/src\lib\api.js:18:  // If you need tenant scoping toggles, that belongs INSIDE authClient, not here.
backend\crown_api\shell_backend_contract.py:12:            "schoolHeaderName": "X-School-Id",
backend\crown_api\shell_backend_contract.py:36:            "schoolHeaderName": "X-School-Id",
backend\crown_api\shell_backend_contract.py:60:            "schoolHeaderName": "X-School-Id",
backend\crown_api\shell_backend_contract.py:84:            "schoolHeaderName": "X-School-Id",
backend\crown_api\shell_backend_contract.py:108:            "schoolHeaderName": "X-School-Id",
backend\crown_api\settings.py.phase9_backup_20260508_172135:139:# When True, TenantHeaderRequiredMiddleware requires X-School-Id on /api/v1/* routes.
backend\crown_api\settings.py.phase9_backup_20260508_172135:236:    # Platform layer (multi-tenant SaaS scaling)
backend\crown_api\settings.py.phase9_backup_20260508_172135:237:    'tenants.apps.TenantsConfig',
backend\crown_api\settings.py.phase9_backup_20260508_172135:267:    'core.tenant_header_middleware.TenantHeaderRequiredMiddleware',  # Tenant guard ├â┬ó├óΓÇÜ┬¼├óΓé¼┬¥ after auth so user.school_id is available for header-less fallback
backend\crown_api\settings.py.phase9_backup_20260508_172135:268:    'crown_api.tenant_middleware.TenantContextMiddleware',  # Tenant resolution (after JWT auth)
backend\crown_api\settings.py.phase9_backup_20260508_172135:383:        "rest_framework.permissions.IsAuthenticated",
backend\crown_api\settings.py.phase9_backup_20260508_172117:139:# When True, TenantHeaderRequiredMiddleware requires X-School-Id on /api/v1/* routes.
backend\crown_api\settings.py.phase9_backup_20260508_172117:236:    # Platform layer (multi-tenant SaaS scaling)
backend\crown_api\settings.py.phase9_backup_20260508_172117:237:    'tenants.apps.TenantsConfig',
backend\crown_api\settings.py.phase9_backup_20260508_172117:267:    'core.tenant_header_middleware.TenantHeaderRequiredMiddleware',  # Tenant guard ├â┬ó├óΓÇÜ┬¼├óΓé¼┬¥ after auth so user.school_id is available for header-less fallback
backend\crown_api\settings.py.phase9_backup_20260508_172117:268:    'crown_api.tenant_middleware.TenantContextMiddleware',  # Tenant resolution (after JWT auth)
backend\crown_api\settings.py.phase9_backup_20260508_172117:383:        "rest_framework.permissions.IsAuthenticated",
backend\comms\teams_service.py:4:Requires the app to have ChannelMessage.Send application permission
backend\crown_api\settings.py.phase9_backup_20260508_155955:139:# When True, TenantHeaderRequiredMiddleware requires X-School-Id on /api/v1/* routes.
backend\crown_api\settings.py.phase9_backup_20260508_155955:220:    # Platform layer (multi-tenant SaaS scaling)
backend\crown_api\settings.py.phase9_backup_20260508_155955:221:    'tenants.apps.TenantsConfig',
backend\crown_api\settings.py.phase9_backup_20260508_155955:251:    'core.tenant_header_middleware.TenantHeaderRequiredMiddleware',  # Tenant guard ├â┬ó├óΓÇÜ┬¼├óΓé¼┬¥ after auth so user.school_id is available for header-less fallback
backend\crown_api\settings.py.phase9_backup_20260508_155955:252:    'crown_api.tenant_middleware.TenantContextMiddleware',  # Tenant resolution (after JWT auth)
backend\crown_api\settings.py.phase9_backup_20260508_155955:367:        "rest_framework.permissions.IsAuthenticated",
backend\athletics\tests\test_athletics.py:4:39 passing target: URL routing, permissions, CRUD, tenant isolation,
backend\athletics\tests\test_athletics.py:52:def _mk_user(role="coach"):
backend\athletics\tests\test_athletics.py:54:        username=f"{role}_{uuid.uuid4().hex[:8]}",
backend\athletics\tests\test_athletics.py:518:# 11. Tenant isolation
backend\athletics\tests\test_athletics.py:534:    def test_season_cross_tenant_hidden(self):
backend\athletics\tests\test_athletics.py:540:    def test_event_cross_tenant_hidden(self):
backend\crown_api\settings.py.phase12_duplicate_block_backup_20260508_175040:139:# When True, TenantHeaderRequiredMiddleware requires X-School-Id on /api/v1/* routes.
backend\crown_api\settings.py.phase12_duplicate_block_backup_20260508_175040:236:    # Platform layer (multi-tenant SaaS scaling)
backend\crown_api\settings.py.phase12_duplicate_block_backup_20260508_175040:237:    'tenants.apps.TenantsConfig',
backend\crown_api\settings.py.phase12_duplicate_block_backup_20260508_175040:267:    'core.tenant_header_middleware.TenantHeaderRequiredMiddleware',  # Tenant guard ├â┬ó├óΓÇÜ┬¼├óΓé¼┬¥ after auth so user.school_id is available for header-less fallback
backend\crown_api\settings.py.phase12_duplicate_block_backup_20260508_175040:268:    'crown_api.tenant_middleware.TenantContextMiddleware',  # Tenant resolution (after JWT auth)
backend\crown_api\settings.py.phase12_duplicate_block_backup_20260508_175040:383:        "rest_framework.permissions.IsAuthenticated",
backend\term_structure_wizard\views.py:17:  - Tenant: every lookup filtered on school_id from X-School-Id header
backend\term_structure_wizard\views.py:44:    permission_classes,
backend\term_structure_wizard\views.py:46:from rest_framework.permissions import IsAuthenticated
backend\term_structure_wizard\views.py:235:@permission_classes(_PERM)
backend\term_structure_wizard\views.py:258:@permission_classes(_PERM)
backend\term_structure_wizard\views.py:302:@permission_classes(_PERM)
backend\term_structure_wizard\views.py:344:@permission_classes(_PERM)
backend\term_structure_wizard\views.py:484:@permission_classes(_PERM)
backend\crown_api\settings.py:145:# When True, TenantHeaderRequiredMiddleware requires X-School-Id on /api/v1/* routes.
backend\crown_api\settings.py:229:    # Platform layer (multi-tenant SaaS scaling)
backend\crown_api\settings.py:230:    'tenants.apps.TenantsConfig',
backend\crown_api\settings.py:260:    'core.tenant_header_middleware.TenantHeaderRequiredMiddleware',  # Tenant guard ├â┬ó├óΓÇÜ┬¼├óΓé¼┬¥ after auth so user.school_id is available for header-less fallback
backend\crown_api\settings.py:261:    'crown_api.tenant_middleware.TenantContextMiddleware',  # Tenant resolution (after JWT auth)
backend\crown_api\settings.py:376:        "rest_framework.permissions.IsAuthenticated",
backend\crown_api\serializers_households.py:21:            "role",
backend\crown_api\seeded_contract_probe.py:7:from crown_api.tenant_seed_adapter import (
backend\crown_api\seeded_contract_probe.py:65:                "schoolHeaderName": str(entry.get("schoolHeaderName") or "X-School-Id").strip(),
backend\crown_api\seeded_contract_probe.py:136:    school_header_name = str(entry.get("schoolHeaderName") or "X-School-Id").strip()
backend\crown_api\seeded_contract_probe.py:179:        errors.append("endpoint returned 404 with seeded tenant context")
backend\crown_api\seeded_contract_probe.py:181:        errors.append("endpoint returned 5xx with seeded tenant context")
backend\crown_api\seeded_contract_probe.py:183:        errors.append("endpoint redirected with seeded tenant context")
backend\core\management\commands\print_shell_backend_seeded_proof.py:13:    help = "Print seeded tenant shell/backend proof findings."
backend\core\management\commands\print_shell_backend_seeded_proof.py:33:        self.stdout.write(self.style.SUCCESS("No seeded tenant contract failures found."))
backend\term_structure_wizard\tests\test_views.py:8:  - Tenant isolation (X-School-Id required; mismatch ΓåÆ 404)
backend\term_structure_wizard\tests\test_views.py:152:# 2. Tenant isolation
backend\term_structure_wizard\tests\test_views.py:503:    def test_cross_tenant_isolation(self):
backend\crown_api\release_gate_views.py:3:from rest_framework.permissions import IsAuthenticated
backend\crown_api\release_gate_views.py:7:from crown_api.exports.permissions import IsFinanceRole
backend\crown_api\release_gate_views.py:13:    permission_classes = [IsAuthenticated]
backend\crown_api\release_gate_views.py:31:    permission_classes = [IsAuthenticated]
backend\crown_api\release_gate_views.py:49:    permission_classes = [IsAuthenticated, IsFinanceRole]
backend\crown_api\release_gate_views.py:76:    permission_classes = [IsAuthenticated, IsFinanceRole]
backend\crown_api\rbac_views.py:3:from .permissions import require_roles
backend\crown_api\rbac_views.py:6:@require_roles(["admin", "finance"])
backend\crown_api\permissions.py:6:def _get_user_role(request):
backend\crown_api\permissions.py:8:    Crown demo-friendly role resolution.
backend\crown_api\permissions.py:10:      1) request.user.role (if your User model has it)
backend\crown_api\permissions.py:17:    HARDENING: role values are normalized to lowercase for consistent comparisons.
backend\crown_api\permissions.py:25:    # 1) user.role
backend\crown_api\permissions.py:27:    role = _norm(getattr(user, "role", None))
backend\crown_api\permissions.py:28:    if role:
backend\crown_api\permissions.py:29:        return role
backend\crown_api\permissions.py:49:def require_roles(allowed_roles):
backend\crown_api\permissions.py:51:    Decorator enforcing that request has one of allowed roles.
backend\crown_api\permissions.py:52:    Returns JSON 403 with required_roles and actual_role.
backend\crown_api\permissions.py:54:    allowed = set(str(r) for r in allowed_roles)
backend\crown_api\permissions.py:59:            actual = _get_user_role(request)
backend\crown_api\permissions.py:65:                        "required_roles": sorted(list(allowed)),
backend\crown_api\permissions.py:66:                        "actual_role": actual,
backend\crown_api\ops_views.py:18:from rest_framework.decorators import api_view, permission_classes
backend\crown_api\ops_views.py:19:from rest_framework.permissions import AllowAny
backend\crown_api\ops_views.py:61:@permission_classes([AllowAny])
backend\crown_api\ops_views.py:112:    # Bind tenant context
backend\crown_api\ops_views.py:119:    # Ensure CI user has director role for smoke tests
backend\crown_api\ops_views.py:122:        defaults={"school": school, "role_code": "AID_DIRECTOR"}
backend\crown_api\models_households.py:61:    role = models.CharField(max_length=32, choices=ROLE_CHOICES)
backend\crown_api\models_households.py:67:                fields=["household", "person", "role"],
backend\crown_api\models_households.py:68:                name="uniq_household_person_role",
backend\crown_api\models_households.py:74:                    role__in=GUARDIAN_ROLES,
backend\crown_api\models_households.py:79:        ordering = ["household", "role", "person__last_name", "person__first_name"]
backend\crown_api\models_households.py:83:        if self.is_primary and self.role not in set(GUARDIAN_ROLES):
backend\crown_api\models_households.py:84:            raise ValidationError({"is_primary": "Primary is only valid for guardian roles."})
backend\crown_api\models_households.py:87:        return f"{self.household} - {self.person} ({self.role})"
backend\outreach\migrations\0001_initial_outreach.py:15:        ('core', '0005_crown_permission_engine'),
backend\crown_api\dashboards\views.py:4:from rest_framework.permissions import AllowAny
backend\crown_api\dashboards\views.py:8:from core.permissions import user_has_permission
backend\crown_api\dashboards\views.py:14:from rest_framework.decorators import api_view, permission_classes
backend\crown_api\dashboards\views.py:15:from rest_framework.permissions import IsAuthenticated
backend\crown_api\dashboards\views.py:26:    """Resolve school from X-School-Id header only; never uses user.school_id fallback."""
backend\crown_api\dashboards\views.py:30:        raise ValidationError({"detail": "X-School-Id header is required."})
backend\crown_api\dashboards\views.py:34:        raise ValidationError({"detail": "Invalid X-School-Id (must be a UUID)."})
backend\crown_api\dashboards\views.py:38:    # Cross-tenant check: non-staff users may only access their own school
backend\crown_api\dashboards\views.py:49:@permission_classes([IsAuthenticated])
backend\crown_api\dashboards\views.py:51:    """Return authenticated user's school context and roles."""
backend\crown_api\dashboards\views.py:54:    roles = list(
backend\crown_api\dashboards\views.py:55:        UserRole.objects.filter(user=request.user, school=school).values_list('role_code', flat=True)
backend\crown_api\dashboards\views.py:57:    if not roles:
backend\crown_api\dashboards\views.py:61:            roles = ['SCHOOL_MEMBER']
backend\crown_api\dashboards\views.py:64:        "roles": roles,
backend\crown_api\dashboards\views.py:71:@permission_classes([IsAuthenticated])
backend\crown_api\dashboards\views.py:92:@permission_classes([IsAuthenticated])
backend\crown_api\dashboards\views.py:108:@permission_classes([IsAuthenticated])
backend\crown_api\dashboards\views.py:117:    permission_classes = [AllowAny]
backend\crown_api\dashboards\views.py:128:            if not user_has_permission(user, 'spiritual_life.view', school=school):
backend\crown_api\dashboards\urls.py:11:    # Role contract API endpoints (test_dashboards_role_contract)
backend\crown_api\dashboards\tenant.py:12:    """Dashboards require an explicit tenant header (no fallback to user.school_id).
backend\crown_api\dashboards\tenant.py:14:    - Missing tenant header -> 400
backend\crown_api\dashboards\tenant.py:24:                        f"Missing {CANONICAL_SCHOOL_HEADER} header (tenant context required)."
backend\crown_api\dashboards\summary.py:2:Dashboard summary service ΓÇö builds role-specific widget payloads.
backend\crown_api\dashboards\summary.py:10:- All DB queries are scoped to school_id (tenant safety).
backend\crown_api\dashboards\summary.py:29:def _quick_actions(role: str) -> dict:
backend\crown_api\dashboards\summary.py:31:    actions_by_role = {
backend\crown_api\dashboards\summary.py:65:    return {"actions": actions_by_role.get(role, default_actions)}
backend\crown_api\dashboards\summary.py:190:# Widget builders per role ΓÇö returns sorted list of widget dicts.
backend\crown_api\dashboards\summary.py:194:    # Present for ALL roles
backend\crown_api\dashboards\summary.py:231:def build_widgets_for_role(role: str, school_id: str) -> list[dict]:
backend\crown_api\dashboards\summary.py:232:    """Build the ordered widget list for a role, populating data fields."""
backend\crown_api\dashboards\summary.py:236:        "quick_actions": _quick_actions(role),
backend\crown_api\dashboards\summary.py:246:    if role in ("admin", "registrar"):
backend\crown_api\dashboards\summary.py:258:    if role == "teacher":
backend\crown_api\dashboards\summary.py:271:    if role == "parent":
backend\crown_api\dashboards\summary.py:281:    if role == "student":
backend\crown_api\dashboards\summary.py:290:    if role == "finance":
backend\crown_api\dashboards\summary.py:309:def build_dashboard_summary(role: str, school_id: str) -> dict:
backend\crown_api\dashboards\summary.py:311:        "role": role,
backend\crown_api\dashboards\summary.py:314:        "widgets": build_widgets_for_role(role, str(school_id)),
backend\crown_api\dashboards\serializers.py:10:    roles = serializers.ListField(child=serializers.CharField())
backend\crown_api\dashboards\serializers.py:32:    role = serializers.CharField()
backend\athletics\migrations\0001_initial_athletics.py:15:        ('core', '0005_crown_permission_engine'),
backend\term_structure_wizard\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
backend\crown_api\dashboards\sample_payloads.py:445:            alert('2 tenant data migrations are stalled', 'High', 'Platform engineering must unblock by EOD.'),
backend\crown_api\dashboards\sample_payloads.py:447:            alert('One tenant has an expired SSL certificate in 14 days', 'Low', 'Renew before expiration.'),
backend\crown_api\dashboards\sample_payloads.py:450:            queue_item('Unblock stalled tenant data migrations'),
backend\crown_api\dashboards\sample_payloads.py:452:            queue_item('Initiate SSL certificate renewal for flagged tenant'),
backend\crown_api\dashboards\sample_payloads.py:518:            alert('3 open positions have no active candidate pipeline', 'Medium', 'Post roles and initiate sourcing.'),
backend\crown_api\dashboards\sample_payloads.py:523:            queue_item('Post 3 open roles and activate hiring pipeline'),
backend\crown_api\dashboards\sample_payloads.py:663:            alert('Fine arts field trip permission slips are at 72% return', 'Low', 'Send final reminder to families.'),
backend\crown_api\dashboards\sample_payloads.py:668:            queue_item('Send field trip permission slip reminders'),
backend\crown_api\migrations\0009_crownuser.py:21:                ('role', models.CharField(db_index=True, max_length=50)),
backend\crown_api\migrations\0008_auditevent.py:22:                ('actor_role', models.CharField(blank=True, max_length=50, null=True)),
backend\core\demo\heritage_demo_credentials.json:8:    "tenant_prefill": "heritage-christian-academy",
backend\core\demo\heritage_demo_credentials.json:10:      {"key": "school_admin", "label": "School Administrator", "role": "admin", "email": "admin@heritage.example.org", "password": "CrownDemo!2026", "display_name": "Nathan Brooks"},
backend\core\demo\heritage_demo_credentials.json:11:      {"key": "head_of_school", "label": "Head of School", "role": "executive_admin", "email": "miriam.caldwell@heritage.example.org", "password": "CrownDemo!2026", "display_name": "Miriam Caldwell"},
backend\core\demo\heritage_demo_credentials.json:12:      {"key": "admissions_director", "label": "Admissions Director", "role": "admissions_admin", "email": "admissions@heritage.example.org", "password": "CrownDemo!2026", "display_name": "Samuel Hayes"},
backend\core\demo\heritage_demo_credentials.json:13:      {"key": "registrar", "label": "Registrar", "role": "registrar", "email": "registrar@heritage.example.org", "password": "CrownDemo!2026", "display_name": "Monica Dean"},
backend\core\demo\heritage_demo_credentials.json:14:      {"key": "finance_director", "label": "Finance Director", "role": "finance_admin", "email": "finance@heritage.example.org", "password": "CrownDemo!2026", "display_name": "Olivia Mercer"},
backend\core\demo\heritage_demo_credentials.json:15:      {"key": "teacher", "label": "Teacher", "role": "teacher", "email": "teacher.lower@heritage.example.org", "password": "CrownDemo!2026", "display_name": "Hannah Porter"},
backend\core\demo\heritage_demo_credentials.json:16:      {"key": "parent", "label": "Parent", "role": "parent", "email": "parent.reed@heritage.example.org", "password": "CrownDemo!2026", "display_name": "Daniel Reed"},
backend\core\demo\heritage_demo_credentials.json:17:      {"key": "student", "label": "Student", "role": "student", "email": "student.avery.reed11@heritage.example.org", "password": "CrownDemo!2026", "display_name": "Avery Reed"}
backend\crown_api\migrations\0001_initial.py:69:                ('role', models.CharField(choices=[('PRIMARY_GUARDIAN', 'Primary Guardian'), ('GUARDIAN', 'Guardian'), ('FINANCIALLY_RESPONSIBLE', 'Financially Responsible'), ('EMERGENCY_CONTACT', 'Emergency Contact'), ('AUTHORIZED_PICKUP', 'Authorized Pickup')], max_length=32)),
backend\crown_api\migrations\0001_initial.py:75:                'ordering': ['household', 'role', 'person__last_name', 'person__first_name'],
backend\crown_api\migrations\0001_initial.py:76:                'constraints': [models.UniqueConstraint(fields=('household', 'person', 'role'), name='uniq_household_person_role'), models.UniqueConstraint(condition=models.Q(('is_primary', True), ('role__in', ['PRIMARY_GUARDIAN', 'GUARDIAN'])), fields=('household',), name='uniq_household_primary_guardian')],
backend\crown_api\audit_models.py:16:    # Optional multi-tenant fields (safe to be null until full tenancy is wired)
backend\crown_api\audit_models.py:19:    actor_role = models.CharField(max_length=50, null=True, blank=True)
backend\crown_api\audit.py:8:from crown_api.permissions import _get_user_role
backend\crown_api\audit.py:14:        hdr = request.headers.get("X-School-Id")
backend\crown_api\audit.py:49:        actor_role=_get_user_role(request),
backend\crown_api\dashboards\finance.py:4:from rest_framework.permissions import IsAuthenticated
backend\crown_api\dashboards\finance.py:9:from crown_api.dashboards.tenant import get_dashboard_school_id
backend\crown_api\dashboards\finance.py:16:    permission_classes = [IsAuthenticated]
backend\crown_api\dashboards\admissions.py:8:from rest_framework.permissions import IsAuthenticated
backend\crown_api\dashboards\admissions.py:14:from crown_api.dashboards.tenant import get_dashboard_school_id
backend\crown_api\dashboards\admissions.py:20:    permission_classes = [IsAuthenticated]
backend\crown_api\dashboards\academics.py:7:from rest_framework.permissions import IsAuthenticated
backend\crown_api\dashboards\academics.py:11:from crown_api.dashboards.tenant import get_dashboard_school_id
backend\crown_api\dashboards\academics.py:32:    - Requires X-School-Id header (or user.school_id)
backend\crown_api\dashboards\academics.py:33:    - Missing tenant ΓåÆ 400 MissingSchoolContext
backend\crown_api\dashboards\academics.py:39:    permission_classes = [IsAuthenticated]
backend\crown_api\metrics_views.py:25:from core.permissions import require_permission
backend\crown_api\metrics_views.py:35:@require_permission("admin.view")
backend\crown_api\metrics_views.py:71:@require_permission("board.view")
backend\crown_api\metrics_views.py:113:@require_permission("finance.view")
backend\crown_api\metrics_views.py:156:@require_permission("teacher.view")
backend\crown_api\metrics_views.py:176:@require_permission("parent.view")
backend\crown_api\metrics_views.py:210:@require_permission("student.view")
backend\crown_api\metrics_views.py:234:@require_permission("it.view")
backend\crown_api\metrics_views.py:259:@require_permission("financial_aid.view")
backend\crown_api\metrics_views.py:286:@require_permission("marketing.view")
backend\crown_api\metrics_views.py:315:@require_permission("spiritual_life.view")
backend\crown_api\metrics_views.py:340:@require_permission("office.view")
backend\crown_api\metrics_views.py:372:@require_permission("health.view")
backend\crown_api\metrics_views.py:412:@require_permission("counseling.view")
backend\crown_api\metrics_views.py:449:@require_permission("food.view")
backend\crown_api\metrics_views.py:492:@require_permission("athletics.view")
backend\crown_api\metrics_views.py:529:@require_permission("advancement.view")
backend\crown_api\metrics_views.py:568:@require_permission("transportation.view")
backend\crown_api\metrics_views.py:601:@require_permission("facilities.view")
backend\crown_api\metrics_views.py:641:@require_permission("security.view")
backend\crown_api\metrics_views.py:676:@require_permission("academic_support.view")
backend\crown_api\metrics_views.py:719:@require_permission("fine_arts.view")
backend\crown_api\metrics_views.py:756:@require_permission("library.view")
backend\crown_api\metrics_views.py:797:@require_permission("extended_care.view")
backend\crown_api\metrics_views.py:835:@require_permission("registrar.view")
backend\crown_api\metrics_views.py:875:@require_permission("communications.view")
backend\crown_api\metrics_views.py:913:@require_permission("pd.view")
backend\crown_api\metrics_views.py:951:@require_permission("student_services.view")
backend\tenants\test_smoke.py:6:        from tenants.apps import TenantsConfig
backend\tenants\test_smoke.py:8:        self.assertEqual(TenantsConfig.name, "tenants")
backend\tenants\test_smoke.py:10:    def test_tenant_context_importable(self):
backend\tenants\test_smoke.py:11:        from tenants import tenant_context
backend\tenants\test_smoke.py:13:        self.assertIsNotNone(tenant_context)
backend\crown_api\api_urls.py:159:    # Phase 2 invariants ΓÇö read-only sanity check, tenant-scoped
backend\tenants\tenant_context.py:6:structured access to the resolved tenant rather than a bare UUID.
backend\tenants\tenant_context.py:19:    """Resolved tenant for the current request."""
backend\tenants\tenant_context.py:33:    Returns None (or raises) if no tenant can be resolved and required=True.
backend\tenants\tenant_context.py:40:def resolve_tenant(request: HttpRequest) -> Optional[TenantContext]:
backend\tenants\tenant_context.py:42:    Return a TenantContext for the current request, or None if no tenant is set.
backend\crown_api\billing_api\views.py:10:from rest_framework.permissions import IsAuthenticated
backend\crown_api\billing_api\views.py:20:from .permissions import IsFinanceRole
backend\crown_api\billing_api\views.py:47:    permission_classes = [IsAuthenticated]
backend\crown_api\billing_api\views.py:120:    permission_classes = [IsAuthenticated]
backend\crown_api\billing_api\views.py:217:    permission_classes = [IsAuthenticated]
backend\crown_api\billing_api\views.py:282:    permission_classes = [IsAuthenticated, IsFinanceRole]
backend\comms\management\commands\seed_comms_demo.py:22:    "Please complete the permission slip by Wednesday. Let us know if you have questions.",
backend\crown_api\api\wizards.py:9:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\crown_api\api\wizards.py:10:from rest_framework.permissions import IsAuthenticated
backend\crown_api\api\wizards.py:23:@permission_classes(_PERM)
backend\crown_api\management\commands\reset_demo_passwords.py:13:    {"username": "teacher", "email": "teacher@crown-demo.local", "role_code": "TEACHER"},
backend\crown_api\management\commands\reset_demo_passwords.py:14:    {"username": "parent", "email": "parent@crown-demo.local", "role_code": "PARENT"},
backend\crown_api\management\commands\reset_demo_passwords.py:70:                    role_code=spec["role_code"],
backend\crown_api\admin.py:49:    list_display = ("household", "person", "role", "is_primary", "created_at")
backend\crown_api\admin.py:50:    list_filter = ("role", "is_primary")
backend\crown_api\management\commands\proof_phase4_gradebook_demo.py:107:                "X-School-Id": str(school.id),
backend\crown_api\management\commands\proof_phase3_runtime.py:21:    2. Tenant header enforced (request without X-School-Id rejected)
backend\crown_api\management\commands\proof_phase3_runtime.py:22:    3. Ledger invariants endpoint responds 200 with auth + tenant
backend\crown_api\management\commands\proof_phase3_runtime.py:175:            "X-School-Id": str(school_id),
backend\crown_api\management\commands\proof_phase3_runtime.py:180:        # 2. Tenant header enforcement: same endpoint WITHOUT X-School-Id
backend\crown_api\management\commands\proof_phase3_runtime.py:184:        no_tenant_headers = {"Authorization": f"Bearer {token}"}
backend\crown_api\management\commands\proof_phase3_runtime.py:185:        st2, bd2 = _req("GET", inv_url, headers=no_tenant_headers)
backend\crown_api\management\commands\proof_phase3_runtime.py:188:                "tenant_header_required", False, st2,
backend\crown_api\management\commands\proof_phase3_runtime.py:189:                "Expected rejection without X-School-Id but got 200 ΓÇö tenant enforcement missing"
backend\crown_api\management\commands\proof_phase3_runtime.py:192:            raise CommandError("PHASE3_RUNTIME_PROOF: FAIL at tenant_header_required")
backend\crown_api\management\commands\proof_phase3_runtime.py:193:        results.append(StepResult("tenant_header_required", True, st2, "tenant header enforced"))
backend\crown_api\management\commands\proof_phase3_runtime.py:196:        # 3. Ledger invariants (with auth + tenant)
backend\crown_api\billing_api\tests\test_school_override_header.py:26:    # Non-staff users must not be able to override tenant context.
backend\tenants\models.py:5:core.School is the tenant root entity ΓÇö never duplicate it here.
backend\tenants\models.py:7:TenantProfile: operational/billing fields per school tenant.
backend\tenants\models.py:18:    Adds fields required for multi-tenant SaaS operations that are
backend\tenants\models.py:44:    # Link back to the authoritative tenant entity
backend\tenants\models.py:48:        related_name="tenant_profile",
backend\crown_api\billing_api\tests\test_payments_record_multi_alloc_api.py:129:def test_record_payment_multi_allocation_requires_finance_role_403(non_finance_client):
backend\outreach\api\views.py:35:from outreach.api.permissions import IsStudentOrStaff, IsStaffOnly, _is_coordinator
backend\outreach\api\views.py:59:    permission_classes = [IsStaffOnly]
backend\outreach\api\views.py:70:    permission_classes = [IsStaffOnly]
backend\outreach\api\views.py:79:    permission_classes = [IsStaffOnly]
backend\outreach\api\views.py:88:    permission_classes = [IsStaffOnly]
backend\outreach\api\views.py:97:    permission_classes = [IsStaffOnly]
backend\outreach\api\views.py:108:    permission_classes = [IsStaffOnly]
backend\outreach\api\views.py:120:    permission_classes = [IsStudentOrStaff]
backend\outreach\api\views.py:156:        permission_classes=[IsStaffOnly]
backend\outreach\api\views.py:175:        permission_classes=[IsStaffOnly]
backend\outreach\api\views.py:194:        permission_classes=[IsStaffOnly]
backend\outreach\api\views.py:216:        permission_classes=[IsStaffOnly]
backend\outreach\api\views.py:298:        permission_classes=[IsStaffOnly]
backend\crown_api\management\commands\ensure_ci_user.py:57:                "role": "director",
backend\crown_api\billing_api\tests\test_payments_record_api.py:81:def test_record_payment_requires_finance_role(non_finance_client):
backend\crown_api\lifecycle_contract_probe.py:7:from crown_api.tenant_seed_adapter import (
backend\crown_api\lifecycle_contract_probe.py:78:                "schoolHeaderName": str(entry.get("schoolHeaderName") or "X-School-Id").strip(),
backend\crown_api\lifecycle_contract_probe.py:215:    school_header_name = str(entry.get("schoolHeaderName") or "X-School-Id").strip()
backend\crown_api\jwt_utils.py:77:def build_access_token(*, user_id: str, email: str, role: str, school_id: Optional[str], ttl_seconds: int = 900) -> str:
backend\crown_api\jwt_utils.py:83:        "role": role,
backend\athletics\api\views.py:19:from athletics.api.permissions import IsAthleticDirector, IsCoachOrAD
backend\athletics\api\views.py:32:# Crown canonical tenant helper
backend\athletics\api\views.py:46:    permission_classes = [IsAthleticDirector]
backend\athletics\api\views.py:57:    permission_classes = [IsAthleticDirector]
backend\athletics\api\views.py:68:    permission_classes = [IsAthleticDirector]
backend\athletics\api\views.py:82:    permission_classes = [IsAthleticDirector]
backend\athletics\api\views.py:93:    permission_classes = [IsAthleticDirector]
backend\athletics\api\views.py:109:    permission_classes = [IsAthleticDirector]
backend\athletics\api\views.py:123:    permission_classes = [IsCoachOrAD]
backend\athletics\api\views.py:160:    permission_classes = [IsCoachOrAD]
backend\athletics\api\views.py:181:    permission_classes = [IsCoachOrAD]
backend\crown_api\billing_api\permissions.py:1:from rest_framework.permissions import BasePermission
backend\crown_api\billing_api\permissions.py:11:    message = "You do not have permission to perform billing actions."
backend\crown_api\billing_api\permissions.py:13:    def has_permission(self, request, view):
backend\crown_api\billing_api\permissions.py:32:def has_finance_runtime_role(user) -> bool:
backend\crown_api\billing_api\permissions.py:44:    def has_permission(self, request, view):
backend\crown_api\billing_api\permissions.py:45:        return has_finance_runtime_role(request.user)
backend\crown_api\financial_aid_views.py:9:from rest_framework.decorators import api_view, permission_classes
backend\crown_api\financial_aid_views.py:10:from rest_framework.permissions import IsAuthenticated
backend\crown_api\financial_aid_views.py:55:    return request.headers.get("X-School-Id") or request.META.get("HTTP_X_SCHOOL_ID")
backend\crown_api\financial_aid_views.py:73:@permission_classes([IsAuthenticated])
backend\crown_api\financial_aid_views.py:77:    Tenant-scoped via X-School-Id.
backend\crown_api\financial_aid_views.py:82:            {"detail": "Missing X-School-Id header."},
backend\crown_api\financial_aid_views.py:95:    # Base queryset (tenant-scoped AidApplication).
backend\crown_api\billing_api\drf_views.py:10:from rest_framework.permissions import IsAuthenticated
backend\crown_api\billing_api\drf_views.py:21:    permission_classes = [IsAuthenticated]
backend\crown_api\auth_views.py:47:        role=str(user.role).strip().lower(),
backend\crown_api\auth_views.py:87:        role=str(user.role).strip().lower(),
backend\crown_api\auth_views.py:104:                "role": getattr(u, "role", None),
backend\crown_api\auth_models.py:16:    # Tenant + role
backend\crown_api\auth_models.py:18:    role = models.CharField(max_length=50, db_index=True)
backend\crown_api\auth_models.py:28:        return f"{self.email} ({self.role})"
backend\crown_api\auth_middleware.py:32:      - Sets request.user with {id, email, role, school_id, is_authenticated=True}
backend\crown_api\auth_middleware.py:56:                    role=p.get("role"),
backend\tenants\migrations\0001_initial.py:13:        ('core', '0005_crown_permission_engine'),
backend\tenants\migrations\0001_initial.py:47:                ('school', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='tenant_profile', to='core.school')),
backend\crown_api\authenticated_contract_probe.py:64:                "schoolHeaderName": str(entry.get("schoolHeaderName") or "X-School-Id").strip(),
backend\crown_api\authenticated_contract_probe.py:226:    school_header_name = str(entry.get("schoolHeaderName") or "X-School-Id").strip()
backend\crown_api\audit_views.py:8:from crown_api.permissions import require_roles
backend\crown_api\audit_views.py:12:@require_roles(["admin", "finance"])
backend\crown_api\audit_views.py:26:    # Tenant filter: scope to school when X-School-Id header is provided.
backend\crown_api\audit_views.py:27:    # This prevents cross-tenant audit event leakage for school-scoped callers.
backend\crown_api\audit_views.py:28:    raw_sid = request.META.get("HTTP_X_SCHOOL_ID") or request.headers.get("X-School-Id")
backend\crown_api\audit_views.py:33:            return JsonResponse({"ok": False, "error": "invalid X-School-Id header"}, status=400)
backend\crown_api\audit_views.py:46:                "actor_role": e.actor_role,
backend\tenants\middleware.py:2:Tenant-aware middleware for the tenants app.
backend\tenants\middleware.py:4:NOTE: Crown2026 already ships two tenant middleware layers:
backend\tenants\middleware.py:5:  - core.tenant_header_middleware.TenantHeaderRequiredMiddleware (enforces X-School-Id header)
backend\tenants\middleware.py:6:  - crown_api.tenant_middleware.TenantContextMiddleware (resolves + attaches school to request)
backend\tenants\middleware.py:10:  TenantMiddleware ΓÇö attaches request.tenant_profile (TenantProfile ORM object) after the
backend\tenants\middleware.py:15:      secondary safety net scoped to the tenants app.
backend\tenants\middleware.py:29:# Paths that are exempt from tenant requirements (platform-level endpoints are cross-tenant)
backend\tenants\middleware.py:52:    Attaches request.tenant_profile (TenantProfile | None) after school_id is resolved.
backend\tenants\middleware.py:55:    If no school_id is resolved, or the school has no TenantProfile, tenant_profile is None.
backend\tenants\middleware.py:58:        'tenants.middleware.TenantMiddleware',
backend\tenants\middleware.py:65:        self._attach_tenant_profile(request)
backend\tenants\middleware.py:69:    def _attach_tenant_profile(request: HttpRequest) -> None:
backend\tenants\middleware.py:70:        request.tenant_profile = None
backend\tenants\middleware.py:75:            from tenants.models import TenantProfile  # noqa: PLC0415
backend\tenants\middleware.py:76:            request.tenant_profile = TenantProfile.objects.select_related("school").get(
backend\tenants\middleware.py:82:            logger.warning("TenantMiddleware: could not attach tenant_profile: %s", exc)
backend\tenants\middleware.py:94:        'tenants.middleware.RequireTenantMiddleware',
backend\crown_api\director_views.py:9:from rest_framework.decorators import api_view, permission_classes
backend\crown_api\director_views.py:10:from rest_framework.permissions import IsAuthenticated, AllowAny
backend\crown_api\director_views.py:45:    3. Users with director role codes
backend\crown_api\director_views.py:57:    # Check authenticated + role
backend\crown_api\director_views.py:64:    return UserRole.objects.filter(user_id=user_id, role_code__in=ALLOWED_ROLE_CODES).exists()
backend\crown_api\director_views.py:67:def user_has_director_role(user):
backend\crown_api\director_views.py:75:    return UserRole.objects.filter(user_id=user_id, role_code__in=ALLOWED_ROLE_CODES).exists()
backend\crown_api\director_views.py:168:@permission_classes([IsAuthenticated])
backend\crown_api\director_views.py:176:    # Check authorization (dev mode + superuser + role-based)
backend\crown_api\director_views.py:222:@permission_classes([IsAuthenticated])
backend\crown_api\director_views.py:230:    # Check authorization (dev mode + superuser + role-based)
backend\crown_api\director_views.py:280:@permission_classes([IsAuthenticated])
backend\crown_api\director_views.py:288:    # Check authorization (dev mode + superuser + role-based)
backend\crown_api\director_views.py:329:@permission_classes([IsAuthenticated])
backend\crown_api\director_views.py:469:@permission_classes([IsAuthenticated])
backend\crown_api\director_views.py:781:@permission_classes([IsAuthenticated])
backend\crown_api\director_views.py:1076:@permission_classes([IsAuthenticated])
backend\crown_api\director_views.py:1242:from rest_framework.decorators import api_view, permission_classes, authentication_classes
backend\crown_api\director_views.py:1265:@permission_classes([AllowAny])
backend\crown_api\director_router.py:4:This router determines which director "home" a user should see based on their role:
backend\crown_api\director_router.py:30:    # Get user's roles
backend\crown_api\director_router.py:31:    user_roles = UserRole.objects.filter(user_account=user).values_list('role_code', flat=True)
backend\crown_api\director_router.py:33:    # Priority order (if user has multiple director roles)
backend\crown_api\director_router.py:34:    role_mapping = {
backend\crown_api\director_router.py:42:    # Return first matching role in priority order
backend\crown_api\director_router.py:43:    for role_code, persona in role_mapping.items():
backend\crown_api\director_router.py:44:        if role_code in user_roles:
backend\crown_api\exports\model_resolver.py:50:        "user_permissions",
backend\outreach\api\permissions.py:1:from rest_framework.permissions import BasePermission, SAFE_METHODS
backend\outreach\api\permissions.py:15:    role = (request.headers.get("X-Role") or "").lower()
backend\outreach\api\permissions.py:16:    return role in ("staff", "admin", "coordinator")
backend\outreach\api\permissions.py:20:    """Allow anyone authenticated; writes restricted to recognised roles."""
backend\outreach\api\permissions.py:22:    def has_permission(self, request, view):
backend\outreach\api\permissions.py:27:        role = (request.headers.get("X-Role") or "").lower()
backend\outreach\api\permissions.py:28:        return role in ("student", "staff", "admin", "coordinator") or _is_coordinator(request)
backend\outreach\api\permissions.py:34:    def has_permission(self, request, view):
backend\crown_api\exports\views.py:8:from rest_framework.permissions import IsAuthenticated
backend\crown_api\exports\views.py:15:from .permissions import IsFinanceRole
backend\crown_api\exports\views.py:90:    permission_classes = [IsAuthenticated, IsFinanceRole]
backend\crown_api\exports\views.py:171:    permission_classes = [IsAuthenticated, IsFinanceRole]
backend\crown_api\exports\views.py:254:    permission_classes = [IsAuthenticated]
backend\crown_api\exports\views.py:381:    permission_classes = [IsAuthenticated, IsFinanceRole]
backend\crown_api\exports\views.py:432:    permission_classes = [IsAuthenticated, IsFinanceRole]
backend\crown_api\exports\views.py:490:    permission_classes = [IsAuthenticated, IsFinanceRole]
backend\crown_api\exports\views.py:579:    permission_classes = [IsAuthenticated, IsFinanceRole]
backend\crown_api\exports\views.py:767:    permission_classes = [IsAuthenticated, IsFinanceRole]
backend\crown_api\exports\views.py:1175:    permission_classes = [IsAuthenticated, IsFinanceRole]
backend\crown_api\exports\views.py:1390:    permission_classes = [IsAuthenticated, IsFinanceRole]
backend\tenants\apps.py:6:    name = "tenants"
backend\athletics\api\permissions.py:1:# backend/athletics/api/permissions.py
backend\athletics\api\permissions.py:4:from rest_framework.permissions import BasePermission
backend\athletics\api\permissions.py:17:def _role(request) -> str:
backend\athletics\api\permissions.py:27:    def has_permission(self, request, view) -> bool:
backend\athletics\api\permissions.py:33:        return _role(request) == "athletic_director"
backend\athletics\api\permissions.py:42:    def has_permission(self, request, view) -> bool:
backend\athletics\api\permissions.py:48:        return _role(request) in ("athletic_director", "coach")
backend\comms\api\views.py:4:from rest_framework import permissions, status
backend\comms\api\views.py:26:    school_id = request.headers.get("X-School-Id")
backend\comms\api\views.py:46:    permission_classes = [permissions.IsAuthenticated]
backend\comms\api\views.py:57:    permission_classes = [permissions.IsAuthenticated]
backend\comms\api\views.py:72:    permission_classes = [permissions.IsAuthenticated]
backend\comms\api\views.py:96:    permission_classes = [permissions.IsAuthenticated]
backend\comms\api\views.py:154:        school_id ΓÇö tenant UUID              (optional, defaults to smoke-test sentinel)
backend\comms\api\views.py:160:    permission_classes = [permissions.IsAuthenticated]
backend\crown_api\exports\tests\test_exports_accounting_qb_csv.py:55:    u = User.objects.create_user(username="user_qb_nonrole", password=TEST_AUTH_SECRET)
backend\crown_api\exports\tests\test_exports_accounting_qb_csv.py:75:def test_payments_qb_csv_requires_finance_role(non_finance_client):
backend\crown_api\exports\tests\test_exports_jwt_auth.py:24:def test_financial_export_allows_jwt_for_finance_role(django_user_model, finance_user):
backend\crown_api\exports\tests\test_exports_financial_csv.py:48:    u = User.objects.create_user(username="user_financial_nonrole", password=TEST_AUTH_SECRET)
backend\crown_api\exports\tests\test_exports_financial_csv.py:87:def test_ledger_charges_csv_requires_finance_role(non_finance_client):
backend\crown_api\exports\tests\test_exports_financial_csv.py:92:def test_ledger_allocations_csv_requires_finance_role(non_finance_client):
backend\crown_api\exports\tests\test_exports_financial_csv.py:97:def test_payments_csv_requires_finance_role(non_finance_client):
backend\crown_api\exports\tests\test_exports_year_end_csv.py:55:    u = User.objects.create_user(username="user_year_end_nonrole", password=TEST_AUTH_SECRET)
backend\crown_api\exports\tests\test_exports_year_end_csv.py:75:def test_year_end_tuition_paid_csv_requires_finance_role(non_finance_client):
backend\crown_api\exports\tests\test_exports_csv.py:77:def test_exports_invoices_csv_requires_finance_role(non_finance_client):
backend\crown_api\exports\tests\test_exports_csv.py:82:def test_exports_installment_schedule_csv_requires_finance_role(non_finance_client):
backend\crown_api\exports\tests\test_exports_statements_csv.py:55:    u = User.objects.create_user(username="user_statements_nonrole", password=TEST_AUTH_SECRET)
backend\crown_api\exports\tests\test_exports_statements_csv.py:75:def test_statements_csv_requires_finance_role(non_finance_client):
backend\crown_api\exports\tests\test_exports_statement_lines_csv.py:55:    u = User.objects.create_user(username="user_statement_lines_nonrole", password=TEST_AUTH_SECRET)
backend\crown_api\exports\tests\test_exports_statement_lines_csv.py:75:def test_statement_lines_csv_requires_finance_role(non_finance_client):
backend\crown_api\exports\permissions.py:1:from rest_framework.permissions import BasePermission
backend\crown_api\exports\permissions.py:11:    message = "You do not have permission to access financial exports."
backend\crown_api\exports\permissions.py:13:    def has_permission(self, request, view):
backend\classroom\views.py:4:from core.permissions import CrownModulePermission
backend\classroom\views.py:14:    school_id = request.headers.get("X-School-Id") or request.META.get("HTTP_X_SCHOOL_ID")
backend\classroom\views.py:16:        raise PermissionDenied("Missing X-School-Id header.")
backend\classroom\views.py:26:    Scoping: requires X-School-Id, filters by school.
backend\classroom\views.py:28:    permission_classes = [CrownModulePermission("classroom.view")]
backend\graduation\views_breakdown.py:6:from rest_framework.permissions import IsAuthenticated
backend\graduation\views_breakdown.py:15:    permission_classes = [IsAuthenticated]
backend\apps\compliance\services\faith_permissions.py:1:from rest_framework.permissions import BasePermission
backend\apps\compliance\services\faith_permissions.py:6:    Elevated permission gate for spiritual/pastoral data.
backend\apps\compliance\services\faith_permissions.py:9:    def has_permission(self, request, view):
backend\facops\tests\test_facops.py:7:  - Permission enforcement (unauthenticated, authenticated read-only, write roles)
backend\facops\tests\test_facops.py:9:  - Cross-tenant isolation
backend\facops\tests\test_facops.py:50:def _client(user, school: School, role: str = "admin") -> APIClient:
backend\facops\tests\test_facops.py:55:        HTTP_X_ROLE=role,
backend\facops\tests\test_facops.py:115:    def test_create_denied_for_readonly_role(self):
backend\facops\tests\test_facops.py:118:        c = _client(u, s, role="teacher")
backend\facops\tests\test_facops.py:122:    def test_cross_tenant_isolation(self):
backend\facops\tests\test_facops.py:177:    def test_asset_cross_tenant(self):
backend\facops\tests\test_facops.py:208:        c = _client(u, s, role="teacher")
backend\facops\tests\test_facops.py:249:    def test_cross_tenant_work_orders(self):
backend\facops\tests\test_facops.py:280:        c = _client(u, s, role="safety_officer")
backend\facops\tests\test_facops.py:287:        c = _client(u, s, role="safety_officer")
backend\facops\tests\test_facops.py:294:        c = _client(u, s, role="teacher")
backend\facops\tests\test_facops.py:298:    def test_cross_tenant(self):
backend\facops\tests\test_facops.py:305:        c = _client(u1, s1, role="safety_officer")
backend\facops\tests\test_facops.py:324:        c = _client(u, s, role="safety_officer")
backend\facops\tests\test_facops.py:331:        c = _client(u, s, role="safety_officer")
backend\facops\tests\test_facops.py:338:        c = _client(u, s, role="teacher")
backend\facops\tests\test_facops.py:355:        c = _client(u, s, role="safety_officer")
backend\facops\tests\test_facops.py:363:        c = _client(u, s, role="safety_officer")
backend\facops\tests\test_facops.py:367:    def test_cross_tenant(self):
backend\facops\tests\test_facops.py:374:        c = _client(u1, s1, role="safety_officer")
backend\facops\tests\test_facops.py:392:        c = _client(u, s, role="safety_officer")
backend\facops\tests\test_facops.py:399:        c = _client(u, s, role="safety_officer")
backend\facops\tests\test_facops.py:411:        c = _client(u, s, role="safety_officer")
backend\facops\tests\test_facops.py:418:        c = _client(u, s, role="teacher")
backend\facops\tests\test_facops.py:455:        c = _client(u, s, role="safety_officer")
backend\graduation\views.py:5:from core.tenant_models import get_current_school
backend\graduation\views.py:14:    permission_classes = []
backend\graduation\views.py:19:            # If tenant middleware is configured, this should never happen; fail closed anyway.
backend\apps\compliance\services\consent_service.py:6:    tenant_id,
backend\apps\compliance\services\consent_service.py:14:        tenant_id=tenant_id,
backend\graduation\services.py:4:from core.tenant_models import tenant_context
backend\graduation\services.py:141:        # Ensure tenant context for any auto-scoped reads
backend\graduation\services.py:142:        with tenant_context(school):
backend\apps\compliance\models\consent.py:13:    tenant_id = models.CharField(max_length=64)
backend\apps\compliance\models\consent.py:35:        return f"{self.consent_type} - {self.tenant_id}"
backend\onboarding\views.py:14:All endpoints are tenant-scoped via X-School-Id ΓåÆ get_request_school_id().
backend\onboarding\views.py:15:Tenant isolation: every ImportSession lookup uses ImportSession.objects.get(pk=ΓÇª, school_id=ΓÇª).
backend\onboarding\views.py:25:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\onboarding\views.py:26:from rest_framework.permissions import IsAuthenticated
backend\onboarding\views.py:62:# Helper: resolve ImportSession scoped to the request's tenant
backend\onboarding\views.py:66:    """Return ImportSession or 404, always tenant-scoped (school_id enforced)."""
backend\onboarding\views.py:175:@permission_classes(PERM_CLASSES)
backend\onboarding\views.py:203:@permission_classes(PERM_CLASSES)
backend\onboarding\views.py:255:@permission_classes(PERM_CLASSES)
backend\onboarding\views.py:292:@permission_classes(PERM_CLASSES)
backend\onboarding\views.py:330:@permission_classes(PERM_CLASSES)
backend\onboarding\views.py:474:@permission_classes(PERM_CLASSES)
backend\integrations_real\api.py:1:from rest_framework.decorators import api_view, permission_classes
backend\integrations_real\api.py:2:from rest_framework.permissions import IsAuthenticated
backend\integrations_real\api.py:9:@permission_classes([IsAuthenticated])
backend\integrations_real\api.py:15:@permission_classes([IsAuthenticated])
backend\graduation\models.py:5:from core.tenant_models import TenantScopedModel
backend\support\api_support.py:12:from rest_framework.decorators import api_view, permission_classes
backend\support\api_support.py:13:from rest_framework.permissions import IsAuthenticated
backend\support\api_support.py:23:@permission_classes([IsAuthenticated])
backend\support\api_support.py:66:@permission_classes([IsAuthenticated])
backend\support\api_support.py:81:@permission_classes([IsAuthenticated])
backend\apps\compliance\migrations\0001_initial.py:21:                ('tenant_id', models.CharField(max_length=64)),
backend\classroom\models.py:4:from core.tenant_models import TenantScopedModel
backend\onboarding\tests\test_views.py:6:- Tenant isolation (cross-school session access denied)
backend\onboarding\tests\test_views.py:132:# 3. Tenant isolation
backend\onboarding\tests\test_parent_enrollment_guidance.py:51:            role_code="parent",
backend\onboarding\tests\test_parent_enrollment_guidance.py:196:    def test_tenant_isolation_remains_enforced(self):
backend\facops\migrations\0001_initial.py:13:        ('core', '0005_crown_permission_engine'),
backend\integrations\tests\test_oneroster.py:10:- Tenant isolation: only exports data for requested school
backend\integrations\tests\test_oneroster.py:189:# Tenant isolation
backend\subscriptions\views.py:8:  - X-School-Id header (standard tenant middleware)
backend\subscriptions\views.py:37:    Returns all module entitlements for the school in X-School-Id header.
backend\subscriptions\views.py:41:        return JsonResponse({"error": "X-School-Id header required"}, status=400)
backend\subscriptions\views.py:87:        return JsonResponse({"error": "X-School-Id header required"}, status=400)
backend\subscriptions\views.py:149:        return JsonResponse({"error": "X-School-Id header required"}, status=400)
backend\subscriptions\views.py:185:        return JsonResponse({"error": "X-School-Id header required"}, status=400)
backend\apps\compliance\api\parent_rights.py:1:from rest_framework.permissions import IsAuthenticated
backend\apps\compliance\api\parent_rights.py:9:    permission_classes = [IsAuthenticated]
backend\apps\compliance\api\parent_rights.py:19:        tenant = getattr(request, "tenant", None)
backend\apps\compliance\api\parent_rights.py:20:        tenant_id = str(getattr(tenant, "id", "unknown"))
backend\apps\compliance\api\parent_rights.py:23:            tenant_id=tenant_id,
backend\onboarding\models_tasks.py:82:    role_code = models.CharField(max_length=64, blank=True, default="")
backend\facops\api\views.py:6:from rest_framework.decorators import action, api_view, permission_classes
backend\facops\api\views.py:7:from rest_framework.permissions import IsAuthenticated
backend\facops\api\views.py:10:# Crown canonical tenant helper
backend\facops\api\views.py:23:from facops.api.permissions import (
backend\facops\api\views.py:41:    permission_classes = [IsAuthenticated]
backend\facops\api\views.py:57:    permission_classes = [IsAuthenticated, IsFacilitiesStaffOrReadOnly]
backend\facops\api\views.py:72:    permission_classes = [IsAuthenticated, IsFacilitiesStaffOrReadOnly]
backend\facops\api\views.py:87:    permission_classes = [IsAuthenticated, CanCreateWorkOrder]
backend\facops\api\views.py:128:    permission_classes = [IsAuthenticated, IsSafetyOfficerOrReadOnly]
backend\facops\api\views.py:144:    permission_classes = [IsAuthenticated, IsSafetyOfficerOrReadOnly]
backend\facops\api\views.py:160:    permission_classes = [IsAuthenticated, IsSafetyOfficerOrReadOnly]
backend\facops\api\views.py:175:    permission_classes = [IsAuthenticated, IsSafetyOfficerOrReadOnly]
backend\facops\api\views.py:206:@permission_classes([IsAuthenticated])
backend\facops\api\views.py:229:@permission_classes([IsAuthenticated])
backend\integrations\oneroster.py:18:Access: staff/admin only. Requires X-School-Id header.
backend\integrations\oneroster.py:27:from rest_framework.decorators import api_view, permission_classes
backend\integrations\oneroster.py:28:from rest_framework.permissions import IsAuthenticated
backend\integrations\oneroster.py:166:        "userSourcedId", "role",
backend\integrations\oneroster.py:179:            "student",                                      # role
backend\integrations\oneroster.py:192:@permission_classes([IsAuthenticated])
backend\integrations\oneroster.py:212:    # Fetch data ΓÇô tenant-scoped throughout
backend\subscriptions\tests\test_permissions_enforcement.py:2:API permission enforcement tests.
backend\grade_weights_wizard\views.py:15:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\grade_weights_wizard\views.py:16:from rest_framework.permissions import IsAuthenticated
backend\grade_weights_wizard\views.py:50:@permission_classes(_PERM)
backend\grade_weights_wizard\views.py:69:@permission_classes(_PERM)
backend\grade_weights_wizard\views.py:107:@permission_classes(_PERM)
backend\grade_weights_wizard\views.py:159:@permission_classes(_PERM)
backend\grade_weights_wizard\views.py:224:@permission_classes(_PERM)
backend\facops\api\permissions.py:1:# backend/facops/api/permissions.py
backend\facops\api\permissions.py:4:from rest_framework.permissions import BasePermission, SAFE_METHODS
backend\facops\api\permissions.py:21:def _role(request) -> str:
backend\facops\api\permissions.py:32:    Writes: staff/superuser or recognised facilities role.
backend\facops\api\permissions.py:35:    def has_permission(self, request, view) -> bool:
backend\facops\api\permissions.py:40:        return _is_staff_or_super(request) or _role(request) in FACILITIES_WRITE_ROLES
backend\facops\api\permissions.py:46:    def has_permission(self, request, view) -> bool:
backend\facops\api\permissions.py:53:    Writes: staff/superuser or recognised safety role.
backend\facops\api\permissions.py:56:    def has_permission(self, request, view) -> bool:
backend\facops\api\permissions.py:61:        return _is_staff_or_super(request) or _role(request) in SAFETY_WRITE_ROLES
backend\subscriptions\services.py:5:  1. Plan entitlement  ΓÇö defines base enabled/limit for all tenants on this plan
backend\subscriptions\services.py:40:    Resolve feature entitlements for a given school/tenant.
backend\subscriptions\services.py:72:        # Step 2: per-tenant override (non-None values take precedence)
backend\subscriptions\services.py:96:        """Raise PermissionError if the feature is not enabled for this tenant."""
backend\onboarding\migrations\0004_solomonaudience_solomoncategory_solomontopic_and_more.py:20:                ('role_code', models.CharField(blank=True, default='', max_length=64)),
backend\grade_weights_wizard\tests\test_views.py:126:    def test_cross_tenant_returns_404(self):
backend\integrations\graph_client.py:40:    tenant = _first_env("GRAPH_TENANT_ID", "AZURE_TENANT_ID")
backend\integrations\graph_client.py:44:    if not all([tenant, client_id, client_secret]):
backend\integrations\graph_client.py:46:            "GRAPH/AZURE tenant, client id, and client secret must be set"
backend\integrations\graph_client.py:49:    url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
backend\integrations\graph_client.py:70:    Requires Mail.Send application permission on the App Registration.
backend\classroom\management\commands\seed_classroom_demo.py:19:    help = "Seed deterministic classroom demo data for the selected school (requires X-School-Id when using APIs)."
backend\subscriptions\models.py:9:Add-on features (optional, per-tenant overrides):
backend\subscriptions\models.py:74:    Subscription history per tenant/school.
backend\subscriptions\models.py:75:    school_id aligns with the X-School-ID tenant header UUID.
backend\subscriptions\models.py:94:    Per-tenant overrides applied on top of plan entitlements.
backend\subscriptions\models.py:130:    """Tracks add-on module entitlements per school (tenant)."""
backend\onboarding\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
backend\financial_aid\workflows.py:332:        "suggested_roles": WORK_STUDY_ROLE_LIBRARY,
backend\onboarding\api_onboarding.py:12:from rest_framework.decorators import api_view, permission_classes
backend\onboarding\api_onboarding.py:13:from rest_framework.permissions import AllowAny, IsAuthenticated
backend\onboarding\api_onboarding.py:18:from core.permissions import user_has_permission
backend\onboarding\api_onboarding.py:42:@permission_classes([IsAuthenticated])
backend\onboarding\api_onboarding.py:81:@permission_classes([IsAuthenticated])
backend\onboarding\api_onboarding.py:101:@permission_classes([IsAuthenticated])
backend\onboarding\api_onboarding.py:132:        or user_has_permission(user, "admin.view")
backend\onboarding\api_onboarding.py:137:@permission_classes([IsAuthenticated])
backend\onboarding\api_onboarding.py:149:@permission_classes([AllowAny])
backend\onboarding\api_onboarding.py:214:@permission_classes([AllowAny])
backend\onboarding\api_onboarding.py:224:@permission_classes([AllowAny])
backend\onboarding\api_onboarding.py:240:@permission_classes([AllowAny])
backend\onboarding\api_onboarding.py:247:@permission_classes([AllowAny])
backend\onboarding\api_onboarding.py:259:@permission_classes([AllowAny])
backend\integrations\api\views.py:2:from rest_framework import permissions
backend\integrations\api\views.py:13:    school_id = request.headers.get("X-School-Id")
backend\integrations\api\views.py:27:    permission_classes = [permissions.IsAuthenticated]
backend\apps\accounting\policies\security_rules.md:18:   - tenant validation
backend\financial_aid\views.py:5:from rest_framework.permissions import IsAuthenticated
backend\financial_aid\views.py:8:from core.permissions import user_has_permission
backend\financial_aid\views.py:13:    permission_classes = [IsAuthenticated]
backend\financial_aid\views.py:16:        # Canonical scoping: missing header -> 400, wrong-tenant non-staff -> 404.
backend\financial_aid\views.py:19:        if not user_has_permission(request.user, "financial_aid.view", school=school):
backend\financial_aid\views.py:102:    permission_classes = [IsAuthenticated]
backend\financial_aid\views.py:105:        # Canonical scoping: missing header -> 400, wrong-tenant non-staff -> 404.
backend\financial_aid\views.py:108:        if not user_has_permission(request.user, "financial_aid.view", school=school):
backend\financial_aid\views.py:111:        can_see_rationale = user_has_permission(
backend\executive360\api\views.py:11:from rest_framework import permissions
backend\executive360\api\views.py:24:    sid = request.headers.get("X-School-Id")
backend\executive360\api\views.py:42:    permission_classes = [permissions.IsAuthenticated]
backend\subscriptions\migrations\0003_schoolmodule.py:13:        ("subscriptions", "0002_remove_tenant_subscription_school_id_unique"),
backend\subscriptions\migrations\0002_remove_tenant_subscription_school_id_unique.py:14:            model_name='tenantsubscription',
backend\grade_weights_wizard\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
backend\msauth\views.py:6:  2. /auth/microsoft/callback/   ΓåÆ exchange code ΓåÆ create session ΓåÆ redirect to /dash/<role>
backend\msauth\views.py:59:def _resolve_role_from_groups(group_ids: set[str]) -> str | None:
backend\msauth\views.py:62:    role whose Entra group ID appears in the userΓÇÖs membership set.
backend\msauth\views.py:65:    for role, gid in ROLE_GROUP_MAP.items():
backend\msauth\views.py:67:            return role
backend\msauth\views.py:97:    Exchange authorization code for token, resolve group-based role,
backend\msauth\views.py:98:    create Django session, redirect to /dash/<role>.
backend\msauth\views.py:141:    # ---- Resolve group-based role --------------------------------------
backend\msauth\views.py:145:    resolved_role = _resolve_role_from_groups(user_group_ids)
backend\msauth\views.py:146:    if not resolved_role:
backend\msauth\views.py:148:            "SSO login blocked ΓÇö no authorized role group: %s groups=%s",
backend\msauth\views.py:151:        return JsonResponse({"error": "No authorized role group found"}, status=403)
backend\msauth\views.py:163:    # ---- Sync role if Entra groups diverge from DB --------------------
backend\msauth\views.py:164:    if getattr(user, "role", None) != resolved_role:
backend\msauth\views.py:166:            user.role = resolved_role
backend\msauth\views.py:167:            user.save(update_fields=["role"])
backend\msauth\views.py:168:            logger.info("Role updated for %s: %s", email, resolved_role)
backend\msauth\views.py:170:            logger.exception("Failed to sync role for %s", email)
backend\msauth\views.py:175:    logger.info("SSO login: %s ΓåÆ /dash/%s", email, resolved_role)
backend\msauth\views.py:177:    return HttpResponseRedirect(_frontend_url(f"/dash/{resolved_role}"))
backend\msauth\views.py:197:        "role":      str(getattr(request.user, "role", "") or ""),
backend\subscriptions\management\commands\seed_plans.py:24:    ("identity.rbac", "RBAC", "Role-based access control"),
backend\subscriptions\management\commands\seed_plans.py:59:    "identity.rbac",
backend\financial_aid\tests\test_workflows.py:52:        self.assertIn("suggested_roles", result["work_study_plan"])
backend\financial_aid\tests\test_financial_aid_endpoints.py:16:        UserRole.objects.create(user=self.user, school=self.school, role_code="AID_DIRECTOR")
backend\financial_aid\tests\test_financial_aid_endpoints.py:20:        RolePermission.objects.get_or_create(role_code="AID_DIRECTOR", permission=_perm)
backend\financial_aid\tests\test_financial_aid_endpoints.py:224:        """Verify X-School-Id header is required."""
backend\financial_aid\tests\test_financial_aid_authz.py:5:# Verifies that roles WITHOUT financial_aid.view are hard-blocked (403),
backend\financial_aid\tests\test_financial_aid_authz.py:6:# and that roles WITH it reach the data layer (200).
backend\financial_aid\tests\test_financial_aid_authz.py:8:# Tenant isolation (row scope) is also proven here:
backend\financial_aid\tests\test_financial_aid_authz.py:27:def _enable_tenant_middleware(settings):
backend\financial_aid\tests\test_financial_aid_authz.py:29:    The root conftest.py disables it globally; permission gate and cross-tenant
backend\financial_aid\tests\test_financial_aid_authz.py:50:def _assign_role(user, school, role_code):
backend\financial_aid\tests\test_financial_aid_authz.py:51:    return UserRole.objects.create(user=user, school=school, role_code=role_code)
backend\financial_aid\tests\test_financial_aid_authz.py:54:def _grant(role_code, perm_code):
backend\financial_aid\tests\test_financial_aid_authz.py:58:    RolePermission.objects.get_or_create(role_code=role_code, permission=perm)
backend\financial_aid\tests\test_financial_aid_authz.py:83:# 403 gate: roles that must never reach financial aid data
backend\financial_aid\tests\test_financial_aid_authz.py:89:    @pytest.mark.parametrize("role_code,perm_code", [
backend\financial_aid\tests\test_financial_aid_authz.py:94:    def test_role_blocked_on_summary(self, role_code, perm_code):
backend\financial_aid\tests\test_financial_aid_authz.py:96:        user = _user(role_code.lower())
backend\financial_aid\tests\test_financial_aid_authz.py:97:        _assign_role(user, school, role_code)
backend\financial_aid\tests\test_financial_aid_authz.py:98:        _grant(role_code, perm_code)
backend\financial_aid\tests\test_financial_aid_authz.py:107:            f"Role {role_code!r} should be blocked from financial-aid/summary/ "
backend\financial_aid\tests\test_financial_aid_authz.py:111:    @pytest.mark.parametrize("role_code,perm_code", [
backend\financial_aid\tests\test_financial_aid_authz.py:116:    def test_role_blocked_on_drilldown(self, role_code, perm_code):
backend\financial_aid\tests\test_financial_aid_authz.py:118:        user = _user(f"{role_code.lower()}_dd")
backend\financial_aid\tests\test_financial_aid_authz.py:119:        _assign_role(user, school, role_code)
backend\financial_aid\tests\test_financial_aid_authz.py:120:        _grant(role_code, perm_code)
backend\financial_aid\tests\test_financial_aid_authz.py:129:            f"Role {role_code!r} should be blocked from financial-aid/drilldown/ "
backend\financial_aid\tests\test_financial_aid_authz.py:146:# 200 gate: roles that must reach financial aid data
backend\financial_aid\tests\test_financial_aid_authz.py:152:    @pytest.mark.parametrize("role_code", ["AID_DIRECTOR", "FINANCE_DIRECTOR"])
backend\financial_aid\tests\test_financial_aid_authz.py:153:    def test_role_reaches_summary(self, role_code):
backend\financial_aid\tests\test_financial_aid_authz.py:155:        user = _user(role_code.lower())
backend\financial_aid\tests\test_financial_aid_authz.py:156:        _assign_role(user, school, role_code)
backend\financial_aid\tests\test_financial_aid_authz.py:157:        _grant(role_code, "financial_aid.view")
backend\financial_aid\tests\test_financial_aid_authz.py:166:            f"Role {role_code!r} should reach financial-aid/summary/ "
backend\financial_aid\tests\test_financial_aid_authz.py:170:    @pytest.mark.parametrize("role_code", ["AID_DIRECTOR", "FINANCE_DIRECTOR"])
backend\financial_aid\tests\test_financial_aid_authz.py:171:    def test_role_reaches_drilldown(self, role_code):
backend\financial_aid\tests\test_financial_aid_authz.py:173:        user = _user(f"{role_code.lower()}_dd2")
backend\financial_aid\tests\test_financial_aid_authz.py:174:        _assign_role(user, school, role_code)
backend\financial_aid\tests\test_financial_aid_authz.py:175:        _grant(role_code, "financial_aid.view")
backend\financial_aid\tests\test_financial_aid_authz.py:185:            f"Role {role_code!r} should reach financial-aid/drilldown/ "
backend\financial_aid\tests\test_financial_aid_authz.py:191:# Tenant isolation (row scope)
backend\financial_aid\tests\test_financial_aid_authz.py:197:    def test_cross_tenant_row_isolation_on_drilldown(self):
backend\financial_aid\tests\test_financial_aid_authz.py:202:        user = _user("aiddir_isolation")
backend\financial_aid\tests\test_financial_aid_authz.py:203:        _assign_role(user, school_a, "AID_DIRECTOR")
backend\financial_aid\tests\test_financial_aid_authz.py:212:        # Request against school_b while user only has a role in school_a.
backend\financial_aid\tests\test_financial_aid_authz.py:214:        # user_has_permission(user, "financial_aid.view", school=school_b) ΓåÆ False
backend\financial_aid\tests\test_financial_aid_authz.py:215:        # (user has AID_DIRECTOR role in school_a, not school_b)
backend\financial_aid\tests\test_financial_aid_authz.py:221:            f"User with role in school_a should be blocked from school_b FA data, "
backend\financial_aid\tests\test_financial_aid_authz.py:225:    def test_same_tenant_drilldown_returns_own_data_only(self):
backend\financial_aid\tests\test_financial_aid_authz.py:230:        _assign_role(user, school_a, "AID_DIRECTOR")
backend\financial_aid\tests\test_financial_aid_authz.py:265:    AID_DIRECTOR holds this permission ΓåÆ sees the text.
backend\financial_aid\tests\test_financial_aid_authz.py:273:        _assign_role(user, school, "AID_DIRECTOR")
backend\financial_aid\tests\test_financial_aid_authz.py:295:        _assign_role(user, school, "FINANCE_DIRECTOR")
backend\financial_aid\tests\test_financial_aid_authz.py:317:        _assign_role(user, school, "HEAD_OF_SCHOOL")
backend\financial_aid\tests\test_auth_smoke.py:7:  400 ΓåÆ tenant-header/middleware fail-closed deny
backend\financial_aid\tests\test_auth_smoke.py:10:  403 ΓåÆ DRF permission denied
backend\financial_aid\tests\test_auth_smoke.py:19:where a refactor swapped in an AllowAny permission or dropped the decorator.
backend\financial_aid\tests\test_auth_smoke.py:40:    An unauthenticated request must be denied by auth/tenant wall.
backend\financial_aid\tests\test_auth_smoke.py:43:    - 200/500 ΓåÆ auth/permission wiring broken
backend\financial_aid\tests\test_auth_smoke.py:50:        f"Expected 400/302/401/403 (auth/tenant wall).\n"
backend\financial_aid\tests\test_auth_smoke.py:52:        f"  200 ΓåÆ @login_required / permission class missing\n"
backend\financial_aid\tenant.py:5:    raw = request.headers.get("X-School-Id")
backend\financial_aid\tenant.py:7:        raise ValidationError({"detail": "Missing required header: X-School-Id"})
backend\financial_aid\tenant.py:11:        raise ValidationError({"detail": "Invalid X-School-Id (must be UUID)"})
backend\apps\accounting\models\ledger.py:19:    tenant_id = models.UUIDField(db_index=True)
backend\apps\accounting\models\ledger.py:35:        unique_together = ("tenant_id", "code")
backend\apps\accounting\models\ledger.py:45:    tenant_id = models.UUIDField(db_index=True)
backend\apps\accounting\models\ledger.py:79:    tenant_id = models.UUIDField(db_index=True)
backend\hr\models.py:10:    role = models.CharField(max_length=120)
backend\hr\models.py:20:        return f"{self.first_name} {self.last_name} ({self.role})"
backend\financial_aid\api.py:13:from rest_framework.decorators import api_view, permission_classes
backend\financial_aid\api.py:14:from rest_framework.permissions import IsAuthenticated
backend\financial_aid\api.py:18:from core.permissions import require_permission
backend\financial_aid\api.py:70:@permission_classes([IsAuthenticated])
backend\financial_aid\api.py:81:@permission_classes([IsAuthenticated])
backend\financial_aid\api.py:92:@permission_classes([IsAuthenticated])
backend\financial_aid\api.py:110:@require_permission("financial_aid.view")
backend\subscriptions\api\views.py:5:  GET  /api/v1/subscriptions/me/entitlements/    ΓÇö current tenant's full entitlement snapshot
backend\subscriptions\api\views.py:16:from rest_framework.decorators import api_view, permission_classes
backend\subscriptions\api\views.py:17:from rest_framework.permissions import IsAdminUser, IsAuthenticated
backend\subscriptions\api\views.py:42:@permission_classes([IsAuthenticated])
backend\subscriptions\api\views.py:45:    Return an entitlement snapshot for the current tenant (from X-School-ID header).
backend\subscriptions\api\views.py:96:@permission_classes([IsAuthenticated])
backend\subscriptions\api\views.py:111:@permission_classes([IsAuthenticated])
backend\subscriptions\api\views.py:124:@permission_classes([IsAdminUser])
backend\subscriptions\api\urls.py:6:  GET  subscriptions/me/entitlements/    - entitlement snapshot for current tenant
backend\enrollment_period_wizard\views.py:12:Auth: JWT or Session. All endpoints tenant-scoped via X-School-Id.
backend\enrollment_period_wizard\views.py:27:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\enrollment_period_wizard\views.py:28:from rest_framework.permissions import IsAuthenticated
backend\enrollment_period_wizard\views.py:94:@permission_classes(_PERM)
backend\enrollment_period_wizard\views.py:116:@permission_classes(_PERM)
backend\enrollment_period_wizard\views.py:189:@permission_classes(_PERM)
backend\enrollment_period_wizard\views.py:248:@permission_classes(_PERM)
backend\enrollment_period_wizard\views.py:350:@permission_classes(_PERM)
backend\subscriptions\api\permissions.py:2:DRF permission helpers for entitlement-gated views.
backend\subscriptions\api\permissions.py:5:    from subscriptions.api.permissions import RequiresEntitlement
backend\subscriptions\api\permissions.py:8:    @permission_classes([IsAuthenticated, RequiresEntitlement("admissions.pipeline")])
backend\subscriptions\api\permissions.py:12:Since DRF permission_classes expects classes (not instances), wrap with
backend\subscriptions\api\permissions.py:18:from rest_framework.permissions import BasePermission
backend\subscriptions\api\permissions.py:27:    Usage in permission_classes:
backend\subscriptions\api\permissions.py:28:        permission_classes = [IsAuthenticated, RequiresEntitlement("comms.sms")]
backend\subscriptions\api\permissions.py:32:        def has_permission(self, request, view) -> bool:
backend\apps\accounting\migrations\0001_initial.py:20:                ('tenant_id', models.UUIDField(db_index=True)),
backend\apps\accounting\migrations\0001_initial.py:36:                ('tenant_id', models.UUIDField(db_index=True)),
backend\apps\accounting\migrations\0001_initial.py:53:                ('tenant_id', models.UUIDField(db_index=True)),
backend\apps\accounting\migrations\0001_initial.py:61:                'unique_together': {('tenant_id', 'code')},
backend\apps\accounting\migrations\0001_initial.py:68:                ('tenant_id', models.UUIDField(db_index=True)),
backend\hr\migrations\0001_initial.py:22:                ('role', models.CharField(max_length=120)),
backend\enrollment_period_wizard\tests\test_views.py:8:  - Tenant isolation (X-School-Id required; mismatch ΓåÆ 404)
backend\enrollment_period_wizard\tests\test_views.py:142:# Tenant isolation
backend\enrollment_period_wizard\tests\test_views.py:483:    def test_cross_tenant_isolation(self):
backend\apps\accounting\audit\models.py:14:    tenant_id = models.UUIDField(db_index=True)
backend\finance_setup\wizard_api.py:20:from .tenant import school_id_from_request
backend\grade_scale_wizard\views.py:18:  - Tenant: every lookup filtered on school_id from X-School-Id header
backend\grade_scale_wizard\views.py:35:    permission_classes,
backend\grade_scale_wizard\views.py:37:from rest_framework.permissions import IsAuthenticated
backend\grade_scale_wizard\views.py:241:@permission_classes(_PERM)
backend\grade_scale_wizard\views.py:264:@permission_classes(_PERM)
backend\grade_scale_wizard\views.py:330:@permission_classes(_PERM)
backend\grade_scale_wizard\views.py:370:@permission_classes(_PERM)
backend\grade_scale_wizard\views.py:414:@permission_classes(_PERM)
backend\grade_scale_wizard\views.py:547:@permission_classes(_PERM)
backend\hr\api.py:2:from rest_framework.decorators import api_view, permission_classes
backend\hr\api.py:4:from rest_framework.permissions import IsAuthenticated
backend\hr\api.py:9:from core.permissions import CrownModulePermission
backend\hr\api.py:19:        raise PermissionDenied("Tenant context required (X-School-Id header missing).")
backend\hr\api.py:25:    permission_classes = [CrownModulePermission("hr.view", write_code="hr.edit")]
backend\hr\api.py:52:@permission_classes([IsAuthenticated])
backend\student_records\views.py:2:from rest_framework.permissions import IsAuthenticated
backend\student_records\views.py:5:from tenants.tenant_context import get_request_school_id
backend\student_records\views.py:11:    permission_classes = [IsAuthenticated]
backend\student_records\views.py:20:    permission_classes = [IsAuthenticated]
backend\grade_scale_wizard\tests\test_views.py:8:  - Tenant isolation (X-School-Id required; mismatch ΓåÆ 404)
backend\grade_scale_wizard\tests\test_views.py:155:# Tenant isolation
backend\grade_scale_wizard\tests\test_views.py:577:    def test_cross_tenant_isolation(self):
backend\finance_setup\tests\test_finance_setup_tenant_scoping.py:2:Tests: Finance Setup tenant scoping
backend\gradebook_setup_wizard\views.py:7:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\gradebook_setup_wizard\views.py:8:from rest_framework.permissions import IsAuthenticated
backend\gradebook_setup_wizard\views.py:48:@permission_classes(_PERM)
backend\gradebook_setup_wizard\views.py:67:@permission_classes(_PERM)
backend\gradebook_setup_wizard\views.py:97:@permission_classes(_PERM)
backend\gradebook_setup_wizard\views.py:150:@permission_classes(_PERM)
backend\gradebook_setup_wizard\views.py:210:@permission_classes(_PERM)
backend\finance_setup\tests\test_finance_setup_locking.py:80:_patch_tenant = patch("finance_setup.wizard_api.school_id_from_request", return_value=SCHOOL_ID)
backend\finance_setup\tests\test_finance_setup_locking.py:103:@_patch_tenant
backend\finance_setup\tests\test_finance_setup_locking.py:112:@_patch_tenant
backend\finance_setup\tests\test_finance_setup_locking.py:123:@_patch_tenant
backend\finance_setup\tests\test_finance_setup_locking.py:133:@_patch_tenant
backend\finance_setup\tests\test_finance_setup_locking.py:143:@_patch_tenant
backend\finance_setup\tests\test_finance_setup_locking.py:155:@_patch_tenant
backend\student_records\tests\test_student_records_routes.py:70:def test_list_scopes_to_tenant_school():
backend\student_records\tests\test_student_records_routes.py:89:def test_detail_cross_tenant_returns_404():
backend\student_records\tests\test_student_records_routes.py:108:def test_detail_not_found_returns_404_with_valid_tenant():
backend\finance_setup\tenant.py:6:    Thin wrapper around the canonical tenant resolver.
backend\enrollment_period_wizard\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
backend\households\views.py:2:from rest_framework import permissions, viewsets
backend\households\views.py:10:def _user_has_parent_role(user, school_id):
backend\households\views.py:11:    """Return True if user holds a PARENT role at this school."""
backend\households\views.py:15:    roles = UserRole.objects.filter(user_id=user_id, role_code="PARENT")
backend\households\views.py:17:        roles = roles.filter(school_id=school_id)
backend\households\views.py:18:    return roles.exists()
backend\households\views.py:25:	permission_classes = [permissions.IsAuthenticated]
backend\households\views.py:41:		# Apply guardian scoping if enabled - PARENT role users only
backend\households\views.py:46:			if _user_has_parent_role(user, school_id):
backend\households\views.py:67:		# DO NOT add inline role checks here - add them to core/scoping.py instead.
backend\grade_scale_wizard\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
backend\gradebook_setup_wizard\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
backend\households\tests\test_tenant_isolation.py:2:Tenant isolation tests per TENANT_PRIVACY_CANON.md
backend\households\tests\test_tenant_isolation.py:5:- Missing tenant context ΓåÆ fail-closed deny (400/401/403)
backend\households\tests\test_tenant_isolation.py:6:- Wrong tenant context ΓåÆ 404 (non-staff)
backend\households\tests\test_tenant_isolation.py:7:- Correct tenant context ΓåÆ 200
backend\households\tests\test_tenant_isolation.py:8:- Querysets never return cross-tenant rows
backend\households\tests\test_tenant_isolation.py:26:    Tenant isolation enforcement tests.
backend\households\tests\test_tenant_isolation.py:83:    def test_missing_tenant_fails_closed_or_empty_scope(self):
backend\households\tests\test_tenant_isolation.py:85:        Missing tenant context must fail closed (400/401/403), and
backend\households\tests\test_tenant_isolation.py:86:        no-school authenticated requests must not leak cross-tenant data.
backend\households\tests\test_tenant_isolation.py:88:        # Anonymous request (no auth, no tenant)
backend\households\tests\test_tenant_isolation.py:90:        # Missing tenant context may be denied by auth layer (401/403)
backend\households\tests\test_tenant_isolation.py:91:        # or tenant middleware (400), all of which are fail-closed outcomes.
backend\households\tests\test_tenant_isolation.py:110:    def test_wrong_tenant_returns_404_non_staff(self):
backend\households\tests\test_tenant_isolation.py:112:        CANON Rule 3: Non-staff cross-tenant access MUST return 404 (not 403)
backend\households\tests\test_tenant_isolation.py:124:    def test_correct_tenant_returns_200(self):
backend\households\tests\test_tenant_isolation.py:126:        CANON Rule 6: Correct tenant context MUST return 200 and scoped data
backend\households\tests\test_tenant_isolation.py:150:    def test_staff_can_override_tenant(self):
backend\households\tests\test_tenant_isolation.py:152:        CANON Rule 2: Staff may use X-School-Id header to override
backend\households\tests\test_tenant_isolation.py:166:    def test_invalid_tenant_header_returns_400(self):
backend\households\tests\test_tenant_isolation.py:168:        Invalid UUID in tenant header MUST return 400
backend\households\tests\test_tenant_isolation.py:178:    def test_nonexistent_tenant_returns_404(self):
backend\households\tests\test_tenant_isolation.py:191:    def test_queryset_never_crosses_tenants(self):
backend\households\tests\test_tenant_isolation.py:193:        CANON Rule 6: Querysets MUST NOT return cross-tenant rows
backend\households\tests\test_tenant_isolation.py:207:    def test_finance_endpoint_respects_tenant(self):
backend\households\tests\test_tenant_isolation.py:209:        Sensitive endpoints (finance) MUST enforce tenant isolation
backend\households\tests\test_tenant_isolation.py:217:        # Should either succeed with School A data or require explicit tenant
backend\households\tests\test_guardian_scoping.py:8:#   - Non-PARENT roles (REGISTRAR, TEACHER) are NOT filtered by guardian
backend\households\tests\test_guardian_scoping.py:13:# Uses Django TestCase + @override_settings (matches test_tenant_isolation.py).
backend\households\tests\test_guardian_scoping.py:39:def _assign_role(user, school, role_code):
backend\households\tests\test_guardian_scoping.py:40:    return UserRole.objects.create(user=user, school=school, role_code=role_code)
backend\households\tests\test_guardian_scoping.py:78:    """PARENT role users see only their own household via guardian email match."""
backend\households\tests\test_guardian_scoping.py:86:        _assign_role(self.parent_user, self.school, "PARENT")
backend\households\tests\test_guardian_scoping.py:106:        _assign_role(parent_user, school, "PARENT")
backend\households\tests\test_guardian_scoping.py:127:    """PARENT role users see only students in their own household."""
backend\households\tests\test_guardian_scoping.py:135:        _assign_role(self.parent_user, self.school, "PARENT")
backend\households\tests\test_guardian_scoping.py:157:# Non-PARENT roles must NOT be guardian-filtered
backend\households\tests\test_guardian_scoping.py:174:        _assign_role(self.registrar, self.school, "REGISTRAR")
backend\households\tests\test_guardian_scoping.py:177:        _assign_role(self.teacher, self.school, "TEACHER")
backend\households\models.py:21:	# Multi-tenant scoping anchor
backend\households\models.py:57:	# Spine: keep roles simple; expand later (custody, billing responsibility, etc.)
backend\student_import_wizard\views.py:13:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\student_import_wizard\views.py:14:from rest_framework.permissions import IsAuthenticated
backend\student_import_wizard\views.py:41:@permission_classes(_PERM)
backend\student_import_wizard\views.py:60:@permission_classes(_PERM)
backend\student_import_wizard\views.py:95:@permission_classes(_PERM)
backend\student_import_wizard\views.py:147:@permission_classes(_PERM)
backend\student_import_wizard\views.py:222:@permission_classes(_PERM)
backend\student_import_wizard\tests\test_views.py:109:    def test_cross_tenant_returns_404(self):
backend\gradebook\views_parent.py:4:from rest_framework.decorators import api_view, permission_classes
backend\gradebook\views_parent.py:5:from rest_framework.permissions import IsAuthenticated
backend\gradebook\views_parent.py:15:@permission_classes([IsAuthenticated])
backend\households\scoping.py:8:from crown_api.tenant import resolve_tenant_school_id
backend\households\scoping.py:12:CANONICAL_SCHOOL_HEADER = "X-School-Id"
backend\households\scoping.py:19:    Raised when tenant context is required but missing or invalid.
backend\households\scoping.py:23:    default_detail = "Missing or invalid school context (X-School-Id)"
backend\households\scoping.py:36:    Canonical tenant resolver with validation.
backend\households\scoping.py:41:    - No tenant when required ΓåÆ 400
backend\households\scoping.py:42:    - Non-staff using header for different school ΓåÆ 404 (prevent cross-tenant leakage)
backend\households\scoping.py:43:    - Staff can use header to override tenant
backend\households\scoping.py:50:        MissingSchoolContext (400): Invalid header UUID or no tenant when required
backend\households\scoping.py:51:        NotFound (404): Valid UUID but school doesn't exist, or non-staff cross-tenant
backend\households\scoping.py:53:    res = resolve_tenant_school_id(request)
backend\households\scoping.py:57:        raise MissingSchoolContext("Invalid tenant header UUID")
backend\households\scoping.py:59:    # 400: No tenant resolved and it's required
backend\households\scoping.py:75:    # 404: Non-staff user attempting cross-tenant access via header
backend\households\scoping.py:89:    Apply school-level tenant scoping to a queryset.
backend\households\scoping.py:92:        request: The HTTP request containing tenant context
backend\households\scoping.py:94:        required: If True, raises MissingSchoolContext when tenant is missing (default: True)
backend\households\scoping.py:95:                  If False, returns qs.none() when tenant is missing (legacy behavior)
backend\households\scoping.py:98:        Filtered queryset scoped to the tenant's school_id
backend\gradebook\views.py:7:from rest_framework.decorators import api_view, permission_classes
backend\gradebook\views.py:9:from rest_framework.permissions import IsAuthenticated
backend\gradebook\views.py:15:from crown_api.tenant_decorators import require_tenant
backend\gradebook\views.py:78:def _role_codes(user, school_id) -> set[str]:
backend\gradebook\views.py:85:        UserRole.objects.filter(user_id=user_id, school_id=school_id).values_list("role_code", flat=True)
backend\gradebook\views.py:89:def _is_staffish(user, roles: set[str]) -> bool:
backend\gradebook\views.py:93:        or ("HEAD_OF_SCHOOL" in roles)
backend\gradebook\views.py:99:    roles = _role_codes(user, school_id)
backend\gradebook\views.py:107:    if _is_staffish(user, roles):
backend\gradebook\views.py:110:    if "TEACHER" in roles:
backend\gradebook\views.py:127:    permission_classes = [IsAuthenticated]
backend\gradebook\views.py:136:@permission_classes([IsAuthenticated])
backend\gradebook\views.py:137:@require_tenant
backend\gradebook\views.py:159:@permission_classes([IsAuthenticated])
backend\gradebook\views.py:160:@require_tenant
backend\gradebook\views.py:176:@permission_classes([IsAuthenticated])
backend\gradebook\views.py:184:    # grade entries scoped to tenant + section
backend\gradebook\views.py:219:@permission_classes([IsAuthenticated])
backend\gradebook\views.py:220:@require_tenant
backend\gradebook\views.py:295:@permission_classes([IsAuthenticated])
backend\gradebook\views.py:311:@permission_classes([IsAuthenticated])
backend\gradebook\views.py:335:@permission_classes([IsAuthenticated])
backend\gradebook\views.py:485:@permission_classes([IsAuthenticated])
backend\gradebook\views.py:492:    Tenant-scoped: must include X-School-Id header matching entry's school_id.
backend\gradebook\views.py:527:@permission_classes([IsAuthenticated])
backend\gradebook\views.py:532:    Requires TEACHER, HEAD_OF_SCHOOL, or ADMIN role.
backend\gradebook\views.py:542:    roles = _role_codes(request.user, school_id)
backend\gradebook\views.py:543:    if not roles.intersection({"TEACHER", "HEAD_OF_SCHOOL", "ADMIN"}):
backend\gradebook\views.py:544:        raise PermissionDenied("Grade write requires TEACHER, HEAD_OF_SCHOOL, or ADMIN role.")
backend\gradebook\views.py:571:                # Skip unknown students (including cross-tenant IDs); do not fail the whole batch
backend\gradebook\management\commands\seed_gradebook_demo.py:98:        parser.add_argument("--school-id", required=True, help="UUID of the tenant school to seed.")
backend\finance\tests\test_finance_tenant.py:2:finance/tests/test_finance_tenant.py ΓÇö Tenant isolation invariants for Finance module.
backend\finance\tests\test_finance_tenant.py:5:  1. Missing X-School-Id header ΓåÆ fail-closed (400/403/404).
backend\finance\tests\test_finance_tenant.py:10:  python manage.py test finance.tests.test_finance_tenant
backend\finance\tests\test_finance_tenant.py:62:        """No X-School-Id header ΓåÆ 400 (MissingSchoolContext)."""
backend\finance\tests\test_finance_tenant.py:67:        """Valid X-School-Id header ΓåÆ 200."""
backend\finance\tests\test_finance_services.py:230:        """Obligation from a different school ΓåÆ DoesNotExist (tenant guard)."""
backend\student_import_wizard\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
backend\gradebook\tests\test_parent_grades_e2e.py:6:- Tenant scoping works (X-School-Id required)
backend\gradebook\tests\test_parent_grades_e2e.py:109:def test_parent_grades_summary_invalid_tenant_header_returns_400():
backend\gradebook\tests\test_parent_grades_e2e.py:110:    """Malformed UUID in X-School-Id must return 400 (header_invalid path)."""
backend\gradebook\tests\test_gradeentry_upsert.py:6:- Authenticated user without TEACHER role ΓåÆ 403 (RBAC gate)
backend\gradebook\tests\test_gradeentry_upsert.py:28:    The tenant middleware fires before DRF permission checks (returns 400 for
backend\gradebook\tests\test_gradeentry_upsert.py:29:    missing X-School-Id), so any of 400/401/403 is acceptable ΓÇö the endpoint
backend\gradebook\tests\test_gradeentry_upsert.py:40:    """Authenticated user with no X-School-Id header is rejected by tenant middleware."""
backend\gradebook\tests\test_gradeentry_upsert.py:48:    # No X-School-Id header ΓåÆ get_request_school_id raises ΓåÆ 400 or 403
backend\gradebook\tests\test_gradebook_section_summary.py:26:def _assign_role(*, user, school: School, role_code: str):
backend\gradebook\tests\test_gradebook_section_summary.py:27:    """Assign a role to the user."""
backend\gradebook\tests\test_gradebook_section_summary.py:28:    UserRole.objects.create(school=school, user=user, role_code=role_code)
backend\gradebook\tests\test_gradebook_section_summary.py:89:    _assign_role(user=user, school=school, role_code="HEAD_OF_SCHOOL")
backend\gradebook\tests\test_gradebook_section_summary.py:118:    _assign_role(user=user, school=school, role_code="HEAD_OF_SCHOOL")
backend\gradebook\tests\test_gradebook_ro_api.py:26:def _assign_role(*, user, school: School, role_code: str):
backend\gradebook\tests\test_gradebook_ro_api.py:27:    UserRole.objects.create(school=school, user=user, role_code=role_code)
backend\gradebook\tests\test_gradebook_ro_api.py:59:        role_type="TEACHER",
backend\gradebook\tests\test_gradebook_ro_api.py:74:    _assign_role(user=user, school=school, role_code="TEACHER")
backend\gradebook\tests\test_gradebook_ro_api.py:113:    _assign_role(user=user, school=school, role_code="TEACHER")
backend\gradebook\tests\test_gradebook_ro_api.py:127:def test_non_teacher_role_forbidden():
backend\gradebook\tests\test_gradebook_ro_api.py:132:    _assign_role(user=user, school=school, role_code="PARENT")
backend\gradebook\tests\test_gradebook_ro_api.py:176:    _assign_role(user=user, school=school, role_code="TEACHER")
backend\gradebook\tests\test_gradebook_list_endpoints.py:26:def _assign_role(*, user, school: School, role_code: str):
backend\gradebook\tests\test_gradebook_list_endpoints.py:27:    UserRole.objects.create(school=school, user=user, role_code=role_code)
backend\gradebook\tests\test_gradebook_list_endpoints.py:63:        role_type="TEACHER",
backend\gradebook\tests\test_gradebook_list_endpoints.py:96:    _assign_role(user=user, school=school, role_code="TEACHER")
backend\gradebook\tests\test_gradebook_list_endpoints.py:113:    _assign_role(user=user, school=school, role_code="TEACHER")
backend\gradebook\tests\test_gradebook_list_endpoints.py:130:    _assign_role(user=user, school=school, role_code="TEACHER")
backend\gradebook\tests\test_gradebook_list_endpoints.py:150:    _assign_role(user=user, school=school, role_code="TEACHER")
backend\gradebook\tests\test_gradebook_list_endpoints.py:164:def test_assignments_list_non_teacher_role_forbidden():
backend\gradebook\tests\test_gradebook_list_endpoints.py:169:    _assign_role(user=user, school=school, role_code="PARENT")
backend\gradebook\tests\test_gradebook_list_endpoints.py:178:def test_students_list_non_teacher_role_forbidden():
backend\gradebook\tests\test_gradebook_list_endpoints.py:183:    _assign_role(user=user, school=school, role_code="PARENT")
backend\gradebook\tests\test_gradebook_list_endpoints.py:200:    _assign_role(user=user, school=school, role_code="TEACHER")
backend\gradebook\tests\test_gradebook_list_endpoints.py:222:    _assign_role(user=user, school=school, role_code="TEACHER")
backend\gradebook\tests\test_gradebook_list_endpoints.py:254:    _assign_role(user=user, school=school, role_code="TEACHER")
backend\gradebook\tests\test_gradebook_list_endpoints.py:291:    _assign_role(user=user, school=school, role_code="TEACHER")
backend\gradebook\tests\test_gradebook_drilldown.py:26:def _assign_role(*, user, school: School, role_code: str):
backend\gradebook\tests\test_gradebook_drilldown.py:27:    """Assign a role to the user."""
backend\gradebook\tests\test_gradebook_drilldown.py:28:    UserRole.objects.create(school=school, user=user, role_code=role_code)
backend\gradebook\tests\test_gradebook_drilldown.py:92:    _assign_role(user=user, school=school, role_code="HEAD_OF_SCHOOL")
backend\gradebook\tests\test_gradebook_drilldown.py:142:    _assign_role(user=user, school=school, role_code="HEAD_OF_SCHOOL")
backend\gradebook\tests\test_gradebook_drilldown.py:169:    _assign_role(user=user, school=school, role_code="HEAD_OF_SCHOOL")
backend\gradebook\tests\test_gradebook_api_smoke.py:35:def _assign_role(*, user, school: School, role_code: str):
backend\gradebook\tests\test_gradebook_api_smoke.py:36:    """Assign a role to the user."""
backend\gradebook\tests\test_gradebook_api_smoke.py:37:    UserRole.objects.create(school=school, user=user, role_code=role_code)
backend\gradebook\tests\test_gradebook_api_smoke.py:79:        role_type="TEACHER",
backend\gradebook\tests\test_gradebook_api_smoke.py:105:    _assign_role(user=user, school=school, role_code="TEACHER")
backend\gradebook\tests\test_gradebook_api_smoke.py:131:    _assign_role(user=user, school=school, role_code="TEACHER")
backend\invoice_run_wizard\views.py:7:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\invoice_run_wizard\views.py:8:from rest_framework.permissions import IsAuthenticated
backend\invoice_run_wizard\views.py:43:@permission_classes(_PERM)
backend\invoice_run_wizard\views.py:62:@permission_classes(_PERM)
backend\invoice_run_wizard\views.py:104:@permission_classes(_PERM)
backend\invoice_run_wizard\views.py:141:@permission_classes(_PERM)
backend\invoice_run_wizard\views.py:219:@permission_classes(_PERM)
backend\governance\views.py:1:from rest_framework.decorators import api_view, permission_classes
backend\governance\views.py:2:from rest_framework.permissions import IsAuthenticated
backend\governance\views.py:13:@permission_classes([IsAuthenticated])
backend\governance\views.py:21:@permission_classes([IsAuthenticated])
backend\guardian_household_wizard\views.py:14:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\guardian_household_wizard\views.py:15:from rest_framework.permissions import IsAuthenticated
backend\guardian_household_wizard\views.py:45:@permission_classes(_PERM)
backend\guardian_household_wizard\views.py:64:@permission_classes(_PERM)
backend\guardian_household_wizard\views.py:90:@permission_classes(_PERM)
backend\guardian_household_wizard\views.py:133:@permission_classes(_PERM)
backend\guardian_household_wizard\views.py:176:@permission_classes(_PERM)
backend\guardian_household_wizard\views.py:244:@permission_classes(_PERM)
backend\finance\migrations\0003_phase8_obligations_invoices_payments.py:12:        ('core', '0005_crown_permission_engine'),
backend\applications\views_admissions.py:15:from rest_framework.decorators import api_view, permission_classes
backend\applications\views_admissions.py:16:from rest_framework.permissions import AllowAny
backend\applications\views_admissions.py:17:from rest_framework.permissions import IsAuthenticated
backend\applications\views_admissions.py:21:from crown_api.tenant import resolve_tenant_school_id
backend\applications\views_admissions.py:893:@permission_classes([AllowAny])
backend\applications\views_admissions.py:900:    Resolve tenant school for admissions endpoints.
backend\applications\views_admissions.py:903:    In some test/dev contexts tenant enforcement is disabled, so we fall back to
backend\applications\views_admissions.py:910:    resolved = resolve_tenant_school_id(request)
backend\applications\views_admissions.py:916:                "detail": "Invalid X-School-Id (must be UUID).",
backend\applications\views_admissions.py:917:                "code": "invalid_tenant_header",
backend\applications\views_admissions.py:925:                "detail": "Missing required header: X-School-Id.",
backend\applications\views_admissions.py:926:                "code": "missing_tenant",
backend\applications\views_admissions.py:935:                "detail": "Unknown X-School-Id.",
backend\applications\views_admissions.py:936:                "code": "invalid_tenant",
backend\applications\views_admissions.py:947:    school, tenant_error = _resolve_school(request)
backend\applications\views_admissions.py:951:    error_code = (tenant_error.data or {}).get("code") if hasattr(tenant_error, "data") else None
backend\applications\views_admissions.py:952:    if error_code == "invalid_tenant_header":
backend\applications\views_admissions.py:953:        return None, tenant_error
backend\applications\views_admissions.py:959:            "Missing required header: X-School-Id. Provide inquiry.campus for public submit routing.",
backend\applications\views_admissions.py:960:            code="missing_tenant",
backend\applications\views_admissions.py:971:                "code": "invalid_tenant",
backend\applications\views_admissions.py:982:@permission_classes([IsAuthenticated])
backend\applications\views_admissions.py:985:    from core.permissions import user_has_permission
backend\applications\views_admissions.py:986:    school, tenant_error = _resolve_school(request)
backend\applications\views_admissions.py:987:    if tenant_error is not None:
backend\applications\views_admissions.py:988:        return tenant_error
backend\applications\views_admissions.py:989:    if not user_has_permission(request.user, "admissions.view", school=school):
backend\applications\views_admissions.py:1052:@permission_classes([AllowAny])
backend\applications\views_admissions.py:1057:    school, tenant_error = _resolve_school_for_submit(request, payload)
backend\applications\views_admissions.py:1058:    if tenant_error is not None:
backend\applications\views_admissions.py:1059:        return _attach_correlation(tenant_error, correlation_id)
backend\applications\views_admissions.py:1128:@permission_classes([IsAuthenticated])
backend\applications\views_admissions.py:1131:    from core.permissions import user_has_permission
backend\applications\views_admissions.py:1132:    school, tenant_error = _resolve_school(request)
backend\applications\views_admissions.py:1133:    if tenant_error is not None:
backend\applications\views_admissions.py:1134:        return tenant_error
backend\applications\views_admissions.py:1135:    if not user_has_permission(request.user, "admissions.view", school=school):
backend\guardian_household_wizard\tests\test_views.py:100:    def test_cross_tenant_returns_404(self):
backend\invoice_run_wizard\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
backend\financial_aid_wizard\views.py:8:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\financial_aid_wizard\views.py:9:from rest_framework.permissions import IsAuthenticated
backend\financial_aid_wizard\views.py:53:@permission_classes(_PERM)
backend\financial_aid_wizard\views.py:75:@permission_classes(_PERM)
backend\financial_aid_wizard\views.py:99:@permission_classes(_PERM)
backend\financial_aid_wizard\views.py:145:@permission_classes(_PERM)
backend\financial_aid_wizard\views.py:213:@permission_classes(_PERM)
backend\financial_aid_wizard\views.py:289:@permission_classes(_PERM)
backend\finance\api_views.py:4:Tenant isolation: every view calls get_request_school_id(request, required=True),
backend\finance\api_views.py:19:from rest_framework.decorators import api_view, permission_classes
backend\finance\api_views.py:20:from rest_framework.permissions import IsAuthenticated
backend\finance\api_views.py:81:@permission_classes([IsAuthenticated])
backend\finance\api_views.py:147:@permission_classes([IsAuthenticated])
backend\finance\api_views.py:204:@permission_classes([IsAuthenticated])
backend\finance\api_views.py:220:@permission_classes([IsAuthenticated])
backend\finance\api_views.py:254:@permission_classes([IsAuthenticated])
backend\finance\api_views.py:262:    explicit tenant context assertion.
backend\finance\api_views.py:265:    # user.school_id for payment operations (tenant isolation requirement).
backend\finance\api_views.py:315:@permission_classes([IsAuthenticated])
backend\finance\api_views.py:353:@permission_classes([IsAuthenticated])
backend\finance\api_views.py:398:@permission_classes([IsAuthenticated])
backend\finance\api_views.py:437:@permission_classes([IsAuthenticated])
backend\guardian_household_wizard\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
backend\applications\tests\test_admissions_tenant_scoping.py:2:Regression tests: cross-tenant header must NOT grant access to another school's
backend\applications\tests\test_admissions_tenant_scoping.py:9:  - View permission check uses school=request.school (School B instance).
backend\applications\tests\test_admissions_tenant_scoping.py:10:  - user_has_permission(user, "admissions.view", school=School B) -> False.
backend\applications\tests\test_admissions_tenant_scoping.py:36:        # Grant admissions.view permission to REGISTRAR role.
backend\applications\tests\test_admissions_tenant_scoping.py:41:        RolePermission.objects.get_or_create(role_code="REGISTRAR", permission=_perm)
backend\applications\tests\test_admissions_tenant_scoping.py:43:        # Assign REGISTRAR role at School A ONLY ΓÇö not at School B.
backend\applications\tests\test_admissions_tenant_scoping.py:44:        UserRole.objects.create(user=self.user, school=self.school_a, role_code="REGISTRAR")
backend\applications\tests\test_admissions_tenant_scoping.py:48:    # ΓöÇΓöÇ Cross-tenant ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
backend\applications\tests\test_admissions_tenant_scoping.py:50:    def test_summary_cross_tenant_header_is_403(self):
backend\applications\tests\test_admissions_tenant_scoping.py:58:    def test_drilldown_cross_tenant_header_is_403(self):
backend\ledger\api_finance.py:13:from rest_framework.decorators import api_view, permission_classes
backend\ledger\api_finance.py:14:from rest_framework.permissions import IsAuthenticated
backend\ledger\api_finance.py:30:            {"ok": False, "error": "X-School-Id header required"}, status=400
backend\ledger\api_finance.py:45:@permission_classes([IsAuthenticated])
backend\ledger\api_finance.py:67:@permission_classes([IsAuthenticated])
backend\ledger\api_finance.py:93:@permission_classes([IsAuthenticated])
backend\ledger\api_finance.py:105:@permission_classes([IsAuthenticated])
backend\ledger\api_finance.py:132:@permission_classes([IsAuthenticated])
backend\applications\tests\test_admissions_endpoints.py:27:        RolePermission.objects.get_or_create(role_code="REGISTRAR", permission=_perm)
backend\applications\tests\test_admissions_endpoints.py:34:        UserRole.objects.create(user=self.user, school=self.school, role_code="REGISTRAR")
backend\applications\tests\test_admissions_endpoints.py:158:        """Missing X-School-Id should return 400."""
backend\applications\tests\test_admissions_endpoints.py:161:        self.assertIn("X-School-Id", r.json()["detail"])
backend\applications\tests\test_admissions_endpoints.py:228:        # User must have a role at other_school now that permission is scoped.
backend\applications\tests\test_admissions_endpoints.py:229:        UserRole.objects.create(user=self.user, school=other_school, role_code="REGISTRAR")
backend\applications\tests\test_admissions_endpoints.py:241:        """Missing X-School-Id should return 400."""
backend\applications\tests\test_admissions_endpoints.py:347:        # User must have a role at other_school now that permission is scoped.
backend\applications\tests\test_admissions_endpoints.py:348:        UserRole.objects.create(user=self.user, school=other_school, role_code="REGISTRAR")
backend\applications\tests\test_admissions_endpoints.py:416:    def test_submit_requires_campus_when_no_tenant_header(self):
backend\applications\tests\test_admissions_endpoints.py:417:        """Public submit must include inquiry.campus when no tenant header is provided."""
backend\applications\tests\test_admissions_endpoints.py:425:        self.assertEqual(r.data.get("code"), "missing_tenant")
backend\applications\tests\test_admissions_endpoints.py:564:    def test_public_config_allows_missing_tenant_header(self):
backend\applications\tests\test_admissions_endpoints.py:565:        """Public config must be reachable without X-School-Id for public funnel bootstrap."""
backend\ledger\api.py:10:from rest_framework.decorators import api_view, permission_classes
backend\ledger\api.py:11:from rest_framework.permissions import IsAuthenticated
backend\ledger\api.py:117:@permission_classes([IsAuthenticated])
backend\ledger\api.py:151:@permission_classes([IsAuthenticated])
backend\ledger\api.py:174:@permission_classes([IsAuthenticated])
backend\ledger\api.py:221:@permission_classes([IsAuthenticated])
backend\ledger\api.py:447:@permission_classes([IsAuthenticated])
backend\ledger\api.py:514:@permission_classes([IsAuthenticated])
backend\ledger\api.py:575:# Phase 2 Priority 2 ΓÇö Ledger Invariants (read-only, tenant-scoped)
backend\ledger\api.py:580:@permission_classes([IsAuthenticated])
backend\ledger\api.py:601:    roles = set(
backend\ledger\api.py:603:        .values_list("role_code", flat=True)
backend\ledger\api.py:605:    if not roles.intersection({"HEAD_OF_SCHOOL", "FINANCE_DIRECTOR"}):
backend\ledger\api.py:606:        return _json_error("Forbidden: requires HEAD_OF_SCHOOL or FINANCE_DIRECTOR role.", status=403)
backend\ledger\api.py:664:@permission_classes([IsAuthenticated])
backend\ledger\api.py:695:@permission_classes([IsAuthenticated])
backend\financial_aid_wizard\tests\test_views.py:91:    def test_configure_isolation(self):
backend\financial_aid_wizard\tests\test_views.py:100:    def test_buckets_isolation(self):
backend\financial_aid_wizard\tests\test_views.py:109:    def test_awards_isolation(self):
backend\financial_aid_wizard\tests\test_views.py:118:    def test_commit_isolation(self):
backend\financial_aid_wizard\tests\test_views.py:127:    def test_verify_isolation(self):
backend\fee_schedule_wizard\views.py:12:Auth: JWT or Session. All endpoints tenant-scoped via X-School-Id.
backend\fee_schedule_wizard\views.py:21:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\fee_schedule_wizard\views.py:22:from rest_framework.permissions import IsAuthenticated
backend\fee_schedule_wizard\views.py:89:@permission_classes(_PERM)
backend\fee_schedule_wizard\views.py:110:@permission_classes(_PERM)
backend\fee_schedule_wizard\views.py:153:@permission_classes(_PERM)
backend\fee_schedule_wizard\views.py:205:@permission_classes(_PERM)
backend\fee_schedule_wizard\views.py:314:@permission_classes(_PERM)
backend\applications\models.py:24:	# multi-tenant anchor
backend\financial_aid_wizard\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
backend\journal\tests\test_journal_invariants.py:84:    def test_cross_tenant_account_fails(self):
backend\fee_schedule_wizard\tests\test_views.py:8:  - Tenant isolation (X-School-Id required; mismatch ΓåÆ 404)
backend\fee_schedule_wizard\tests\test_views.py:120:# Tenant isolation
backend\fee_schedule_wizard\tests\test_views.py:431:        # school_a schedule remains active (different tenant)
backend\fee_schedule_wizard\tests\test_views.py:433:        self.assertTrue(sched_a.is_active, "Cross-tenant schedule must not be deactivated")
backend\student360\api\views.py:13:from rest_framework import permissions
backend\student360\api\views.py:24:    Fail-closed tenant scoping helper.
backend\student360\api\views.py:34:        f"for tenant scoping in student360"
backend\student360\api\views.py:68:    sid = request.headers.get("X-School-Id")
backend\student360\api\views.py:183:    permission_classes = [permissions.IsAuthenticated]
backend\student360\api\views.py:523:    permission_classes = [permissions.IsAuthenticated]
backend\scripts\seed_households.py:85:        role=ROLE_PRIMARY_GUARDIAN,
backend\scripts\seed_households.py:91:        role=ROLE_FINANCIALLY_RESPONSIBLE,
backend\scripts\seed_households.py:97:        role=ROLE_GUARDIAN,
backend\scripts\seed_households.py:103:        role=ROLE_EMERGENCY_CONTACT,
backend\scripts\seed_households.py:109:        role=ROLE_AUTHORIZED_PICKUP,
backend\scripts\seed_households.py:125:        role=ROLE_PRIMARY_GUARDIAN,
backend\scripts\seed_households.py:131:        role=ROLE_FINANCIALLY_RESPONSIBLE,
backend\scripts\seed_households.py:137:        role=ROLE_GUARDIAN,
backend\scripts\seed_households.py:143:        role=ROLE_EMERGENCY_CONTACT,
backend\scripts\seed_households.py:149:        role=ROLE_AUTHORIZED_PICKUP,
backend\scripts\seed_comms.py:66:        role=ROLE_GUARDIAN,
backend\scripts\seed_comms.py:72:        role=ROLE_GUARDIAN,
backend\fee_schedule_wizard\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
backend\reenrollment\views.py:14:All endpoints are tenant-scoped via X-School-Id ΓåÆ get_request_school_id().
backend\reenrollment\views.py:15:Tenant isolation: every ReenrollmentSession lookup uses school=school on the FK.
backend\reenrollment\views.py:22:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\reenrollment\views.py:23:from rest_framework.permissions import IsAuthenticated
backend\reenrollment\views.py:56:@permission_classes(PERM_CLASSES)
backend\reenrollment\views.py:79:@permission_classes(PERM_CLASSES)
backend\reenrollment\views.py:142:@permission_classes(PERM_CLASSES)
backend\reenrollment\views.py:176:@permission_classes(PERM_CLASSES)
backend\reenrollment\views.py:225:@permission_classes(PERM_CLASSES)
backend\reenrollment\views.py:337:@permission_classes(PERM_CLASSES)
backend\staff_setup_wizard\views.py:7:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\staff_setup_wizard\views.py:8:from rest_framework.permissions import IsAuthenticated
backend\staff_setup_wizard\views.py:29:@permission_classes(_PERM)
backend\staff_setup_wizard\views.py:40:@permission_classes(_PERM)
backend\staff_setup_wizard\views.py:77:@permission_classes(_PERM)
backend\staff_setup_wizard\views.py:113:@permission_classes(_PERM)
backend\scripts\seed_academics_readonly.py:125:                "role_type": "TEACHER",
backend\promotion_wizard\views.py:7:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\promotion_wizard\views.py:8:from rest_framework.permissions import IsAuthenticated
backend\promotion_wizard\views.py:29:@permission_classes(_PERM)
backend\promotion_wizard\views.py:40:@permission_classes(_PERM)
backend\promotion_wizard\views.py:81:@permission_classes(_PERM)
backend\promotion_wizard\views.py:115:@permission_classes(_PERM)
backend\platform_ops\models.py:13:    Represents one attempt to fully provision a new school tenant.
backend\platform_ops\models.py:33:    # Link to the authoritative tenant entity
backend\platform_ops\models.py:84:    # school_id stored as UUID (not FK) ΓÇö some events are cross-tenant
backend\platform_ops\views.py:5:No X-School-ID header is required ΓÇö these are cross-tenant super-admin operations.
backend\platform_ops\views.py:9:  GET  /api/platform/schools/list            ΓÇö paginated list of all tenants
backend\platform_ops\views.py:20:from rest_framework.decorators import api_view, permission_classes
backend\platform_ops\views.py:21:from rest_framework.permissions import IsAdminUser
backend\platform_ops\views.py:34:@permission_classes([IsAdminUser])
backend\platform_ops\views.py:37:    Create a new school tenant and queue its provisioning job.
backend\platform_ops\views.py:122:@permission_classes([IsAdminUser])
backend\platform_ops\views.py:125:    Return a paginated list of all school tenants with TenantProfile data.
backend\platform_ops\views.py:132:    from tenants.models import TenantProfile  # noqa: PLC0415
backend\platform_ops\views.py:180:@permission_classes([IsAdminUser])
backend\reenrollment\tests\test_views.py:6:- Tenant isolation (cross-school session access denied on all 6 endpoints)
backend\reenrollment\tests\test_views.py:116:# 2. Tenant isolation
backend\platform_ops\migrations\0001_initial.py:13:        ('core', '0005_crown_permission_engine'),
backend\staff_setup_wizard\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
backend\platform_ops\provisioning.py:92:    Idempotently create a school tenant and queue its provisioning job.
backend\platform_ops\provisioning.py:105:    from tenants.models import SchoolSettings, TenantProfile  # noqa: PLC0415
backend\platform_ops\provisioning.py:183:    from tenants.models import TenantProfile  # noqa: PLC0415
backend\platform_ops\provisioning.py:212:            from tenants.models import SchoolSettings  # noqa: PLC0415
backend\scheduling_wizard\views.py:7:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\scheduling_wizard\views.py:8:from rest_framework.permissions import IsAuthenticated
backend\scheduling_wizard\views.py:50:@permission_classes(_PERM)
backend\scheduling_wizard\views.py:72:@permission_classes(_PERM)
backend\scheduling_wizard\views.py:101:@permission_classes(_PERM)
backend\scheduling_wizard\views.py:180:@permission_classes(_PERM)
backend\scheduling_wizard\views.py:251:@permission_classes(_PERM)
backend\scheduling_wizard\views.py:338:@permission_classes(_PERM)
backend\promotion_wizard\migrations\0001_initial.py:13:        ('core', '0005_crown_permission_engine'),
backend\scheduling_wizard\tests\test_views.py:86:    def test_configure_isolation(self):
backend\scheduling_wizard\tests\test_views.py:95:    def test_courses_isolation(self):
backend\scheduling_wizard\tests\test_views.py:104:    def test_sections_isolation(self):
backend\scheduling_wizard\tests\test_views.py:113:    def test_commit_isolation(self):
backend\scheduling_wizard\tests\test_views.py:122:    def test_verify_isolation(self):
backend\router_demo.py:22:logger.info("   2. User profile fields (persona, role, profile.persona, profile.role)")
backend\reenrollment\migrations\0001_initial.py:15:        ('core', '0005_crown_permission_engine'),
backend\scheduling_wizard\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
backend\staff_onboarding_wizard\views.py:14:  - Are tenant-scoped via X-School-Id header ΓåÆ get_request_school_id()
backend\staff_onboarding_wizard\views.py:15:  - Enforce school isolation: session lookups include school_id
backend\staff_onboarding_wizard\views.py:24:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\staff_onboarding_wizard\views.py:25:from rest_framework.permissions import IsAuthenticated
backend\staff_onboarding_wizard\views.py:62:@permission_classes(_PERM)
backend\staff_onboarding_wizard\views.py:83:@permission_classes(_PERM)
backend\staff_onboarding_wizard\views.py:91:    role_type  = (request.data.get("role_type")  or "").strip()
backend\staff_onboarding_wizard\views.py:100:    if not role_type:
backend\staff_onboarding_wizard\views.py:101:        errors.append("role_type is required")
backend\staff_onboarding_wizard\views.py:102:    elif role_type not in VALID_ROLES:
backend\staff_onboarding_wizard\views.py:103:        errors.append(f"role_type must be one of: {sorted(VALID_ROLES)}")
backend\staff_onboarding_wizard\views.py:111:    session.role_type  = role_type
backend\staff_onboarding_wizard\views.py:125:@permission_classes(_PERM)
backend\staff_onboarding_wizard\views.py:150:            "role_type":  session.role_type,
backend\staff_onboarding_wizard\views.py:167:@permission_classes(_PERM)
backend\staff_onboarding_wizard\views.py:188:                "role_type":  session.role_type,
backend\staff_onboarding_wizard\views.py:196:            "role_type": staff.role_type,
backend\staff_onboarding_wizard\views.py:217:                "role_type": result["role_type"],
backend\staff_onboarding_wizard\views.py:236:@permission_classes(_PERM)
backend\staff_onboarding_wizard\tests\test_views.py:8:  - Tenant isolation (X-School-Id required, mismatch ΓåÆ 404)
backend\staff_onboarding_wizard\tests\test_views.py:59:        "role_type":  "TEACHER",
backend\staff_onboarding_wizard\tests\test_views.py:120:# Tenant isolation
backend\staff_onboarding_wizard\tests\test_views.py:192:    def test_configure_invalid_role(self):
backend\staff_onboarding_wizard\tests\test_views.py:199:            _configure_payload(role_type="WIZARD_LORD"),
backend\staff_onboarding_wizard\tests\test_views.py:204:        self.assertIn("role_type must be one of", str(r2.data["errors"]))
backend\staff_onboarding_wizard\tests\test_views.py:206:    def test_all_valid_roles_accepted(self):
backend\staff_onboarding_wizard\tests\test_views.py:209:        for role in ("TEACHER", "DIRECTOR", "ADMIN", "SUPPORT"):
backend\staff_onboarding_wizard\tests\test_views.py:214:                _configure_payload(role_type=role, email=f"{role.lower()}_{uuid.uuid4().hex[:4]}@test.com"),
backend\staff_onboarding_wizard\tests\test_views.py:218:            self.assertEqual(r2.status_code, 200, f"Role {role} failed: {r2.data}")
backend\staff_onboarding_wizard\tests\test_views.py:250:            email=email, role_type="ADMIN"
backend\staff_onboarding_wizard\tests\test_views.py:294:            email=email, role_type="TEACHER"
backend\pdhub\api.py:2:from rest_framework.decorators import api_view, permission_classes
backend\pdhub\api.py:4:from rest_framework.permissions import IsAuthenticated
backend\pdhub\api.py:11:from core.permissions import CrownModulePermission, require_permission
backend\pdhub\api.py:20:        raise PermissionDenied("Tenant context required (X-School-Id header missing).")
backend\pdhub\api.py:26:    permission_classes = [CrownModulePermission("pd.view", write_code="pd.edit")]
backend\pdhub\api.py:53:    permission_classes = [CrownModulePermission("pd.view", write_code="pd.edit")]
backend\pdhub\api.py:78:@require_permission("pd.view")
backend\ledger\tests\test_ledger_invariants.py:38:    UserRole.objects.create(school_id=sid, user=user, role_code="HEAD_OF_SCHOOL")
backend\ledger\tests\test_ledger_invariants.py:87:# Test 3: over-allocation is detected + tenant isolation
backend\ledger\tests\test_ledger_invariants.py:113:# Test 4: tenant isolation ├óΓé¼ΓÇ¥ other school's violations invisible
backend\ledger\tests\test_ledger_invariants.py:116:def test_invariants_tenant_isolation():
backend\ledger\tests\test_ledger_invariants.py:120:    school_b's user must see clean=True (no cross-tenant bleed).
backend\ledger\tests\test_ledger_invariants.py:147:# Test 5: service rejects cross-tenant allocation (payment school_a, arg school_b)
backend\ledger\tests\test_ledger_invariants.py:150:def test_allocation_cross_tenant_guard():
backend\room_setup_wizard\views.py:7:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\room_setup_wizard\views.py:8:from rest_framework.permissions import IsAuthenticated
backend\room_setup_wizard\views.py:29:@permission_classes(_PERM)
backend\room_setup_wizard\views.py:40:@permission_classes(_PERM)
backend\room_setup_wizard\views.py:77:@permission_classes(_PERM)
backend\room_setup_wizard\views.py:107:@permission_classes(_PERM)
backend\staff_onboarding_wizard\models.py:8:    ΓåÆ configured   (POST /configure/  ΓÇö first_name, last_name, email, role_type)
backend\staff_onboarding_wizard\models.py:65:    role_type  = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True)
backend\room_setup_wizard\migrations\0001_initial.py:13:        ('core', '0005_crown_permission_engine'),
backend\runserver.ps1:2:# Runs Django development server with proper process isolation to prevent immediate exit
backend\ledger\signals.py:138:    # Find the original JE for this charge (tenant-safe by school_id)
backend\ledger\signals.py:186:    # Find the original JE for this payment (tenant-safe by school_id)
backend\staff_onboarding_wizard\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
backend\staff_onboarding_wizard\migrations\0001_initial.py:26:                ('role_type', models.CharField(blank=True, choices=[('TEACHER', 'Teacher'), ('DIRECTOR', 'Director'), ('ADMIN', 'Admin'), ('SUPPORT', 'Support')], max_length=20)),
backend\safety\api.py:2:from rest_framework.decorators import api_view, permission_classes
backend\safety\api.py:4:from rest_framework.permissions import IsAuthenticated
backend\safety\api.py:9:from core.permissions import CrownModulePermission
backend\safety\api.py:19:        raise PermissionDenied("Tenant context required (X-School-Id header missing).")
backend\safety\api.py:25:    permission_classes = [CrownModulePermission("safety.view", write_code="safety.edit")]
backend\safety\api.py:52:@permission_classes([IsAuthenticated])
backend\smoke_test_curriculum_demo.py:252:            log_pass(f"Scoping: School B sees 0 courses (correct isolation)")
backend\spiritual_life\api\views.py:4:from rest_framework import status, permissions
backend\spiritual_life\api\views.py:40:    Canonical tenant resolver for spiritual_life views.
backend\spiritual_life\api\views.py:42:    - Missing / invalid X-School-Id header ├óΓÇáΓÇÖ MissingSchoolContext (400)
backend\spiritual_life\api\views.py:53:    Returns True for Django staff users, superusers, and HEAD_OF_SCHOOL role holders.
backend\spiritual_life\api\views.py:57:    return user.roles.filter(role_code="HEAD_OF_SCHOOL").exists()
backend\spiritual_life\api\views.py:70:    permission_classes = [permissions.IsAuthenticated]
backend\spiritual_life\api\views.py:116:    permission_classes = [permissions.IsAuthenticated]
backend\spiritual_life\api\views.py:157:    permission_classes = [permissions.IsAuthenticated]
backend\spiritual_life\api\views.py:215:    permission_classes = [permissions.IsAuthenticated]
backend\spiritual_life\api\views.py:262:    permission_classes = [permissions.IsAuthenticated]
backend\spiritual_life\api\views.py:291:    permission_classes = [permissions.IsAuthenticated]
backend\spiritual_life\api\views.py:336:    permission_classes = [permissions.IsAuthenticated]
backend\spiritual_life\api\views.py:371:    permission_classes = [permissions.IsAuthenticated]
backend\spiritual_life\api\views.py:404:    permission_classes = [permissions.IsAuthenticated]
backend\spiritual_life\api\views.py:443:    permission_classes = [permissions.IsAuthenticated]
backend\spiritual_life\api\views.py:489:    permission_classes = [permissions.IsAuthenticated]
backend\spiritual_life\api\views.py:548:    permission_classes = [permissions.IsAuthenticated]
backend\spiritual_life\api\views.py:586:    permission_classes = [permissions.IsAuthenticated]
backend\spiritual_life\api\views.py:628:    permission_classes = [permissions.IsAuthenticated]
backend\solomon\models.py:34:    ROLE = "role", "Role"
backend\solomon\models.py:76:    role_code = models.CharField(max_length=64, blank=True, default="")
backend\section_staffing_wizard\views.py:16:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\section_staffing_wizard\views.py:17:from rest_framework.permissions import IsAuthenticated
backend\section_staffing_wizard\views.py:53:@permission_classes(_PERM)
backend\section_staffing_wizard\views.py:72:@permission_classes(_PERM)
backend\section_staffing_wizard\views.py:108:@permission_classes(_PERM)
backend\section_staffing_wizard\views.py:145:@permission_classes(_PERM)
backend\section_staffing_wizard\views.py:169:        role = a.get("role", "primary")
backend\section_staffing_wizard\views.py:170:        if role not in VALID_ROLES:
backend\section_staffing_wizard\views.py:171:            errors.append(f"assignments[{i}].role must be one of {sorted(VALID_ROLES)}")
backend\section_staffing_wizard\views.py:194:@permission_classes(_PERM)
backend\section_staffing_wizard\views.py:222:                    defaults={"role": a.get("role", "primary"), "school_id": school_id},
backend\section_staffing_wizard\views.py:243:@permission_classes(_PERM)
backend\section_assign_wizard\views.py:6:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\section_assign_wizard\views.py:7:from rest_framework.permissions import IsAuthenticated
backend\section_assign_wizard\views.py:49:@permission_classes(_PERM)
backend\section_assign_wizard\views.py:68:@permission_classes(_PERM)
backend\section_assign_wizard\views.py:112:@permission_classes(_PERM)
backend\section_assign_wizard\views.py:160:@permission_classes(_PERM)
backend\section_assign_wizard\views.py:214:@permission_classes(_PERM)
backend\section_assign_wizard\views.py:278:@permission_classes(_PERM)
backend\solomon\views.py:6:from rest_framework.decorators import api_view, permission_classes
backend\solomon\views.py:7:from rest_framework.permissions import IsAuthenticated
backend\solomon\views.py:10:from .permissions import solomon_api_enabled, can_access_governance_queue
backend\solomon\views.py:41:@permission_classes([IsAuthenticated])
backend\solomon\views.py:50:@permission_classes([IsAuthenticated])
backend\solomon\views.py:59:@permission_classes([IsAuthenticated])
backend\solomon\views.py:68:@permission_classes([IsAuthenticated])
backend\solomon\views.py:84:@permission_classes([IsAuthenticated])
backend\solomon\views.py:99:@permission_classes([IsAuthenticated])
backend\solomon\views.py:116:@permission_classes([IsAuthenticated])
backend\spiritual_life\tests\test_spiritual_life.py:80:def _assign_role(*, user: User, school: School, role_code: str) -> None:
backend\spiritual_life\tests\test_spiritual_life.py:81:    UserRole.objects.create(school=school, user=user, role_code=role_code)
backend\spiritual_life\tests\test_spiritual_life.py:125:        # User A sends school B's UUID ΓÇö non-staff, cross-tenant ΓåÆ 404
backend\spiritual_life\tests\test_spiritual_life.py:690:        # Non-staff user with TEACHER role
backend\spiritual_life\tests\test_spiritual_life.py:692:        _assign_role(user=user, school=school, role_code="TEACHER")
backend\spiritual_life\tests\test_spiritual_life.py:716:        _assign_role(user=teacher, school=school, role_code="TEACHER")
backend\spiritual_life\tests\test_spiritual_life.py:765:        _assign_role(user=teacher, school=school, role_code="TEACHER")
backend\spiritual_life\tests\test_spiritual_life.py:893:    def test_tenant_isolation_pastoral_notes(self):
backend\spiritual_life\tests\test_spiritual_life.py:905:        # Staff A (is_staff=True) can override tenant header ΓÇö so should only see school A's notes
backend\section_staffing_wizard\tests\test_views.py:20:    {"section_id": SECTIONS_POOL[0]["section_id"], "teacher_id": str(uuid.uuid4()), "role": "primary"},
backend\section_staffing_wizard\tests\test_views.py:99:        bad_assignment = [{"section_id": str(uuid.uuid4()), "teacher_id": str(uuid.uuid4()), "role": "primary"}]
backend\section_staffing_wizard\tests\test_views.py:110:    def test_cross_tenant_returns_404(self):
backend\solomon\migrations\0001_initial.py:28:                ("role_code", models.CharField(blank=True, default="", max_length=64)),
backend\solomon\migrations\0001_initial.py:226:                            ("role", "Role"),
backend\solomon\admin.py:35:    list_display = ("name", "slug", "role_code", "is_public")
backend\solomon\admin.py:36:    search_fields = ("name", "slug", "role_code", "description")
backend\spiritual_life\migrations\0001_initial_spiritual_life.py:14:        ('core', '0005_crown_permission_engine'),
backend\solomon\tests\test_review_queue.py:46:            role_code="test",
backend\solomon\tests\test_models.py:39:            role_code="teacher",
backend\solomon\tests\test_api.py:57:            role_code="teacher",
backend\solomon\tests\test_api.py:63:            role_code="director",
backend\solomon\tests\test_adapters.py:39:            role_code="parent",
backend\solomon\tests\test_adapters.py:161:            role_code="parent",
backend\solomon\tests\test_adapters.py:264:            role_code="student",
backend\solomon\tests\test_adapters.py:336:            role_code="student",
backend\solomon\tests\test_adapters.py:393:            role_code="student",
backend\section_staffing_wizard\models.py:41:    # [{section_id, teacher_id, role: "primary"|"aide"|"co-teacher"}]
backend\section_assign_wizard\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
backend\solomon\services.py:21:from .permissions import (
backend\solomon\services.py:61:		| Q(audiences__role_code__iexact=audience)
backend\solomon\services.py:129:			| Q(audience__role_code__iexact=normalized_text(audience))
backend\solomon\services.py:233:	RBAC visibility is NOT enforced here (staff/admin only via view permission).
backend\solomon\services.py:386:	Fail-closed: returns empty queryset if request permission cannot be determined.
backend\signals\migrations\0002_rebuild_uuid_fks.py:25:        ("core", "0005_crown_permission_engine"),
backend\solomon\adapters\base.py:22:    request: Optional[HttpRequest] = None  # Current request for tenant context
backend\solomon\serializers.py:16:from .permissions import can_view_restricted_solomon_content
backend\solomon\serializers.py:36:		fields = ("id", "name", "slug", "role_code", "description", "is_public")
backend\section_staffing_wizard\migrations\0001_initial.py:14:        ('core', '0005_crown_permission_engine'),
backend\solomon\permissions.py:22:	role_value = str(
backend\solomon\permissions.py:23:		getattr(user, "role", "") or getattr(user, "role_code", "") or ""
backend\solomon\permissions.py:25:	return role_value in {"admin", "staff"}
backend\solomon\permissions.py:85:	role_value = str(
backend\solomon\permissions.py:86:		getattr(user, "role", "") or getattr(user, "role_code", "") or ""
backend\solomon\permissions.py:88:	return role_value in {"admin", "staff"}
backend\servicehours\api\views.py:4:from rest_framework import permissions
backend\servicehours\api\views.py:16:    school_id = request.headers.get("X-School-Id")
backend\servicehours\api\views.py:25:    permission_classes = [permissions.IsAuthenticated]
backend\servicehours\api\views.py:73:    permission_classes = [permissions.IsAuthenticated]
backend\servicehours\api\views.py:98:    permission_classes = [permissions.IsAuthenticated]
backend\servicehours\api\views.py:109:    permission_classes = [permissions.IsAuthenticated]
backend\signals\api.py:5:from .tenant import school_id_from_request
backend\section_scheduler_wizard\migrations\0001_initial.py:13:        ('core', '0005_crown_permission_engine'),
backend\section_scheduler_wizard\migrations\0002_initial.py:12:        ('core', '0005_crown_permission_engine'),
backend\section_scheduler_wizard\views.py:9:from rest_framework.decorators import api_view, authentication_classes, permission_classes
backend\section_scheduler_wizard\views.py:10:from rest_framework.permissions import IsAuthenticated
backend\section_scheduler_wizard\views.py:37:@permission_classes(_PERM)
backend\section_scheduler_wizard\views.py:48:@permission_classes(_PERM)
backend\section_scheduler_wizard\views.py:88:@permission_classes(_PERM)
backend\section_scheduler_wizard\views.py:151:@permission_classes(_PERM)
backend\section_scheduler_wizard\views.py:241:@permission_classes(_PERM)
backend\signals\management\commands\compute_signals.py:14:            help="UUID primary key of the tenant School record",
