/**
 * Wizard manifest — Crown2026
 * ============================
 * NO React imports. Safe to use from Playwright tests, Node scripts, and the app.
 *
 * Slugs must match backend wizard_registry.py → url_prefix segment [2].
 * e.g.  url_prefix "api/v1/billing-wizard/sessions/" → slug "billing-wizard"
 *
 * To add a wizard:
 *   1. Add an entry here (slug + title matching backend registry).
 *   2. Add the full entry (path, component, apiPrefix, ...) to WIZARD_REGISTRY in wizards.js.
 *   3. The Playwright contract test will enforce that backend matches this list.
 */
export const WIZARD_MANIFEST = [
  { slug: "onboarding",                   title: "Student Onboarding",       path: "/onboarding" },
  { slug: "reenrollment",                 title: "Re-enrollment",             path: "/reenrollment" },
  { slug: "billing-wizard",               title: "Billing Setup",             path: "/billing-setup" },
  { slug: "aid-wizard",                   title: "Financial Aid Setup",       path: "/aid-setup" },
  { slug: "scheduling-wizard",            title: "Scheduling Setup",          path: "/scheduling-setup" },
  { slug: "comms-wizard",                 title: "Communications Campaign",   path: "/comms-setup" },
  { slug: "section-assign-wizard",        title: "Section Assignments",       path: "/section-assign-setup" },
  { slug: "bell-schedule-wizard",         title: "Bell Schedule",             path: "/bell-schedule-setup" },
  { slug: "gradebook-setup-wizard",       title: "Gradebook Setup",           path: "/gradebook-setup" },
  { slug: "attendance-rules-wizard",      title: "Attendance Rules",          path: "/attendance-rules-setup" },
  { slug: "enrollment-conversion-wizard", title: "Enrollment Conversion",     path: "/enrollment-conversion" },
  { slug: "invoice-run-wizard",           title: "Invoice Run",               path: "/invoice-run" },
  { slug: "staff-onboarding-wizard",      title: "Staff Onboarding",          path: "/staff-onboarding" },
  { slug: "fee-schedule-wizard",          title: "Fee Schedule Setup",         path: "/fee-schedule-setup" },
  { slug: "academic-year-wizard",         title: "Academic Year Rollover",     path: "/academic-year-rollover" },
  { slug: "enrollment-period-wizard",     title: "Enrollment Period Setup",     path: "/enrollment-period-setup" },
  { slug: "grade-scale-wizard",           title: "Grade Scale Setup",           path: "/grade-scale-setup" },
  { slug: "term-structure-wizard",        title: "Term Structure Setup",        path: "/term-structure-setup" },
  // ↓ Add new wizards here (one line, include path matching WIZARD_REGISTRY)
  { slug: "section-scheduler-wizard",    title: "Section Scheduler Seed",      path: "/section-scheduler-setup" },
  { slug: "staff-setup-wizard",          title: "Staff & Roles Setup",         path: "/staff-setup" },
  { slug: "course-catalog-wizard",       title: "Course Catalog Setup",        path: "/course-catalog-setup" },
  { slug: "room-setup-wizard",           title: "Rooms Setup",                 path: "/room-setup" },
  { slug: "promotion-wizard",            title: "Promotion Map Setup",         path: "/promotion-setup" },
  { slug: "student-import-wizard",       title: "Student Import",               path: "/student-import-setup" },
  { slug: "guardian-household-wizard",   title: "Guardian & Household Setup",   path: "/guardian-household-setup" },
  { slug: "section-staffing-wizard",     title: "Section Staffing",             path: "/section-staffing-setup" },
  { slug: "attendance-codes-wizard",     title: "Attendance Codes Setup",       path: "/attendance-codes-setup" },
  { slug: "grade-weights-wizard",        title: "Grade Weights & Categories",   path: "/grade-weights-setup" },
];

/** Flat slug list — the frontend's commitment to which wizard slugs exist. */
export const WIZARD_SLUGS = WIZARD_MANIFEST.map((w) => w.slug);
