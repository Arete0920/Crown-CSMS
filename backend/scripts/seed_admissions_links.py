"""Deterministic local seed for Admissions linkages.

Safe-by-default:
- Refuses to run on Azure (WEBSITE_HOSTNAME/WEBSITE_INSTANCE_ID present)
- Uses get_or_create so it can be re-run without duplicating

Creates a couple AdmissionsApplication rows linked to:
- household only
- household + sis_student

Usage (PowerShell):
  cd backend
  C:/Users/JMega/OneDrive/Desktop/Crown2026/.venv/Scripts/python.exe ..\backend\scripts\seed_admissions_links.py
"""

import os
from datetime import date


def _refuse_if_azure() -> None:
    if os.getenv("WEBSITE_HOSTNAME") or os.getenv("WEBSITE_INSTANCE_ID"):
        raise SystemExit("Refusing to run seed_admissions_links on Azure/production.")


def run() -> None:
    _refuse_if_azure()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")

    import django

    django.setup()

    from admissions.models import AdmissionsApplication
    from core.models import AcademicYear, Family, School
    from crown_api.models import Household, Person, Student

    school, _ = School.objects.get_or_create(name="Crown Academy")

    year, _ = AcademicYear.objects.get_or_create(
        school=school,
        name="2026–2027",
        defaults={"start_date": date(2026, 8, 1), "end_date": date(2027, 6, 15)},
    )

    fam1, _ = Family.objects.get_or_create(school=school, family_name="Megahan")
    fam2, _ = Family.objects.get_or_create(school=school, family_name="Carter")

    h1, _ = Household.objects.get_or_create(household_name="The Megahan Family")
    h2, _ = Household.objects.get_or_create(household_name="The Carter Family")

    s_person, _ = Person.objects.get_or_create(
        email="seed.student@example.com",
        defaults={"first_name": "Seed", "last_name": "Student"},
    )
    sis_student, _ = Student.objects.get_or_create(
        person=s_person,
        defaults={"household": h2, "grade_level": "5", "active": True},
    )

    app1, _ = AdmissionsApplication.objects.get_or_create(
        school=school,
        academic_year=year,
        family=fam1,
        defaults={"status": AdmissionsApplication.STATUS_SUBMITTED},
    )
    if app1.household_id != h1.id:
        app1.household = h1
        app1.save(update_fields=["household", "updated_at"])

    app2, _ = AdmissionsApplication.objects.get_or_create(
        school=school,
        academic_year=year,
        family=fam2,
        defaults={"status": AdmissionsApplication.STATUS_UNDER_REVIEW},
    )
    changed = False
    if app2.household_id != h2.id:
        app2.household = h2
        changed = True
    if app2.sis_student_id != sis_student.id:
        app2.sis_student = sis_student
        changed = True
    if changed:
        app2.save(update_fields=["household", "sis_student", "updated_at"])

    print("Seeded admissions applications:")
    print(f"- {app1.id} (household only)")
    print(f"- {app2.id} (household + student)")


if __name__ == "__main__":
    run()
