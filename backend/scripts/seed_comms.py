"""Deterministic local seed for Communications module (threads + messages).

Safe-by-default:
- Refuses to run on Azure (WEBSITE_HOSTNAME/WEBSITE_INSTANCE_ID present)
- Uses get_or_create so it can be re-run without duplicating

Usage (PowerShell):
  cd backend
    .\\venv\\Scripts\\python.exe ..\\backend\\scripts\\seed_comms.py

Note: This seed will create households/students if missing.
"""

import os
import logging
from datetime import datetime, timedelta, timezone


logger = logging.getLogger(__name__)


def _refuse_if_azure() -> None:
    if os.getenv("WEBSITE_HOSTNAME") or os.getenv("WEBSITE_INSTANCE_ID"):
        raise SystemExit("Refusing to run seed_comms on Azure/production.")


def _dt(y, m, d, hh, mm) -> datetime:
    return datetime(y, m, d, hh, mm, tzinfo=timezone.utc)


def run() -> None:
    _refuse_if_azure()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")

    import django

    django.setup()

    from crown_api.models import (
        Household,
        HouseholdMember,
        Message,
        MessageThread,
        Person,
        Student,
    )
    from crown_api.models_households import ROLE_GUARDIAN

    # Two demo households
    household_a, _ = Household.objects.get_or_create(household_name="Household A")
    household_b, _ = Household.objects.get_or_create(household_name="Household B")

    guardian_a, _ = Person.objects.get_or_create(
        email="guardian.a@example.com",
        defaults={"first_name": "Guardian", "last_name": "A", "phone": None},
    )
    guardian_b, _ = Person.objects.get_or_create(
        email="guardian.b@example.com",
        defaults={"first_name": "Guardian", "last_name": "B", "phone": None},
    )

    HouseholdMember.objects.get_or_create(
        household=household_a,
        person=guardian_a,
        role=ROLE_GUARDIAN,
        defaults={"is_primary": False},
    )
    HouseholdMember.objects.get_or_create(
        household=household_b,
        person=guardian_b,
        role=ROLE_GUARDIAN,
        defaults={"is_primary": False},
    )

    # Ensure one student per household (for student-specific threads)
    student_a = Student.objects.filter(household=household_a).select_related("person").first()
    if not student_a:
        student_a_person, _ = Person.objects.get_or_create(
            email="student.a@example.com",
            defaults={"first_name": "Student", "last_name": "A", "phone": None},
        )
        student_a = Student.objects.create(
            person=student_a_person,
            household=household_a,
            grade_level="3",
            active=True,
        )

    student_b = Student.objects.filter(household=household_b).select_related("person").first()
    if not student_b:
        student_b_person, _ = Person.objects.get_or_create(
            email="student.b@example.com",
            defaults={"first_name": "Student", "last_name": "B", "phone": None},
        )
        student_b = Student.objects.create(
            person=student_b_person,
            household=household_b,
            grade_level="4",
            active=True,
        )

    staff_sender, _ = Person.objects.get_or_create(
        email="staff.sender@example.com",
        defaults={"first_name": "Staff", "last_name": "Sender", "phone": None},
    )

    def ensure_thread(household, student, subject, thread_type, created_by):
        return MessageThread.objects.get_or_create(
            household=household,
            student=student,
            subject=subject,
            thread_type=thread_type,
            defaults={"created_by": created_by, "last_message_at": None},
        )

    threads = []

    t1, _ = ensure_thread(
        household_a,
        None,
        "Welcome",
        "GENERAL",
        guardian_a,
    )
    threads.append(t1)

    t2, _ = ensure_thread(
        household_a,
        student_a,
        "Attendance follow-up",
        "ATTENDANCE",
        guardian_a,
    )
    threads.append(t2)

    t3, _ = ensure_thread(
        household_b,
        None,
        "Billing reminder",
        "BILLING",
        guardian_b,
    )
    threads.append(t3)

    t4, _ = ensure_thread(
        household_b,
        student_b,
        "General question",
        "GENERAL",
        guardian_b,
    )
    threads.append(t4)

    base = _dt(2026, 1, 1, 12, 0)

    for idx, thread in enumerate(threads, start=1):
        # Deterministic per-thread window
        thread_base = base + timedelta(days=idx)
        bodies = [
            f"Message 1 for thread {idx}",
            f"Message 2 for thread {idx}",
            f"Message 3 for thread {idx}",
        ]
        senders = [thread.created_by, staff_sender, thread.created_by]

        last_sent = None
        for j in range(3):
            sent_at = thread_base + timedelta(minutes=j * 10)
            Message.objects.get_or_create(
                thread=thread,
                sent_at=sent_at,
                defaults={"sender_person": senders[j], "body": bodies[j]},
            )
            last_sent = sent_at

        if last_sent and thread.last_message_at != last_sent:
            thread.last_message_at = last_sent
            thread.save(update_fields=["last_message_at", "updated_at"])

    logger.info("Seeded communications:")
    logger.info("- Threads: %s", MessageThread.objects.count())
    logger.info("- Messages: %s", Message.objects.count())


if __name__ == "__main__":
    run()
