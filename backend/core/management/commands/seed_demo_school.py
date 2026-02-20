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
from aid.models import AidApplication, AidAward
from finance.models import ChartAccount, JournalBatch


FIRST_NAMES = [
    "Noah", "Liam", "Elijah", "Oliver", "James", "William", "Benjamin", "Lucas", "Henry", "Theodore",
    "Olivia", "Emma", "Charlotte", "Amelia", "Sophia", "Isabella", "Ava", "Mia", "Evelyn", "Harper",
    "Caleb", "Ethan", "Logan", "Mason", "Aiden", "Jackson", "Sebastian", "Jack", "Owen", "Wyatt",
    "Abigail", "Emily", "Ella", "Scarlett", "Grace", "Chloe", "Victoria", "Riley", "Zoey", "Hannah",
]

LAST_NAMES = [
    "Adams", "Baker", "Carter", "Davis", "Edwards", "Foster", "Garcia", "Harris", "Iverson", "Johnson",
    "King", "Lewis", "Miller", "Nelson", "Owens", "Parker", "Quinn", "Roberts", "Stewart", "Turner",
    "Underwood", "Vaughn", "Walker", "Young", "Zimmerman", "Brooks", "Campbell", "Coleman", "Diaz", "Evans",
    "Fisher", "Gonzalez", "Hill", "Ingram", "Jenkins", "Kelly", "Lopez", "Mitchell", "Reed", "Sanchez",
]

GRADE_CODES = ["PK", "K", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]


def cents(dollars: float) -> int:
    return int(round(dollars * 100))


class Command(BaseCommand):
    help = "Seed a realistic demo school for Crown (PK–12, ~300 students, $12k tuition, 35% aid)."

    def add_arguments(self, parser):
        parser.add_argument("--students", type=int, default=300)
        parser.add_argument("--tuition", type=int, default=12000)
        parser.add_argument("--aid_pct", type=int, default=35)
        parser.add_argument("--school_name", type=str, default="Crown Demo Christian Academy")
        parser.add_argument("--year_name", type=str, default="2026–2027")
        parser.add_argument("--wipe", action="store_true", help="DANGER: wipe demo data for this school name before seeding")

    @transaction.atomic
    def handle(self, *args, **options):
        students_target = int(options["students"])
        tuition_dollars = int(options["tuition"])
        aid_pct = int(options["aid_pct"])
        school_name = options["school_name"].strip()
        year_name = options["year_name"].strip()
        wipe = bool(options["wipe"])

        self.stdout.write(self.style.WARNING(
            f"Seeding: {school_name} | {year_name} | students={students_target} | tuition=${tuition_dollars} | aid={aid_pct}%"
        ))

        # --- 1) School + Academic Year ---
        school, _ = School.objects.get_or_create(
            name=school_name,
            defaults={"timezone": "America/New_York", "is_active": True},
        )

        if wipe:
            self._wipe_school(school)
            self.stdout.write(self.style.WARNING("Wipe complete."))

        ay, _ = AcademicYear.objects.get_or_create(
            school=school,
            name=year_name,
            defaults={"start_date": date(2026, 8, 15), "end_date": date(2027, 6, 10), "is_current": True},
        )

        # Ensure only one current year
        AcademicYear.objects.filter(school=school).exclude(id=ay.id).update(is_current=False)

        # --- 2) Grade levels PK–12 ---
        grades_by_code = {}
        for idx, code in enumerate(GRADE_CODES, start=1):
            label = "Pre-K" if code == "PK" else ("Kindergarten" if code == "K" else f"Grade {code}")
            gl, _ = GradeLevel.objects.get_or_create(
                school=school,
                code=code,
                defaults={"label": label, "sort_order": idx},
            )
            if gl.sort_order != idx or gl.label != label:
                gl.sort_order = idx
                gl.label = label
                gl.save(update_fields=["sort_order", "label"])
            grades_by_code[code] = gl

        # --- 3) Finance: Chart of Accounts + Tuition Plan ---
        coa = self._ensure_chart_accounts(school)
        tuition_plan, _ = TuitionPlan.objects.get_or_create(
            school=school,
            academic_year=ay,
            defaults={"name": "Standard Tuition", "annual_amount_cents": cents(tuition_dollars), "is_active": True},
        )

        # --- 4) Staff + Crown UserAccounts + Roles (Directors) ---
        directors = self._ensure_directors(school)

        # --- 5) Create families/guardians/students/enrollments ---
        families = self._create_families(school, target_students=students_target)
        self.stdout.write(self.style.SUCCESS(f"Families created/ensured: {len(families)}"))

        base_per_grade = 20
        remainder = max(0, students_target - base_per_grade * len(GRADE_CODES))
        distribution = {code: base_per_grade for code in GRADE_CODES}
        preferred = ["6", "7", "8", "9", "10", "5", "11", "4", "12", "3", "2", "1", "K", "PK"]
        i = 0
        while remainder > 0:
            distribution[preferred[i % len(preferred)]] += 1
            remainder -= 1
            i += 1

        created_students = []
        student_counter_start = Student.objects.filter(school=school).count() + 1

        for code in GRADE_CODES:
            count = distribution[code]
            gl = grades_by_code[code]
            for _ in range(count):
                family = random.choice(families)
                st = self._create_student(
                    school=school,
                    family=family,
                    grade_level=gl,
                    student_number=f"S{student_counter_start:05d}",
                )
                student_counter_start += 1
                created_students.append(st)

                Enrollment.objects.get_or_create(
                    school=school,
                    student=st,
                    academic_year=ay,
                    grade_level=gl,
                    defaults={"start_date": ay.start_date, "status": "ENROLLED"},
                )

        self.stdout.write(self.style.SUCCESS(f"Students created/ensured: {len(created_students)}"))

        # --- 6) Tuition: StudentTuition + Ledger postings (TUITION) ---
        tuition_batch = JournalBatch.objects.create(
            school=school,
            academic_year=ay,
            batch_date=timezone.now().date(),
            description="Tuition Set - Demo Seed",
            status="OPEN",
            created_by=directors["finance_user"],
        )

        for st in created_students:
            st_tuition, created = StudentTuition.objects.get_or_create(
                school=school,
                academic_year=ay,
                student=st,
                defaults={
                    "tuition_plan": tuition_plan,
                    "annual_amount_cents": tuition_plan.annual_amount_cents,
                    "discounts_cents": 0,
                    "net_annual_cents": tuition_plan.annual_amount_cents,
                },
            )
            if not created:
                st_tuition.tuition_plan = tuition_plan
                st_tuition.annual_amount_cents = tuition_plan.annual_amount_cents
                st_tuition.discounts_cents = 0
                st_tuition.net_annual_cents = tuition_plan.annual_amount_cents
                st_tuition.save(update_fields=["tuition_plan", "annual_amount_cents", "discounts_cents", "net_annual_cents"])

            exists = LedgerEntry.objects.filter(
                school=school,
                academic_year=ay,
                student=st,
                account=coa["TUITION"],
                source=LedgerEntry.SOURCE_TUITION_SET,
            ).exists()
            if not exists:
                LedgerEntry.objects.create(
                    school=school,
                    academic_year=ay,
                    family=st.family,
                    student=st,
                    entry_date=ay.start_date,
                    account=coa["TUITION"],
                    amount_cents=st_tuition.net_annual_cents,
                    memo="Annual Tuition Set",
                    source=LedgerEntry.SOURCE_TUITION_SET,
                    batch=tuition_batch,
                    created_by_user=directors["finance_user"],
                )

        self.stdout.write(self.style.SUCCESS("Tuition posted to ledger."))

        # --- 7) Aid: 35% of families get applications; create awards; post to ledger ---
        aid_families_count = max(1, int(round(len(families) * (aid_pct / 100.0))))
        aid_families = random.sample(families, aid_families_count)

        aid_batch = JournalBatch.objects.create(
            school=school,
            academic_year=ay,
            batch_date=timezone.now().date(),
            description="Aid Awards - Demo Seed",
            status="OPEN",
            created_by=directors["aid_user"],
        )

        students_by_family = {}
        for st in created_students:
            students_by_family.setdefault(st.family_id, []).append(st)

        apps_created = 0
        awards_created = 0
        posted = 0

        for idx, fam in enumerate(aid_families):
            # Distribute applications into workflow states:
            # 85% SUBMITTED, 10% NEEDS_INFO, 5% UNDER_REVIEW
            rand = random.random()
            if rand < 0.10:
                app_status = AidApplication.STATUS_NEEDS_INFO
            elif rand < 0.15:
                app_status = AidApplication.STATUS_UNDER_REVIEW
            else:
                app_status = AidApplication.STATUS_SUBMITTED
            
            app, created = AidApplication.objects.get_or_create(
                school=school,
                academic_year=ay,
                family=fam,
                defaults={
                    "status": app_status,
                    "submitted_at": timezone.now(),
                    "household_size": random.randint(3, 7),
                    "income_annual_cents": cents(random.randint(45000, 140000)),
                    "notes_internal": "Demo seed application.",
                },
            )
            if created:
                apps_created += 1

            for st in students_by_family.get(fam.id, []):
                if AidAward.objects.filter(school=school, academic_year=ay, student=st).exists():
                    continue

                pct = random.choice([10, 12, 15, 18, 20, 25, 30, 35, 40, 45])
                award_cents = int(round(tuition_plan.annual_amount_cents * (pct / 100.0)))

                # Distribute awards into workflow states:
                # 80% POSTED, 10% OFFERED (not accepted), 10% ACCEPTED (not posted)
                award_rand = random.random()
                if award_rand < 0.10:
                    # Offered but not accepted
                    award = AidAward.objects.create(
                        school=school,
                        academic_year=ay,
                        student=st,
                        award_type=random.choice([AidAward.TYPE_NEED, AidAward.TYPE_MISSION, AidAward.TYPE_HARDSHIP]),
                        awarded_cents=award_cents,
                        decision_status=AidAward.DECISION_OFFERED,
                    )
                    awards_created += 1
                elif award_rand < 0.20:
                    # Accepted but not posted
                    award = AidAward.objects.create(
                        school=school,
                        academic_year=ay,
                        student=st,
                        award_type=random.choice([AidAward.TYPE_NEED, AidAward.TYPE_MISSION, AidAward.TYPE_HARDSHIP]),
                        awarded_cents=award_cents,
                        decision_status=AidAward.DECISION_ACCEPTED,
                    )
                    awards_created += 1
                else:
                    # Accept and post to ledger
                    award = AidAward.objects.create(
                        school=school,
                        academic_year=ay,
                        student=st,
                        award_type=random.choice([AidAward.TYPE_NEED, AidAward.TYPE_MISSION, AidAward.TYPE_HARDSHIP]),
                        awarded_cents=award_cents,
                        decision_status=AidAward.DECISION_OFFERED,
                    )
                    awards_created += 1
                    award.mark_accepted_and_post(actor_user=directors["aid_user"], batch=aid_batch)
                    posted += 1

        self.stdout.write(self.style.SUCCESS(f"Aid applications created: {apps_created}"))
        self.stdout.write(self.style.SUCCESS(f"Aid awards created+accepted+posted: {posted} (created {awards_created})"))

        # --- 8) SEED_ATTENDANCE_DEMO_V1: deterministic attendance for demo realism ---
        try:
            from datetime import timedelta
            from crown_api.models_academics_core import AttendanceRecord as _AR

            STATUSES = ["PRESENT", "PRESENT", "PRESENT", "TARDY", "ABSENT", "EXCUSED", "PRESENT"]
            attendance_sample = created_students[:30]  # seed first 30 students; fast + realistic enough
            att_dates = [date.today() - timedelta(days=i) for i in range(1, 6)]  # last 5 school days

            att_created = 0
            for idx, st in enumerate(attendance_sample):
                for d_offset, att_date in enumerate(att_dates):
                    status = STATUSES[(idx + d_offset) % len(STATUSES)]
                    _, was_created = _AR.objects.update_or_create(
                        student=st,
                        course=None,
                        date=att_date,
                        defaults={"status": status},
                    )
                    if was_created:
                        att_created += 1

            self.stdout.write(self.style.SUCCESS(f"Attendance demo records seeded: {att_created} new rows."))
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"Attendance seed skipped (non-fatal): {exc}"))

        self.stdout.write(self.style.SUCCESS("✅ Demo school seed complete. Now review in Django Admin."))

    def _ensure_chart_accounts(self, school: School):
        accounts = {
            "TUITION": ("Tuition Revenue", "INCOME"),
            "AID": ("Financial Aid", "EXPENSE"),
            "FEES": ("Fees Revenue", "INCOME"),
            "PAYMENT": ("Payments Received", "ASSET"),
        }
        out = {}
        for code, (name, typ) in accounts.items():
            obj, _ = ChartAccount.objects.get_or_create(
                school=school,
                code=code,
                defaults={"name": name, "account_type": typ, "is_active": True},
            )
            changed = False
            if obj.name != name:
                obj.name = name
                changed = True
            if obj.account_type != typ:
                obj.account_type = typ
                changed = True
            if not obj.is_active:
                obj.is_active = True
                changed = True
            if changed:
                obj.save()
            out[code] = obj
        return out

    def _ensure_directors(self, school: School):
        def ensure_staff(first, last, email, role_type):
            st, _ = Staff.objects.get_or_create(
                school=school,
                email=email,
                defaults={"first_name": first, "last_name": last, "role_type": role_type, "status": "ACTIVE"},
            )
            return st

        def ensure_user(email, staff=None):
            ua, created = UserAccount.objects.get_or_create(
                school=school,
                email=email,
                defaults={"username": email, "is_active": True, "is_staff": True, "is_superuser": True, "staff": staff},
            )
            if created:
                ua.set_password("demo1234")
                ua.save(update_fields=["password"])
            if staff and ua.staff_id != staff.id:
                ua.staff = staff
                ua.save(update_fields=["staff"])
            return ua

        def ensure_role(user, role_code):
            UserRole.objects.get_or_create(school=school, user=user, role_code=role_code)

        head_staff = ensure_staff("Jordan", "Shepherd", "head@crown-demo.local", "DIRECTOR")
        fin_staff = ensure_staff("Morgan", "Ledger", "finance@crown-demo.local", "DIRECTOR")
        aid_staff = ensure_staff("Casey", "Steward", "aid@crown-demo.local", "DIRECTOR")
        reg_staff = ensure_staff("Taylor", "Registrar", "registrar@crown-demo.local", "DIRECTOR")

        head_user = ensure_user("head@crown-demo.local", head_staff)
        finance_user = ensure_user("finance@crown-demo.local", fin_staff)
        aid_user = ensure_user("aid@crown-demo.local", aid_staff)
        registrar_user = ensure_user("registrar@crown-demo.local", reg_staff)

        ensure_role(head_user, "HEAD_OF_SCHOOL")
        ensure_role(finance_user, "FINANCE_DIRECTOR")
        ensure_role(aid_user, "AID_DIRECTOR")
        ensure_role(registrar_user, "REGISTRAR")

        return {
            "head_user": head_user,
            "finance_user": finance_user,
            "aid_user": aid_user,
            "registrar_user": registrar_user,
        }

    def _create_families(self, school: School, target_students: int):
        desired_families = max(1, int(round(target_students * 0.60)))
        existing = list(Family.objects.filter(school=school))
        families = existing[:]
        used_names = {f.family_name for f in families}

        while len(families) < desired_families:
            last = random.choice(LAST_NAMES)
            base_name = f"{last} Family"
            fam_name = base_name
            suffix = 1
            # ensure uniqueness per school
            while fam_name in used_names:
                suffix += 1
                fam_name = f"{base_name} #{suffix}"
            used_names.add(fam_name)

            fam = Family.objects.create(
                school=school,
                family_name=fam_name,
                address_line1=f"{random.randint(100, 999)} {random.choice(['Maple', 'Oak', 'Pine', 'Cedar', 'Elm'])} St",
                city=random.choice(["Bear", "Newark", "Townsend", "Middletown", "Wilmington"]),
                state="DE",
                zip_code=str(random.randint(19701, 19999)),
                status="ACTIVE",
            )
            # First guardian
            email1 = f"{last.lower()}.{random.randint(1000,9999)}@demo.local"
            Guardian.objects.get_or_create(
                school=school,
                email=email1,
                defaults={
                    "family": fam,
                    "first_name": random.choice(FIRST_NAMES),
                    "last_name": last,
                    "phone": f"302-{random.randint(200,999)}-{random.randint(1000,9999)}",
                    "relationship": "GUARDIAN",
                    "portal_access": True,
                    "custody_flag": False,
                },
            )
            # Second guardian
            email2 = f"{last.lower()}.{random.randint(1000,9999)}@demo.local"
            Guardian.objects.get_or_create(
                school=school,
                email=email2,
                defaults={
                    "family": fam,
                    "first_name": random.choice(FIRST_NAMES),
                    "last_name": last,
                    "phone": f"302-{random.randint(200,999)}-{random.randint(1000,9999)}",
                    "relationship": "GUARDIAN",
                    "portal_access": True,
                    "custody_flag": False,
                },
            )

            families.append(fam)

        return families

    def _create_student(self, school: School, family: Family, grade_level: GradeLevel, student_number: str):
        first = random.choice(FIRST_NAMES)
        last = family.family_name.replace(" Family", "")
        today = date.today()
        grade_map = {"PK": 4, "K": 5, "1": 6, "2": 7, "3": 8, "4": 9, "5": 10, "6": 11, "7": 12, "8": 13, "9": 14, "10": 15, "11": 16, "12": 17}
        age = grade_map.get(grade_level.code, 10)
        dob_year = today.year - age
        dob = date(dob_year, random.randint(1, 12), random.randint(1, 28))

        st, _ = Student.objects.get_or_create(
            school=school,
            student_number=student_number,
            defaults={
                "family": family,
                "first_name": first,
                "last_name": last,
                "dob": dob,
                "current_grade_level": grade_level,
                "status": "ACTIVE",
            },
        )
        changed = False
        if st.family_id != family.id:
            st.family = family
            changed = True
        if st.current_grade_level_id != grade_level.id:
            st.current_grade_level = grade_level
            changed = True
        if changed:
            st.save(update_fields=["family", "current_grade_level"])
        return st

    def _wipe_school(self, school: School):
        # Import here to avoid circular dependency
        from financial_aid.models import AidAuditEvent
        
        # Delete audit events for this school AND any that reference user accounts we're about to delete
        user_ids = list(UserAccount.objects.filter(school=school).values_list('id', flat=True))
        AidAuditEvent.objects.filter(school_id=school.id).delete()
        if user_ids:
            AidAuditEvent.objects.filter(actor_user_id__in=user_ids).delete()
        
        # Continue with original deletions
        AidAward.objects.filter(school=school).delete()
        AidApplication.objects.filter(school=school).delete()
        LedgerEntry.objects.filter(school=school).delete()
        StudentTuition.objects.filter(school=school).delete()
        TuitionPlan.objects.filter(school=school).delete()
        JournalBatch.objects.filter(school=school).delete()
        ChartAccount.objects.filter(school=school).delete()
        Enrollment.objects.filter(school=school).delete()
        Student.objects.filter(school=school).delete()
        Guardian.objects.filter(school=school).delete()
        Family.objects.filter(school=school).delete()
        UserRole.objects.filter(school=school).delete()
        UserAccount.objects.filter(school=school).delete()
        Staff.objects.filter(school=school).delete()
        GradeLevel.objects.filter(school=school).delete()
        AcademicYear.objects.filter(school=school).delete()
