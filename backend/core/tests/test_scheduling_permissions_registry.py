from io import StringIO

import pytest
from django.core.management import call_command

from core.models import CrownPermission, RolePermission

pytestmark = pytest.mark.django_db

SCHEDULING_CODES = {
    "scheduling.view",
    "scheduling.configure",
    "scheduling.edit",
    "scheduling.publish",
}


def test_seed_permissions_registers_scheduling_codes_and_current_roles():
    call_command("seed_permissions", stdout=StringIO())

    assert set(
        CrownPermission.objects.filter(code__in=SCHEDULING_CODES).values_list("code", flat=True)
    ) == SCHEDULING_CODES

    for role_code in ("HEAD_OF_SCHOOL", "REGISTRAR"):
        assert set(
            RolePermission.objects.filter(
                role_code=role_code,
                permission__code__in=SCHEDULING_CODES,
            ).values_list("permission__code", flat=True)
        ) == SCHEDULING_CODES
