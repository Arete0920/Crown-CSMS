"""
reenrollment/urls.py

URL patterns for the re-enrollment wizard.
Mounted at /api/v1/reenrollment/sessions/ in crown_api/urls.py.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Step 1: create session
    path('', views.create_session, name='reenrollment-create'),

    # Step 2: configure (set year label + fee, snapshot candidates)
    path('<uuid:session_id>/configure/', views.configure_session, name='reenrollment-configure'),

    # Step 3: list eligible candidates
    path('<uuid:session_id>/candidates/', views.list_candidates, name='reenrollment-candidates'),

    # Step 4: update student exclusion list
    path('<uuid:session_id>/select/', views.select_students, name='reenrollment-select'),

    # Step 5: commit (create BillingRun + Invoices + InvoiceLines)
    path('<uuid:session_id>/commit/', views.commit_session, name='reenrollment-commit'),

    # Step 6: verify results
    path('<uuid:session_id>/verify/', views.verify_session, name='reenrollment-verify'),
]
