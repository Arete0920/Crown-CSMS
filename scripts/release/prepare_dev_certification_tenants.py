"""Prepare two isolated synthetic DEV fixtures using the existing domain models.

Run only in the authorized DEV PostgreSQL workflow. Tokens are short lived,
masked, and written outside uploaded evidence. No existing school is reseeded.
"""
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from uuid import NAMESPACE_URL, uuid5


def validate_target(environment, vendor, database_url):
    target = urlsplit(database_url)
    if environment != "dev" or vendor != "postgresql" or target.scheme not in ("postgres", "postgresql") or target.hostname != "crown-pg-dev.postgres.database.azure.com":
        raise ValueError("Only the authorized DEV PostgreSQL target is permitted")


def prepare(output):
    from django.conf import settings
    from django.db import connection, transaction
    from core.models import School, UserAccount, UserRole
    from crown_api.jwt_utils import build_access_token
    from households.models import Household, Student, Guardian
    from sandbox_demo.catalog import SANDBOX_PERSONAS
    from sandbox_demo.permissions import ensure_sandbox_role_permissions

    validate_target(settings.CROWN_ENV, connection.vendor, os.environ["DATABASE_URL"])
    roles = ("school_admin", "teacher", "parent", "student", "board", "finance_director")
    result = []
    with transaction.atomic():
        for label in ("a", "b"):
            key = "crown-dev-certification-" + label
            school_id = uuid5(NAMESPACE_URL, key)
            school, _ = School.objects.get_or_create(id=school_id, defaults={"name": "Synthetic Certification School " + label.upper(), "is_active": True})
            assert school.name == "Synthetic Certification School " + label.upper() and school.is_active
            family, _ = Household.objects.get_or_create(id=uuid5(school_id, "household"), defaults={"school_id": school_id, "name": "Synthetic Certification Family " + label.upper()})
            assert family.school_id == school_id
            actors = {}
            for role in roles:
                persona = SANDBOX_PERSONAS[role]
                email = role + "@" + key + ".invalid"
                user, created = UserAccount.objects.get_or_create(username=email, defaults={"email": email, "school": school, "is_active": True, "is_staff": False, "is_superuser": False})
                assert user.school_id == school_id and not user.is_staff and not user.is_superuser and user.is_active
                if created:
                    user.set_unusable_password()
                    user.save(update_fields=["password"])
                # Only the deterministic .invalid DEV certification Board actor
                # can lose the previous incorrect Head-of-School assignment.
                if role == "board":
                    UserRole.objects.filter(
                        school=school, user=user, role_code="HEAD_OF_SCHOOL"
                    ).delete()
                UserRole.objects.get_or_create(school=school, user=user, role_code=persona.role_code)
                ensure_sandbox_role_permissions(persona.role_code)
                token = build_access_token(user_id=str(user.id), email=email, role=role, school_id=str(school_id), ttl_seconds=1800)
                print("::add-mask::" + token)
                actors[role] = {"token": token, "user_id": str(user.id)}
            student, _ = Student.objects.get_or_create(id=uuid5(school_id, "student"), defaults={"school_id": school_id, "household": family, "account_id": actors["student"]["user_id"], "first_name": "Synthetic", "last_name": "Certification" + label.upper()})
            assert student.school_id == school_id and student.household_id == family.id and str(student.account_id) == actors["student"]["user_id"]
            guardian, _ = Guardian.objects.get_or_create(id=uuid5(school_id, "guardian"), defaults={"school_id": school_id, "household": family, "account_id": actors["parent"]["user_id"], "first_name": "Synthetic", "last_name": "Guardian" + label.upper()})
            assert guardian.school_id == school_id and str(guardian.account_id) == actors["parent"]["user_id"]
            result.append({"school_id": str(school_id), "student_id": str(student.id), "household_id": str(family.id), "actors": actors})
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(mode=0o600, exist_ok=True)
    path.chmod(0o600)
    path.write_text(json.dumps(result))
    print("DEV_SYNTHETIC_FIXTURES=2_SCHOOLS_6_ROLES; tokens excluded from artifacts")


if __name__ == "__main__":
    import django
    django.setup()
    prepare(os.environ["CROWN_DEV_TENANT_FIXTURE"])
