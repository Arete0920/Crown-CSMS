from django.contrib.auth import get_user_model
import os
import logging


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

User = get_user_model()

# Delete existing admin if exists
User.objects.filter(username='admin').delete()

# Create new superuser
user = User.objects.create_superuser(
    username='admin',
    email='admin@crown.local',
    password=os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Crown2026!')
)

# Attach a school context for tenant-scoped APIs (exports/billing/etc.).
# Many local flows use a superuser without a School assigned, which will 403.
try:
    from core.models import School

    school = School.objects.first()
    if school is not None and hasattr(user, "school_id"):
        user.school = school
        user.save(update_fields=["school"])
        logger.info("  School: %s (%s)", school.id, school.name)
except Exception:
    # If core.School isn't available in this deployment, skip silently.
    logger.debug("create_superuser: School model unavailable or user school assignment failed")

logger.info("Superuser created: %s", user.username)
logger.info("  Username: admin")
logger.info("  Password: (set via DJANGO_SUPERUSER_PASSWORD env var or default)")
