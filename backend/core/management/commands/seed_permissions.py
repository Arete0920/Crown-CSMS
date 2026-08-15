# backend/core/management/commands/seed_permissions.py
#
# Seeds CrownPermission codes and RolePermission defaults.
# Idempotent — safe to re-run at any time.
# Supports --dry-run to preview without writing.
#
# Usage:
#   python manage.py seed_permissions
#   python manage.py seed_permissions --dry-run

from django.core.management.base import BaseCommand

from core.models import CrownPermission, RolePermission


PERMISSIONS = [
    ("health.view", "View health / system-status dashboard"),
    ("director.actions", "Execute director-level admin actions"),
    ("metrics.view", "View all KPI dashboards"),
    ("finance.edit", "Post ledger entries, reverse transactions"),
    ("finance.period_lock", "Lock / unlock accounting periods"),
    ("aid.view", "View aid applications and awards"),
    ("aid.edit", "Create or modify aid awards"),
    ("admissions.view", "View admissions pipeline and applicants"),
    ("admissions.edit", "Advance, waitlist, or deny applicants"),
    ("academics.view", "View course enrollment, grades, attendance"),
    ("academics.edit", "Enter grades and attendance records"),
    ("attendance.configure", "Configure canonical tenant attendance policies and codes"),
    ("admin.view", "View administration dashboard"),
    ("board.view", "View board / governance dashboard"),
    ("finance.view", "View financial summaries and ledger"),
    ("billing.view", "View billing and fee dashboard"),
    ("office.view", "View office operations dashboard"),
    ("it.view", "View IT / infrastructure dashboard"),
    ("facilities.view", "View facilities dashboard"),
    ("transportation.view", "View transportation dashboard"),
    ("financial_aid.view", "View financial aid dashboard"),
    ("financial_aid.edit", "Create or modify aid awards"),
    ("financial_aid.view_rationale", "View per-award case rationale text"),
    ("marketing.view", "View marketing / enrollment funnel"),
    ("advancement.view", "View advancement / fundraising dashboard"),
    ("advancement.edit", "Create or modify advancement / fundraising records"),
    ("teacher.view", "View teacher dashboard"),
    ("registrar.view", "View registrar dashboard"),
    ("rosters.edit", "Create or modify canonical section roster assignments"),
    ("scheduling.view", "View scheduling configuration and published placements"),
    ("scheduling.configure", "Configure scheduling sessions and academic scope"),
    ("scheduling.edit", "Stage or edit canonical section placements"),
    ("scheduling.publish", "Publish canonical section placements"),
    ("academic_support.view", "View SPED / academic-support dashboard"),
    ("fine_arts.view", "View fine-arts dashboard"),
    ("library.view", "View library dashboard"),
    ("pd.view", "View professional-development dashboard"),
    ("pd.edit", "Create or modify professional-development records"),
    ("parent.view", "View parent dashboard"),
    ("student.view", "View student dashboard"),
    ("health.dashboard.view", "View student health dashboard"),
    ("counseling.view", "View counseling dashboard"),
    ("food.view", "View food-services dashboard"),
    ("athletics.view", "View athletics dashboard"),
    ("spiritual_life.view", "View spiritual-life dashboard"),
    ("extended_care.view", "View extended-care dashboard"),
    ("communications.view", "View communications dashboard"),
    ("student_services.view", "View student-services dashboard"),
    ("classroom.view", "View classroom roster and snapshot data"),
    ("hr.view", "View HR / staff directory dashboard"),
    ("hr.edit", "Create and edit employee records"),
    ("safety.view", "View campus safety / incident dashboard"),
    ("safety.edit", "Create and resolve safety incidents"),
    ("security.view", "View security / safety dashboard"),
    ("integrity.view", "View academic-integrity dashboard"),
]


ROLE_PERMISSIONS: dict = {
    "HEAD_OF_SCHOOL": [
        "admin.view", "board.view", "finance.view", "billing.view", "admissions.view", "financial_aid.view",
        "academics.view", "teacher.view", "registrar.view", "academic_support.view", "library.view", "rosters.edit",
        "attendance.configure", "scheduling.view", "scheduling.configure", "scheduling.edit", "scheduling.publish",
        "extended_care.view", "pd.view", "communications.view", "health.view", "counseling.view", "food.view",
        "athletics.view", "fine_arts.view", "spiritual_life.view", "student_services.view", "office.view", "it.view",
        "facilities.view", "transportation.view", "security.view", "integrity.view", "metrics.view", "director.actions",
        "marketing.view", "advancement.view", "advancement.edit", "pd.edit", "hr.view", "hr.edit", "safety.view",
        "safety.edit", "classroom.view",
    ],
    "FINANCE_DIRECTOR": ["finance.view", "finance.edit", "finance.period_lock", "billing.view", "financial_aid.view", "integrity.view", "metrics.view", "director.actions"],
    "AID_DIRECTOR": ["financial_aid.view", "financial_aid.edit", "financial_aid.view_rationale", "admissions.view", "metrics.view"],
    "REGISTRAR": ["admissions.view", "admissions.edit", "academics.view", "registrar.view", "classroom.view", "metrics.view", "rosters.edit", "attendance.configure", "scheduling.view", "scheduling.configure", "scheduling.edit", "scheduling.publish"],
    "TEACHER": ["teacher.view", "academics.view", "academics.edit", "classroom.view"],
    "SUPPORT": ["health.view", "metrics.view", "academic_support.view", "student_services.view"],
    "PARENT": ["parent.view"],
    "STUDENT": ["student.view"],
    "head_of_school": [
        "admin.view", "board.view", "finance.view", "billing.view", "admissions.view", "financial_aid.view",
        "academics.view", "teacher.view", "registrar.view", "academic_support.view", "library.view", "rosters.edit",
        "attendance.configure", "scheduling.view", "scheduling.configure", "scheduling.edit", "scheduling.publish",
        "extended_care.view", "pd.view", "communications.view", "health.view", "counseling.view", "food.view",
        "athletics.view", "fine_arts.view", "spiritual_life.view", "student_services.view", "office.view", "it.view",
        "facilities.view", "transportation.view", "security.view", "integrity.view", "metrics.view", "director.actions",
        "marketing.view", "advancement.view", "advancement.edit", "pd.edit", "hr.view", "hr.edit", "safety.view",
        "safety.edit", "classroom.view",
    ],
    "finance": ["finance.view", "finance.edit", "billing.view", "integrity.view"],
    "aid_director": ["financial_aid.view", "financial_aid.edit", "financial_aid.view_rationale", "admissions.view"],
    "registrar": ["admissions.view", "academics.view", "registrar.view", "classroom.view", "rosters.edit", "attendance.configure", "scheduling.view", "scheduling.configure", "scheduling.edit", "scheduling.publish"],
    "teacher": ["teacher.view", "academics.view", "academics.edit", "classroom.view"],
    "nurse": ["health.view"], "health": ["health.view"], "counselor": ["counseling.view"],
    "food_service": ["food.view"], "athletic_director": ["athletics.view"], "transportation": ["transportation.view"],
    "facilities": ["facilities.view"], "hr": ["hr.view", "hr.edit"], "safety": ["safety.view", "safety.edit"],
    "security": ["security.view"], "it": ["it.view", "integrity.view"], "marketing": ["marketing.view"],
    "advancement": ["advancement.view", "advancement.edit"], "pd": ["pd.view", "pd.edit"],
    "chaplain": ["spiritual_life.view"], "spiritual_life": ["spiritual_life.view"], "office_manager": ["office.view"],
    "parent": ["parent.view"], "student": ["student.view"], "board": ["board.view"],
    "school_admin": [
        "admin.view", "board.view", "finance.view", "billing.view", "admissions.view", "financial_aid.view",
        "academics.view", "teacher.view", "registrar.view", "academic_support.view", "library.view", "rosters.edit",
        "attendance.configure", "scheduling.view", "scheduling.configure", "scheduling.edit", "scheduling.publish",
        "extended_care.view", "pd.view", "communications.view", "health.view", "counseling.view", "food.view",
        "athletics.view", "fine_arts.view", "spiritual_life.view", "student_services.view", "office.view", "it.view",
        "facilities.view", "transportation.view", "security.view", "integrity.view", "metrics.view", "director.actions",
        "marketing.view", "advancement.view", "advancement.edit", "pd.edit", "hr.view", "hr.edit", "safety.view",
        "safety.edit", "classroom.view",
    ],
    "finance_admin": ["finance.view", "finance.edit", "billing.view", "integrity.view"],
    "admissions_manager": ["admissions.view", "admissions.edit", "academics.view", "registrar.view"],
    "advancement_officer": ["advancement.view", "advancement.edit"], "hr_manager": ["hr.view", "hr.edit"],
    "facilities_manager": ["facilities.view"], "safety_manager": ["safety.view", "safety.edit"],
    "security_officer": ["security.view"], "transportation_manager": ["transportation.view"],
    "food_service_manager": ["food.view"], "athletics_director": ["athletics.view"],
    "it_support": ["it.view", "integrity.view"], "board_member": ["board.view"],
}


class Command(BaseCommand):
    help = "Seeds CrownPermission codes and RolePermission defaults (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Print actions without writing to the database.")

    def handle(self, *args, **options):
        dry_run = bool(options.get("dry_run"))
        new_perms = 0
        new_maps = 0
        for code, description in PERMISSIONS:
            if dry_run:
                self.stdout.write(f"[dry-run] ensure permission: {code}")
                continue
            _, created = CrownPermission.objects.get_or_create(code=code, defaults={"description": description})
            if created:
                new_perms += 1
        for role_code, perm_codes in ROLE_PERMISSIONS.items():
            for perm_code in perm_codes:
                if dry_run:
                    self.stdout.write(f"[dry-run] map role={role_code} -> {perm_code}")
                    continue
                try:
                    perm = CrownPermission.objects.get(code=perm_code)
                except CrownPermission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"SKIP: {role_code} -> {perm_code} (not found)"))
                    continue
                _, created = RolePermission.objects.get_or_create(role_code=role_code, permission=perm)
                if created:
                    new_maps += 1
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run complete. No changes written."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Seed complete. New permissions: {new_perms}. New role mappings: {new_maps}."))
