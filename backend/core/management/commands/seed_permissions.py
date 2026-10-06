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
    ("student_health.view", "View restricted school clinical records"),
    ("student_health.edit", "Record restricted school clinical evidence"),
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
    ("gradebook.edit", "Create or modify grades within authorized sections"),
    ("attendance.configure", "Configure canonical tenant attendance policies and codes"),
    ("admin.view", "View administration dashboard"),
    ("board.view", "View board / governance dashboard"),
    ("finance.view", "View financial summaries and ledger"),
    ("billing.view", "View billing and fee dashboard"),
    ("office.view", "View office operations dashboard"),
    ("it.view", "View IT / infrastructure dashboard"),
    ("facilities.view", "View facilities dashboard"),
    ("transportation.view", "View transportation dashboard"),
    ("transportation.edit", "Create or modify transportation operational records"),
    ("financial_aid.view", "View financial aid dashboard"),
    ("financial_aid.edit", "Create or modify aid awards"),
    ("financial_aid.view_rationale", "View per-award case rationale text"),
    ("marketing.view", "View marketing / enrollment funnel"),
    ("marketing.edit", "Create and manage marketing campaigns and touchpoints"),
    ("advancement.view", "View advancement / fundraising dashboard"),
    ("advancement.edit", "Create or modify advancement / fundraising records"),
    ("crownpass.scan", "Scan and redeem CrownPass admission credentials"),
    ("crownpass.manage", "Manage CrownPass ticketing configuration and operations"),
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
    ("service.self", "View and submit the authenticated student's own service-hour records"),
    ("service.manage", "View and manage school service-hour records"),
    ("service.approve", "Approve or reject school service-hour records"),
    ("integrations.view", "View integration and automation surfaces"),
    ("integrations.run", "Run approved integration preview or execution surfaces"),
    ("extended_care.view", "View extended-care dashboard"),
    ("extended_care.edit", "Create or modify extended-care records"),
    ("home_academy.view", "View Home Academy programs, enrollments, and offerings"),
    ("home_academy.edit", "Create or modify Home Academy programs, enrollments, and offerings"),
    ("communications.view", "View communications dashboard"),
    ("communications.create", "Create and stage school communications"),
    ("communications.send", "Commit school communications for delivery"),
    ("student_services.view", "View student-services dashboard"),
    ("student-care.view", "View Student Care incident lists and non-restricted summaries"),
    ("student-care.view_restricted", "View restricted Student Care incident details and action notes"),
    ("student-care.create", "Create Student Care incidents"),
    ("student-care.edit", "Edit Student Care incidents and actions"),
    ("student-care.close", "Close Student Care incidents"),
    ("student-care.export", "Export Student Care records"),
    ("classroom.view", "View classroom roster and snapshot data"),
    ("hr.view", "View HR / staff directory dashboard"),
    ("hr.edit", "Create and edit employee records"),
    ("safety.view", "View campus safety / incident dashboard"),
    ("safety.edit", "Create and resolve safety incidents"),
    ("security.view", "View security / safety dashboard"),
    ("integrity.view", "View academic-integrity dashboard"),
    ("forms.manage", "Create, issue, and manage electronic forms and signature envelopes"),
]


ROLE_PERMISSIONS: dict = {
    "HEAD_OF_SCHOOL": [
        "admin.view", "board.view", "finance.view", "billing.view", "admissions.view", "financial_aid.view",
        "academics.view", "teacher.view", "registrar.view", "academic_support.view", "library.view", "rosters.edit",
        "gradebook.edit", "attendance.configure", "scheduling.view", "scheduling.configure", "scheduling.edit", "scheduling.publish",
        "extended_care.view", "extended_care.edit", "home_academy.view", "home_academy.edit", "pd.view", "communications.view", "communications.create", "communications.send", "health.view", "counseling.view", "food.view",
        "athletics.view", "fine_arts.view", "spiritual_life.view", "student_services.view", "office.view", "it.view",
        "facilities.view", "transportation.view", "transportation.edit", "security.view", "integrity.view", "metrics.view", "director.actions",
        "marketing.view", "advancement.view", "advancement.edit", "crownpass.scan", "crownpass.manage", "pd.edit", "hr.view", "hr.edit", "safety.view",
        "safety.edit", "classroom.view", "student-care.view", "student-care.view_restricted", "student-care.create",
        "student-care.edit", "student-care.close", "student-care.export", "service.manage", "service.approve", "integrations.view", "integrations.run", "forms.manage",
    ],
    "FINANCE_DIRECTOR": ["finance.view", "finance.edit", "finance.period_lock", "billing.view", "financial_aid.view", "integrity.view", "metrics.view", "director.actions"],
    "AID_DIRECTOR": ["financial_aid.view", "financial_aid.edit", "financial_aid.view_rationale", "admissions.view", "metrics.view"],
    "REGISTRAR": ["admissions.view", "admissions.edit", "academics.view", "registrar.view", "home_academy.view", "home_academy.edit", "classroom.view", "metrics.view", "rosters.edit", "gradebook.edit", "attendance.configure", "scheduling.view", "scheduling.configure", "scheduling.edit", "scheduling.publish", "forms.manage"],
    "TEACHER": ["teacher.view", "academics.view", "academics.edit", "gradebook.edit", "classroom.view"],
    "SUPPORT": ["health.view", "metrics.view", "academic_support.view", "student_services.view"],
    "PARENT": ["parent.view"],
    "STUDENT": ["student.view", "service.self"],
    "head_of_school": [
        "admin.view", "board.view", "finance.view", "billing.view", "admissions.view", "financial_aid.view",
        "academics.view", "teacher.view", "registrar.view", "academic_support.view", "library.view", "rosters.edit",
        "gradebook.edit", "attendance.configure", "scheduling.view", "scheduling.configure", "scheduling.edit", "scheduling.publish",
        "extended_care.view", "extended_care.edit", "home_academy.view", "home_academy.edit", "pd.view", "communications.view", "communications.create", "communications.send", "health.view", "counseling.view", "food.view",
        "athletics.view", "fine_arts.view", "spiritual_life.view", "student_services.view", "office.view", "it.view",
        "facilities.view", "transportation.view", "transportation.edit", "security.view", "integrity.view", "metrics.view", "director.actions",
        "marketing.view", "advancement.view", "advancement.edit", "crownpass.scan", "crownpass.manage", "pd.edit", "hr.view", "hr.edit", "safety.view",
        "safety.edit", "classroom.view", "student-care.view", "student-care.view_restricted", "student-care.create",
        "student-care.edit", "student-care.close", "student-care.export", "service.manage", "service.approve", "integrations.view", "integrations.run", "forms.manage",
    ],
    "finance": ["finance.view", "finance.edit", "billing.view", "integrity.view"],
    "aid_director": ["financial_aid.view", "financial_aid.edit", "financial_aid.view_rationale", "admissions.view"],
    "registrar": ["admissions.view", "academics.view", "registrar.view", "home_academy.view", "home_academy.edit", "classroom.view", "rosters.edit", "gradebook.edit", "attendance.configure", "scheduling.view", "scheduling.configure", "scheduling.edit", "scheduling.publish", "forms.manage"],
    "teacher": ["teacher.view", "academics.view", "academics.edit", "gradebook.edit", "classroom.view"],
    "nurse": ["health.view", "student_health.view", "student_health.edit"],
    "health": ["health.view", "student_health.view", "student_health.edit"],
    "health_office": ["student_health.view", "student_health.edit"],
    "NURSE": ["student_health.view", "student_health.edit"],
    "HEALTH_OFFICE": ["student_health.view", "student_health.edit"],
    "counselor": ["counseling.view"],
    "food_service": ["food.view"], "athletic_director": ["athletics.view", "crownpass.scan", "crownpass.manage"], "transportation": ["transportation.view", "transportation.edit"],
    "facilities": ["facilities.view"], "hr": ["hr.view", "hr.edit"], "safety": ["safety.view", "safety.edit"],
    "security": ["security.view"], "it": ["it.view", "integrity.view"], "marketing": ["marketing.view"],
    "advancement": ["advancement.view", "advancement.edit", "crownpass.scan", "crownpass.manage"], "pd": ["pd.view", "pd.edit"],
    "chaplain": ["spiritual_life.view"], "spiritual_life": ["spiritual_life.view"], "office_manager": ["office.view"],
    "parent": ["parent.view"], "student": ["student.view", "service.self"], "board": ["board.view"],
    "school_admin": [
        "admin.view", "board.view", "finance.view", "billing.view", "admissions.view", "financial_aid.view",
        "academics.view", "teacher.view", "registrar.view", "academic_support.view", "library.view", "rosters.edit",
        "attendance.configure", "scheduling.view", "scheduling.configure", "scheduling.edit", "scheduling.publish",
        "extended_care.view", "extended_care.edit", "home_academy.view", "home_academy.edit", "pd.view", "communications.view", "communications.create", "communications.send", "health.view", "counseling.view", "food.view",
        "athletics.view", "fine_arts.view", "spiritual_life.view", "student_services.view", "office.view", "it.view",
        "facilities.view", "transportation.view", "transportation.edit", "security.view", "integrity.view", "metrics.view", "director.actions",
        "marketing.view", "advancement.view", "advancement.edit", "crownpass.scan", "crownpass.manage", "pd.edit", "hr.view", "hr.edit", "safety.view",
        "safety.edit", "classroom.view", "service.manage", "service.approve", "integrations.view", "integrations.run", "forms.manage",
    ],
    "communications_director": ["communications.view", "communications.create", "communications.send"],
    "finance_admin": ["finance.view", "finance.edit", "billing.view", "integrity.view"],
    "admissions_manager": ["admissions.view", "admissions.edit", "academics.view", "registrar.view", "forms.manage"],
    "advancement_officer": ["advancement.view", "advancement.edit", "crownpass.scan", "crownpass.manage"], "hr_manager": ["hr.view", "hr.edit"],
    "facilities_manager": ["facilities.view"], "safety_manager": ["safety.view", "safety.edit"],
    "security_officer": ["security.view"], "transportation_manager": ["transportation.view", "transportation.edit"],
    "food_service_manager": ["food.view"], "athletics_director": ["athletics.view", "crownpass.scan", "crownpass.manage"],
    "it_support": ["it.view", "integrity.view", "integrations.view", "integrations.run"], "board_member": ["board.view"],
    "service_learning_coordinator": ["service.manage", "service.approve"],
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
