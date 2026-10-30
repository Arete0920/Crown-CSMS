"""Enable school-scoped camp grants without a staff or superuser bypass."""
from django.db import migrations


DEFAULT_ROLES = ("HEAD_OF_SCHOOL", "head_of_school", "school_admin")
CAMP_PERMISSIONS = (
    ("summer_camp.view", "View school-scoped summer camp operations"),
    ("summer_camp.edit", "Edit school-scoped summer camp operations"),
)


def seed_summer_camp_permissions(apps, schema_editor):
    permission_model = apps.get_model("core", "CrownPermission")
    role_permission_model = apps.get_model("core", "RolePermission")
    for code, description in CAMP_PERMISSIONS:
        permission, _ = permission_model.objects.get_or_create(
            code=code, defaults={"description": description},
        )
        for role_code in DEFAULT_ROLES:
            role_permission_model.objects.get_or_create(
                role_code=role_code, permission=permission,
            )


def unseed_summer_camp_permissions(apps, schema_editor):
    # Do not revoke potentially pre-existing or subsequently granted RBAC
    # assignments when rolling back a schema-independent seed migration.
    # Operators must explicitly review any grant-removal decision.
    return


class Migration(migrations.Migration):
    dependencies = [("core", "0018_student_health_permissions")]

    operations = [
        migrations.RunPython(seed_summer_camp_permissions, unseed_summer_camp_permissions),
    ]
