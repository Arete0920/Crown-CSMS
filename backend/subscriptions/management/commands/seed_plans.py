"""
Seed canonical plans, features, and plan entitlements.

Usage:
    python manage.py seed_plans

Idempotent: safe to run multiple times (uses get_or_create throughout).

Tier definitions:
  smart_start — core SIS + Admissions + Billing + Payments + Financial Aid + Comms + Dashboards
  next_level  — Smart Start + Attendance + Gradebook + Scheduling + Discipline + Activities/Events
  all_access  — full platform, highest limits, board dashboards/exports, full integrations
"""
from django.core.management.base import BaseCommand

from subscriptions.models import Feature, Plan, PlanEntitlement

# ─────────────────────────────────────────────────────────────────────────────
# Feature registry
# (key, name, description)
# ─────────────────────────────────────────────────────────────────────────────
FEATURES = [
    # Core identity / auth
    ("identity.rbac", "RBAC", "Role-based access control"),
    # Admissions
    ("admissions.pipeline", "Admissions Pipeline", "Application intake, status tracking, enrolment"),
    # Billing & payments
    ("billing.obligations", "Billing Obligations", "Tuition schedules and invoice management"),
    ("payments.ledger", "Payments + Ledger", "Payment processing and ledger entries"),
    # Financial Aid
    ("financial_aid.awards", "Financial Aid Awards", "Award creation, allocation, and reporting"),
    # Communications
    ("comms.messaging", "Messaging", "In-app messaging and email notifications"),
    ("comms.sms", "SMS/Text Bundle", "SMS messaging (metered, usage-based)"),
    # Dashboards
    ("dashboards.reporting", "Dashboards & Reporting", "Standard operational dashboards"),
    ("dashboards.board", "Board Dashboards & Exports", "Board-level dashboards and benchmark exports"),
    # Academics (next_level+)
    ("academics.attendance", "Attendance", "Daily and period-level attendance tracking"),
    ("academics.gradebook", "Gradebook", "Assignment creation, grading, and grade reports"),
    ("academics.scheduling", "Scheduling", "Bell schedules and class assignment"),
    # Student care (next_level+)
    ("discipline.incidents", "Discipline & Care", "Incident reporting and student care workflow"),
    ("activities.events", "Activities & Events", "Co-curricular activities and event management"),
    # Integrations (all_access)
    ("integrations.premium", "Premium Integrations", "Third-party SIS and LMS integrations"),
    # Analytics (add-on)
    ("analytics.advanced", "Advanced Analytics", "Benchmarking and advanced analytics pack"),
    # Solomon KB (add-on)
    ("solomon.kb", "Solomon Knowledge Base", "Premium content library and certifications"),
]

# ─────────────────────────────────────────────────────────────────────────────
# Plan entitlement matrix
# Maps each plan code → set of feature keys it includes by default.
# Features absent = PlanEntitlement with enabled=False.
# ─────────────────────────────────────────────────────────────────────────────
SMART_START_FEATURES = {
    "identity.rbac",
    "admissions.pipeline",
    "billing.obligations",
    "payments.ledger",
    "financial_aid.awards",
    "comms.messaging",
    "dashboards.reporting",
}

NEXT_LEVEL_FEATURES = SMART_START_FEATURES | {
    "academics.attendance",
    "academics.gradebook",
    "academics.scheduling",
    "discipline.incidents",
    "activities.events",
}

ALL_ACCESS_FEATURES = NEXT_LEVEL_FEATURES | {
    "dashboards.board",
    "integrations.premium",
    "comms.sms",
    "analytics.advanced",
    "solomon.kb",
}

PLAN_MATRIX = {
    "smart_start": SMART_START_FEATURES,
    "next_level": NEXT_LEVEL_FEATURES,
    "all_access": ALL_ACCESS_FEATURES,
}


class Command(BaseCommand):
    help = "Seed canonical subscription plans, features, and plan entitlements."

    def handle(self, *args, **kwargs):
        # ── Plans ─────────────────────────────────────────────────────────────
        smart, _ = Plan.objects.get_or_create(
            code="smart_start",
            defaults={"name": "Smart Start", "sort_order": 10, "is_active": True},
        )
        nextl, _ = Plan.objects.get_or_create(
            code="next_level",
            defaults={"name": "Next Level", "sort_order": 20, "is_active": True},
        )
        allx, _ = Plan.objects.get_or_create(
            code="all_access",
            defaults={"name": "All Access", "sort_order": 30, "is_active": True},
        )
        plans = {"smart_start": smart, "next_level": nextl, "all_access": allx}

        # ── Features ──────────────────────────────────────────────────────────
        feature_objs: dict[str, Feature] = {}
        for key, name, desc in FEATURES:
            f, created = Feature.objects.get_or_create(
                key=key, defaults={"name": name, "description": desc}
            )
            feature_objs[key] = f
            if created:
                self.stdout.write(f"  Created feature: {key}")

        # ── Plan Entitlements ─────────────────────────────────────────────────
        for plan_code, included_keys in PLAN_MATRIX.items():
            plan = plans[plan_code]
            for key, feature in feature_objs.items():
                enabled = key in included_keys
                pe, created = PlanEntitlement.objects.get_or_create(
                    plan=plan,
                    feature=feature,
                    defaults={"enabled": enabled},
                )
                if not created and pe.enabled != enabled:
                    pe.enabled = enabled
                    pe.save(update_fields=["enabled"])

        self.stdout.write(
            self.style.SUCCESS(
                "seed_plans: 3 plans, "
                f"{len(feature_objs)} features seeded."
            )
        )
