"""
onboarding/solomon_seed.py

Seed helper for Solomon knowledge-base data.
"""


def ensure_solomon_seed_data():
    """Ensure default Solomon seed data is loaded into the database."""
    from onboarding.models_tasks import SolomonCategory, SolomonAudience, SolomonTopic

    default_audiences = [
        {"slug": "director", "name": "Director"},
        {"slug": "teacher", "name": "Teacher"},
        {"slug": "parent", "name": "Parent"},
        {"slug": "staff", "name": "Staff"},
    ]
    for a in default_audiences:
        SolomonAudience.objects.get_or_create(slug=a["slug"], defaults={"name": a["name"]})

    default_categories = [
        {"slug": "getting-started", "name": "Getting Started"},
        {"slug": "admissions", "name": "Admissions"},
        {"slug": "billing", "name": "Billing"},
        {"slug": "academics", "name": "Academics"},
    ]
    for c in default_categories:
        SolomonCategory.objects.get_or_create(slug=c["slug"], defaults={"name": c["name"]})

    default_topics = [
        {"slug": "setup", "name": "Setup"},
        {"slug": "enrollment", "name": "Enrollment"},
        {"slug": "payments", "name": "Payments"},
    ]
    for t in default_topics:
        SolomonTopic.objects.get_or_create(slug=t["slug"], defaults={"name": t["name"]})
