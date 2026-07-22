from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from django.apps import apps
from django.core.management import BaseCommand, CommandError
from django.db.models import Count, F, Subquery


RELATIONSHIPS = (
    ("households.Guardian", "household__school_id", "household"),
    ("households.Student", "household__school_id", "household"),
    ("applications.Application", "household__school_id", "household"),
    ("applications.Applicant", "application__school_id", "application"),
    ("applications.Applicant", "student__school_id", "student"),
    ("applications.ApplicationEvent", "application__school_id", "application"),
    ("applications.ApplicationChecklistItem", "application__school_id", "application"),
    (
        "applications.ApplicationChecklistDocument",
        "checklist_item__school_id",
        "checklist_item",
    ),
    ("applications.EnrollmentContract", "application__school_id", "application"),
    ("academics.Term", "academic_year__school_id", "academic_year"),
    ("academics.Section", "course__school_id", "course"),
    ("academics.Section", "term_ref__school_id", "term_ref"),
    ("academics.Enrollment", "section__school_id", "section"),
    ("academics.Enrollment", "student__school_id", "student"),
    ("academics.TeacherAssignment", "section__school_id", "section"),
    ("academics.TeacherAssignment", "staff__school_id", "staff"),
    ("academics.AssignmentCategory", "section__school_id", "section"),
    ("academics.Assignment", "section__school_id", "section"),
    ("academics.Assignment", "category__school_id", "category"),
    ("academics.Assignment", "lesson__school_id", "lesson"),
    ("academics.Assignment", "objective__school_id", "objective"),
    ("gradebook.GradeEntry", "section__school_id", "section"),
    ("gradebook.GradeEntry", "student__school_id", "student"),
    ("gradebook.GradeEntry", "assignment__school_id", "assignment"),
    ("academics.Unit", "course__school_id", "course"),
    ("academics.Unit", "curriculum_source__school_id", "curriculum_source"),
    ("academics.Lesson", "unit__school_id", "unit"),
    ("academics.PublisherObjective", "lesson__school_id", "lesson"),
    ("academics.Submission", "assignment__school_id", "assignment"),
    ("academics.Submission", "enrollment__school_id", "enrollment"),
)


def _row_keys(model_label, queryset):
    return {
        (model_label, str(primary_key))
        for primary_key in queryset.values_list("pk", flat=True).iterator()
    }


class Command(BaseCommand):
    help = (
        "Read-only audit of tenant-owned child/parent relationships. "
        "Emits JSON and performs no writes."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            help="Optional path for the JSON evidence file.",
        )
        parser.add_argument(
            "--fail-on-anomaly",
            action="store_true",
            help="Exit non-zero when any invalid tenant or relationship mismatch exists.",
        )

    def handle(self, *args, **options):
        school_model = apps.get_model("core", "School")
        valid_school_ids = Subquery(school_model.objects.values("id"))
        results = []
        totals = defaultdict(int)
        mismatch_row_keys = set()
        invalid_school_row_keys = set()

        for model_label, parent_tenant_path, relation_name in RELATIONSHIPS:
            app_label, model_name = model_label.split(".", 1)
            model = apps.get_model(app_label, model_name)
            queryset = model.objects.all()

            relation_field = model._meta.get_field(relation_name)
            relation_is_nullable = bool(getattr(relation_field, "null", False))
            related_filter = {f"{relation_name}__isnull": False}
            related_rows = queryset.filter(**related_filter)

            mismatch_rows = related_rows.exclude(
                school_id=F(parent_tenant_path)
            )
            invalid_school_rows = queryset.exclude(
                school_id__in=valid_school_ids
            )

            by_tenant = list(
                queryset.values("school_id")
                .annotate(row_count=Count("pk"))
                .order_by("school_id")
            )
            mismatch_by_tenant = list(
                mismatch_rows.values("school_id")
                .annotate(row_count=Count("pk"))
                .order_by("school_id")
            )

            row_count = queryset.count()
            mismatch_count = mismatch_rows.count()
            invalid_school_count = invalid_school_rows.count()
            null_parent_count = (
                queryset.filter(**{f"{relation_name}__isnull": True}).count()
                if relation_is_nullable
                else 0
            )

            mismatch_row_keys.update(_row_keys(model_label, mismatch_rows))
            invalid_school_row_keys.update(
                _row_keys(model_label, invalid_school_rows)
            )

            totals["relationships"] += 1
            totals["rows"] += row_count
            totals["mismatches"] += mismatch_count
            totals["invalid_school_ids"] += invalid_school_count
            totals["nullable_parent_rows"] += null_parent_count

            results.append(
                {
                    "model": model_label,
                    "relation": relation_name,
                    "parent_tenant_path": parent_tenant_path,
                    "relation_nullable": relation_is_nullable,
                    "row_count": row_count,
                    "invalid_school_id_count": invalid_school_count,
                    "parent_tenant_mismatch_count": mismatch_count,
                    "nullable_parent_row_count": null_parent_count,
                    "rows_by_tenant": by_tenant,
                    "mismatches_by_tenant": mismatch_by_tenant,
                }
            )

        unique_anomaly_rows = mismatch_row_keys | invalid_school_row_keys
        totals["unique_mismatch_rows"] = len(mismatch_row_keys)
        totals["unique_invalid_school_rows"] = len(invalid_school_row_keys)
        totals["unique_anomaly_rows"] = len(unique_anomaly_rows)

        payload = {
            "schema_version": 2,
            "mode": "read_only",
            "production_authorization": False,
            "totals": dict(totals),
            "relationships": results,
        }
        rendered = json.dumps(payload, indent=2, sort_keys=True, default=str)

        if options.get("output"):
            output_path = Path(options["output"])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered + "\n", encoding="utf-8")

        self.stdout.write(rendered)

        anomaly_count = totals["unique_anomaly_rows"]
        if options.get("fail_on_anomaly") and anomaly_count:
            raise CommandError(
                "Tenant relationship integrity audit found "
                f"{anomaly_count} unique unexplained anomaly row(s)."
            )
