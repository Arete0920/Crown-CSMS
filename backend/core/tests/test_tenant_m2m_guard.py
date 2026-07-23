import uuid

import pytest
from django.core.exceptions import ValidationError

from board_oversight.models import BoardPacket, BoardReportSnapshot


@pytest.mark.django_db
def test_same_tenant_implicit_m2m_add_succeeds():
    school_id = uuid.uuid4()
    packet = BoardPacket.objects.create(school_id=school_id, title="Packet")
    snapshot = BoardReportSnapshot.objects.create(
        school_id=school_id,
        as_of_date="2026-07-22",
        period_label="July",
    )

    packet.snapshots.add(snapshot)

    assert packet.snapshots.filter(pk=snapshot.pk).exists()


@pytest.mark.django_db
def test_same_tenant_multi_record_add_succeeds():
    school_id = uuid.uuid4()
    packet = BoardPacket.objects.create(school_id=school_id, title="Packet")
    snapshots = [
        BoardReportSnapshot.objects.create(
            school_id=school_id,
            as_of_date=f"2026-07-{day:02d}",
            period_label=f"Day {day}",
        )
        for day in (21, 22)
    ]

    packet.snapshots.add(*snapshots)

    assert packet.snapshots.count() == 2


@pytest.mark.django_db(transaction=True)
def test_cross_tenant_implicit_m2m_add_is_rejected():
    packet = BoardPacket.objects.create(school_id=uuid.uuid4(), title="Packet")
    snapshot = BoardReportSnapshot.objects.create(
        school_id=uuid.uuid4(),
        as_of_date="2026-07-22",
        period_label="July",
    )

    with pytest.raises(ValidationError, match="same tenant"):
        packet.snapshots.add(snapshot)

    assert not packet.snapshots.exists()


@pytest.mark.django_db(transaction=True)
def test_reverse_cross_tenant_implicit_m2m_add_is_rejected():
    packet = BoardPacket.objects.create(school_id=uuid.uuid4(), title="Packet")
    snapshot = BoardReportSnapshot.objects.create(
        school_id=uuid.uuid4(),
        as_of_date="2026-07-22",
        period_label="July",
    )

    with pytest.raises(ValidationError, match="same tenant"):
        snapshot.boardpacket_set.add(packet)

    assert not packet.snapshots.exists()


@pytest.mark.django_db(transaction=True)
def test_mixed_batch_is_atomic_and_rejected():
    school_id = uuid.uuid4()
    packet = BoardPacket.objects.create(school_id=school_id, title="Packet")
    valid = BoardReportSnapshot.objects.create(
        school_id=school_id,
        as_of_date="2026-07-21",
        period_label="Valid",
    )
    invalid = BoardReportSnapshot.objects.create(
        school_id=uuid.uuid4(),
        as_of_date="2026-07-22",
        period_label="Invalid",
    )

    with pytest.raises(ValidationError, match="same tenant"):
        packet.snapshots.add(valid, invalid)

    assert not packet.snapshots.exists()


@pytest.mark.django_db
def test_direct_through_create_rejects_cross_tenant_row():
    packet = BoardPacket.objects.create(school_id=uuid.uuid4(), title="Packet")
    snapshot = BoardReportSnapshot.objects.create(
        school_id=uuid.uuid4(),
        as_of_date="2026-07-22",
        period_label="Invalid",
    )
    through = BoardPacket.snapshots.through

    with pytest.raises(ValidationError, match="same tenant"):
        through.objects.create(boardpacket=packet, boardreportsnapshot=snapshot)

    assert through.objects.count() == 0


@pytest.mark.django_db
def test_direct_through_bulk_create_rejects_cross_tenant_rows_atomically():
    school_id = uuid.uuid4()
    packet = BoardPacket.objects.create(school_id=school_id, title="Packet")
    valid = BoardReportSnapshot.objects.create(
        school_id=school_id,
        as_of_date="2026-07-21",
        period_label="Valid",
    )
    invalid = BoardReportSnapshot.objects.create(
        school_id=uuid.uuid4(),
        as_of_date="2026-07-22",
        period_label="Invalid",
    )
    through = BoardPacket.snapshots.through

    with pytest.raises(ValidationError, match="same tenant"):
        through.objects.bulk_create(
            [
                through(boardpacket=packet, boardreportsnapshot=valid),
                through(boardpacket=packet, boardreportsnapshot=invalid),
            ]
        )

    assert through.objects.count() == 0


@pytest.mark.django_db
def test_queryset_update_cannot_change_implicit_through_endpoints():
    school_id = uuid.uuid4()
    packet = BoardPacket.objects.create(school_id=school_id, title="Packet")
    snapshot = BoardReportSnapshot.objects.create(
        school_id=school_id,
        as_of_date="2026-07-22",
        period_label="Valid",
    )
    replacement = BoardReportSnapshot.objects.create(
        school_id=uuid.uuid4(),
        as_of_date="2026-07-23",
        period_label="Invalid replacement",
    )
    packet.snapshots.add(snapshot)
    through = BoardPacket.snapshots.through

    with pytest.raises(ValidationError, match="cannot be changed"):
        through.objects.update(boardreportsnapshot_id=replacement.pk)

    assert packet.snapshots.get().pk == snapshot.pk


@pytest.mark.django_db
def test_partial_direct_save_endpoint_update_is_rejected():
    school_one = uuid.uuid4()
    school_two = uuid.uuid4()
    packet_one = BoardPacket.objects.create(school_id=school_one, title="Packet 1")
    packet_two = BoardPacket.objects.create(school_id=school_two, title="Packet 2")
    snapshot_one = BoardReportSnapshot.objects.create(
        school_id=school_one,
        as_of_date="2026-07-22",
        period_label="One",
    )
    snapshot_two = BoardReportSnapshot.objects.create(
        school_id=school_two,
        as_of_date="2026-07-23",
        period_label="Two",
    )
    packet_one.snapshots.add(snapshot_one)
    through = BoardPacket.snapshots.through
    row = through.objects.get()

    row.boardpacket = packet_two
    row.boardreportsnapshot = snapshot_two
    with pytest.raises(ValidationError, match="include both endpoints"):
        row.save(update_fields=["boardpacket"])

    row.refresh_from_db()
    assert row.boardpacket_id == packet_one.pk
    assert row.boardreportsnapshot_id == snapshot_one.pk


@pytest.mark.django_db
def test_partial_bulk_update_endpoint_change_is_rejected():
    school_id = uuid.uuid4()
    packet = BoardPacket.objects.create(school_id=school_id, title="Packet")
    original = BoardReportSnapshot.objects.create(
        school_id=school_id,
        as_of_date="2026-07-22",
        period_label="Original",
    )
    replacement = BoardReportSnapshot.objects.create(
        school_id=school_id,
        as_of_date="2026-07-23",
        period_label="Replacement",
    )
    packet.snapshots.add(original)
    through = BoardPacket.snapshots.through
    row = through.objects.get()
    row.boardreportsnapshot = replacement

    with pytest.raises(ValidationError, match="include both endpoints"):
        through.objects.bulk_update([row], ["boardreportsnapshot"])

    row.refresh_from_db()
    assert row.boardreportsnapshot_id == original.pk


@pytest.mark.django_db
def test_raw_partial_direct_save_endpoint_update_is_rejected():
    school_one = uuid.uuid4()
    school_two = uuid.uuid4()
    packet_one = BoardPacket.objects.create(school_id=school_one, title="Packet 1")
    packet_two = BoardPacket.objects.create(school_id=school_two, title="Packet 2")
    snapshot_one = BoardReportSnapshot.objects.create(
        school_id=school_one,
        as_of_date="2026-07-22",
        period_label="One",
    )
    packet_one.snapshots.add(snapshot_one)
    through = BoardPacket.snapshots.through
    row = through.objects.get()
    row.boardpacket = packet_two

    with pytest.raises(ValidationError, match="include both endpoints"):
        row.save_base(raw=True, update_fields=["boardpacket"])

    row.refresh_from_db()
    assert row.boardpacket_id == packet_one.pk
    assert row.boardreportsnapshot_id == snapshot_one.pk


@pytest.mark.django_db
def test_raw_direct_save_base_rejects_cross_tenant_insert():
    packet = BoardPacket.objects.create(school_id=uuid.uuid4(), title="Packet")
    snapshot = BoardReportSnapshot.objects.create(
        school_id=uuid.uuid4(),
        as_of_date="2026-07-22",
        period_label="Invalid",
    )
    through = BoardPacket.snapshots.through
    row = through(boardpacket=packet, boardreportsnapshot=snapshot)

    with pytest.raises(ValidationError, match="same tenant"):
        row.save_base(raw=True, force_insert=True)

    assert through.objects.count() == 0


@pytest.mark.django_db
def test_raw_full_endpoint_repoint_rejects_cross_tenant_update():
    school_one = uuid.uuid4()
    school_two = uuid.uuid4()
    packet_one = BoardPacket.objects.create(school_id=school_one, title="Packet 1")
    packet_two = BoardPacket.objects.create(school_id=school_two, title="Packet 2")
    snapshot_one = BoardReportSnapshot.objects.create(
        school_id=school_one,
        as_of_date="2026-07-22",
        period_label="One",
    )
    packet_one.snapshots.add(snapshot_one)
    through = BoardPacket.snapshots.through
    row = through.objects.get()

    row.boardpacket = packet_two
    row.boardreportsnapshot = snapshot_one
    with pytest.raises(ValidationError, match="same tenant"):
        row.save_base(
            raw=True,
            update_fields=["boardpacket", "boardreportsnapshot"],
        )

    row.refresh_from_db()
    assert row.boardpacket_id == packet_one.pk
    assert row.boardreportsnapshot_id == snapshot_one.pk
