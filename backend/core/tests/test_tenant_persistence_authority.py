"""Tenant write isolation across instance and bulk ORM entry points."""
import uuid

import pytest
from django.core.management import call_command, CommandError

from classroom.models import Classroom
from core.models import School
from core.tenant_models import (
    clear_current_school, get_current_school, tenant_context,
    TenantContextRequired, TenantWriteViolation,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def schools():
    clear_current_school()
    yield School.objects.create(name="Persistence A"), School.objects.create(name="Persistence B")
    clear_current_school()


def row_in(school):
    with tenant_context(school):
        return Classroom.objects.create(name=f"Room-{uuid.uuid4()}")


def test_missing_context_denies_create_update_and_instance_delete(schools):
    school, _ = schools
    row = row_in(school)
    for operation in (
        lambda: Classroom.objects.create(name="Unscoped", school=school),
        lambda: row.save(), lambda: row.delete(),
    ):
        with pytest.raises(TenantContextRequired):
            operation()
    assert Classroom._base_manager.filter(pk=row.pk).exists()
    assert not Classroom._base_manager.filter(name="Unscoped").exists()


def test_school_cannot_be_reparented_through_instance_save(schools):
    a, b = schools
    row = row_in(a)
    row.school = b
    with tenant_context(b), pytest.raises(TenantWriteViolation):
        row.save()
    assert Classroom._base_manager.get(pk=row.pk).school_id == a.id


def test_wrong_context_cannot_delete_instance(schools):
    a, b = schools
    row = row_in(a)
    with tenant_context(b), pytest.raises(TenantWriteViolation):
        row.delete()
    assert Classroom._base_manager.filter(pk=row.pk).exists()


def test_missing_context_denies_bulk_create_and_bulk_update(schools):
    a, _ = schools
    row = row_in(a)
    with pytest.raises(TenantContextRequired):
        Classroom.objects.bulk_create([Classroom(name="Bulk", school=a)])
    with pytest.raises(TenantContextRequired):
        Classroom.objects.bulk_update([row], ["name"])


def test_bulk_create_rejects_mixed_tenants_before_any_insert(schools):
    a, b = schools
    with tenant_context(a), pytest.raises(TenantWriteViolation):
        Classroom.objects.bulk_create([Classroom(name="Valid", school=a), Classroom(name="Wrong", school=b)])
    assert Classroom._base_manager.count() == 0


def test_bulk_update_rejects_mixed_tenants_before_any_update(schools):
    a, b = schools
    ra, rb = row_in(a), row_in(b)
    before = ra.name
    ra.name, rb.name = "Changed A", "Changed B"
    with tenant_context(a), pytest.raises(TenantWriteViolation):
        Classroom.objects.bulk_update([ra, rb], ["name"])
    assert Classroom._base_manager.get(pk=ra.pk).name == before


def test_queryset_mutations_cannot_reparent_school(schools):
    a, b = schools
    row = row_in(a)
    with tenant_context(a):
        for values in ({"school": b}, {"school_id": b.id}):
            with pytest.raises(TenantWriteViolation):
                Classroom.objects.update(**values)
        with pytest.raises(TenantWriteViolation):
            Classroom.objects.bulk_update([row], ["school"])
    assert Classroom._base_manager.get(pk=row.pk).school_id == a.id


def test_explicit_tenant_bulk_lifecycle_and_cleanup(schools):
    a, b = schools
    with tenant_context(a):
        rows = Classroom.objects.bulk_create([Classroom(name="Bulk A"), Classroom(name="Bulk B")])
        rows[0].name = "Updated"
        assert Classroom.objects.bulk_update([rows[0]], ["name"]) == 1
        with tenant_context(b):
            assert Classroom.objects.count() == 0
        assert get_current_school().id == a.id
        rows[0].delete()
        assert Classroom.objects.count() == 1
    assert get_current_school() is None


@pytest.mark.parametrize("command", ["seed_classroom_demo", "seed_graduation_demo"])
def test_seed_rejects_ambiguous_and_invalid_school_without_context_leak(schools, command):
    with pytest.raises(CommandError):
        call_command(command)
    with pytest.raises(CommandError):
        call_command(command, school_id=str(uuid.uuid4()))
    assert get_current_school() is None


def test_graduation_seed_is_explicit_and_idempotent(schools):
    from graduation.models import GraduationRule
    a, b = schools
    call_command("seed_graduation_demo", school_id=str(a.id))
    call_command("seed_graduation_demo", school_id=str(a.id))
    assert GraduationRule._base_manager.filter(school=a).count() == 1
    assert GraduationRule._base_manager.filter(school=b).count() == 0
    assert get_current_school() is None
