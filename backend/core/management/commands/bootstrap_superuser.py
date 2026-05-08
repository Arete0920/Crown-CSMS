import logging
import os
import secrets

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or reset the local admin superuser with safe defaults."

    def handle(self, *args, **kwargs):
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        logger = logging.getLogger(__name__)

        env_name = os.environ.get("DJANGO_ENV", "").strip().lower()
        if env_name in {"prod", "production"} and os.environ.get("ALLOW_SUPERUSER_BOOTSTRAP") != "true":
            raise RuntimeError(
                "Refusing to run bootstrap_superuser in production without ALLOW_SUPERUSER_BOOTSTRAP=true"
            )

        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        if not password:
            password = secrets.token_urlsafe(24)
            logger.warning(
                "DJANGO_SUPERUSER_PASSWORD not set; generated one-time password for this run."
            )

        user_model = get_user_model()
        user_model.objects.filter(username="admin").delete()

        user = user_model.objects.create_superuser(
            username="admin",
            email="admin@crown.local",
            password=password,
        )

        try:
            from core.models import School

            school = School.objects.first()
            if school is not None and hasattr(user, "school_id"):
                user.school = school
                user.save(update_fields=["school"])
                logger.info("  School: %s (%s)", school.id, school.name)
        except Exception:
            logger.debug("bootstrap_superuser: School model unavailable or user school assignment failed")

        logger.info("Superuser created: %s", user.username)
        logger.info("  Username: admin")
        logger.info("  Password: (set via DJANGO_SUPERUSER_PASSWORD env var or generated one-time value)")
