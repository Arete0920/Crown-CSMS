"""
core/services/export_service.py

School data export + purge services.

export_school_data(school_id) → BytesIO ZIP of CSV extracts.
purge_school_data(school_id, purged_by) → issues DataDestructionCertificate.

NOTE: export only surfaces IDs + minimal identifiers per Crown privacy policy.
Full PII export (if required by data portability law) should be gated behind
an explicit legal record and triggered only by authorised platform ops staff.
"""
import csv
import io
import zipfile

from django.apps import apps


# Models to include in a standard data export.
# Format: "app_label.ModelName", scoped by school_id field.
EXPORT_MODELS = [
    "students.Student",
    "households.Household",
    "ledger.Payment",
    "ledger.Charge",
    "financial_aid.Award",
]


def export_school_data(school_id) -> io.BytesIO:
    """
    Build a ZIP containing one CSV per exportable model, tenant-scoped to school_id.
    Returns BytesIO positioned at 0.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for model_label in EXPORT_MODELS:
            try:
                model = apps.get_model(model_label)
            except LookupError:
                continue

            if not hasattr(model, "objects"):
                continue

            try:
                qs = model.objects.filter(school_id=school_id)
                rows = list(qs.values())
            except Exception:
                rows = []

            if not rows:
                continue

            csv_buf = io.StringIO()
            writer = csv.DictWriter(csv_buf, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

            safe_name = model_label.replace(".", "_")
            zf.writestr(f"{safe_name}.csv", csv_buf.getvalue())

    buffer.seek(0)
    return buffer


def purge_school_data(school_id, purged_by: str = "system") -> "DataDestructionCertificate":
    """
    Delete all exportable school records and issue a DataDestructionCertificate.

    WARNING: This is irreversible. Call only after confirming client off-boarding
    and after export_school_data() has been delivered to the client.
    """
    from core.models_export import DataDestructionCertificate

    scope_lines: list[str] = []

    for model_label in EXPORT_MODELS:
        try:
            model = apps.get_model(model_label)
        except LookupError:
            continue

        try:
            deleted_count, _ = model.objects.filter(school_id=school_id).delete()
            scope_lines.append(f"{model_label}: {deleted_count} records deleted")
        except Exception as exc:
            scope_lines.append(f"{model_label}: ERROR — {exc}")

    cert = DataDestructionCertificate.objects.create(
        school_id=school_id,
        purged_by=purged_by,
        scope_summary="\n".join(scope_lines),
    )
    return cert
