"""Synthetic, fail-closed custody visit foundation tests.

No re-entry endpoint or service activation is included in this slice.
"""
from datetime import datetime, timedelta, timezone as datetime_timezone
from uuid import uuid4
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit, urlunsplit
import os
import re
import shutil
import subprocess
import sys

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

from aftercare.models import DaycareAttendance, DaycareReentryAuthorization, DaycareRelease, DaycareSite, DaycareRoom
from aftercare.daycare_checkin import CheckinRefused
from aftercare.tests.test_daycare_checkin import setup, check
from aftercare.tests.test_daycare_release import release
from core.models import UserRole
from audit.models import AuditLog

pytestmark = pytest.mark.django_db


def test_first_visit_preserves_number_and_never_reenters_without_approval():
    data = setup()
    first = check(data)
    assert first.visit_number == 1
    assert first.reentry_approval_id is None
    release(data, first)
    with pytest.raises(CheckinRefused, match="repeat_same_day_requires_review"):
        check(data)
    assert DaycareAttendance.objects.filter(child=data["child"]).count() == 1
    assert AuditLog.objects.filter(action="diadem.daycare.checkin").count() == 1


def test_director_approval_is_append_only_and_cannot_authorize_unreleased_visit():
    data = setup()
    first = check(data)
    UserRole.objects.create(school=data["school"], user=data["director"], role_code="DAYCARE_DIRECTOR")
    now = timezone.now()
    args = dict(
        school=data["school"], site=data["site"], child=data["child"],
        previous_attendance=first, director=data["director"],
        care_date=first.care_date, reason_code="DIRECTOR_REVIEWED",
        approved_at=now, expires_at=now+timedelta(minutes=10),
    )
    with pytest.raises(ValidationError):
        DaycareReentryAuthorization.objects.create(**args)
    assert not DaycareReentryAuthorization.objects.exists()
    release(data, first)
    args["approved_at"] = timezone.now()
    args["expires_at"] = args["approved_at"] + timedelta(minutes=10)
    approval = DaycareReentryAuthorization.objects.create(**args)
    assert approval.previous_attendance_id == first.id
    with pytest.raises(ValidationError):
        approval.save()
    with pytest.raises(ValidationError):
        approval.delete()
    # Approval persistence alone does not activate the check-in service.
    with pytest.raises(CheckinRefused, match="repeat_same_day_requires_review"):
        check(data)
    assert DaycareAttendance.objects.count() == 1


def test_unassigned_staff_cannot_authorize_reentry():
    data = setup()
    first = check(data)
    release(data, first)
    now = timezone.now()
    with pytest.raises(ValidationError):
        DaycareReentryAuthorization.objects.create(
            school=data["school"], site=data["site"], child=data["child"],
            previous_attendance=first, director=data["actor"],
            care_date=first.care_date, reason_code="DIRECTOR_REVIEWED",
            approved_at=now, expires_at=now+timedelta(minutes=10),
        )
    assert not DaycareReentryAuthorization.objects.exists()


def test_direct_second_visit_without_approval_denied():
    data = setup()
    first = check(data)
    release(data, first)
    with pytest.raises(ValidationError):
        DaycareAttendance.objects.create(
            school=data["school"], site=data["site"], room=data["room"],
            child=data["child"], program=data["program"],
            enrollment=data["enrollment"], actor=data["actor"],
            care_date=first.care_date, checked_in_at=timezone.now(),
            visit_number=2,
        )
    assert DaycareAttendance.objects.count() == 1


def test_backdated_director_authorization_is_rejected_after_handoff():
    data = setup()
    first = check(data)
    UserRole.objects.create(school=data["school"], user=data["director"], role_code="DAYCARE_DIRECTOR")
    before_release = timezone.now()
    release(data, first)
    with pytest.raises(ValidationError, match="cannot precede"):
        DaycareReentryAuthorization.objects.create(
            school=data["school"], site=data["site"], child=data["child"],
            previous_attendance=first, director=data["director"],
            care_date=first.care_date, reason_code="DIRECTOR_REVIEWED",
            approved_at=before_release, expires_at=before_release+timedelta(minutes=10),
        )
    assert not DaycareReentryAuthorization.objects.exists()


def test_reentry_requires_chronological_handoff_and_local_care_day():
    data = setup()
    first = check(data)
    event = release(data, first)
    UserRole.objects.create(school=data["school"], user=data["director"], role_code="DAYCARE_DIRECTOR")
    approved_at = timezone.now()
    approval = DaycareReentryAuthorization.objects.create(
        school=data["school"], site=data["site"], child=data["child"],
        previous_attendance=first, director=data["director"],
        care_date=first.care_date, reason_code="DIRECTOR_REVIEWED",
        approved_at=approved_at, expires_at=approved_at+timedelta(days=2),
    )
    base = dict(
        school=data["school"], site=data["site"], room=data["room"],
        child=data["child"], program=data["program"], enrollment=data["enrollment"],
        actor=data["actor"], care_date=first.care_date, visit_number=2,
        reentry_approval=approval,
    )
    with pytest.raises(ValidationError, match="does not match this released visit"):
        DaycareAttendance.objects.create(
            **base, checked_in_at=event.released_at-timedelta(seconds=1)
        )
    with pytest.raises(ValidationError, match="original local care date"):
        DaycareAttendance.objects.create(
            **base, checked_in_at=approved_at+timedelta(days=1)
        )
    assert DaycareAttendance.objects.count()==1
    assert AuditLog.objects.filter(action="diadem.daycare.checkin").count()==1


def test_database_rejects_visit_without_approval_even_when_orm_is_bypassed():
    # Deliberately exercise only the disposable test database. Production
    # custody writes never use raw SQL; this proves the migration CHECK guard.
    data = setup()
    first = check(data)
    table = connection.ops.quote_name(DaycareAttendance._meta.db_table)
    pk_column = connection.ops.quote_name(DaycareAttendance._meta.pk.column)
    pk_value = DaycareAttendance._meta.pk.get_db_prep_value(first.pk, connection)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    f"UPDATE {table} SET visit_number = 2 WHERE {pk_column} = %s",
                    [pk_value],
                )
    first.refresh_from_db()
    assert first.visit_number == 1
    assert first.reentry_approval_id is None



def _verify_local_postgresql_backup_restore(
    *, attendance_id, release_id, audit_id, school_id,
    attendance_count, release_count, audit_count,
):
    """Restore a pre-0012 synthetic custody dump into a *fresh* local test DB."""
    assert connection.vendor == "postgresql"
    db_name = str(connection.settings_dict["NAME"])
    host = str(connection.settings_dict["HOST"] or "localhost")
    port = str(connection.settings_dict["PORT"] or "5432")
    user = str(connection.settings_dict["USER"])
    assert host in {"localhost", "127.0.0.1"}
    assert db_name.startswith("test_")
    dsn = urlsplit(os.environ.get("DATABASE_URL", ""))
    assert dsn.scheme in {"postgresql", "postgres"}
    assert dsn.hostname in {"localhost", "127.0.0.1"}
    assert dsn.username == user
    assert dsn.path.lstrip("/") and db_name.endswith(dsn.path.lstrip("/"))
    assert os.environ.get("DJANGO_SETTINGS_MODULE") == "crown_api.test_settings"

    server_major = connection.pg_version // 10000
    installed = Path(f"/usr/lib/postgresql/{server_major}/bin")
    clients = {}
    for name in ("pg_dump", "pg_restore", "psql", "createdb", "dropdb"):
        exact = installed / name
        executable = str(exact) if exact.is_file() else shutil.which(name)
        assert executable, f"PostgreSQL client executable required: {name}"
        version = subprocess.run(
            [executable, "--version"], check=True, capture_output=True,
            text=True, timeout=10,
        ).stdout.strip()
        match = re.search(r"\(PostgreSQL\) (\d+)\.", version)
        assert match and int(match.group(1)) == server_major, (
            f"{name} must match PostgreSQL server major {server_major}; "
            f"selected {executable}: {version}"
        )
        clients[name] = executable

    def cli(name):
        return clients[name]

    env = {**os.environ, "PGHOST": host, "PGPORT": port, "PGUSER": user,
           "PGPASSWORD": str(connection.settings_dict["PASSWORD"])}
    def run(*args, process_env=None):
        return subprocess.run(
            list(args), env=process_env or env, check=True,
            capture_output=True, text=True, timeout=240,
        )

    clone = f"test_diadem_restore_{uuid4().hex[:12]}"
    assert clone != db_name and clone.startswith("test_diadem_restore_")
    def scalar(sql):
        return run(cli("psql"), "-X", "-A", "-t", "-d", clone, "-c", sql).stdout.strip()

    attendance_table = connection.ops.quote_name(DaycareAttendance._meta.db_table)
    release_table = connection.ops.quote_name(DaycareRelease._meta.db_table)
    audit_table = connection.ops.quote_name(AuditLog._meta.db_table)
    attendance_id, release_id = str(attendance_id), str(release_id)
    audit_id, school_id = str(audit_id), str(school_id)
    created = False
    with TemporaryDirectory(prefix="diadem-test-restore-") as folder:
        archive = str(Path(folder) / "before-0012.dump")
        try:
            run(cli("pg_dump"), "-Fc", "-d", db_name, "-f", archive)
            assert Path(archive).stat().st_size > 0
            run(cli("createdb"), "--maintenance-db=postgres", clone)
            created = True
            run(cli("pg_restore"), "--exit-on-error", "--no-owner", "--no-acl",
                "-d", clone, archive)

            def verify():
                assert scalar(f"SELECT count(*) FROM {attendance_table}") == str(attendance_count)
                assert scalar(f"SELECT count(*) FROM {release_table}") == str(release_count)
                assert scalar(f"SELECT count(*) FROM {audit_table}") == str(audit_count)
                assert scalar(
                    f"SELECT school_id FROM {attendance_table} WHERE id='{attendance_id}'"
                ) == school_id
                assert scalar(
                    f"SELECT attendance_id FROM {release_table} WHERE id='{release_id}'"
                ) == attendance_id
                assert scalar(
                    f"SELECT object_id FROM {audit_table} WHERE id='{audit_id}'"
                ) == release_id

            verify()
            clone_dsn = urlunsplit((dsn.scheme, dsn.netloc, "/" + clone,
                                   dsn.query, dsn.fragment))
            run(sys.executable, "manage.py", "migrate", "aftercare", "0012",
                "--noinput", "--no-color",
                process_env={**env, "DATABASE_URL": clone_dsn})
            verify()
            assert scalar(
                f"SELECT visit_number FROM {attendance_table} WHERE id='{attendance_id}'"
            ) == "1"
            assert scalar(
                f"SELECT reentry_approval_id IS NULL FROM {attendance_table} "
                f"WHERE id='{attendance_id}'"
            ) == "t"
            assert scalar(
                "SELECT count(*) FROM aftercare_daycarereentryauthorization"
            ) == "0"
        finally:
            if created:
                run(cli("dropdb"), "--if-exists", "--force",
                    "--maintenance-db=postgres", clone)
                remaining = run(
                    cli("psql"), "-X", "-A", "-t", "-d", "postgres",
                    "-c", f"SELECT count(*) FROM pg_database WHERE datname='{clone}'",
                ).stdout.strip()
                assert remaining == "0", "Disposable restore database was not removed"

def _historical_custody_fixture(apps):
    """Build old-schema records without importing newer model fields/validation.

    Migration replay must remain genuine when later setup fields are added.
    Use historical foreign-key IDs, never current-model instances across app states.
    """
    def create(app, model, **values):
        return apps.get_model(app, model).objects.create(**values)
    school = create("core", "School", name="Synthetic historical childcare", timezone="UTC")
    actor = create("core", "UserAccount", username=f"historic-{uuid4().hex}", school_id=school.pk, is_active=True)
    family = create("households", "Household", school_id=school.pk, name="Historical family")
    guardian = create("households", "Guardian", school_id=school.pk, household_id=family.pk,
                      first_name="Synthetic", last_name="Guardian")
    site = create("aftercare", "DaycareSite", school_id=school.pk, code="historic", name="Historical center", is_active=True)
    room = create("aftercare", "DaycareRoom", school_id=school.pk, site_id=site.pk,
                  code="historic", name="Historical room", licensed_capacity=4,
                  max_children_per_staff=4, policy_source="Synthetic reviewed historical policy",
                  policy_verified_by_id=actor.pk, policy_verified_at=timezone.now(), is_active=True)
    child = create("aftercare", "DaycareChild", school_id=school.pk, site_id=site.pk,
                   household_id=family.pk, first_name="Historical", last_name="Synthetic",
                   date_of_birth=datetime(2024, 1, 1).date(), is_active=True)
    program = create("aftercare", "DaycareProgram", school_id=school.pk, site_id=site.pk,
                     code="DAYCARE", name="Historical program", is_active=True)
    enrollment = create("aftercare", "DaycareEnrollment", school_id=school.pk, site_id=site.pk,
                        room_id=room.pk, child_id=child.pk, program_id=program.pk,
                        status="ACTIVE", readiness="READY", start_date=datetime(2026, 1, 1).date(), weekdays=list(range(7)))
    authority = create("aftercare", "DaycareGuardianAuthority", school_id=school.pk,
                       child_id=child.pk, guardian_id=guardian.pk, is_active=True, can_pickup=True,
                       custody_status="CLEAR", verified_by_id=actor.pk, verified_at=timezone.now())
    return locals()


@pytest.mark.django_db(transaction=True)
def test_postgresql_preexisting_custody_survives_visit_migration():
    """Rehearse 0011 -> 0012 with old-model child custody rows and audit IDs.

    This modifies *only* an ephemeral PostgreSQL test database, restores
    the latest migration state in finally, and never connects to Azure.
    """
    if connection.vendor != "postgresql":
        pytest.skip("Real PostgreSQL migration replay only.")
    assert connection.settings_dict["HOST"] in {"localhost", "127.0.0.1"}
    assert str(connection.settings_dict["NAME"]).startswith("test_")

    previous = ("aftercare", "0011_aftercare_pickup_verified_by")
    updated = ("aftercare", "0012_diadem_visit_reentry_foundation")
    original_executor = MigrationExecutor(connection)
    final_targets = original_executor.loader.graph.leaf_nodes()
    try:
        original_executor.migrate([previous])
        historical_apps = MigrationExecutor(connection).loader.project_state(
            [previous]
        ).apps
        HistoricalAttendance = historical_apps.get_model(
            "aftercare", "DaycareAttendance"
        )
        HistoricalRelease = historical_apps.get_model(
            "aftercare", "DaycareRelease"
        )
        data = _historical_custody_fixture(historical_apps)
        checked_in_at = datetime(2026, 11, 1, 12, 0, tzinfo=datetime_timezone.utc)
        old_row = HistoricalAttendance.objects.create(
            school_id=data["school"].id, site_id=data["site"].id,
            room_id=data["room"].id, child_id=data["child"].id,
            program_id=data["program"].id, enrollment_id=data["enrollment"].id,
            actor_id=data["actor"].id, care_date=checked_in_at.date(),
            checked_in_at=checked_in_at, request_key=uuid4(),
        )
        old_release = HistoricalRelease.objects.create(
            school_id=data["school"].id, site_id=data["site"].id,
            room_id=data["room"].id, child_id=data["child"].id,
            attendance_id=old_row.id, guardian_authority_id=data["authority"].id,
            actor_id=data["actor"].id,
            released_at=checked_in_at + timedelta(minutes=10),
            identity_method="GOVERNMENT_PHOTO_ID", identity_verified=True,
            guardian_name_snapshot="Synthetic Guardian", request_key=uuid4(),
        )
        audit = AuditLog.objects.create(
            user_id=data["actor"].id, action="diadem.daycare.release",
            model="DaycareRelease", object_id=str(old_release.pk),
            metadata={"school_id": str(data["school"].id), "synthetic": True},
        )
        historical_ids = (old_row.id, old_release.id, audit.pk)
        assert not hasattr(old_row, "visit_number")
        assert HistoricalAttendance.objects.count() == 1
        assert HistoricalRelease.objects.count() == 1
        _verify_local_postgresql_backup_restore(
            attendance_id=old_row.pk, release_id=old_release.pk,
            audit_id=audit.pk, school_id=data["school"].pk,
            attendance_count=HistoricalAttendance.objects.count(),
            release_count=HistoricalRelease.objects.count(),
            audit_count=AuditLog.objects.count(),
        )

        MigrationExecutor(connection).migrate([updated])
        accepted_row = DaycareAttendance.objects.get(pk=historical_ids[0])
        accepted_release = DaycareRelease.objects.get(pk=historical_ids[1])
        accepted_audit = AuditLog.objects.get(pk=historical_ids[2])
        assert accepted_row.visit_number == 1
        assert accepted_row.reentry_approval_id is None
        assert accepted_row.child_id == data["child"].id
        assert accepted_row.checked_in_at == checked_in_at
        assert accepted_release.attendance_id == accepted_row.pk
        assert accepted_release.guardian_authority_id == data["authority"].id
        assert accepted_release.released_at == checked_in_at + timedelta(minutes=10)
        assert accepted_audit.object_id == str(accepted_release.pk)
        assert DaycareAttendance.objects.count() == 1
        assert DaycareRelease.objects.count() == 1
        assert DaycareReentryAuthorization.objects.count() == 0

        # The pre-0012 application model omits visit_number entirely.
        # PostgreSQL must retain a persistent database default so an older
        # still-running image can write a new first admission during rollout.
        legacy_child = type(data["child"]).objects.create(
            school=data["school"], site=data["site"],
            household=data["family"], first_name="Legacy",
            last_name="Synthetic", date_of_birth=data["child"].date_of_birth,
            is_active=True,
        )
        legacy_enrollment = type(data["enrollment"]).objects.create(
            school=data["school"], site=data["site"], room=data["room"],
            child=legacy_child, program=data["program"], status="ACTIVE",
            readiness="READY",
            start_date=checked_in_at.date() - timedelta(days=5),
            weekdays=list(range(7)),
        )
        old_image_row = HistoricalAttendance.objects.create(
            school_id=data["school"].id, site_id=data["site"].id,
            room_id=data["room"].id, child_id=legacy_child.pk,
            program_id=data["program"].id, enrollment_id=legacy_enrollment.pk,
            actor_id=data["actor"].id, care_date=checked_in_at.date(),
            checked_in_at=checked_in_at, request_key=uuid4(),
        )
        migrated_old_image_row = DaycareAttendance.objects.get(pk=old_image_row.pk)
        assert migrated_old_image_row.visit_number == 1
        assert migrated_old_image_row.reentry_approval_id is None
        assert migrated_old_image_row.child_id == legacy_child.pk
        assert migrated_old_image_row.enrollment_id == legacy_enrollment.pk
        # Later additive setup fields preserve accepted custody and never
        # guess a historical center's operating mode, jurisdiction or policy.
        MigrationExecutor(connection).migrate(final_targets)
        site = DaycareSite.objects.get(pk=data["site"].pk)
        room = DaycareRoom.objects.get(pk=data["room"].pk)
        assert site.operating_mode == site.jurisdiction == ""
        assert site.is_active and room.is_active
        assert room.proposed_min_age_months is room.proposed_max_age_months is None
        assert room.proposed_policy_from is room.proposed_policy_until is None
        assert DaycareAttendance.objects.count() == 2
        assert DaycareRelease.objects.get(pk=historical_ids[1]).attendance_id == historical_ids[0]
        assert AuditLog.objects.get(pk=historical_ids[2]).object_id == str(historical_ids[1])
    finally:
        MigrationExecutor(connection).migrate(final_targets)
