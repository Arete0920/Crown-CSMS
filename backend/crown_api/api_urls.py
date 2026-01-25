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
)
from crown_api.views_households import household_detail, households_list
from crown_api.views_students import student_detail, students_list
from crown_api.views_academics import student_attendance_list, student_grades_list
from crown_api.views_billing import household_billing_summary
from crown_api.views_scheduling import terms_list, term_sections, student_schedule
from crown_api.views_comms import threads_list, thread_detail
from applications import api as applications_api
from ledger import api as ledger_api
from financial_aid import api as financial_aid_api

urlpatterns = [
    # Persona-specific API routes (NEW - per user spec)
    path("aid/", include("aid.api_urls")),
    path("admissions/", include("admissions.api_urls")),

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
    path("ledger/charges/", ledger_api.create_charge, name="ledger-create-charge"),
    path("ledger/payments/", ledger_api.record_payment, name="ledger-record-payment"),

    path("financial-aid/applications/", financial_aid_api.aid_applications, name="aid-applications"),
    path(
        "financial-aid/applications/<str:aid_application_id>/submit/",
        financial_aid_api.aid_submit,
        name="aid-submit",
    ),
    path(
        "financial-aid/applications/<str:aid_application_id>/decide/",
        financial_aid_api.aid_decide,
        name="aid-decide",
    ),
    path(
        "financial-aid/awards/<str:award_id>/disburse/",
        financial_aid_api.aid_disburse,
        name="aid-disburse",
    ),

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
]
