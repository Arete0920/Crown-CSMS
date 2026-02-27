from django.urls import path
from . import views

urlpatterns = [
    # 1. Create import session
    path("", views.create_session, name="onboarding_create_session"),
    # 2. Upload CSV file
    path("<int:session_id>/upload/", views.upload_file, name="onboarding_upload"),
    # 3. Validate (dry run)
    path("<int:session_id>/validate/", views.validate_session, name="onboarding_validate"),
    # 4. Preview sample rows
    path("<int:session_id>/preview/", views.preview_session, name="onboarding_preview"),
    # 5. Commit to DB
    path("<int:session_id>/commit/", views.commit_session, name="onboarding_commit"),
    # 6. Post-commit verification
    path("<int:session_id>/verify/", views.verify_session, name="onboarding_verify"),
]
