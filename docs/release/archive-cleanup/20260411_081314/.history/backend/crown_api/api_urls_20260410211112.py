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
from core.views_nav import nav_view
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
from crown_api.metrics_views import (
    admin_metrics, finance_metrics,
    teacher_metrics, parent_metrics, student_metrics,
    it_metrics, marketing_metrics,
    spiritual_life_metrics, office_metrics,
    health_metrics, counseling_metrics, food_metrics,
    athletics_metrics, transportation_metrics,
    facilities_metrics, security_metrics,
    academic_support_metrics, fine_arts_metrics, library_metrics,
    extended_care_metrics, registrar_metrics, communications_metrics,
    student_services_metrics,
    # advancement_metrics, pd_metrics omitted: real backends in app urls.py
)
from crown_api.views_students import student_detail, students_list
from crown_api.views_academics import student_attendance_list, student_grades_list
from crown_api.views_billing import household_billing_summary
from crown_api.views_scheduling import terms_list, term_sections, student_schedule
from crown_api.views_comms import threads_list, thread_detail
from applications import api as applications_api
from ledger import api as ledger_api
from ledger import api_finance as finance_api
from academics import api as academics_api
from billing import api as billing_api
from onboarding import api_onboarding
from board_oversight import api_governance
from governance import views as governance_views
from support import api_support
from analytics import api_health

urlpatterns = [
    # Permission-derived navigation
    path('nav/',                    nav_view,               name='nav'),

    # Dashboard metrics endpoints (read-only, persona-scoped)
    path('admin/metrics/',          admin_metrics,          name='admin-metrics'),
    path('finance/metrics/',        finance_metrics,        name='finance-metrics'),
    path('teacher/metrics/',        teacher_metrics,        name='teacher-metrics'),
    path('parent/metrics/',         parent_metrics,         name='parent-metrics'),
    path('student/metrics/',        student_metrics,        name='student-metrics'),
    path('it/metrics/',             it_metrics,             name='it-metrics'),
    # financial-aid/metrics/ is registered in financial_aid/urls.py (real DB view)
    path('marketing/metrics/',      marketing_metrics,      name='marketing-metrics'),
    path('spiritual-life/metrics/', spiritual_life_metrics, name='spiritual-life-metrics'),
    path('office/metrics/',         office_metrics,         name='office-metrics'),
    path('health/metrics/',         health_metrics,         name='health-metrics'),
    path('counseling/metrics/',     counseling_metrics,     name='counseling-metrics'),
    path('food/metrics/',           food_metrics,           name='food-metrics'),
    path('athletics/metrics/',      athletics_metrics,      name='athletics-metrics'),
    # NOTE: advancement/metrics/, pd/metrics/, safety/metrics/ are intentionally
    # omitted here. Those real backends live in advancement/urls.py, pdhub/urls.py,
    # and safety/urls.py, which are included BEFORE this file in api_v1_urls.py.
    # Registering them here would create duplicate named-URL collisions and these
    # stubs would shadow the real implementations.
    path('transportation/metrics/', transportation_metrics, name='transportation-metrics'),
    path('facilities/metrics/',     facilities_metrics,     name='facilities-metrics'),
    path('security/metrics/',       security_metrics,       name='security-metrics'),
    path('academic-support/metrics/', academic_support_metrics, name='academic-support-metrics'),
    path('fine-arts/metrics/',       fine_arts_metrics,      name='fine-arts-metrics'),
    path('library/metrics/',         library_metrics,        name='library-metrics'),
    path('extended-care/metrics/',   extended_care_metrics,  name='extended-care-metrics'),
    path('registrar/metrics/',       registrar_metrics,      name='registrar-metrics'),
    path('communications/metrics/',  communications_metrics, name='communications-metrics'),
    path('student-services/metrics/', student_services_metrics, name='student-services-metrics'),

    path('360/', include('student360.api.urls')),
    path('parent360/', include('parent360.api.urls')),
    path('comms/', include('comms.api.urls')),
    # Persona-specific API routes (NEW - per user spec)
    path("aid/", include("aid.api_urls")),
    # financial-aid/ registered in api_v1_urls.py (position 16) — do not re-register here
    path("admissions/", include("admissions.api_urls")),
    path("portrait/", include("portrait.urls")),

    # New demo pillars (discipline, service hours, Teams integration)
    path("discipline/", include("discipline.api.urls")),
    path("service/", include("servicehours.api.urls")),
    path("integrations/", include("integrations.api.urls")),
    path("spiritual-life/", include("spiritual_life.api.urls")),
    path("outreach/", include("outreach.api.urls")),
    path("athletics/", include("athletics.api.urls")),
    path("", include("facops.api.urls")),
    path("transportation/", include("transportation.api.urls")),

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
    path("ledger/charges/<str:charge_id>/void/", ledger_api.void_charge, name="ledger-void-charge"),
    path("ledger/payments/", ledger_api.record_payment, name="ledger-record-payment"),
    path("ledger/payments/<str:payment_id>/void/", ledger_api.void_payment, name="ledger-void-payment"),

    # 0102: open items helpers
    path("ledger/charges/open/", ledger_api.open_charges, name="ledger-open-charges"),
    path("ledger/invoices/open/", ledger_api.open_invoices, name="ledger-open-invoices"),

    path("ledger/payments/<str:payment_id>/allocate/", ledger_api.payment_allocate, name="ledger-payment-allocate"),
    path("ledger/accounts/<str:account_id>/balance/", ledger_api.ledger_account_balance, name="ledger-account-balance"),
    path("ledger/charges/<str:charge_id>/balance/", ledger_api.charge_balance, name="ledger-charge-balance"),
    # Phase 2 invariants — read-only sanity check, tenant-scoped
    path("ledger/invariants/", ledger_api.ledger_invariants, name="ledger-invariants"),

    # Stage 2 — Finance & Revenue Integrity (CFO dashboard endpoints)
    path("v1/finance/kpis/", finance_api.finance_kpis, name="finance-kpis"),
    path("v1/finance/chargebacks/", finance_api.chargeback_metrics, name="finance-chargebacks"),
    path("v1/finance/monthly-summary/", finance_api.monthly_financial_summary, name="finance-monthly-summary"),
    path("v1/finance/payout-audit/", finance_api.payout_audit_list, name="finance-payout-audit"),
    path("v1/finance/dunning/", finance_api.dunning_status, name="finance-dunning"),


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

    # Signal Engine + Crown Compass 2.0 + Intervention Workflow
    path("signals/", include("signals.urls")),
    # Aftercare Module
    path("aftercare/", include("aftercare.urls")),
    # Finance Setup (Policy Wizard)
    path("v1/finance-setup/", include("finance_setup.urls")),

    # ── Stage 3: Onboarding + Import Engine ──────────────────────────────
    path("v1/onboarding/<str:school_id>/progress/", api_onboarding.onboarding_progress, name="onboarding-progress"),
    path("v1/onboarding/<str:school_id>/tasks/<int:task_id>/complete/", api_onboarding.mark_task_complete, name="onboarding-task-complete"),
    path("v1/onboarding/<str:school_id>/can-activate/", api_onboarding.activation_gate, name="onboarding-activation-gate"),
    path("v1/help/<slug:slug>/", api_onboarding.help_article, name="help-article"),
    path("v1/solomon/articles/", api_onboarding.solomon_articles, name="solomon-articles"),
    path("v1/solomon/articles/<slug:slug>/", api_onboarding.solomon_article_detail, name="solomon-article-detail"),
    path("v1/solomon/context/", api_onboarding.solomon_context, name="solomon-context"),
    path("v1/solomon/categories/", api_onboarding.solomon_categories, name="solomon-categories"),
    path("v1/solomon/playbooks/", api_onboarding.solomon_playbooks, name="solomon-playbooks"),
    path("v1/solomon/search/", api_onboarding.solomon_search, name="solomon-search"),

    # ── Stage 4: Board Intelligence ──────────────────────────────────────
    path("v1/governance/", include("governance.urls")),
    path("v1/dashboards/school-board/summary", governance_views.governance_dashboard, name="dashboard-school-board-summary"),
    path("v1/board/packet/download/", api_governance.download_board_packet, name="board-packet-download"),
    path("v1/board/compass/", api_governance.compass_executive, name="board-compass"),
    path("v1/board/initiatives/", api_governance.initiative_summary, name="board-initiatives"),
    path("v1/board/trends/", api_governance.board_trends, name="board-trends"),
    path("v1/board/roadmap/", api_governance.public_roadmap, name="board-roadmap"),
    path("v1/board/releases/", api_governance.release_notes, name="board-releases"),

    # ── Stage 5: Support, Health, Export, Status ─────────────────────────
    path("v1/support/tickets/", api_support.tickets, name="support-tickets"),
    path("v1/support/tickets/<int:ticket_id>/resolve/", api_support.resolve_ticket, name="support-resolve-ticket"),
    path("v1/support/escalation/run/", api_support.run_escalation, name="support-run-escalation"),
    path("v1/analytics/health/", api_health.customer_health, name="analytics-customer-health"),
    path("v1/analytics/export/", api_health.export_school, name="analytics-export"),
    path("v1/status/", api_health.public_status, name="public-status"),
]


