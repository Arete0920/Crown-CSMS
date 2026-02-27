"""
Crown2026 — Wizard Registry (single source of truth)
=====================================================
Why this exists:
  Prevents additive merge conflicts when adding new wizard apps / routes.
  settings.py pulls WIZARD_INSTALLED_APPS; urls.py calls get_wizard_urlpatterns().
  Adding a new wizard requires editing ONLY this file + the wizard app itself.

To add a wizard:
  1. Create the wizard app (manage.py startapp <name>_wizard, add apps.py/models/views/urls/tests).
  2. Append ONE entry to WIZARDS below.
  3. Done. settings.py and urls.py auto-pick it up.

Design note:
  WIZARD_INSTALLED_APPS is derived from WIZARDS at module level -- safe to import from
  settings.py before Django apps are fully loaded (strings only, no Django calls).

  get_wizard_urlpatterns() uses a deferred import of path/include so it is only
  called from urls.py (AFTER apps are ready) and never at settings import time.
"""

from __future__ import annotations
from typing import TypedDict


class _WizardEntry(TypedDict):
    name: str           # human label (for docs / debugging)
    app_config: str     # dotted path to AppConfig, e.g. "myapp.apps.MyAppConfig"
    url_prefix: str     # URL prefix, e.g. "api/v1/my-wizard/sessions/"
    urls_module: str    # dotted module path for include(), e.g. "myapp.urls"


# ------------------------------------------------------------------
# WIZARDS — single source of truth.  To add a wizard, append here.
# ------------------------------------------------------------------
WIZARDS: list[_WizardEntry] = [
    # #1 — Student Onboarding
    {
        "name":       "Student Onboarding",
        "app_config": "onboarding.apps.OnboardingConfig",
        "url_prefix": "api/v1/onboarding/imports/",
        "urls_module": "onboarding.urls",
    },
    # #2 — Re-enrollment
    {
        "name":       "Re-enrollment",
        "app_config": "reenrollment.apps.ReenrollmentConfig",
        "url_prefix": "api/v1/reenrollment/sessions/",
        "urls_module": "reenrollment.urls",
    },
    # #3 — Billing Setup
    {
        "name":       "Billing Setup",
        "app_config": "billing_wizard.apps.BillingWizardConfig",
        "url_prefix": "api/v1/billing-wizard/sessions/",
        "urls_module": "billing_wizard.urls",
    },
    # #4 — Financial Aid Setup
    {
        "name":       "Financial Aid Setup",
        "app_config": "financial_aid_wizard.apps.FinancialAidWizardConfig",
        "url_prefix": "api/v1/aid-wizard/sessions/",
        "urls_module": "financial_aid_wizard.urls",
    },
    # #5 — Scheduling Setup
    {
        "name":       "Scheduling Setup",
        "app_config": "scheduling_wizard.apps.SchedulingWizardConfig",
        "url_prefix": "api/v1/scheduling-wizard/sessions/",
        "urls_module": "scheduling_wizard.urls",
    },
    # #6 — Communications Campaign
    {
        "name":       "Communications Campaign",
        "app_config": "comms_wizard.apps.CommsWizardConfig",
        "url_prefix": "api/v1/comms-wizard/sessions/",
        "urls_module": "comms_wizard.urls",
    },
    # #7 — Section Assignments
    {
        "name":       "Section Assignments",
        "app_config": "section_assign_wizard.apps.SectionAssignWizardConfig",
        "url_prefix": "api/v1/section-assign-wizard/sessions/",
        "urls_module": "section_assign_wizard.urls",
    },
    # #8 — Bell Schedule
    {
        "name":       "Bell Schedule",
        "app_config": "bell_schedule_wizard.apps.BellScheduleWizardConfig",
        "url_prefix": "api/v1/bell-schedule-wizard/sessions/",
        "urls_module": "bell_schedule_wizard.urls",
    },
    # #9 — Gradebook Setup
    {
        "name":       "Gradebook Setup",
        "app_config": "gradebook_setup_wizard.apps.GradebookSetupWizardConfig",
        "url_prefix": "api/v1/gradebook-setup-wizard/sessions/",
        "urls_module": "gradebook_setup_wizard.urls",
    },
    # #10 — Attendance Rules
    {
        "name":       "Attendance Rules",
        "app_config": "attendance_rules_wizard.apps.AttendanceRulesWizardConfig",
        "url_prefix": "api/v1/attendance-rules-wizard/sessions/",
        "urls_module": "attendance_rules_wizard.urls",
    },
    # #11 — Enrollment Conversion
    {
        "name":       "Enrollment Conversion",
        "app_config": "enrollment_conversion_wizard.apps.EnrollmentConversionWizardConfig",
        "url_prefix": "api/v1/enrollment-conversion-wizard/sessions/",
        "urls_module": "enrollment_conversion_wizard.urls",
    },
    # #12 — Invoice Run
    {
        "name":       "Invoice Run",
        "app_config": "invoice_run_wizard.apps.InvoiceRunWizardConfig",
        "url_prefix": "api/v1/invoice-run-wizard/sessions/",
        "urls_module": "invoice_run_wizard.urls",
    },
    # #13 — Staff Onboarding
    {
        "name":       "Staff Onboarding",
        "app_config": "staff_onboarding_wizard.apps.StaffOnboardingWizardConfig",
        "url_prefix": "api/v1/staff-onboarding-wizard/sessions/",
        "urls_module": "staff_onboarding_wizard.urls",
    },
    # #14 — Fee Schedule Setup
    {
        "name":       "Fee Schedule Setup",
        "app_config": "fee_schedule_wizard.apps.FeeScheduleWizardConfig",
        "url_prefix": "api/v1/fee-schedule-wizard/sessions/",
        "urls_module": "fee_schedule_wizard.urls",
    },
    # #15 — Academic Year Rollover
    {
        "name":       "Academic Year Rollover",
        "app_config": "academic_year_wizard.apps.AcademicYearWizardConfig",
        "url_prefix": "api/v1/academic-year-wizard/sessions/",
        "urls_module": "academic_year_wizard.urls",
    },
    # #16 — Enrollment Period Setup
    {
        "name":       "Enrollment Period Setup",
        "app_config": "enrollment_period_wizard.apps.EnrollmentPeriodWizardConfig",
        "url_prefix": "api/v1/enrollment-period-wizard/sessions/",
        "urls_module": "enrollment_period_wizard.urls",
    },
    # #17 — Grade Scale & Report Card Settings
    {
        "name":       "Grade Scale Setup",
        "app_config": "grade_scale_wizard.apps.GradeScaleWizardConfig",
        "url_prefix": "api/v1/grade-scale-wizard/sessions/",
        "urls_module": "grade_scale_wizard.urls",
    },
    # #18 — Term & Marking Period Setup
    {
        "name":        "Term Structure Setup",
        "app_config":  "term_structure_wizard.apps.TermStructureWizardConfig",
        "url_prefix":  "api/v1/term-structure-wizard/sessions/",
        "urls_module": "term_structure_wizard.urls",
    },
    # ↓ Add new wizard entries here — one dict, zero other files to touch
]

# ------------------------------------------------------------------
# Derived lists — consumed by settings.py and urls.py respectively.
# DO NOT edit these directly; edit WIZARDS above.
# ------------------------------------------------------------------
WIZARD_INSTALLED_APPS: list[str] = [w["app_config"] for w in WIZARDS]


# ------------------------------------------------------------------
# Public API — consumed by the wizard discovery endpoint.
# ------------------------------------------------------------------

def list_wizards() -> list[dict]:
    """
    Returns a stable, ordered list of wizard metadata for UI consumption.
    Called by GET /api/v1/wizards/ — this is the single source of truth
    for what the backend knows about available wizards.

    Slug is derived from url_prefix: api/v1/<slug>/...
    Key  is derived from urls_module: <app_module>.urls
    """
    result = []
    for w in WIZARDS:
        slug = w["url_prefix"].split("/")[2]          # "api/v1/<slug>/..."
        key  = w["urls_module"].split(".")[0]          # "billing_wizard.urls" → "billing_wizard"
        result.append({
            "key":     key,
            "slug":    slug,
            "title":   w["name"],
            "enabled": True,
        })
    return result


def get_wizard_urlpatterns() -> list:
    """
    Returns a list of URL patterns for all registered wizards.
    MUST only be called from urls.py, never from settings.py.
    Uses deferred import to avoid AppRegistryNotReady at settings load time.
    """
    from django.urls import include, path  # deferred -- safe after app registry ready
    return [path(w["url_prefix"], include(w["urls_module"])) for w in WIZARDS]
