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
  { slug: "onboarding",                   title: "Student Onboarding" },
  { slug: "reenrollment",                 title: "Re-enrollment" },
  { slug: "billing-wizard",               title: "Billing Setup" },
  { slug: "aid-wizard",                   title: "Financial Aid Setup" },
  { slug: "scheduling-wizard",            title: "Scheduling Setup" },
  { slug: "comms-wizard",                 title: "Communications Campaign" },
  { slug: "section-assign-wizard",        title: "Section Assignments" },
  { slug: "bell-schedule-wizard",         title: "Bell Schedule" },
  { slug: "gradebook-setup-wizard",       title: "Gradebook Setup" },
  { slug: "attendance-rules-wizard",      title: "Attendance Rules" },
  { slug: "enrollment-conversion-wizard", title: "Enrollment Conversion" },
  { slug: "invoice-run-wizard",           title: "Invoice Run" },
  // ↓ Add new wizards here (one line)
];

/** Flat slug list — the frontend's commitment to which wizard slugs exist. */
export const WIZARD_SLUGS = WIZARD_MANIFEST.map((w) => w.slug);
