from django.urls import path
from .views import study_collection, study_detail, wizard_collection, wizard_detail

urlpatterns = [
    path("studies/", study_collection, name="market-study-collection"),
    path("studies/<uuid:study_id>/", study_detail, name="market-study-detail"),
    path("wizard/", wizard_collection, name="market-study-wizard-collection"),
    path("wizard/<uuid:session_id>/", wizard_detail, name="market-study-wizard-detail"),
]
