from __future__ import annotations

import uuid

import pytest

from applications.models import Application, Applicant, ApplicationStatus
from core.models import School
from households.models import Guardian, Household

pytestmark = pytest.mark.django_db


def test_applicant_guardian_payload_materializes_household_guardians_without_account_binding():
    school = School.objects.create(name="Guardian Continuity School")
    household = Household.objects.create(school_id=school.id, name="Reed Family")
    application = Application.objects.create(
        school_id=school.id,
        household=household,
        status=ApplicationStatus.SUBMITTED,
    )

    Applicant.objects.create(
        school_id=school.id,
        application=application,
        first_name="Avery",
        last_name="Reed",
        grade_applying_for="6",
        flags={
            "guardians": [
                {
                    "guardianName": "Jordan Reed",
                    "email": "PARENT.REED@example.org",
                    "phone": "555-010-1101",
                    "isPrimary": True,
                },
                {
                    "guardianName": "Casey Reed",
                    "email": "casey.reed@example.org",
                    "phone": "555-010-1102",
                    "isPrimary": False,
                },
            ]
        },
    )

    guardians = Guardian.objects.filter(household=household, school_id=school.id).order_by("email")
    assert guardians.count() == 2
    primary = guardians.get(email="parent.reed@example.org")
    assert primary.first_name == "Jordan"
    assert primary.last_name == "Reed"
    assert primary.phone == "555-010-1101"
    assert primary.is_primary is True
    assert primary.account_id is None


def test_multiple_applicants_for_same_household_do_not_duplicate_guardians():
    school = School.objects.create(name="Guardian Idempotency School")
    household = Household.objects.create(school_id=school.id, name="Reed Family")
    application = Application.objects.create(
        school_id=school.id,
        household=household,
        status=ApplicationStatus.SUBMITTED,
    )
    flags = {
        "guardians": [
            {
                "guardianName": "Jordan Reed",
                "email": "parent.reed@example.org",
                "phone": "555-010-1101",
                "isPrimary": True,
            }
        ]
    }

    for first_name in ("Avery", "Micah"):
        Applicant.objects.create(
            id=uuid.uuid4(),
            school_id=school.id,
            application=application,
            first_name=first_name,
            last_name="Reed",
            grade_applying_for="6",
            flags=flags,
        )

    assert Guardian.objects.filter(
        household=household,
        school_id=school.id,
        email__iexact="parent.reed@example.org",
    ).count() == 1
