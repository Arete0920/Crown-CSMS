/**
 * Wizard Route Registry — Crown2026
 * ===================================
 * Single source of truth for all setup wizard routes.
 *
 * To add a new wizard:
 *   1. Create pages/<WizardName>Wizard.jsx + pages/<wizard_name>_wizard/Step*.jsx
 *   2. Create api/<wizard_name>_wizard.js
 *   3. Add ONE entry to WIZARD_REGISTRY below.
 *   4. router.jsx auto-picks it up via `...wizardRoutes()`.
 *
 * Fields:
 *   path        — browser route path (e.g. '/comms-setup')
 *   component   — React component (statically imported)
 *   name        — human-readable label (used for nav, titles, auditing)
 *   apiPrefix   — backend session URL (for cross-referencing with contract test)
 *   roles       — which roles may access this wizard (optional, for future guard)
 */

import { createElement } from 'react';
import RoleRouteGuard from '../components/routing/RoleRouteGuard.jsx';
import ReleaseStateRoute from '../components/routing/ReleaseStateRoute.jsx';
import { WIZARD_SLUGS } from './wizard-manifest.js';

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
// ↓ Add new wizard imports here
import SectionSchedulerWizard from '../pages/SectionSchedulerWizard.jsx';
import StaffSetupWizard from '../pages/StaffSetupWizard.jsx';
import CourseCatalogWizard from '../pages/CourseCatalogWizard.jsx';
import RoomSetupWizard from '../pages/RoomSetupWizard.jsx';
import PromotionWizard from '../pages/PromotionWizard.jsx';

const readyReadiness = () => ({
  shellReady: true,
  uxReady: true,
  accessReady: true,
  dataReady: true,
});

const placeholderReadiness = () => ({
  shellReady: true,
  uxReady: false,
  accessReady: true,
  dataReady: false,
});

const RAW_WIZARD_ROUTE_DEFINITIONS = [
  {
    path: '/onboarding',
    component: AdmissionsIntakeWizard,
    name: 'Student Onboarding',
    apiPrefix: '/api/v1/onboarding/imports/',
    roles: ['super_admin', 'school_admin', 'admissions_manager'],
  },
  {
    path: '/reenrollment',
    component: ReenrollmentWizard,
    name: 'Re-enrollment',
    apiPrefix: '/api/v1/reenrollment/sessions/',
    roles: ['super_admin', 'school_admin', 'registrar'],
  },
  {
    path: '/billing-setup',
    component: BillingWizard,
    name: 'Billing Setup',
    apiPrefix: '/api/v1/billing-wizard/sessions/',
    roles: ['admin', 'finance'],
  },
  {
    path: '/aid-setup',
    component: FinancialAidWizard,
    name: 'Financial Aid Setup',
    apiPrefix: '/api/v1/aid-wizard/sessions/',
    roles: ['super_admin', 'school_admin', 'finance_admin'],
  },
  {
    path: '/scheduling-setup',
    component: SchedulingWizard,
    name: 'Scheduling Setup',
    apiPrefix: '/api/v1/scheduling-wizard/sessions/',
    roles: ['admin', 'academics'],
  },
  {
    path: '/comms-setup',
    component: CommsWizard,
    name: 'Communications Campaign',
    apiPrefix: '/api/v1/comms-wizard/sessions/',
    roles: ['admin', 'communications'],
  },
  {
    path: '/section-assign-setup',
    component: SectionAssignWizard,
    name: 'Section Assignments',
    apiPrefix: '/api/v1/section-assign-wizard/sessions/',
    roles: ['admin', 'academics'],
  },
  {
    path: '/bell-schedule-setup',
    component: BellScheduleWizard,
    name: 'Bell Schedule',
    apiPrefix: '/api/v1/bell-schedule-wizard/sessions/',
    roles: ['admin', 'academics'],
  },
  {
    path: '/gradebook-setup',
    component: GradebookSetupWizard,
    name: 'Gradebook Setup',
    apiPrefix: '/api/v1/gradebook-setup-wizard/sessions/',
    roles: ['admin', 'academics'],
  },
  {
    path: '/attendance-rules-setup',
    component: AttendanceRulesWizard,
    name: 'Attendance Rules',
    apiPrefix: '/api/v1/attendance-rules-wizard/sessions/',
    roles: ['admin', 'academics', 'registrar'],
  },
  {
    path: '/enrollment-conversion',
    component: EnrollmentConversionWizard,
    name: 'Enrollment Conversion',
    apiPrefix: '/api/v1/enrollment-conversion-wizard/sessions/',
    roles: ['super_admin', 'school_admin', 'admissions_manager', 'registrar'],
  },
  {
    path: '/invoice-run',
    component: InvoiceRunWizard,
    name: 'Invoice Run',
    apiPrefix: '/api/v1/invoice-run-wizard/sessions/',
    roles: ['admin', 'finance'],
  },
  {
    path: '/staff-onboarding',
    component: StaffOnboardingWizard,
    name: 'Staff Onboarding',
    apiPrefix: '/api/v1/staff-onboarding-wizard/sessions/',
    roles: ['admin', 'director', 'hr'],
  },
  {
    path: '/fee-schedule-setup',
    component: FeeScheduleWizard,
    name: 'Fee Schedule Setup',
    apiPrefix: '/api/v1/fee-schedule-wizard/sessions/',
    roles: ['admin', 'finance', 'director'],
  },
  {
    path: '/academic-year-rollover',
    component: AcademicYearWizard,
    name: 'Academic Year Rollover',
    apiPrefix: '/api/v1/academic-year-wizard/sessions/',
    roles: ['admin', 'director'],
  },
  {
    path: '/enrollment-period-setup',
    component: EnrollmentPeriodWizard,
    name: 'Enrollment Period Setup',
    apiPrefix: '/api/v1/enrollment-period-wizard/sessions/',
    roles: ['super_admin', 'school_admin', 'registrar'],
  },
  {
    path: '/grade-scale-setup',
    component: GradeScaleWizard,
    name: 'Grade Scale Setup',
    apiPrefix: '/api/v1/grade-scale-wizard/sessions/',
    roles: ['admin', 'academics', 'director'],
  },
  {
    path: '/term-structure-setup',
    component: TermStructureWizard,
    name: 'Term Structure Setup',
    apiPrefix: '/api/v1/term-structure-wizard/sessions/',
    roles: ['admin', 'academics', 'director'],
  },
  // ↓ Add new wizard entries here
  {
    path: '/section-scheduler-setup',
    component: SectionSchedulerWizard,
    name: 'Section Scheduler Seed',
    apiPrefix: '/api/v1/section-scheduler-wizard/sessions/',
    roles: ['admin', 'academics', 'director'],
  },
  {
    path: '/staff-setup',
    component: StaffSetupWizard,
    name: 'Staff & Roles Setup',
    apiPrefix: '/api/v1/staff-setup-wizard/sessions/',
    roles: ['admin', 'director'],
  },
  {
    path: '/course-catalog-setup',
    component: CourseCatalogWizard,
    name: 'Course Catalog Setup',
    apiPrefix: '/api/v1/course-catalog-wizard/sessions/',
    roles: ['admin', 'academics', 'director'],
  },
  {
    path: '/room-setup',
    component: RoomSetupWizard,
    name: 'Rooms Setup',
    apiPrefix: '/api/v1/room-setup-wizard/sessions/',
    roles: ['admin', 'director'],
  },
  {
    path: '/promotion-setup',
    component: PromotionWizard,
    name: 'Promotion Map Setup',
    apiPrefix: '/api/v1/promotion-wizard/sessions/',
    roles: ['admin', 'academics', 'director'],
  },
];

function normalizeWizardRoute(route) {
  const releaseState = route.releaseState || 'ready';
  const readiness = route.readiness || (releaseState === 'ready' ? readyReadiness() : placeholderReadiness());

  return {
    ...route,
    moduleKey: route.moduleKey || route.path.replace(/^\//, '') || route.name,
    moduleType: route.moduleType || 'wizard',
    owner: route.owner || 'wizardRoutes',
    releaseState,
    readiness,
  };
}

export const WIZARD_ROUTE_DEFINITIONS = RAW_WIZARD_ROUTE_DEFINITIONS.map(normalizeWizardRoute);

// Backward compatibility for existing imports in tests/components.
export const WIZARD_REGISTRY = WIZARD_ROUTE_DEFINITIONS;

/**
 * Slugs imported from wizard-manifest.js (React-free) — safe for Playwright tests.
 * Re-exported here for consumers within the app.
 */
export { WIZARD_SLUGS };

function buildWizardElement(route) {
  const element = createElement(route.component);
  const wrappedElement = createElement(ReleaseStateRoute, { route }, element);

  if (Array.isArray(route.roles) && route.roles.length > 0) {
    return createElement(RoleRouteGuard, { allowedRoles: route.roles || [] }, wrappedElement);
  }

  return wrappedElement;
}

/**
 * Returns React Router route objects for all registered wizards.
 * Spread into the routes array in router.jsx.
 *
 * Usage:
 *   import { wizardRoutes } from './wizards.js';
 *   ...
 *   export const router = createBrowserRouter([
 *     ...otherRoutes,
 *     ...wizardRoutes(),
 *   ]);
 */
export function wizardRoutes() {
  return WIZARD_ROUTE_DEFINITIONS.map((route) => ({
    path: route.path,
    element: buildWizardElement(route),
  }));
}

export default wizardRoutes;
