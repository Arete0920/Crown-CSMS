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
import { WIZARD_SLUGS } from './wizard-manifest.js';

import AdmissionsIntakeWizard from '../pages/AdmissionsIntakeWizard.jsx';
import ReenrollmentWizard     from '../pages/ReenrollmentWizard.jsx';
import BillingWizard          from '../pages/BillingWizard.jsx';
import FinancialAidWizard     from '../pages/FinancialAidWizard.jsx';
import SchedulingWizard       from '../pages/SchedulingWizard.jsx';
import CommsWizard            from '../pages/CommsWizard.jsx';
import SectionAssignWizard         from '../pages/SectionAssignWizard.jsx';
import BellScheduleWizard          from '../pages/BellScheduleWizard.jsx';
import GradebookSetupWizard        from '../pages/GradebookSetupWizard.jsx';
import AttendanceRulesWizard       from '../pages/AttendanceRulesWizard.jsx';
import EnrollmentConversionWizard  from '../pages/EnrollmentConversionWizard.jsx';
import InvoiceRunWizard            from '../pages/InvoiceRunWizard.jsx';
import StaffOnboardingWizard       from '../pages/StaffOnboardingWizard.jsx';
// ↓ Add new wizard imports here

export const WIZARD_REGISTRY = [
  {
    path:      '/onboarding',
    component: AdmissionsIntakeWizard,
    name:      'Student Onboarding',
    apiPrefix: '/api/v1/onboarding/imports/',
    roles:     ['admin', 'registrar', 'admissions'],
  },
  {
    path:      '/reenrollment',
    component: ReenrollmentWizard,
    name:      'Re-enrollment',
    apiPrefix: '/api/v1/reenrollment/sessions/',
    roles:     ['admin', 'registrar', 'finance'],
  },
  {
    path:      '/billing-setup',
    component: BillingWizard,
    name:      'Billing Setup',
    apiPrefix: '/api/v1/billing-wizard/sessions/',
    roles:     ['admin', 'finance'],
  },
  {
    path:      '/aid-setup',
    component: FinancialAidWizard,
    name:      'Financial Aid Setup',
    apiPrefix: '/api/v1/aid-wizard/sessions/',
    roles:     ['admin', 'finance'],
  },
  {
    path:      '/scheduling-setup',
    component: SchedulingWizard,
    name:      'Scheduling Setup',
    apiPrefix: '/api/v1/scheduling-wizard/sessions/',
    roles:     ['admin', 'academics'],
  },
  {
    path:      '/comms-setup',
    component: CommsWizard,
    name:      'Communications Campaign',
    apiPrefix: '/api/v1/comms-wizard/sessions/',
    roles:     ['admin', 'communications'],
  },
  {
    path:      '/section-assign-setup',
    component: SectionAssignWizard,
    name:      'Section Assignments',
    apiPrefix: '/api/v1/section-assign-wizard/sessions/',
    roles:     ['admin', 'academics'],
  },
  {
    path:      '/bell-schedule-setup',
    component: BellScheduleWizard,
    name:      'Bell Schedule',
    apiPrefix: '/api/v1/bell-schedule-wizard/sessions/',
    roles:     ['admin', 'academics'],
  },
  {
    path:      '/gradebook-setup',
    component: GradebookSetupWizard,
    name:      'Gradebook Setup',
    apiPrefix: '/api/v1/gradebook-setup-wizard/sessions/',
    roles:     ['admin', 'academics'],
  },
  {
    path:      '/attendance-rules-setup',
    component: AttendanceRulesWizard,
    name:      'Attendance Rules',
    apiPrefix: '/api/v1/attendance-rules-wizard/sessions/',
    roles:     ['admin', 'academics', 'registrar'],
  },
  {
    path:      '/enrollment-conversion',
    component: EnrollmentConversionWizard,
    name:      'Enrollment Conversion',
    apiPrefix: '/api/v1/enrollment-conversion-wizard/sessions/',
    roles:     ['admin', 'registrar', 'admissions'],
  },
  {
    path:      '/invoice-run',
    component: InvoiceRunWizard,
    name:      'Invoice Run',
    apiPrefix: '/api/v1/invoice-run-wizard/sessions/',
    roles:     ['admin', 'finance'],
  },
  {
    path:      '/staff-onboarding',
    component: StaffOnboardingWizard,
    name:      'Staff Onboarding',
    apiPrefix: '/api/v1/staff-onboarding-wizard/sessions/',
    roles:     ['admin', 'director', 'hr'],
  },
  // ↓ Add new wizard entries here
];

/**
 * Slugs imported from wizard-manifest.js (React-free) — safe for Playwright tests.
 * Re-exported here for consumers within the app.
 */
export { WIZARD_SLUGS };

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
  return WIZARD_REGISTRY.map(({ path, component }) => ({
    path,
    element: createElement(component),
  }));
}
