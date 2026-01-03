import random
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import (
    AcademicYear,
    Enrollment,
    Family,
    GradeLevel,
    Guardian,
    LedgerEntry,
    School,
    Staff,
    Student,
    StudentTuition,
    TuitionPlan,
    UserAccount,
    UserRole,
)
from finance.models import ChartAccount, JournalBatch


class Command(BaseCommand):
    help = "Seed a full demo school with students, families, staff, tuition, and ledger entries."

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(42)
        school_name = "Crown Demo Academy"
        self.stdout.write(self.style.WARNING(f"Resetting data for {school_name}..."))
        School.objects.filter(name=school_name).delete()

        school = School.objects.create(name=school_name, timezone="America/New_York", is_active=True)
        year = AcademicYear.objects.create(
            school=school,
            name="2025-2026",
            start_date=date(2025, 8, 1),
            end_date=date(2026, 6, 15),
            is_current=True,
        )
        self.stdout.write(self.style.SUCCESS(f"✓ Created school + academic year: {year}"))

        grade_defs = [
            ("PK", "Pre-K", 1),
            ("K", "Kindergarten", 2),
            ("1", "Grade 1", 3),
            ("2", "Grade 2", 4),
            ("3", "Grade 3", 5),
            ("4", "Grade 4", 6),
            ("5", "Grade 5", 7),
            ("6", "Grade 6", 8),
            ("7", "Grade 7", 9),
            ("8", "Grade 8", 10),
            ("9", "Grade 9", 11),
            ("10", "Grade 10", 12),
            ("11", "Grade 11", 13),
            ("12", "Grade 12", 14),
        ]
        grade_levels = []
        for code, label, order in grade_defs:
            gl, _ = GradeLevel.objects.get_or_create(
                school=school,
                code=code,
                defaults={"label": label, "sort_order": order},
            )
            grade_levels.append(gl)
        grade_levels = sorted(grade_levels, key=lambda g: g.sort_order)
        self.stdout.write(self.style.SUCCESS(f"✓ Grade levels: {len(grade_levels)}"))

        # Chart accounts
        accounts = {
            "TUITION": {"name": "Tuition", "account_type": "INCOME"},
            "AID": {"name": "Financial Aid", "account_type": "EXPENSE"},
            "FEES": {"name": "Fees", "account_type": "INCOME"},
            "PAYMENT": {"name": "Payments", "account_type": "ASSET"},
        }
        for code, meta in accounts.items():
            ChartAccount.objects.update_or_create(
                school=school,
                code=code,
                defaults={"name": meta["name"], "account_type": meta["account_type"]},
            )
        tuition_account = ChartAccount.objects.get(school=school, code="TUITION")
        self.stdout.write(self.style.SUCCESS("✓ Chart of accounts ready"))

        # Staff + roles + users
        staff_specs = [
            ("Head", "School", "head@demoacademy.edu", "HEAD_OF_SCHOOL", "DIRECTOR", True, False),
            ("Fiona", "Finance", "finance@demoacademy.edu", "FINANCE_DIRECTOR", "DIRECTOR", True, False),
            ("Amy", "Aid", "aid@demoacademy.edu", "AID_DIRECTOR", "DIRECTOR", True, False),
            ("Rita", "Registrar", "registrar@demoacademy.edu", "REGISTRAR", "ADMIN", True, False),
        ]
        users = []
        for first, last, email, role_code, role_type, is_staff, is_superuser in staff_specs:
            staff = Staff.objects.create(
                school=school,
                first_name=first,
                last_name=last,
                email=email,
                role_type=role_type,
                status="ACTIVE",
            )
            user = UserAccount.objects.create_user(
                username=email,
                email=email,
                password="demo1234",
                school=school,
                is_staff=is_staff,
                is_superuser=is_superuser,
            )
            user.staff = staff
            user.save(update_fields=["staff"])
            UserRole.objects.create(school=school, user=user, role_code=role_code)
            users.append(user)
        self.stdout.write(self.style.SUCCESS(f"✓ Staff & roles: {len(users)} users"))

        # Tuition plan
        tuition_plan, _ = TuitionPlan.objects.get_or_create(
            school=school,
            academic_year=year,
            name="Standard Tuition",
            defaults={"annual_amount_cents": 1_200_000, "is_active": True},
        )
        self.stdout.write(self.style.SUCCESS("✓ Tuition plan ready ($12,000)"))

        # Families and guardians
        family_count = 180
        families = []
        aid_family_ids = set(random.sample(range(family_count), k=int(family_count * 0.35)))
        for i in range(family_count):
            fam = Family.objects.create(
                school=school,
                family_name=f"Family {i+1:03d}",
                city="Springfield",
                state="NY",
                zip_code="10001",
                status="ACTIVE",
            )
            Guardian.objects.create(
                school=school,
                family=fam,
                first_name="Pat",
                last_name=fam.family_name,
                email=f"parent{i+1:03d}@demoacademy.edu",
                relationship="GUARDIAN",
                portal_access=True,
            )
            fam.aid_eligible = i in aid_family_ids  # convenience flag for later aid seeding
            families.append(fam)
        self.stdout.write(self.style.SUCCESS(f"✓ Families created: {len(families)} (aid-eligible: {len(aid_family_ids)})"))

        # Students
        student_target = 300
        batch = JournalBatch.objects.create(
            school=school,
            academic_year=year,
            description="Tuition charges for demo",
            status="OPEN",
            created_by=users[0] if users else None,
            batch_date=year.start_date,
        )

        def approximate_dob_for_grade(code: str) -> date:
            base_year = year.start_date.year
            age_map = {
                "PK": 4,
                "K": 5,
                "1": 6,
                "2": 7,
                "3": 8,
                "4": 9,
                "5": 10,
                "6": 11,
                "7": 12,
                "8": 13,
                "9": 14,
                "10": 15,
                "11": 16,
                "12": 17,
            }
            age = age_map.get(code, 10)
            return date(base_year - age, 6, 15)

        students = []
        for idx in range(student_target):
            family = families[idx % len(families)]
            grade = grade_levels[idx % len(grade_levels)]
            student = Student.objects.create(
                school=school,
                family=family,
                student_number=f"S{idx+1:04d}",
                first_name=f"Student{idx+1:04d}",
                last_name=family.family_name,
                dob=approximate_dob_for_grade(grade.code),
                status="ACTIVE",
                current_grade_level=grade,
            )
            Enrollment.objects.create(
                school=school,
                student=student,
                academic_year=year,
                grade_level=grade,
                start_date=year.start_date,
                status="ENROLLED",
            )
            StudentTuition.objects.create(
                school=school,
                student=student,
                academic_year=year,
                tuition_plan=tuition_plan,
                annual_amount_cents=tuition_plan.annual_amount_cents,
                discounts_cents=0,
                net_annual_cents=tuition_plan.annual_amount_cents,
            )
            LedgerEntry.objects.create(
                school=school,
                family=family,
                student=student,
                academic_year=year,
                account=tuition_account,
                batch=batch,
                entry_date=year.start_date,
                amount_cents=tuition_plan.annual_amount_cents,
                memo=f"Tuition charge for {year.name}",
                source=LedgerEntry.SOURCE_TUITION_SET,
                created_by_user=users[0] if users else None,
            )
            students.append(student)
        self.stdout.write(self.style.SUCCESS(f"✓ Students created: {len(students)}"))

        self.stdout.write(self.style.SUCCESS("Demo data seeding complete."))
        self.stdout.write(
            self.style.HTTP_INFO(
                "Login as head@demoacademy.edu / demo1234 (or your existing superuser) to view dashboards."
            )
        )
