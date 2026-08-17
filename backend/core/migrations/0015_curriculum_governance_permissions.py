from django.db import migrations


PERMISSIONS = {
    "curriculum.view": "View curriculum maps and governed versions",
    "curriculum.edit": "Create and edit draft curriculum maps, units, and lessons",
    "curriculum.publish": "Approve, publish, and retire governed curriculum versions",
}

VIEW_ROLES = (
    "HEAD_OF_SCHOOL",
    "REGISTRAR",
    "TEACHER",
    "head_of_school",
    "registrar",
    "teacher",
    "school_admin",
)
GOVERNANCE_ROLES = (
    "HEAD_OF_SCHOOL",
    "REGISTRAR",
    "head_of_school",
    "registrar",
    "school_admin",
)


def seed_curriculum_governance_permissions(apps, schema_editor):
    CrownPermission = apps.get_model("core", "CrownPermission")
    RolePermission = apps.get_model("core", "RolePermission")

    permissions = {}
    for code, description in PERMISSIONS.items():
        permission, _ = CrownPermission.objects.get_or_create(
            code=code,
            defaults={"description": description},
        )
        permissions[code] = permission

    for role_code in VIEW_ROLES:
        RolePermission.objects.get_or_create(
            role_code=role_code,
            permission=permissions["curriculum.view"],
        )

    for role_code in GOVERNANCE_ROLES:
        for code in ("curriculum.edit", "curriculum.publish"):
            RolePermission.objects.get_or_create(
                role_code=role_code,
                permission=permissions[code],
            )


def remove_curriculum_governance_permissions(apps, schema_editor):
    CrownPermission = apps.get_model("core", "CrownPermission")
    RolePermission = apps.get_model("core", "RolePermission")

    permissions = CrownPermission.objects.filter(code__in=PERMISSIONS.keys())
    RolePermission.objects.filter(permission__in=permissions).delete()
    permissions.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0014_gradebook_edit_permission"),
    ]

    operations = [
        migrations.RunPython(
            seed_curriculum_governance_permissions,
            remove_curriculum_governance_permissions,
        ),
    ]
