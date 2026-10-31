"""Grant custody handoff only to explicit Diadem roles; not legacy school roles."""
from django.db import migrations


def seed_release_permission(apps, schema_editor):
    Permission = apps.get_model("core", "CrownPermission")
    RolePermission = apps.get_model("core", "RolePermission")
    permission, _ = Permission.objects.get_or_create(
        code="diadem.daycare.release",
        defaults={"description": "Staff-attested, audited child custody release"},
    )
    for role in ("DAYCARE_DIRECTOR", "DAYCARE_STAFF"):
        RolePermission.objects.get_or_create(role_code=role, permission=permission)


class Migration(migrations.Migration):
    dependencies = [("core", "0019_diadem_daycare_staff_roles")]
    operations = [migrations.RunPython(seed_release_permission, migrations.RunPython.noop)]
