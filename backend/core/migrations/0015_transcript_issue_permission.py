from django.db import migrations


PERMISSION_CODE = "transcript.issue"
ROLE_CODES = ("HEAD_OF_SCHOOL", "REGISTRAR")


def add_permission(apps, schema_editor):
    CrownPermission = apps.get_model("core", "CrownPermission")
    RolePermission = apps.get_model("core", "RolePermission")

    permission, _ = CrownPermission.objects.get_or_create(
        code=PERMISSION_CODE,
        defaults={"description": "Issue official student transcripts"},
    )
    for role_code in ROLE_CODES:
        RolePermission.objects.get_or_create(
            role_code=role_code,
            permission=permission,
        )


def remove_permission(apps, schema_editor):
    CrownPermission = apps.get_model("core", "CrownPermission")
    RolePermission = apps.get_model("core", "RolePermission")

    permission = CrownPermission.objects.filter(code=PERMISSION_CODE).first()
    if permission is None:
        return
    RolePermission.objects.filter(
        permission=permission,
        role_code__in=ROLE_CODES,
    ).delete()
    permission.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0014_gradebook_edit_permission"),
    ]

    operations = [
        migrations.RunPython(add_permission, remove_permission),
    ]
