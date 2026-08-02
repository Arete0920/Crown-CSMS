from datetime import datetime, timezone
from types import SimpleNamespace

from applications import views_admissions as admissions


def test_build_document_lifecycle_maps_ready_and_pending_actions():
    result = admissions._build_document_lifecycle(
        {
            "transcriptReady": True,
            "recommendationsReady": False,
            "pastorReferenceReady": 1,
            "immunizationReady": None,
        }
    )

    assert result == [
        {
            "key": "transcript",
            "label": "Transcript",
            "status": "ready",
            "next_action": "Await reviewer verification",
        },
        {
            "key": "recommendations",
            "label": "Recommendations",
            "status": "pending",
            "next_action": "Submit during review phase",
        },
        {
            "key": "pastor_reference",
            "label": "Pastor/Church Reference",
            "status": "ready",
            "next_action": "Await reviewer verification",
        },
        {
            "key": "immunization",
            "label": "Immunization Records",
            "status": "pending",
            "next_action": "Submit during review phase",
        },
    ]


def test_checklist_status_from_documents_uses_definition_flag():
    item_def = next(
        entry
        for entry in admissions.CHECKLIST_REQUIRED_ITEMS
        if entry["key"] == "transcript"
    )

    assert admissions._checklist_status_from_documents(
        item_def,
        {item_def["document_flag"]: True},
    ) == admissions.ChecklistItemStatus.SUBMITTED
    assert admissions._checklist_status_from_documents(
        item_def,
        {},
    ) == admissions.ChecklistItemStatus.MISSING


def test_infer_document_quality_status_classifies_metadata():
    assert admissions._infer_document_quality_status(
        filename="",
        content_type="application/pdf",
    ) == ("rejected", "Missing filename metadata.")
    assert admissions._infer_document_quality_status(
        filename="scan.tiff",
        content_type="image/tiff",
    ) == ("review", "Image format may reduce review readability.")
    assert admissions._infer_document_quality_status(
        filename="TRANSCRIPT.PDF",
        content_type="application/pdf",
    ) == ("ready", "File type accepted for review.")
    assert admissions._infer_document_quality_status(
        filename="notes.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ) == ("review", "File uploaded, but preferred type is PDF or clear image.")


def test_checklist_dependency_state_reports_blocking_items():
    item_def = {
        "depends_on": ["transcript", "pastor_reference"],
    }
    siblings = [
        SimpleNamespace(
            item_key="transcript",
            status=admissions.ChecklistItemStatus.APPROVED,
        ),
        SimpleNamespace(
            item_key="pastor_reference",
            status=admissions.ChecklistItemStatus.MISSING,
        ),
    ]
    item = SimpleNamespace(
        application=SimpleNamespace(
            checklist_items=SimpleNamespace(all=lambda: siblings),
        )
    )

    assert admissions._checklist_dependency_state(item, item_def) == {
        "blocked": True,
        "depends_on": ["transcript", "pastor_reference"],
        "blocking_items": ["pastor_reference"],
        "dependency_status": "blocked",
    }


def test_checklist_dependency_state_without_dependencies_is_ready():
    item = SimpleNamespace(application=SimpleNamespace(checklist_items=None))

    assert admissions._checklist_dependency_state(
        item,
        {"depends_on": []},
    ) == {
        "blocked": False,
        "depends_on": [],
        "blocking_items": [],
        "dependency_status": "ready",
    }


def test_checklist_summary_counts_only_required_items():
    items = [
        SimpleNamespace(
            is_required=True,
            status=admissions.ChecklistItemStatus.SUBMITTED.value,
        ),
        SimpleNamespace(
            is_required=True,
            status=admissions.ChecklistItemStatus.APPROVED.value,
        ),
        SimpleNamespace(
            is_required=True,
            status=admissions.ChecklistItemStatus.REJECTED.value,
        ),
        SimpleNamespace(
            is_required=False,
            status=admissions.ChecklistItemStatus.MISSING.value,
        ),
    ]

    assert admissions._checklist_summary(items) == {
        "required_total": 3,
        "submitted_count": 2,
        "missing_count": 1,
        "ready_for_review": False,
    }


def test_checklist_item_definition_returns_known_and_fallback_values():
    known = admissions._checklist_item_definition("transcript")
    fallback = admissions._checklist_item_definition("custom_item")

    assert known["title"] == "Official Transcript"
    assert known["document_flag"] == "transcriptReady"
    assert fallback == {
        "key": "custom_item",
        "title": "custom_item",
        "office": "",
        "owner": "",
        "due_days": 0,
        "depends_on": [],
        "parent_visible": True,
        "reminder_days": [],
        "document_flag": "",
    }


def test_checklist_due_at_iso_uses_submission_then_creation_date():
    submitted_at = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
    created_at = datetime(2026, 7, 30, 9, 30, tzinfo=timezone.utc)
    item = SimpleNamespace(
        application=SimpleNamespace(
            submitted_at=submitted_at,
            created_at=created_at,
        )
    )

    assert admissions._checklist_due_at_iso(
        item,
        {"due_days": 5},
    ) == "2026-08-06T12:00:00+00:00"

    item.application.submitted_at = None
    assert admissions._checklist_due_at_iso(
        item,
        {"due_days": 2},
    ) == "2026-08-01T09:30:00+00:00"
    assert admissions._checklist_due_at_iso(
        item,
        {"due_days": 0},
    ) is None


def test_checklist_parent_status_maps_internal_states():
    assert admissions._checklist_parent_status(
        SimpleNamespace(status=admissions.ChecklistItemStatus.SUBMITTED.value)
    ) == "Ready for Review"
    assert admissions._checklist_parent_status(
        SimpleNamespace(status=admissions.ChecklistItemStatus.UNDER_REVIEW.value)
    ) == "Ready for Review"
    assert admissions._checklist_parent_status(
        SimpleNamespace(status=admissions.ChecklistItemStatus.APPROVED.value)
    ) == "Checklist Complete"
    assert admissions._checklist_parent_status(
        SimpleNamespace(status=admissions.ChecklistItemStatus.MISSING.value)
    ) == "Checklist Incomplete"
