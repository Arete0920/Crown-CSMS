"""
seed_demo -- populate deterministic demo data for dashboard proof.

Creates (idempotently):
  - 1 School  (name="Crown Academy Demo")
  - 5 Households + Guardians + 5 Students
  - AftercareProgramConfig
  - AftercareEnrollment (school_fk + student_fk set, M-F flat monthly)
  - AftercareAttendance with late pickups for 2 students (triggers signals)
  - AftercareIncident for 1 student (triggers aftercare_incident_spike)
  - 2 SignalDefinitions (aftercare_late_spike, aftercare_incident_spike)
  - Runs compute_snapshots_for_school + compute_board_metrics

Usage:
    python manage.py seed_demo
    python manage.py seed_demo --reset    # Wipe all demo data first
"""
from datetime import date, timedelta
import uuid

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


DEMO_SCHOOL_NAME = "Crown Academy Demo"

DEMO_FAMILIES = [
    {"last": "Johnson",  "first": "Marcus",  "grade": "5",  "guardian_first": "Patricia",  "guardian_email": "pjohnson@demo.test"},
    {"last": "Williams", "first": "Aisha",   "grade": "3",  "guardian_first": "DeShawn",   "guardian_email": "dwilliams@demo.test"},
    {"last": "Garcia",   "first": "Sofia",   "grade": "K",  "guardian_first": "Elena",     "guardian_email": "egarcia@demo.test"},
    {"last": "Thompson", "first": "Elijah",  "grade": "7",  "guardian_first": "Denise",    "guardian_email": "dthompson@demo.test"},
    {"last": "Lee",      "first": "Naomi",   "grade": "2",  "guardian_first": "James",     "guardian_email": "jlee@demo.test"},
]

# Students index 0 and 1 will have many late pickups to trigger HIGH risk signals
# Student index 2 will have incidents
LATE_PICKUPS = {0: 5, 1: 4, 2: 1, 3: 0, 4: 0}
INCIDENTS    = {0: 0, 1: 0, 2: 3, 3: 0, 4: 0}


class Command(BaseCommand):
    help = "Seed deterministic demo data for Crown signals + board dashboard proof."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing demo data before seeding",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        from aftercare.models import (
            AftercareAttendance,
            AftercareEnrollment,
            AftercareIncident,
            AftercareProgramConfig,
        )
        from core.models import School
        from households.models import Guardian, Household, Student
        from signals.engine import compute_board_metrics, compute_snapshots_for_school
        from signals.models import SignalDefinition

        if opts["reset"]:
            self._reset()

        # ---- School ------------------------------------------------------ #
        school, created = School.objects.get_or_create(
            name=DEMO_SCHOOL_NAME,
            defaults={"timezone": "America/New_York", "is_active": True},
        )
        self.stdout.write(f"{'Created' if created else 'Found'} school: {school.name} ({school.pk})")

        # Use a fixed fake integer for the legacy aftercare school_id field.
        # The engine now routes through school_fk; this value is for backward-compat only.
        DEMO_INT_SCHOOL_ID = 9001

        # ---- AftercareProgramConfig -------------------------------------- #
        AftercareProgramConfig.objects.get_or_create(
            school_id=DEMO_INT_SCHOOL_ID,
            defaults={
                "start_time":  "15:00",
                "end_time":    "18:00",
                "late_fee_per_10_min": "10.00",
                "late_fee_grace_minutes": 5,
                "late_fee_cap": "100.00",
                "default_billing_model": "FLAT_MONTHLY",
                "monthly_rate_5_days": "210.00",
            },
        )

        # ---- SignalDefinitions ------------------------------------------- #
        SignalDefinition.objects.get_or_create(
            school=school,
            key="aftercare_late_spike",
            defaults={
                "name": "Aftercare Late Pickup Spike",
                "description": "Student picked up late 3+ times in 30 days.",
                "severity_weight": 30,
                "is_active": True,
                "rule": {"type": "aftercare_late_spike", "window_days": 30, "threshold_count": 3},
            },
        )
        SignalDefinition.objects.get_or_create(
            school=school,
            key="aftercare_incident_spike",
            defaults={
                "name": "Aftercare Incident Spike",
                "description": "Student involved in 2+ incidents in 30 days.",
                "severity_weight": 40,
                "is_active": True,
                "rule": {"type": "aftercare_incident_spike", "window_days": 30, "threshold_count": 2},
            },
        )

        # ---- Households + Guardians + Students + Enrollments + Attendance -- #
        today = timezone.now().date()
        start_of_year = date(today.year, 9, 1) if today.month >= 9 else date(today.year - 1, 9, 1)

        students_list = []

        for idx, fam in enumerate(DEMO_FAMILIES):
            # Household
            hh, _ = Household.objects.get_or_create(
                school_id=school.pk,
                name=f"{fam['last']} Family",
                defaults={"is_active": True},
            )

            # Guardian
            Guardian.objects.get_or_create(
                school_id=school.pk,
                household=hh,
                last_name=fam["last"],
                first_name=fam["guardian_first"],
                defaults={
                    "email": fam["guardian_email"],
                    "is_primary": True,
                },
            )

            # Student
            student, _ = Student.objects.get_or_create(
                school_id=school.pk,
                household=hh,
                last_name=fam["last"],
                first_name=fam["first"],
                defaults={
                    "grade_level": fam["grade"],
                    "is_active": True,
                },
            )
            students_list.append(student)

            # Legacy integer student_id (throwaway; engine uses student_fk)
            int_student_id = 1001 + idx

            # AftercareEnrollment
            AftercareEnrollment.objects.get_or_create(
                school_fk=school,
                student_fk=student,
                defaults={
                    "school_id": DEMO_INT_SCHOOL_ID,
                    "student_id": int_student_id,
                    "start_date": start_of_year,
                    "days_of_week": ["MON", "TUE", "WED", "THU", "FRI"],
                    "billing_model": "FLAT_MONTHLY",
                    "monthly_rate": "210.00",
                    "is_active": True,
                },
            )

            # AftercareAttendance: late pickups for some students
            late_count = LATE_PICKUPS.get(idx, 0)
            for i in range(late_count):
                att_date = today - timedelta(days=3 + i * 5)
                AftercareAttendance.objects.get_or_create(
                    school_fk=school,
                    student_fk=student,
                    date=att_date,
                    defaults={
                        "school_id": DEMO_INT_SCHOOL_ID,
                        "student_id": int_student_id,
                        "checkin_time": timezone.make_aware(
                            timezone.datetime(att_date.year, att_date.month, att_date.day, 15, 5)
                        ),
                        "checkout_time": timezone.make_aware(
                            timezone.datetime(att_date.year, att_date.month, att_date.day, 18, 25)
                        ),
                        "late_minutes": 25,
                        "late_fee_cents": 2500,
                        "pickup_name_freeform": fam["guardian_first"] + " " + fam["last"],
                        "pickup_verified": True,
                    },
                )

            # AftercareIncident: for student index 2
            incident_count = INCIDENTS.get(idx, 0)
            for i in range(incident_count):
                inc_time = timezone.now() - timedelta(days=5 + i * 4)
                AftercareIncident.objects.get_or_create(
                    school_fk=school,
                    student_fk=student,
                    occurred_at=inc_time,
                    defaults={
                        "school_id": DEMO_INT_SCHOOL_ID,
                        "student_id": int_student_id,
                        "severity": "MODERATE",
                        "description": f"Demo incident {i+1}: altercation during snack time.",
                        "parent_notified": True,
                    },
                )

        self.stdout.write(f"Seeded {len(students_list)} students with aftercare data.")

        # ---- Run signal engine ------------------------------------------- #
        self.stdout.write("Running signal engine...")
        compute_snapshots_for_school(school)
        compute_board_metrics(school)
        self.stdout.write(self.style.SUCCESS("Done. Demo data seeded and signals computed."))

    def _reset(self):
        """Wipe all demo school data (signals, aftercare, households)."""
        from aftercare.models import AftercareAttendance, AftercareEnrollment, AftercareIncident
        from core.models import School
        from households.models import Guardian, Household, Student
        from signals.models import (
            BoardExecutiveMetric, InterventionCase,
            SignalDefinition, SignalEvent, StudentRiskSnapshot,
        )

        try:
            school = School.objects.get(name=DEMO_SCHOOL_NAME)
        except School.DoesNotExist:
            self.stdout.write("No demo school to reset.")
            return

        self.stdout.write(f"Resetting demo school {school.pk}...")

        # Aftercare (by UUID FK)
        AftercareAttendance.objects.filter(school_fk=school).delete()
        AftercareIncident.objects.filter(school_fk=school).delete()
        AftercareEnrollment.objects.filter(school_fk=school).delete()

        # Signals (by UUID FK)
        SignalEvent.objects.filter(school=school).delete()
        StudentRiskSnapshot.objects.filter(school=school).delete()
        InterventionCase.objects.filter(school=school).delete()
        BoardExecutiveMetric.objects.filter(school=school).delete()
        SignalDefinition.objects.filter(school=school).delete()

        # Households: delete Students first (PROTECT), then Guardians, then Households
        Student.objects.filter(school_id=school.pk).delete()
        Guardian.objects.filter(school_id=school.pk).delete()
        Household.objects.filter(school_id=school.pk).delete()

        self.stdout.write("Reset complete.")
