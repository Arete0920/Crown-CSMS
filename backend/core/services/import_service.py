"""
core/services/import_service.py

Thin CSV import service that drives ImportSession state transitions.
Field mapping is stored in onboarding.ImportFieldMapping and resolved
at process time.

NOTE: The core data router (students_guardians mode) lives in
onboarding/views.py commit_session(). This service is the generic
fallback path for future source-system integrations.
"""
import csv
import io

from django.apps import apps
from django.db import transaction


def process_import(session_id: int) -> dict:
    """
    Drive an ImportSession through mapping → processing → completed/failed.

    Returns a summary dict: {"rows_processed": int, "errors": [str]}.
    """
    # Import here to avoid circular at module load time
    from onboarding.models import ImportSession
    from onboarding.models_tasks import OnboardingTask  # noqa: F401 (ensure app is loaded)

    job = ImportSession.objects.get(id=session_id)
    job.status = "processing"
    job.save(update_fields=["status"])

    errors: list[str] = []
    rows_processed = 0

    try:
        # Resolve field mappings if any exist
        # (ImportFieldMapping is registered in onboarding migrations 0002)
        try:
            from onboarding.models_tasks import HelpArticle  # noqa: F401
            ImportFieldMapping = apps.get_model("onboarding", "ImportFieldMapping")
            mappings = ImportFieldMapping.objects.filter(import_session_id=session_id)
            map_dict = {
                m.source_field: (m.target_model, m.target_field)
                for m in mappings
            }
        except LookupError:
            map_dict = {}

        if job.raw_csv:
            reader = csv.DictReader(io.StringIO(job.raw_csv))
            with transaction.atomic():
                for row_num, row in enumerate(reader, start=1):
                    for source_field, value in row.items():
                        if source_field not in map_dict:
                            continue
                        model_label, field_name = map_dict[source_field]
                        try:
                            model = apps.get_model(model_label)
                        except LookupError:
                            errors.append(f"Row {row_num}: unknown model '{model_label}'")
                            continue
                        instance = model()
                        setattr(instance, field_name, value)
                        try:
                            instance.save()
                        except Exception as exc:
                            errors.append(f"Row {row_num}: {exc}")
                    rows_processed += 1

        job.status = "completed" if not errors else "failed"
        job.commit_result = {"rows_processed": rows_processed, "errors": errors}

    except Exception as exc:
        job.status = "failed"
        job.commit_result = {"rows_processed": rows_processed, "errors": [str(exc)]}
        errors.append(str(exc))

    job.save(update_fields=["status", "commit_result"])
    return {"rows_processed": rows_processed, "errors": errors}
