import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

DEMO_USERNAMES = [
    "head@crown-demo.local",
    "finance@crown-demo.local",
    "aid@crown-demo.local",
]

class Command(BaseCommand):
    help = "Reset demo user passwords from CROWN_DEMO_PASSWORD."

    def handle(self, *args, **options):
        pw = os.getenv("CROWN_DEMO_PASSWORD")
        if not pw:
            raise SystemExit("CROWN_DEMO_PASSWORD is not set")

        User = get_user_model()
        changed = 0
        missing = []

        for username in DEMO_USERNAMES:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                missing.append(username)
                continue

            user.set_password(pw)
            user.is_active = True
            user.save(update_fields=["password", "is_active"])
            changed += 1

        self.stdout.write(self.style.SUCCESS(
            f"Reset passwords for {changed} demo users."
        ))
        if missing:
            self.stdout.write(self.style.WARNING(
                f"Missing users (not modified): {missing}"
            ))
