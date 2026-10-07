"""Explicit, transactional administrator bootstrap without executable interpolation."""
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Bootstrap an administrator from environment values under explicit activation."

    @transaction.atomic
    def handle(self, *args, **options):
        explicit = os.getenv("BOOTSTRAP_ADMIN", "").strip().lower() == "true"
        production = bool(os.getenv("WEBSITE_HOSTNAME")) or any(
            os.getenv(key, "").strip().lower() in {"prod", "production", "live"}
            for key in ("CROWN_ENV", "DJANGO_ENV", "ENVIRONMENT", "AZURE_ENVIRONMENT")
        )
        username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin").strip()
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@crown.demo").strip()
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "")
        if production and not explicit:
            raise CommandError("Production administrator bootstrap requires BOOTSTRAP_ADMIN=true.")
        if not explicit and not password:
            raise CommandError("Administrator bootstrap is not activated.")
        if not username or not password:
            raise CommandError("Administrator bootstrap requires a username and nonempty password.")
        model = get_user_model()
        try:
            model._meta.get_field("username").run_validators(username)
            model._meta.get_field("email").run_validators(email)
        except ValidationError as exc:
            raise CommandError("Administrator bootstrap identity is invalid.") from exc
        user, created = model.objects.select_for_update().get_or_create(
            username=username, defaults={"email": email},
        )
        if not created and not (user.is_active and user.is_staff and user.is_superuser):
            raise CommandError("Bootstrap cannot elevate or reset an existing non-administrator account.")
        if created:
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
        try:
            validate_password(password, user=user)
        except ValidationError as exc:
            raise CommandError("Administrator bootstrap password does not satisfy policy.") from exc
        user.set_password(password)
        user.save()
        self.stdout.write(f"Administrator bootstrap complete; created={created}.")
