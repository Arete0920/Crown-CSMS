import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import School, UserRole

DEMO_USERNAMES = [
    "head@crown-demo.local",
    "finance@crown-demo.local",
    "aid@crown-demo.local",
]

EXTRA_DEMO_USERS = [
    {"username": "teacher", "email": "teacher@crown-demo.local", "role_code": "TEACHER"},
    {"username": "parent", "email": "parent@crown-demo.local", "role_code": "PARENT"},
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

        school_id = os.getenv("CROWN_DEMO_SCHOOL_ID")
        school = None
        if school_id:
            school = School.objects.filter(pk=school_id).first()
        if school is None:
            school = School.objects.order_by("name").first()

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

        created = 0
        for spec in EXTRA_DEMO_USERS:
            user, was_created = User.objects.get_or_create(
                username=spec["username"],
                defaults={
                    "email": spec["email"],
                    "is_active": True,
                    "school": school,
                },
            )

            user.email = spec["email"]
            user.is_active = True
            if user.school_id is None and school is not None:
                user.school = school
            user.set_password(pw)
            user.save(update_fields=["email", "is_active", "school", "password"])

            if school is not None:
                UserRole.objects.update_or_create(
                    school=school,
                    user=user,
                    role_code=spec["role_code"],
                )

            changed += 1
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Reset passwords for {changed} demo users."
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Created missing teacher/parent users: {created}."
        ))
        if missing:
            self.stdout.write(self.style.WARNING(
                f"Missing users (not modified): {missing}"
            ))
