import json
import uuid

import pytest
from django.core.management import CommandError, call_command
from django.db import connection

from board_oversight.models import BoardPacket, BoardReportSnapshot
from core.management.commands.audit_implicit_tenant_relationships import (
    build_report,
    discover_relationships,
)


def _relationship(report, owner_model, field):
    return next(
        row
        for row in report["relationships"]
        if row["owner_model"] == owner_model and row["field"] == field
    )


def _insert_corrupt_packet_snapshot_link(packet, snapshot):
    """Insert an intentionally invalid row below the guarded ORM boundary.

    These tests verify that the independent audit command detects historical or
    externally introduced corruption. The normal ORM must remain fail-closed,
    so the anomaly fixture uses direct SQL and derives its table/columns from
    Django metadata rather than weakening or monkeypatching the runtime guard.
    """

    through = BoardPacket.snapshots.through
    packet_field = through._meta.get_field("boardpacket")
    snapshot_field = through._meta.get_field("boardreportsnapshot")
    quote = connection.ops.quote_name
    packet_id = packet_field.target_field.get_db_prep_value(packet.pk, connection)
    snapshot_id = snapshot_field.target_field.get_db_prep_value(snapshot.pk, connection)

    with connection.cursor() as cursor:
        cursor.execute(
            f"INSERT INTO {quote(through._meta.db_table)} "
            f"({quote(packet_field.column)}, {quote(snapshot_field.column)}) "
            "VALUES (%s, %s)",
            [packet_id, snapshot_id],
        )


def test_metadata_discovery_includes_known_tenant_scoped_implicit_relations():
    discovered = {
        (owner._meta.label, field.name)
        for owner, field in discover_relationships()
    }
    assert ("board_oversight.BoardPacket", "snapshots") in discovered
    assert ("spiritual_life.FormationCampaign", "portrait_domains") in discovered
    assert ("spiritual_life.FormationCampaign", "worldview_priorities") in discovered
    assert ("spiritual_life.StudentLeadershipEvent", "attendees") in discovered


@pytest.mark.django_db
def test_clean_board_packet_snapshot_link_is_normal():
    school_id = uuid.uuid4()
    packet = BoardPacket.objects.create(school_id=school_id, title="Board Packet")
    snapshot = BoardReportSnapshot.objects.create(
        school_id=school_id,
        as_of_date="2026-07-22",
        period_label="July",
    )
    packet.snapshots.add(snapshot)

    report = build_report(include_ids=True)
    partition = _relationship(
        report,
        "board_oversight.BoardPacket",
        "snapshots",
    )["identity_partition"]

    assert partition["input"]["count"] == 1
    assert partition["normal"]["count"] == 1
    assert partition["tenant_mismatch"]["count"] == 0
    assert partition["dangling_endpoint"]["count"] == 0
    assert partition["unverified_authority"]["count"] == 0
    assert partition["unexplained"]["count"] == 0
    assert partition["equation_holds"] is True


@pytest.mark.django_db
def test_cross_school_through_row_is_partitioned_as_mismatch():
    packet = BoardPacket.objects.create(school_id=uuid.uuid4(), title="Packet")
    snapshot = BoardReportSnapshot.objects.create(
        school_id=uuid.uuid4(),
        as_of_date="2026-07-22",
        period_label="July",
    )
    _insert_corrupt_packet_snapshot_link(packet, snapshot)

    report = build_report(include_ids=True)
    partition = _relationship(
        report,
        "board_oversight.BoardPacket",
        "snapshots",
    )["identity_partition"]

    assert partition["input"]["count"] == 1
    assert partition["normal"]["count"] == 0
    assert partition["tenant_mismatch"]["count"] == 1
    assert partition["unexplained"]["count"] == 0
    assert partition["accounted_unique_count"] == 1
    assert partition["exclusive_overlap_count"] == 0
    assert partition["equation_holds"] is True


@pytest.mark.django_db
def test_fail_on_anomaly_rejects_cross_school_through_row(capsys):
    packet = BoardPacket.objects.create(school_id=uuid.uuid4(), title="Packet")
    snapshot = BoardReportSnapshot.objects.create(
        school_id=uuid.uuid4(),
        as_of_date="2026-07-22",
        period_label="July",
    )
    _insert_corrupt_packet_snapshot_link(packet, snapshot)

    with pytest.raises(CommandError, match="implicit tenant anomaly"):
        call_command("audit_implicit_tenant_relationships", "--fail-on-anomaly")

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["production_authorization"] is False
    assert payload["totals"]["tenant_mismatches"] >= 1


@pytest.mark.django_db
def test_identity_checksums_are_deterministic():
    school_id = uuid.uuid4()
    packet = BoardPacket.objects.create(school_id=school_id, title="Packet")
    snapshots = [
        BoardReportSnapshot.objects.create(
            school_id=school_id,
            as_of_date=f"2026-07-{day:02d}",
            period_label=f"Day {day}",
        )
        for day in (20, 21, 22)
    ]
    packet.snapshots.add(*snapshots)

    first = _relationship(
        build_report(include_ids=True),
        "board_oversight.BoardPacket",
        "snapshots",
    )["identity_partition"]
    second = _relationship(
        build_report(include_ids=True),
        "board_oversight.BoardPacket",
        "snapshots",
    )["identity_partition"]

    assert first["input"] == second["input"]
    assert first["normal"] == second["normal"]
