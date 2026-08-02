from datetime import datetime, timezone
from types import SimpleNamespace

from applications import views_admissions as admissions


class _DocumentsRelation:
    def __init__(self, latest):
        self.latest = latest
        self.ordering = None

    def order_by(self, ordering):
        self.ordering = ordering
        return self

    def first(self):
        return self.latest


class _ChecklistItemsRelation:
    def __init__(self, items):
        self.items = items

    def all(self):
        return self.items


def test_serialize_checklist_item_includes_document_dependency_and_parent_metadata():
    submitted_at = datetime(2026, 8, 2, 1, 0, tzinfo=timezone.utc)
    created_at = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
    uploaded_at = datetime(2026, 8, 2, 0, 30, tzinfo=timezone.utc)
    latest_doc = SimpleNamespace(
        id="document-1",
        original_filename="transcript.pdf",
        created_at=uploaded_at,
        content_type="application/pdf",
    )
    documents = _DocumentsRelation(latest_doc)
    item = SimpleNamespace(
        id="item-1",
        item_key="transcript",
        title="Official Transcript",
        office=admissions.ACADEMIC_OFFICE,
        is_required=True,
        status=admissions.ChecklistItemStatus.SUBMITTED.value,
        notes="Verified by admissions.",
        submitted_at=submitted_at,
        documents=documents,
    )
    item.application = SimpleNamespace(
        submitted_at=submitted_at,
        created_at=created_at,
        checklist_items=_ChecklistItemsRelation([item]),
    )

    result = admissions._serialize_checklist_item(item)

    assert documents.ordering == "-created_at"
    assert result == {
        "id": "item-1",
        "item_key": "transcript",
        "title": "Official Transcript",
        "office": admissions.ACADEMIC_OFFICE,
        "owner": "Admissions Records",
        "due_at": "2026-08-07T01:00:00+00:00",
        "depends_on": [],
        "dependency_status": "ready",
        "blocking_items": [],
        "is_blocked": False,
        "is_required": True,
        "status": admissions.ChecklistItemStatus.SUBMITTED.value,
        "parent_status": "Ready for Review",
        "parent_visibility": True,
        "reminder_setting": {"enabled": True, "days": [3, 7]},
        "notes": "Verified by admissions.",
        "staff_only_notes": "Verified by admissions.",
        "submitted_at": "2026-08-02T01:00:00+00:00",
        "completion_timestamp": "2026-08-02T01:00:00+00:00",
        "latest_document": {
            "id": "document-1",
            "original_filename": "transcript.pdf",
            "uploaded_at": "2026-08-02T00:30:00+00:00",
            "content_type": "application/pdf",
            "quality_status": "ready",
            "quality_note": "File type accepted for review.",
        },
    }


def test_serialize_checklist_item_uses_fallback_defaults_without_document():
    item = SimpleNamespace(
        id="item-custom",
        item_key="custom_item",
        title="Custom Item",
        office="Admissions Office",
        is_required=False,
        status=admissions.ChecklistItemStatus.MISSING.value,
        notes=None,
        submitted_at=None,
        documents=_DocumentsRelation(None),
    )
    item.application = SimpleNamespace(
        submitted_at=None,
        created_at=None,
        checklist_items=_ChecklistItemsRelation([item]),
    )

    result = admissions._serialize_checklist_item(item)

    assert result["owner"] == "Admissions Office"
    assert result["due_at"] is None
    assert result["parent_status"] == "Checklist Incomplete"
    assert result["parent_visibility"] is True
    assert result["reminder_setting"] == {"enabled": True, "days": [3, 7]}
    assert result["notes"] == ""
    assert result["staff_only_notes"] == ""
    assert result["submitted_at"] is None
    assert result["completion_timestamp"] is None
    assert result["latest_document"] is None


def test_promote_checklist_for_demo_updates_required_items(monkeypatch):
    fixed_now = datetime(2026, 8, 2, 1, 15, tzinfo=timezone.utc)
    captured = {}

    class _QuerySet:
        def update(self, **kwargs):
            captured["update"] = kwargs
            return 3

    class _Manager:
        def filter(self, **kwargs):
            captured["filter"] = kwargs
            return _QuerySet()

    monkeypatch.setattr(admissions.timezone, "now", lambda: fixed_now)
    monkeypatch.setattr(admissions.ApplicationChecklistItem, "objects", _Manager())
    application = SimpleNamespace(id="application-1")

    result = admissions._promote_checklist_for_demo(application)

    assert result is None
    assert captured["filter"] == {
        "application": application,
        "is_required": True,
    }
    assert captured["update"] == {
        "status": admissions.ChecklistItemStatus.APPROVED,
        "submitted_at": fixed_now,
        "notes": "Sandbox demo flow: package completion assumed.",
    }
