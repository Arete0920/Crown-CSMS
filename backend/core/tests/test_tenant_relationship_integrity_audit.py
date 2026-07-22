import json
import uuid
from io import StringIO

import pytest
from django.core.management import CommandError, call_command
from django.db import connection

from core.management.commands import audit_tenant_relationship_integrity as audit_command
from core.models import School
from households.models import Guardian, Household


@pytest.mark.django_db
def test_audit_reports_cross_tenant_household_relationship():
    school_a = School.objects.create(name="School A")
    school_b = School.objects.create(name="School B")
    household = Household.objects.create(school_id=school_a.id, name="Family")
    Guardian.objects.create(
        school_id=school_b.id,
        household=household,
        first_name="Pat",
        last_name="Guardian",
    )

    stdout = StringIO()
    call_command("audit_tenant_relationship_integrity", stdout=stdout)
    payload = json.loads(stdout.getvalue())
    guardian_audit = next(
        item
        for item in payload["relationships"]
        if item["model"] == "households.Guardian" and item["relation"] == "household"
    )

    assert payload["mode"] == "read_only"
    assert payload["production_authorization"] is False
    assert payload["schema_version"] == 4
    assert guardian_audit["parent_tenant_mismatch_count"] == 1
    assert guardian_audit["identity_partition"]["tenant_mismatch"]["count"] == 1
    assert guardian_audit["identity_partition"]["dangling_parent"]["count"] == 0
    assert guardian_audit["identity_partition"]["unexplained"]["count"] == 0
    assert guardian_audit["identity_partition"]["equation_holds"] is True
    assert payload["totals"]["unique_anomaly_rows"] == 1


@pytest.mark.django_db
def test_audit_identity_partition_is_exclusive_and_checksum_backed():
    school = School.objects.create(name="School A")
    household = Household.objects.create(school_id=school.id, name="Family")
    guardian = Guardian.objects.create(
        school_id=school.id,
        household=household,
        first_name="Pat",
        last_name="Guardian",
    )

    stdout = StringIO()
    call_command(
        "audit_tenant_relationship_integrity",
        include_ids=True,
        stdout=stdout,
    )
    payload = json.loads(stdout.getvalue())
    guardian_audit = next(
        item
        for item in payload["relationships"]
        if item["model"] == "households.Guardian" and item["relation"] == "household"
    )
    partition = guardian_audit["identity_partition"]

    assert partition["input"]["ids"] == [str(guardian.pk)]
    assert len(partition["input"]["sha256"]) == 64
    assert partition["normal"]["ids"] == [str(guardian.pk)]
    assert partition["invalid_tenant"]["count"] == 0
    assert partition["null_parent"]["count"] == 0
    assert partition["dangling_parent"]["count"] == 0
    assert partition["tenant_mismatch"]["count"] == 0
    assert partition["unexplained"]["count"] == 0
    assert partition["accounted_unique_count"] == 1
    assert partition["exclusive_overlap_count"] == 0
    assert partition["equation_holds"] is True


@pytest.mark.django_db(transaction=True)
def test_audit_classifies_dangling_parent_as_anomaly(monkeypatch):
    school = School.objects.create(name="School A")
    guardian_id = uuid.uuid4()
    missing_household_id = uuid.uuid4()

    with connection.constraint_checks_disabled():
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO guardian "
                "(id, school_id, household_id, first_name, last_name, email, phone, "
                "is_primary, created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                [
                    str(guardian_id),
                    str(school.id),
                    str(missing_household_id),
                    "Dangling",
                    "Guardian",
                    "",
                    "",
                    False,
                ],
            )

    monkeypatch.setattr(
        audit_command,
        "RELATIONSHIPS",
        (("households.Guardian", "household__school_id", "household"),),
    )
    stdout = StringIO()
    call_command(
        "audit_tenant_relationship_integrity",
        include_ids=True,
        stdout=stdout,
    )
    payload = json.loads(stdout.getvalue())
    relationship = payload["relationships"][0]

    assert relationship["dangling_parent_count"] == 1
    assert relationship["identity_partition"]["dangling_parent"]["ids"] == [str(guardian_id)]
    assert relationship["identity_partition"]["normal"]["count"] == 0
    assert relationship["identity_partition"]["unexplained"]["count"] == 0
    assert relationship["identity_partition"]["equation_holds"] is True
    assert payload["totals"]["unique_dangling_parent_rows"] == 1
    assert payload["totals"]["unique_anomaly_rows"] == 1

    with pytest.raises(CommandError, match="dangling parent row"):
        call_command(
            "audit_tenant_relationship_integrity",
            fail_on_anomaly=True,
            stdout=StringIO(),
        )


@pytest.mark.django_db
def test_audit_fail_on_anomaly_is_nonzero_and_non_destructive():
    school_a = School.objects.create(name="School A")
    school_b = School.objects.create(name="School B")
    household = Household.objects.create(school_id=school_a.id, name="Family")
    guardian = Guardian.objects.create(
        school_id=school_b.id,
        household=household,
        first_name="Pat",
        last_name="Guardian",
    )

    with pytest.raises(CommandError, match="unique anomaly row"):
        call_command(
            "audit_tenant_relationship_integrity",
            fail_on_anomaly=True,
            stdout=StringIO(),
        )

    guardian.refresh_from_db()
    assert guardian.school_id == school_b.id
    assert guardian.household_id == household.id


@pytest.mark.django_db
def test_audit_accepts_tenant_consistent_household_relationships():
    school = School.objects.create(name="School A")
    household = Household.objects.create(school_id=school.id, name="Family")
    Guardian.objects.create(
        school_id=school.id,
        household=household,
        first_name="Pat",
        last_name="Guardian",
    )

    stdout = StringIO()
    call_command(
        "audit_tenant_relationship_integrity",
        fail_on_anomaly=True,
        stdout=stdout,
    )
    payload = json.loads(stdout.getvalue())

    assert payload["totals"]["mismatches"] == 0
    assert payload["totals"]["invalid_school_ids"] == 0
    assert payload["totals"]["dangling_parents"] == 0
    assert payload["totals"]["unique_anomaly_rows"] == 0
    assert payload["totals"]["all_partition_equations_hold"] is True


def test_relationship_registry_covers_campaign3_and_accounting_omissions():
    relationships = set(audit_command.RELATIONSHIPS)
    expected = {
        ("applications.EnrollmentContract", "amended_from__school_id", "amended_from"),
        ("academics.Grade", "submission__school_id", "submission"),
        ("academics.MasteryRecord", "student__school_id", "student"),
        ("academics.TranscriptEntry", "course__school_id", "course"),
        ("home_academy.OfferingEnrollment", "offering__school_id", "offering"),
        ("accounting.LedgerEntry", "journal_entry__tenant_id", "journal_entry"),
        ("accounting.LedgerEntry", "account__tenant_id", "account"),
        ("accounting.JournalEntry", "reversal_of__tenant_id", "reversal_of"),
    }
    assert expected <= relationships


@pytest.mark.django_db
def test_accounting_tenant_relationships_are_reconciled_and_explicitly_unverified(monkeypatch):
    from apps.accounting.models import JournalEntry, LedgerAccount, LedgerEntry

    tenant_id = uuid.uuid4()
    journal = JournalEntry.objects.create(
        tenant_id=tenant_id,
        correlation_id=uuid.uuid4(),
        source_system="test",
        created_by=uuid.uuid4(),
        description="test",
    )
    account = LedgerAccount.objects.create(
        tenant_id=tenant_id,
        code="1000",
        name="Cash",
        account_type="ASSET",
    )
    LedgerEntry.objects.create(
        tenant_id=tenant_id,
        journal_entry=journal,
        account=account,
        entry_type="DEBIT",
        amount="10.00",
        currency="USD",
    )
    monkeypatch.setattr(
        audit_command,
        "RELATIONSHIPS",
        (("accounting.LedgerEntry", "journal_entry__tenant_id", "journal_entry"),),
    )

    stdout = StringIO()
    call_command("audit_tenant_relationship_integrity", stdout=stdout)
    payload = json.loads(stdout.getvalue())
    relationship = payload["relationships"][0]

    assert relationship["tenant_field"] == "tenant_id"
    assert relationship["tenant_anchor"] == "tenant"
    assert relationship["tenant_field_type"] == "UUIDField"
    assert relationship["tenant_authority_verified"] is False
    assert relationship["identity_partition"]["normal"]["count"] == 1
    assert relationship["identity_partition"]["equation_holds"] is True
    assert payload["totals"]["unverified_tenant_authority_relationships"] == 1


@pytest.mark.django_db
def test_overall_anomaly_rows_are_deduplicated_across_relationships(monkeypatch):
    school = School.objects.create(name="School A")
    household = Household.objects.create(school_id=school.id, name="Family")
    Guardian.objects.create(
        school_id="00000000-0000-0000-0000-000000000099",
        household=household,
        first_name="Pat",
        last_name="Guardian",
    )
    monkeypatch.setattr(
        audit_command,
        "RELATIONSHIPS",
        (
            ("households.Guardian", "household__school_id", "household"),
            ("households.Guardian", "household__school_id", "household"),
        ),
    )

    stdout = StringIO()
    call_command("audit_tenant_relationship_integrity", stdout=stdout)
    payload = json.loads(stdout.getvalue())

    assert payload["totals"]["invalid_school_ids"] == 2
    assert payload["totals"]["unique_invalid_school_rows"] == 1
    assert payload["totals"]["unique_anomaly_rows"] == 1


@pytest.mark.django_db
def test_home_academy_integer_tenant_family_is_explicitly_unverified(monkeypatch):
    from home_academy.models import HomeAcademyEnrollment, HomeAcademyProgram

    program = HomeAcademyProgram.objects.create(
        school_id=101,
        public_program_name="Home Academy",
    )
    HomeAcademyEnrollment.objects.create(
        school_id=101,
        student_id=501,
        program=program,
    )
    monkeypatch.setattr(
        audit_command,
        "RELATIONSHIPS",
        (("home_academy.HomeAcademyEnrollment", "program__school_id", "program"),),
    )

    stdout = StringIO()
    call_command("audit_tenant_relationship_integrity", stdout=stdout)
    payload = json.loads(stdout.getvalue())
    relationship = payload["relationships"][0]

    assert relationship["tenant_field_type"] == "IntegerField"
    assert relationship["tenant_authority_verified"] is False
    assert relationship["identity_partition"]["equation_holds"] is True

    with pytest.raises(CommandError, match="unresolved tenant authority family"):
        call_command(
            "audit_tenant_relationship_integrity",
            fail_on_unverified_authority=True,
            stdout=StringIO(),
        )
