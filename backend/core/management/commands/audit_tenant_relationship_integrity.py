from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.core.management import BaseCommand, CommandError
from django.db import models
from django.db.models import Count, F, Subquery


RELATIONSHIPS = (
    ("households.Guardian", "household__school_id", "household"),
    ("households.Student", "household__school_id", "household"),
    ("applications.Application", "household__school_id", "household"),
    ("applications.Applicant", "application__school_id", "application"),
    ("applications.Applicant", "student__school_id", "student"),
    ("applications.ApplicationEvent", "application__school_id", "application"),
    ("applications.ApplicationChecklistItem", "application__school_id", "application"),
    ("applications.ApplicationChecklistDocument", "checklist_item__school_id", "checklist_item"),
    ("applications.EnrollmentContract", "application__school_id", "application"),
    ("applications.EnrollmentContract", "amended_from__school_id", "amended_from"),
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
    ("academics.Submission", "assignment__school_id", "assignment"),
    ("academics.Submission", "enrollment__school_id", "enrollment"),
    ("academics.Grade", "submission__school_id", "submission"),
    ("academics.MasteryRecord", "student__school_id", "student"),
    ("academics.MasteryRecord", "objective__school_id", "objective"),
    ("academics.MasteryRecord", "evidence_assignment__school_id", "evidence_assignment"),
    ("academics.LessonPlan", "section__school_id", "section"),
    ("academics.LessonResource", "lesson__school_id", "lesson"),
    ("academics.TranscriptEntry", "student__school_id", "student"),
    ("academics.TranscriptEntry", "course__school_id", "course"),
    ("academics.TranscriptEntry", "term__school_id", "term"),
    ("gradebook.GradeEntry", "section__school_id", "section"),
    ("gradebook.GradeEntry", "student__school_id", "student"),
    ("gradebook.GradeEntry", "assignment__school_id", "assignment"),
    ("academics.Unit", "course__school_id", "course"),
    ("academics.Unit", "curriculum_source__school_id", "curriculum_source"),
    ("academics.Lesson", "unit__school_id", "unit"),
    ("academics.PublisherObjective", "lesson__school_id", "lesson"),
    ("home_academy.HomeAcademyEnrollment", "program__school_id", "program"),
    ("home_academy.Offering", "program__school_id", "program"),
    ("home_academy.OfferingEnrollment", "offering__school_id", "offering"),
    ("home_academy.OfferingEnrollment", "home_academy_enrollment__school_id", "home_academy_enrollment"),
    ("accounting.LedgerEntry", "journal_entry__tenant_id", "journal_entry"),
    ("accounting.LedgerEntry", "account__tenant_id", "account"),
    ("accounting.JournalEntry", "reversal_of__tenant_id", "reversal_of"),
)

UNVERIFIED_TENANT_AUTHORITY_MODELS = frozenset(
    {
        "accounting.LedgerEntry",
        "accounting.JournalEntry",
    }
)


def _row_ids(queryset) -> set[str]:
    return {str(primary_key) for primary_key in queryset.values_list("pk", flat=True).iterator()}


def _identity_manifest(ids: set[str], include_ids: bool) -> dict:
    ordered = sorted(ids)
    manifest = {
        "count": len(ordered),
        "sha256": hashlib.sha256("\n".join(ordered).encode("utf-8")).hexdigest(),
    }
    if include_ids:
        manifest["ids"] = ordered
    return manifest


def _tenant_field(model) -> models.Field:
    for name in ("school_id", "school", "tenant_id", "tenant"):
        try:
            field = model._meta.get_field(name)
        except FieldDoesNotExist:
            continue
        if name in {"school", "tenant"} and not isinstance(
            field, (models.ForeignKey, models.OneToOneField)
        ):
            continue
        return field
    raise FieldDoesNotExist(f"{model._meta.label} has no supported tenant anchor")


def _tenant_lookup(field: models.Field) -> str:
    return getattr(field, "attname", field.name)


def _tenant_anchor(field: models.Field) -> str:
    lookup = _tenant_lookup(field)
    return lookup[:-3] if lookup.endswith("_id") else field.name


def _tenant_field_type(model) -> str:
    field = _tenant_field(model)
    target_field = getattr(field, "target_field", None)
    return (target_field or field).get_internal_type()


def _valid_school_subquery():
    return Subquery(apps.get_model("core", "School").objects.values("id"))


def _dangling_parent_ids(queryset, relation_field) -> set[str]:
    child_fk_name = relation_field.attname
    parent_target_name = relation_field.target_field.attname
    non_null_rows = queryset.exclude(**{f"{child_fk_name}__isnull": True})
    existing_parent_ids = relation_field.remote_field.model.objects.values(parent_target_name)
    return _row_ids(
        non_null_rows.exclude(**{f"{child_fk_name}__in": existing_parent_ids})
    )


def _relationship_partition(
    model,
    model_label: str,
    parent_tenant_path: str,
    relation_name: str,
    *,
    include_ids: bool,
) -> tuple[dict, dict[str, set[tuple[str, str]]]]:
    queryset = model.objects.all()
    relation_field = model._meta.get_field(relation_name)
    relation_is_nullable = bool(getattr(relation_field, "null", False))
    tenant_field = _tenant_field(model)
    tenant_lookup = _tenant_lookup(tenant_field)
    tenant_anchor = _tenant_anchor(tenant_field)
    input_ids = _row_ids(queryset)

    null_parent_ids = (
        _row_ids(queryset.filter(**{f"{relation_field.attname}__isnull": True}))
        if relation_is_nullable
        else set()
    )
    dangling_parent_ids = _dangling_parent_ids(queryset, relation_field)
    related_rows = queryset.exclude(pk__in=dangling_parent_ids).filter(
        **{f"{relation_field.attname}__isnull": False}
    )
    mismatch_ids = _row_ids(
        related_rows.exclude(**{tenant_lookup: F(parent_tenant_path)})
    )

    tenant_field_type = _tenant_field_type(model)
    tenant_authority_verified = (
        model_label not in UNVERIFIED_TENANT_AUTHORITY_MODELS
        and tenant_anchor == "school"
        and tenant_field_type == "UUIDField"
    )
    invalid_tenant_ids = (
        _row_ids(queryset.exclude(**{f"{tenant_lookup}__in": _valid_school_subquery()}))
        if tenant_authority_verified
        else set()
    )

    invalid_bucket = invalid_tenant_ids
    null_bucket = null_parent_ids - invalid_bucket
    dangling_bucket = dangling_parent_ids - invalid_bucket - null_bucket
    mismatch_bucket = mismatch_ids - invalid_bucket - null_bucket - dangling_bucket
    normal_bucket = input_ids - invalid_bucket - null_bucket - dangling_bucket - mismatch_bucket
    accounted_ids = invalid_bucket | null_bucket | dangling_bucket | mismatch_bucket | normal_bucket
    unexplained_ids = input_ids - accounted_ids
    buckets = (invalid_bucket, null_bucket, dangling_bucket, mismatch_bucket, normal_bucket)
    overlap_count = sum(
        1 for primary_key in input_ids if sum(primary_key in bucket for bucket in buckets) != 1
    )

    by_tenant = list(
        queryset.values(tenant_lookup).annotate(row_count=Count("pk")).order_by(tenant_lookup)
    )
    mismatch_by_tenant = list(
        queryset.filter(pk__in=mismatch_bucket)
        .values(tenant_lookup)
        .annotate(row_count=Count("pk"))
        .order_by(tenant_lookup)
    )

    partition = {
        "input": _identity_manifest(input_ids, include_ids),
        "normal": _identity_manifest(normal_bucket, include_ids),
        "invalid_tenant": _identity_manifest(invalid_bucket, include_ids),
        "null_parent": _identity_manifest(null_bucket, include_ids),
        "dangling_parent": _identity_manifest(dangling_bucket, include_ids),
        "tenant_mismatch": _identity_manifest(mismatch_bucket, include_ids),
        "unexplained": _identity_manifest(unexplained_ids, include_ids),
        "accounted_unique_count": len(accounted_ids),
        "exclusive_overlap_count": overlap_count,
        "equation_holds": len(input_ids) == len(accounted_ids) and not unexplained_ids and overlap_count == 0,
    }
    result = {
        "model": model_label,
        "relation": relation_name,
        "parent_tenant_path": parent_tenant_path,
        "relation_nullable": relation_is_nullable,
        "tenant_field": tenant_lookup,
        "tenant_anchor": tenant_anchor,
        "tenant_field_type": tenant_field_type,
        "tenant_authority_verified": tenant_authority_verified,
        "tenant_authority": (
            "core.School UUID primary key"
            if tenant_authority_verified
            else f"unresolved {tenant_anchor} identifier family"
        ),
        "row_count": len(input_ids),
        "invalid_tenant_id_count": len(invalid_bucket),
        "invalid_school_id_count": len(invalid_bucket) if tenant_anchor == "school" else 0,
        "dangling_parent_count": len(dangling_bucket),
        "parent_tenant_mismatch_count": len(mismatch_bucket),
        "nullable_parent_row_count": len(null_bucket),
        "rows_by_tenant": by_tenant,
        "mismatches_by_tenant": mismatch_by_tenant,
        "identity_partition": partition,
    }
    anomaly_keys = {
        "mismatch": {(model_label, primary_key) for primary_key in mismatch_bucket},
        "invalid": {(model_label, primary_key) for primary_key in invalid_bucket},
        "dangling": {(model_label, primary_key) for primary_key in dangling_bucket},
        "unexplained": {(model_label, primary_key) for primary_key in unexplained_ids},
    }
    return result, anomaly_keys


class Command(BaseCommand):
    help = "Read-only tenant relationship audit with checksum-backed identity reconciliation."

    def add_arguments(self, parser):
        parser.add_argument("--output", help="Optional path for the JSON evidence file.")
        parser.add_argument("--include-ids", action="store_true")
        parser.add_argument("--fail-on-anomaly", action="store_true")
        parser.add_argument("--fail-on-unverified-authority", action="store_true")

    def handle(self, *args, **options):
        results = []
        totals = defaultdict(int)
        anomaly_sets = {name: set() for name in ("mismatch", "invalid", "dangling", "unexplained")}
        invalid_school_row_keys: set[tuple[str, str]] = set()
        unverified_authority_relationships = []

        for model_label, parent_tenant_path, relation_name in RELATIONSHIPS:
            app_label, model_name = model_label.split(".", 1)
            model = apps.get_model(app_label, model_name)
            result, anomaly_keys = _relationship_partition(
                model,
                model_label,
                parent_tenant_path,
                relation_name,
                include_ids=bool(options.get("include_ids")),
            )
            results.append(result)
            for name, keys in anomaly_keys.items():
                anomaly_sets[name].update(keys)
            if result["tenant_anchor"] == "school":
                invalid_school_row_keys.update(anomaly_keys["invalid"])

            partition = result["identity_partition"]
            totals["relationships"] += 1
            totals["rows"] += result["row_count"]
            totals["mismatches"] += result["parent_tenant_mismatch_count"]
            totals["invalid_tenant_ids"] += result["invalid_tenant_id_count"]
            totals["invalid_school_ids"] += result["invalid_school_id_count"]
            totals["dangling_parents"] += result["dangling_parent_count"]
            totals["nullable_parent_rows"] += result["nullable_parent_row_count"]
            totals["unexplained_rows"] += partition["unexplained"]["count"]
            totals["exclusive_overlap_rows"] += partition["exclusive_overlap_count"]
            if not result["tenant_authority_verified"]:
                unverified_authority_relationships.append(
                    {
                        "model": model_label,
                        "relation": relation_name,
                        "tenant_anchor": result["tenant_anchor"],
                        "tenant_field_type": result["tenant_field_type"],
                    }
                )

        unique_anomaly_rows = set().union(*anomaly_sets.values())
        totals["unique_mismatch_rows"] = len(anomaly_sets["mismatch"])
        totals["unique_invalid_tenant_rows"] = len(anomaly_sets["invalid"])
        totals["unique_invalid_school_rows"] = len(invalid_school_row_keys)
        totals["unique_dangling_parent_rows"] = len(anomaly_sets["dangling"])
        totals["unique_unexplained_rows"] = len(anomaly_sets["unexplained"])
        totals["unique_anomaly_rows"] = len(unique_anomaly_rows)
        totals["unverified_tenant_authority_relationships"] = len(unverified_authority_relationships)
        totals["all_partition_equations_hold"] = all(
            result["identity_partition"]["equation_holds"] for result in results
        )

        payload = {
            "schema_version": 4,
            "mode": "read_only",
            "production_authorization": False,
            "partition_precedence": [
                "invalid_tenant",
                "null_parent",
                "dangling_parent",
                "tenant_mismatch",
                "normal",
            ],
            "totals": dict(totals),
            "unverified_tenant_authority_relationships": unverified_authority_relationships,
            "relationships": results,
        }
        rendered = json.dumps(payload, indent=2, sort_keys=True, default=str)
        if options.get("output"):
            output_path = Path(options["output"])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered + "\n", encoding="utf-8")
        self.stdout.write(rendered)

        anomaly_count = totals["unique_anomaly_rows"]
        if options.get("fail_on_anomaly") and (
            anomaly_count or totals["exclusive_overlap_rows"] or not totals["all_partition_equations_hold"]
        ):
            raise CommandError(
                "Tenant relationship integrity audit found "
                f"{anomaly_count} unique anomaly row(s), "
                f"{totals['unique_dangling_parent_rows']} dangling parent row(s), "
                f"{totals['exclusive_overlap_rows']} overlap row(s), and "
                f"{totals['unique_unexplained_rows']} unexplained row(s)."
            )
        if options.get("fail_on_unverified_authority") and unverified_authority_relationships:
            raise CommandError(
                "Tenant relationship integrity audit found "
                f"{len(unverified_authority_relationships)} relationship(s) "
                "using an unresolved tenant authority family."
            )
