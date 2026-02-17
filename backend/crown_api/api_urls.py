"""
URL configuration for Director APIs

PERSONA-SPECIFIC APIs (per user's spec):
- /api/aid/priority-queue/
- /api/aid/metrics/
- /api/aid/timeline/
- /api/admissions/priority-queue/
- /api/admissions/metrics/
- /api/admissions/timeline/

LEGACY unified APIs (deprecated):
- /api/director/* (returns merged data for all personas)
"""

from django.urls import path, include
from crown_api.director_views import (
    aid_summary,
    finance_summary,
    registrar_summary,
    director_dashboard,
    director_priority,
    director_actions,
    director_timeline,
    force_seed_user,
)
from crown_api.views_households import household_detail, households_list
from crown_api.views_students import student_detail, students_list
from crown_api.views_academics import student_attendance_list, student_grades_list
from crown_api.views_billing import household_billing_summary
from crown_api.views_scheduling import terms_list, term_sections, student_schedule
from crown_api.views_comms import threads_list, thread_detail
from applications import api as applications_api
from ledger import api as ledger_api
from academics import api as academics_api
from billing import api as billing_api

urlpatterns = [
    path('360/', include('student360.api.urls')),
    path('comms/', include('comms.api.urls')),
    # Persona-specific API routes (NEW - per user spec)
    path("aid/", include("aid.api_urls")),
    path("admissions/", include("admissions.api_urls")),
    
    # New demo pillars (discipline, service hours, Teams integration)
    path("discipline/", include("discipline.api.urls")),
    path("service/", include("servicehours.api.urls")),
    path("integrations/", include("integrations.api.urls")),

    # Households (Module 4 spine) - read-only
    path("households/", households_list, name="households_list"),
    path("households/<uuid:household_id>/", household_detail, name="household_detail"),

    # Billing (Module 11 spine) - read-only
    path(
        "households/<uuid:household_id>/billing/summary/",
        household_billing_summary,
        name="household_billing_summary",
    ),

    # Scheduling (Block G spine) - read-only
    path("terms/", terms_list, name="terms_list"),
    path("terms/<uuid:term_id>/sections/", term_sections, name="term_sections"),
    path("students/<uuid:student_id>/schedule/", student_schedule, name="student_schedule"),

    # Communications (Block H spine) - read-only
    path("threads/", threads_list, name="threads_list"),
    path("threads/<uuid:thread_id>/", thread_detail, name="thread_detail"),

    # Applications (Module 9 spine) - minimal write + submit transition
    path("applications/", applications_api.applications, name="applications"),
    path("applications/<str:application_id>/", applications_api.application_detail, name="application-detail"),
    path("applications/<str:application_id>/submit/", applications_api.application_submit, name="application-submit"),
    path(
        "applications/<str:application_id>/decision/",
        applications_api.application_decision,
        name="application-decision",
    ),
    path("applicants/", applications_api.applicants, name="applicants"),

    path("ledger/accounts/ensure/", ledger_api.ensure_account, name="ledger-ensure-account"),
    path("ledger/accounts/<str:account_id>/", ledger_api.account_detail, name="ledger-account-detail"),
    # Ledger statement
    path("ledger/accounts/<str:account_id>/statement/", ledger_api.ledger_account_statement, name="ledger-account-statement"),
    path("ledger/charges/", ledger_api.create_charge, name="ledger-create-charge"),
    path("ledger/payments/", ledger_api.record_payment, name="ledger-record-payment"),

    # 0102: open items helpers
    path("ledger/charges/open/", ledger_api.open_charges, name="ledger-open-charges"),
    path("ledger/invoices/open/", ledger_api.open_invoices, name="ledger-open-invoices"),

    path("ledger/payments/<str:payment_id>/allocate/", ledger_api.payment_allocate, name="ledger-payment-allocate"),
    path("ledger/accounts/<str:account_id>/balance/", ledger_api.ledger_account_balance, name="ledger-account-balance"),
    path("ledger/charges/<str:charge_id>/balance/", ledger_api.charge_balance, name="ledger-charge-balance"),


    path("academics/courses/", academics_api.courses, name="academics-courses"),
    path("academics/sections/", academics_api.sections, name="academics-sections"),
    path("academics/enroll/", academics_api.enroll, name="academics-enroll"),
    path(
        "academics/sections/<str:section_id>/roster/",
        academics_api.section_roster,
        name="academics-section-roster",
    ),

    path("billing/runs/", billing_api.billing_runs, name="billing-runs"),
    path("billing/runs/<str:billing_run_id>/", billing_api.billing_run_detail, name="billing-run-detail"),
    # Billing run summary
    path("billing/runs/<str:billing_run_id>/summary/", billing_api.billing_run_summary_view, name="billing-run-summary"),

    # Invoices (Finance v1)
    path("billing/invoices/", billing_api.invoices, name="billing-invoices"),

    # Installment plans
    path("billing/installment-plans/", billing_api.installment_plans, name="billing-installment-plans"),

    # Students (SIS Student Core) - read-only
    path("students/", students_list, name="students_list"),
    path("students/<uuid:student_id>/", student_detail, name="student_detail"),

    # Academics (Module 6 spine) - read-only
    path(
        "students/<uuid:student_id>/attendance/",
        student_attendance_list,
        name="student_attendance_list",
    ),
    path(
        "students/<uuid:student_id>/grades/",
        student_grades_list,
        name="student_grades_list",
    ),
    
    # Legacy unified routes (DEPRECATED - kept for backwards compatibility)
    path("director/aid/summary/", aid_summary, name="aid_summary"),
    path("director/finance/summary/", finance_summary, name="finance_summary"),
    path("director/registrar/summary/", registrar_summary, name="registrar_summary"),
    path("director/dashboard/", director_dashboard, name="director_dashboard"),
    path("director/priority/", director_priority, name="director_priority"),
    path("director/actions/", director_actions, name="director_actions"),
    path("director/timeline/", director_timeline, name="director_timeline"),
    path("director/force_seed_user/", force_seed_user, name="force_seed_user"),
]


