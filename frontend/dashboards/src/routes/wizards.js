import { createElement } from 'react';
import RoleRouteGuard from '../components/routing/RoleRouteGuard.jsx';
import ReleaseStateRoute from '../components/routing/ReleaseStateRoute.jsx';
export { WIZARD_SLUGS } from './wizard-manifest.js';

import AdmissionsIntakeWizard from '../pages/AdmissionsIntakeWizard.jsx';
import ReenrollmentWizard from '../pages/ReenrollmentWizard.jsx';
import BillingWizard from '../pages/BillingWizard.jsx';
import FinancialAidWizard from '../pages/FinancialAidWizard.jsx';
import SchedulingWizard from '../pages/SchedulingWizard.jsx';
import CommsWizard from '../pages/CommsWizard.jsx';
import SectionAssignWizard from '../pages/SectionAssignWizard.jsx';
import BellScheduleWizard from '../pages/BellScheduleWizard.jsx';
import GradebookSetupWizard from '../pages/GradebookSetupWizard.jsx';
import AttendanceRulesWizard from '../pages/AttendanceRulesWizard.jsx';
import EnrollmentConversionWizard from '../pages/EnrollmentConversionWizard.jsx';
import InvoiceRunWizard from '../pages/InvoiceRunWizard.jsx';
import StaffOnboardingWizard from '../pages/StaffOnboardingWizard.jsx';
import FeeScheduleWizard from '../pages/FeeScheduleWizard.jsx';
import AcademicYearWizard from '../pages/AcademicYearWizard.jsx';
import EnrollmentPeriodWizard from '../pages/EnrollmentPeriodWizard.jsx';
import GradeScaleWizard from '../pages/GradeScaleWizard.jsx';
import TermStructureWizard from '../pages/TermStructureWizard.jsx';
import SectionSchedulerWizard from '../pages/SectionSchedulerWizard.jsx';
import StaffSetupWizard from '../pages/StaffSetupWizard.jsx';
import CourseCatalogWizard from '../pages/CourseCatalogWizard.jsx';
import RoomSetupWizard from '../pages/RoomSetupWizard.jsx';
import PromotionWizard from '../pages/PromotionWizard.jsx';
import StudentImportWizard from '../pages/StudentImportWizard.jsx';
import SetupWizardA from '../pages/SetupWizardA.jsx';
import SetupWizardC from '../pages/SetupWizardC.jsx';
import AttendanceSetupWizard from '../pages/AttendanceSetupWizard.jsx';
import CategoriesWizard from '../pages/CategoriesWizard.jsx';

import DisciplinePage from '../pages/DisciplinePage.jsx';
import FinanceDashboard from '../pages/FinanceDashboard.jsx';
import CrownLaunchModulePage from '../pages/CrownLaunchModulePage.jsx';
import SchoolSettingsPage from '../pages/SchoolSettingsPage.jsx';
import OpsCommandCenter from '../components/OpsCommandCenter.jsx';

const readyReadiness = () => ({ shellReady: true, uxReady: true, accessReady: true, dataReady: true });
const placeholderReadiness = () => ({ shellReady: true, uxReady: false, accessReady: true, dataReady: false });
const readyWizardEvidence = () => ({
  artifact: 'audit-artifacts/wizard-independent-review/20260614_070313',
  collectedAt: '2026-06-14T07:03:13Z',
  candidateSha: '8097d4c23e847bfaced4d9a49637a3aa0e20617b',
  releaseBranch: 'main',
});

const RAW_WIZARD_ROUTE_DEFINITIONS = [
  { path: '/onboarding', component: AdmissionsIntakeWizard, name: 'Student Onboarding', apiPrefix: '/api/v1/onboarding/imports/', roles: ['super_admin', 'school_admin', 'admissions_manager'] },
  { path: '/reenrollment', component: ReenrollmentWizard, name: 'Re-enrollment', apiPrefix: '/api/v1/reenrollment/sessions/', roles: ['super_admin', 'school_admin', 'registrar'] },
  { path: '/billing-setup', component: BillingWizard, name: 'Billing Setup', apiPrefix: '/api/v1/billing-wizard/sessions/', roles: ['admin', 'finance'] },
  { path: '/aid-setup', component: FinancialAidWizard, name: 'Financial Aid Setup', apiPrefix: '/api/v1/aid-wizard/sessions/', roles: ['super_admin', 'school_admin', 'finance_admin'] },
  { path: '/scheduling-setup', component: SchedulingWizard, name: 'Scheduling Setup', apiPrefix: '/api/v1/scheduling-wizard/sessions/', roles: ['admin', 'academics'] },
  { path: '/comms-setup', component: CommsWizard, name: 'Communications Campaign', apiPrefix: '/api/v1/comms-wizard/sessions/', roles: ['admin', 'communications'] },
  { path: '/section-assign-setup', component: SectionAssignWizard, name: 'Section Assignments', apiPrefix: '/api/v1/section-assign-wizard/sessions/', roles: ['admin', 'academics'] },
  { path: '/bell-schedule-setup', component: BellScheduleWizard, name: 'Bell Schedule', apiPrefix: '/api/v1/bell-schedule-wizard/sessions/', roles: ['admin', 'academics'] },
  { path: '/gradebook-setup', component: GradebookSetupWizard, name: 'Gradebook Setup', apiPrefix: '/api/v1/gradebook-setup-wizard/sessions/', roles: ['admin', 'academics'] },
  { path: '/attendance-rules-setup', component: AttendanceRulesWizard, name: 'Attendance Rules', apiPrefix: '/api/v1/attendance-rules-wizard/sessions/', roles: ['admin', 'academics', 'registrar'] },
  { path: '/enrollment-conversion', component: EnrollmentConversionWizard, name: 'Enrollment Conversion', apiPrefix: '/api/v1/enrollment-conversion-wizard/sessions/', roles: ['super_admin', 'school_admin', 'admissions_manager', 'registrar'] },
  { path: '/invoice-run', component: InvoiceRunWizard, name: 'Invoice Run', apiPrefix: '/api/v1/invoice-run-wizard/sessions/', roles: ['admin', 'finance'] },
  { path: '/staff-onboarding', component: StaffOnboardingWizard, name: 'Staff Onboarding', apiPrefix: '/api/v1/staff-onboarding-wizard/sessions/', roles: ['admin', 'director', 'hr'] },
  { path: '/fee-schedule-setup', component: FeeScheduleWizard, name: 'Fee Schedule Setup', apiPrefix: '/api/v1/fee-schedule-wizard/sessions/', roles: ['admin', 'finance', 'director'] },
  { path: '/academic-year-rollover', component: AcademicYearWizard, name: 'Academic Year Rollover', apiPrefix: '/api/v1/academic-year-wizard/sessions/', roles: ['admin', 'director'] },
  { path: '/enrollment-period-setup', component: EnrollmentPeriodWizard, name: 'Enrollment Period Setup', apiPrefix: '/api/v1/enrollment-period-wizard/sessions/', roles: ['super_admin', 'school_admin', 'registrar'] },
  { path: '/grade-scale-setup', component: GradeScaleWizard, name: 'Grade Scale Setup', apiPrefix: '/api/v1/grade-scale-wizard/sessions/', roles: ['admin', 'academics', 'director'] },
  { path: '/term-structure-setup', component: TermStructureWizard, name: 'Term Structure Setup', apiPrefix: '/api/v1/term-structure-wizard/sessions/', roles: ['admin', 'academics', 'director'] },
  { path: '/section-scheduler-setup', component: SectionSchedulerWizard, name: 'Section Scheduler Seed', apiPrefix: '/api/v1/section-scheduler-wizard/sessions/', roles: ['admin', 'academics', 'director'] },
  { path: '/staff-setup', component: StaffSetupWizard, name: 'Staff & Roles Setup', apiPrefix: '/api/v1/staff-setup-wizard/sessions/', roles: ['admin', 'director'] },
  { path: '/course-catalog-setup', component: CourseCatalogWizard, name: 'Course Catalog Setup', apiPrefix: '/api/v1/course-catalog-wizard/sessions/', roles: ['admin', 'academics', 'director'] },
  { path: '/room-setup', component: RoomSetupWizard, name: 'Rooms Setup', apiPrefix: '/api/v1/room-setup-wizard/sessions/', roles: ['admin', 'director'] },
  { path: '/promotion-setup', component: PromotionWizard, name: 'Promotion Map Setup', apiPrefix: '/api/v1/promotion-wizard/sessions/', roles: ['admin', 'academics', 'director'] },
  { path: '/student-import-setup', component: StudentImportWizard, name: 'Student Import', apiPrefix: '/api/v1/student-import-wizard/sessions/', roles: ['super_admin', 'school_admin', 'registrar', 'admin'], releaseState: 'ready', evidence: readyWizardEvidence() },
  { path: '/guardian-household-setup', component: SetupWizardA, name: 'Guardian & Household Setup', apiPrefix: '/api/v1/guardian-household-wizard/sessions/', roles: ['super_admin', 'school_admin', 'registrar', 'admin'], releaseState: 'draft' },
  { path: '/section-staffing-setup', component: SetupWizardC, name: 'Section Staffing', apiPrefix: '/api/v1/section-staffing-wizard/sessions/', roles: ['super_admin', 'school_admin', 'academics', 'admin'], releaseState: 'ready', evidence: readyWizardEvidence() },
  { path: '/attendance-codes-setup', component: AttendanceSetupWizard, name: 'Attendance Codes Setup', apiPrefix: '/api/v1/attendance-codes-wizard/sessions/', roles: ['super_admin', 'school_admin', 'registrar', 'academics', 'admin'], releaseState: 'ready', evidence: readyWizardEvidence() },
  { path: '/grade-weights-setup', component: CategoriesWizard, name: 'Grade Weights & Categories', apiPrefix: '/api/v1/grade-weights-wizard/sessions/', roles: ['super_admin', 'school_admin', 'academics', 'admin'], releaseState: 'ready', evidence: readyWizardEvidence() },
];

function normalizeWizardRoute(route) {
  const releaseState = route.releaseState || 'draft';
  const isReadyLike = ['ready', 'live', 'production'].includes(releaseState);
  const readiness = route.readiness || (isReadyLike ? readyReadiness() : placeholderReadiness());
  return { ...route, moduleKey: route.moduleKey || route.path.replace(/^\//, '') || route.name, moduleType: route.moduleType || 'wizard', owner: route.owner || 'wizardRoutes', releaseState, readiness };
}

export const WIZARD_ROUTE_DEFINITIONS = RAW_WIZARD_ROUTE_DEFINITIONS.map(normalizeWizardRoute);
export const WIZARD_REGISTRY = WIZARD_ROUTE_DEFINITIONS;

function buildWizardElement(route) {
  const element = createElement(route.component);
  const wrappedElement = createElement(ReleaseStateRoute, { route }, element);
  if (Array.isArray(route.roles) && route.roles.length > 0) {
    return createElement(RoleRouteGuard, { allowedRoles: route.roles || [] }, wrappedElement);
  }
  return wrappedElement;
}

const FINANCE_ALIAS_ROLES = ['super_admin', 'school_admin', 'head_of_school', 'finance_admin', 'finance', 'biz_office', 'finance_director', 'admin', 'director', 'principal'];
const ACADEMIC_ALIAS_ROLES = ['super_admin', 'school_admin', 'head_of_school', 'academic_admin', 'teacher', 'registrar', 'admin'];
const OPS_ALIAS_ROLES = ['super_admin', 'master_control', 'school_admin', 'head_of_school'];
const SCHOOL_SETTINGS_ALIAS_ROLES = ['super_admin', 'master_control', 'head_of_school'];
const IS_SANDBOX = Boolean(import.meta.env.VITE_DEMO_MODE === 'sandbox' || import.meta.env.VITE_SANDBOX_MODE === '1');
const IS_LAUNCH_PREVIEW = Boolean(import.meta.env.DEV || IS_SANDBOX || import.meta.env.VITE_LAUNCH_UI_TAKEOVER === '1');

function guarded(roles, child) {
  return createElement(RoleRouteGuard, { allowedRoles: roles }, child);
}

function financeAlias(path) {
  const child = IS_LAUNCH_PREVIEW
    ? createElement(CrownLaunchModulePage, { moduleKey: 'finance', activePath: path })
    : createElement(FinanceDashboard);
  return guarded(FINANCE_ALIAS_ROLES, child);
}

const ADVERTISED_ALIAS_ROUTES = [
  { path: '/discipline', element: guarded(ACADEMIC_ALIAS_ROLES, createElement(DisciplinePage)) },
  { path: '/finance/bank-reconciliation', element: financeAlias('/finance/bank-reconciliation') },
  { path: '/finance/dispute-workbench', element: financeAlias('/finance/dispute-workbench') },
  { path: '/finance/disputes', element: financeAlias('/finance/disputes') },
  { path: '/finance/payout-reconciliation', element: financeAlias('/finance/payout-reconciliation') },
  { path: '/ops', element: guarded(OPS_ALIAS_ROLES, createElement(OpsCommandCenter)) },
  { path: '/profile', element: guarded(SCHOOL_SETTINGS_ALIAS_ROLES, createElement(SchoolSettingsPage)) },
];

export function wizardRoutes() {
  return [
    ...WIZARD_ROUTE_DEFINITIONS.map((route) => ({ path: route.path, element: buildWizardElement(route) })),
    ...ADVERTISED_ALIAS_ROUTES,
  ];
}

export default wizardRoutes;
