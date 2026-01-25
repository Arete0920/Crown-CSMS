"""Deterministic local seed for Households module.

Safe-by-default:
- Refuses to run on Azure (WEBSITE_HOSTNAME/WEBSITE_INSTANCE_ID present)
- Uses get_or_create so it can be re-run without duplicating

Usage (PowerShell):
  cd backend
    .\\venv\\Scripts\\python.exe ..\\backend\\scripts\\seed_households.py
"""

import os


def _refuse_if_azure() -> None:
    if os.getenv("WEBSITE_HOSTNAME") or os.getenv("WEBSITE_INSTANCE_ID"):
        raise SystemExit("Refusing to run seed_households on Azure/production.")


def run() -> None:
    _refuse_if_azure()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")

    import django

    django.setup()

    from crown_api.models import Household, HouseholdMember, Person, Student
    from crown_api.models_households import (
        ROLE_AUTHORIZED_PICKUP,
        ROLE_EMERGENCY_CONTACT,
        ROLE_FINANCIALLY_RESPONSIBLE,
        ROLE_GUARDIAN,
        ROLE_PRIMARY_GUARDIAN,
    )

    def person(first_name: str, last_name: str, email: str, phone: str | None = None) -> Person:
        obj, _ = Person.objects.get_or_create(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "phone": phone,
            },
        )
        # Keep deterministic values stable if re-run.
        changed = False
        for field, value in {
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
        }.items():
            if getattr(obj, field) != value:
                setattr(obj, field, value)
                changed = True
        if changed:
            obj.save(update_fields=["first_name", "last_name", "phone", "updated_at"])
        return obj

    def household(name: str, city: str, state: str) -> Household:
        obj, _ = Household.objects.get_or_create(
            household_name=name,
            defaults={"primary_city": city, "primary_state": state},
        )
        return obj

    h1 = household("The Megahan Family", city="Buffalo", state="NY")
    h2 = household("The Carter Family", city="Raleigh", state="NC")

    # Household 1 guardians
    p1 = person("John", "Megahan", "john.megahan@example.com", phone="555-0001")
    p2 = person("Jane", "Megahan", "jane.megahan@example.com", phone="555-0002")

    HouseholdMember.objects.get_or_create(
        household=h1,
        person=p1,
        role=ROLE_PRIMARY_GUARDIAN,
        defaults={"is_primary": True},
    )
    HouseholdMember.objects.get_or_create(
        household=h1,
        person=p1,
        role=ROLE_FINANCIALLY_RESPONSIBLE,
        defaults={"is_primary": False},
    )
    HouseholdMember.objects.get_or_create(
        household=h1,
        person=p2,
        role=ROLE_GUARDIAN,
        defaults={"is_primary": False},
    )
    HouseholdMember.objects.get_or_create(
        household=h1,
        person=p2,
        role=ROLE_EMERGENCY_CONTACT,
        defaults={"is_primary": False},
    )
    HouseholdMember.objects.get_or_create(
        household=h1,
        person=p2,
        role=ROLE_AUTHORIZED_PICKUP,
        defaults={"is_primary": False},
    )

    # Household 1 students
    s1p = person("Alice", "Megahan", "alice.megahan@student.example.com")
    s2p = person("Ben", "Megahan", "ben.megahan@student.example.com")

    Student.objects.get_or_create(
        person=s1p,
        defaults={"household": h1, "grade_level": "3", "active": True},
    )
    Student.objects.get_or_create(
        person=s2p,
        defaults={"household": h1, "grade_level": "1", "active": True},
    )

    # Household 2 guardians
    p3 = person("Mark", "Carter", "mark.carter@example.com", phone="555-1001")
    p4 = person("Mary", "Carter", "mary.carter@example.com", phone="555-1002")

    HouseholdMember.objects.get_or_create(
        household=h2,
        person=p3,
        role=ROLE_PRIMARY_GUARDIAN,
        defaults={"is_primary": True},
    )
    HouseholdMember.objects.get_or_create(
        household=h2,
        person=p3,
        role=ROLE_FINANCIALLY_RESPONSIBLE,
        defaults={"is_primary": False},
    )
    HouseholdMember.objects.get_or_create(
        household=h2,
        person=p4,
        role=ROLE_GUARDIAN,
        defaults={"is_primary": False},
    )
    HouseholdMember.objects.get_or_create(
        household=h2,
        person=p4,
        role=ROLE_EMERGENCY_CONTACT,
        defaults={"is_primary": False},
    )
    HouseholdMember.objects.get_or_create(
        household=h2,
        person=p4,
        role=ROLE_AUTHORIZED_PICKUP,
        defaults={"is_primary": False},
    )

    # Household 2 students
    s3p = person("Chloe", "Carter", "chloe.carter@student.example.com")
    s4p = person("David", "Carter", "david.carter@student.example.com")

    Student.objects.get_or_create(
        person=s3p,
        defaults={"household": h2, "grade_level": "5", "active": True},
    )
    Student.objects.get_or_create(
        person=s4p,
        defaults={"household": h2, "grade_level": "2", "active": True},
    )

    print("Seeded households:")
    print(f"- {h1.household_name}")
    print(f"- {h2.household_name}")


if __name__ == "__main__":
    run()
