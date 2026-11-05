"""Configuration drafts require an explicit director permission, not staff access."""
from django.db import migrations


def seed(apps, schema_editor):
    permission, _ = apps.get_model("core", "CrownPermission").objects.get_or_create(
        code="diadem.daycare.configure",
        defaults={"description": "Create inactive Diadem center and room configuration"},
    )
    apps.get_model("core", "RolePermission").objects.get_or_create(
        role_code="DAYCARE_DIRECTOR", permission=permission,
    )


class Migration(migrations.Migration):
    dependencies = [("core", "0021_diadem_custody_release_permission")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
