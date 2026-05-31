from __future__ import annotations

import re
import uuid
from dataclasses import asdict
from datetime import date, timedelta

from django.conf import settings
from django.db import transaction

from core.models import (
    AcademicYear,
    Enrollment,
    Family,
    GradeLevel,
    Guardian,
    School,
    Staff,
    Student,
    StudentTuition,
    TuitionPlan,
    UserAccount,
    UserRole,
)
from crown_api.jwt_utils import build_access_token, build_refresh_token
from finance.models import FinanceInvoice, FinanceInvoiceLine, FinanceObligation, MoneyStatus, ObligationType

from .catalog import SANDBOX_PERSONAS, SANDBOX_SCHOOLS, SandboxPersona, SandboxSchool, get_persona, get_school


PROHIBITED_FEEDBACK_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    re.compile(r"\b\d{3}[-.) ]?\d{3}[-. ]?\d{4}\b"),
]


def note_has_prohibited_data(note: str) -> bool:
    if not note:
        return False
    return any(pattern.search(note) for pattern in PROHIBITED_FEEDBACK_PATTERNS)


@transaction.atomic
def ensure_demo_school(school_spec: SandboxSchool) -> School:
    school_id = uuid.UUID(school_spec.id)
    school, _ = School.objects.update_or_create(
        id=school_id,
        defaults={
            "name": school_spec.name,
            "timezone": "America/New_York",
            "is_active": True,
        },
    )
    return school


def _role_type_for_persona(persona: SandboxPersona) -> str:
    if persona.key in {"school_admin", "admissions_director", "finance_director"}:
        return "ADMIN"
    if persona.key == "teacher":
        return "TEACHER"
    return "SUPPORT"


@transaction.atomic
def ensure_persona_user(school: School, persona: SandboxPersona) -> UserAccount:
    family = None
    guardian = None
    staff = None

    if persona.key in {"parent", "student"}:
        family, _ = Family.objects.get_or_create(
            school=school,
            family_name="Reed Family",
            defaults={
                "address_line1": "100 Demo Lane",
                "city": "Fairview",
                "state": "PA",
                "zip_code": "19000",
                "status": "ACTIVE",
            },
        )
        guardian, _ = Guardian.objects.update_or_create(
            school=school,
            email="parent.reed@heritage.example.org",
            defaults={
                "family": family,
                "first_name": "Miriam",
                "last_name": "Reed",
                "phone": "555-0100",
                "relationship": "MOTHER",
                "portal_access": True,
                "custody_flag": False,
            },
        )
    else:
        staff, _ = Staff.objects.update_or_create(
            school=school,
            email=persona.email,
            defaults={
                "first_name": persona.first_name,
                "last_name": persona.last_name,
                "role_type": _role_type_for_persona(persona),
                "status": "ACTIVE",
            },
        )

    user, _ = UserAccount.objects.update_or_create(
        username=persona.email,
        defaults={
            "email": persona.email,
            "first_name": persona.first_name,
            "last_name": persona.last_name,
            "school": school,
            "staff": staff,
            "guardian": guardian if persona.key == "parent" else None,
            "is_active": True,
        },
    )

    fallback_password = getattr(settings, "CROWN_SANDBOX_FALLBACK_PASSWORD", "")
    if fallback_password:
        user.set_password(fallback_password)
    else:
        user.set_unusable_password()
    user.save()

    UserRole.objects.update_or_create(
        school=school,
        user=user,
        role_code=persona.role_code,
        defaults={},
    )

    return user


@transaction.atomic
def create_sandbox_session(*, persona_key: str, school_key_or_id: str, guidance: str, tour: str | None = None) -> dict:
    persona = get_persona(persona_key)
    school_spec = get_school(school_key_or_id)
    school = ensure_demo_school(school_spec)
    user = ensure_persona_user(school, persona)
    tour_title = tour or persona.tour_title

    access = build_access_token(
        user_id=str(user.id),
        email=user.email,
        role=persona.key,
        school_id=str(school.id),
        ttl_seconds=int(getattr(settings, "CROWN_SANDBOX_ACCESS_TTL_SECONDS", 60 * 60 * 2)),
    )
    refresh = build_refresh_token(
        user_id=str(user.id),
        ttl_seconds=int(getattr(settings, "CROWN_SANDBOX_REFRESH_TTL_SECONDS", 60 * 60 * 12)),
    )

    return {
        "access": access,
        "refresh": refresh,
        "school_id": str(school.id),
        "school_name": school.name,
        "role": persona.key,
        "role_code": persona.role_code,
        "route": persona.route,
        "guidance": guidance,
        "tour": tour_title,
        "command_center": {
            "track": school_spec.track,
            "school": asdict(school_spec),
            "persona": asdict(persona),
            "guidance": guidance,
            "tour": tour_title,
        },
    }


def _clear_flagship_data(school: School) -> None:
    from finance.models import FinanceAllocation, FinancePayment

    FinanceAllocation.objects.filter(school=school).delete()
    FinanceInvoiceLine.objects.filter(invoice__school=school).delete()
    FinanceInvoice.objects.filter(school=school).delete()
    FinancePayment.objects.filter(school=school).delete()
    FinanceObligation.objects.filter(school=school).delete()
    UserRole.objects.filter(school=school).delete()
    UserAccount.objects.filter(school=school).delete()
    StudentTuition.objects.filter(school=school).delete()
    Enrollment.objects.filter(school=school).delete()
    Student.objects.filter(school=school).delete()
    Guardian.objects.filter(school=school).delete()
    Staff.objects.filter(school=school).delete()
    Family.objects.filter(school=school).delete()
    TuitionPlan.objects.filter(school=school).delete()
    GradeLevel.objects.filter(school=school).delete()
    AcademicYear.objects.filter(school=school).delete()


@transaction.atomic
def seed_heritage_flagship(*, reset: bool = False) -> dict:
    school_spec = SANDBOX_SCHOOLS["heritage-core"]
    school = ensure_demo_school(school_spec)

    if reset:
        _clear_flagship_data(school)

    academic_year, _ = AcademicYear.objects.update_or_create(
        school=school,
        name="2026-2027",
        defaults={
            "start_date": date(2026, 8, 15),
            "end_date": date(2027, 6, 5),
            "is_current": True,
        },
    )

    grade_data = [
        ("PK", "Early Education / Preschool", 0, 180),
        ("K", "Kindergarten", 1, 40),
        ("1", "Grade 1", 2, 38),
        ("2", "Grade 2", 3, 37),
        ("3", "Grade 3", 4, 36),
        ("4", "Grade 4", 5, 35),
        ("5", "Grade 5", 6, 34),
        ("6", "Grade 6", 7, 48),
        ("7", "Grade 7", 8, 45),
        ("8", "Grade 8", 9, 42),
        ("9", "Grade 9", 10, 48),
        ("10", "Grade 10", 11, 42),
        ("11", "Grade 11", 12, 38),
        ("12", "Grade 12", 13, 37),
    ]

    grade_levels = {}
    tuition_plans = {}
    for code, label, sort_order, _target in grade_data:
        grade, _ = GradeLevel.objects.update_or_create(
            school=school,
            code=code,
            defaults={"label": label, "sort_order": sort_order},
        )
        grade_levels[code] = grade

        if code == "PK":
            amount = 1140000
        elif code in {"K", "1", "2", "3", "4", "5"}:
            amount = 875000
        elif code in {"6", "7", "8"}:
            amount = 995000
        else:
            amount = 1125000

        plan, _ = TuitionPlan.objects.update_or_create(
            school=school,
            academic_year=academic_year,
            name=f"{label} Published Tuition",
            defaults={"annual_amount_cents": amount, "is_active": True},
        )
        tuition_plans[code] = plan

    families = []
    for idx in range(1, 287):
        family, _ = Family.objects.update_or_create(
            school=school,
            family_name=f"Demo Family {idx:03d}",
            defaults={
                "address_line1": f"{1000 + idx} Covenant Way",
                "city": "Fairview",
                "state": "PA",
                "zip_code": f"19{idx % 1000:03d}",
                "status": "ACTIVE",
            },
        )
        families.append(family)
        Guardian.objects.update_or_create(
            school=school,
            email=f"guardian{idx:03d}@heritage.example.org",
            defaults={
                "family": family,
                "first_name": f"Guardian{idx:03d}",
                "last_name": "Demo",
                "phone": f"555-01{idx % 100:02d}",
                "relationship": "GUARDIAN",
                "portal_access": True,
                "custody_flag": False,
            },
        )

    student_index = 1
    for code, _label, _sort, target in grade_data:
        grade = grade_levels[code]
        plan = tuition_plans[code]
        for _ in range(target):
            family = families[(student_index - 1) % len(families)]
            student_number = f"HCA-{student_index:04d}"
            student, _ = Student.objects.update_or_create(
                school=school,
                student_number=student_number,
                defaults={
                    "family": family,
                    "first_name": f"Student{student_index:04d}",
                    "last_name": "Demo",
                    "dob": date(2010, 1, 1) - timedelta(days=student_index * 5),
                    "status": "ACTIVE",
                    "current_grade_level": grade,
                },
            )
            Enrollment.objects.update_or_create(
                school=school,
                student=student,
                academic_year=academic_year,
                defaults={
                    "grade_level": grade,
                    "start_date": academic_year.start_date,
                    "end_date": None,
                    "status": "ENROLLED",
                },
            )
            StudentTuition.objects.update_or_create(
                school=school,
                student=student,
                academic_year=academic_year,
                defaults={
                    "tuition_plan": plan,
                    "annual_amount_cents": plan.annual_amount_cents,
                    "discounts_cents": 0,
                    "net_annual_cents": plan.annual_amount_cents,
                },
            )
            student_index += 1

    for persona in SANDBOX_PERSONAS.values():
        ensure_persona_user(school, persona)

    parent_user = UserAccount.objects.filter(username="parent.reed@heritage.example.org", school=school).first()
    if parent_user:
        for n in range(1, 13):
            obligation, _ = FinanceObligation.objects.update_or_create(
                school=school,
                payer_user=parent_user,
                reference=f"HCA-DEMO-TUITION-{n:02d}",
                defaults={
                    "obligation_type": ObligationType.TUITION,
                    "status": MoneyStatus.OPEN,
                    "description": f"Monthly tuition installment {n}",
                    "due_date": date(2026, n, 15),
                    "amount_cents": 87500,
                    "currency": "USD",
                    "academic_year_label": "2026-2027",
                },
            )
            invoice, _ = FinanceInvoice.objects.update_or_create(
                school=school,
                payer_user=parent_user,
                due_date=obligation.due_date,
                defaults={
                    "status": MoneyStatus.OPEN,
                    "period_start": obligation.due_date.replace(day=1),
                    "period_end": obligation.due_date,
                    "subtotal_cents": obligation.amount_cents,
                    "total_cents": obligation.amount_cents,
                    "currency": "USD",
                    "note": "Demo-only family invoice.",
                },
            )
            FinanceInvoiceLine.objects.update_or_create(
                invoice=invoice,
                obligation=obligation,
                defaults={
                    "amount_cents": obligation.amount_cents,
                    "description": obligation.description,
                },
            )

    return proof_metrics(school)


def proof_metrics(school: School) -> dict:
    return {
        "school_id": str(school.id),
        "school_name": school.name,
        "families": Family.objects.filter(school=school).count(),
        "guardians": Guardian.objects.filter(school=school).count(),
        "students": Student.objects.filter(school=school).count(),
        "staff": Staff.objects.filter(school=school).count(),
        "users": UserAccount.objects.filter(school=school).count(),
        "roles": UserRole.objects.filter(school=school).count(),
        "enrollments": Enrollment.objects.filter(school=school).count(),
        "student_tuitions": StudentTuition.objects.filter(school=school).count(),
        "finance_obligations": FinanceObligation.objects.filter(school=school).count(),
        "finance_invoices": FinanceInvoice.objects.filter(school=school).count(),
    }


def assert_flagship_proof() -> list[dict]:
    school = ensure_demo_school(SANDBOX_SCHOOLS["heritage-core"])
    metrics = proof_metrics(school)
    findings = []

    minimums = {
        "families": 286,
        "students": 700,
        "users": 6,
        "roles": 6,
        "enrollments": 700,
        "student_tuitions": 700,
        "finance_obligations": 12,
        "finance_invoices": 12,
    }

    for key, expected in minimums.items():
        actual = metrics.get(key, 0)
        findings.append({
            "level": "PASS" if actual >= expected else "FAIL",
            "message": f"{key}: actual={actual} expected_min={expected}",
        })

    for persona in SANDBOX_PERSONAS.values():
        session = create_sandbox_session(
            persona_key=persona.key,
            school_key_or_id=str(school.id),
            guidance="guided",
            tour=persona.tour_title,
        )
        ok = bool(session.get("access") and session.get("route") == persona.route)
        findings.append({
            "level": "PASS" if ok else "FAIL",
            "message": f"one-click session for {persona.key}",
        })

    return findings
