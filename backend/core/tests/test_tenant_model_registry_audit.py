import json
from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from core.management.commands.audit_tenant_model_registry import (
    build_registry_report,
    discover_tenant_models,
)


def _relationship_index(rows):
    return {
        (row["model"], relation["relation"], relation["parent_tenant_path"]): relation
        for row in rows
        for relation in row["relationships"]
    }


def test_registry_inventory_discovers_known_unregistered_relationships():
    relationships = _relationship_index(discover_tenant_models())

    assert ("academics.Grade", "submission", "submission__school_id") in relationships
    assert relationships[("academics.Grade", "submission", "submission__school_id")]["registered"] is False
    assert ("academics.MasteryRecord", "student", "student__school_id") in relationships
    assert ("academics.TranscriptEntry", "course", "course__school_id") in relationships
    assert ("home_academy.OfferingEnrollment", "offering", "offering__school_id") in relationships


def test_registry_inventory_discovers_implicit_many_to_many_through_tenant_paths():
    rows = discover_tenant_models()
    implicit_relationships = [
        relationship
        for row in rows
        for relationship in row["relationships"]
        if relationship["implicit_through"]
    ]

    board_packet_snapshot = next(
        relationship
        for relationship in implicit_relationships
        if relationship["child_model"].startswith("board_oversight.BoardPacket_")
        and "boardpacket" in relationship.get("child_tenant_path", "")
        and "boardreportsnapshot" in relationship["parent_tenant_path"]
    )

    assert board_packet_snapshot["registered"] is False
    assert board_packet_snapshot["child_tenant_anchor"] == "school"
    assert board_packet_snapshot["parent_tenant_anchor"] == "school"
    assert board_packet_snapshot["tenant_anchor_match"] is True
    assert board_packet_snapshot["child_tenant_type"] == "UUIDField"
    assert board_packet_snapshot["parent_tenant_type"] == "UUIDField"
    assert board_packet_snapshot["tenant_type_match"] is True


def test_registry_inventory_discovers_accounting_tenant_id_relationships():
    relationships = _relationship_index(discover_tenant_models())

    journal = relationships[(
        "accounting.LedgerEntry",
        "journal_entry",
        "journal_entry__tenant_id",
    )]
    account = relationships[(
        "accounting.LedgerEntry",
        "account",
        "account__tenant_id",
    )]

    assert journal["child_tenant_anchor"] == "tenant"
    assert journal["parent_tenant_anchor"] == "tenant"
    assert journal["tenant_anchor_match"] is True
    assert journal["tenant_type_match"] is True
    assert account["tenant_anchor_match"] is True
    assert account["tenant_type_match"] is True


def test_registry_inventory_reports_concrete_tenant_identifier_types():
    stdout = StringIO()
    call_command("audit_tenant_model_registry", stdout=stdout)
    payload = json.loads(stdout.getvalue())

    assert payload["mode"] == "read_only"
    assert payload["production_authorization"] is False
    assert payload["schema_version"] == 4
    assert payload["totals"]["tenant_models"] > 0
    assert payload["totals"]["tenant_relationships"] > 0
    assert payload["totals"]["implicit_through_relationships"] > 0
    assert payload["totals"]["unregistered_relationships"] > 0
    assert "UUIDField" in payload["tenant_field_types"]
    assert "IntegerField" in payload["tenant_field_types"]
    assert "derived" in payload["tenant_field_types"]
    assert payload["tenant_anchors"]["school"] > 0
    assert payload["tenant_anchors"]["tenant"] > 0


def test_registry_comparison_normalizes_model_label_case(monkeypatch):
    from core.management.commands import audit_tenant_model_registry as registry_command

    monkeypatch.setattr(
        registry_command,
        "RELATIONSHIPS",
        (("academics.grade", "submission__school_id", "submission"),),
    )

    report = build_registry_report(discover_tenant_models())
    grade_relationship = next(
        relationship
        for relationship in report["models"]
        if relationship["model"] == "academics.Grade"
    )
    submission = next(
        item
        for item in grade_relationship["relationships"]
        if item["relation"] == "submission"
    )

    assert submission["registered"] is True
    assert not any(
        item["child_model"] == "academics.grade"
        and item["relation"] == "submission"
        for item in report["stale_registered_relationships"]
    )


def test_registry_inventory_reports_stale_and_duplicate_registry_entries(monkeypatch):
    from core.management.commands import audit_tenant_model_registry as registry_command

    monkeypatch.setattr(
        registry_command,
        "RELATIONSHIPS",
        (
            ("academics.Grade", "submission__school_id", "submission"),
            ("academics.grade", "submission__school_id", "submission"),
            ("missing.Model", "parent__school_id", "parent"),
        ),
    )

    report = build_registry_report(discover_tenant_models())

    assert report["totals"]["duplicate_registered_relationships"] == 1
    assert report["totals"]["stale_registered_relationships"] == 1
    assert report["duplicate_registered_relationships"][0]["count"] == 2
    assert report["stale_registered_relationships"][0]["child_model"] == "missing.model"


def test_registry_inventory_can_fail_closed_on_missing_coverage():
    with pytest.raises(CommandError, match="unregistered relationship"):
        call_command(
            "audit_tenant_model_registry",
            fail_on_unregistered=True,
            stdout=StringIO(),
        )


def test_registry_inventory_can_fail_closed_on_any_completeness_defect():
    with pytest.raises(CommandError, match="registry completeness defect"):
        call_command(
            "audit_tenant_model_registry",
            fail_on_incomplete=True,
            stdout=StringIO(),
        )
