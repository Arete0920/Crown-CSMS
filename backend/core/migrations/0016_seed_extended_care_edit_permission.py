from django.db import migrations


def seed_extended_care_edit(apps, schema_editor):
    CrownPermission = apps.get_model("core", "CrownPermission")
    RolePermission = apps.get_model("core", "RolePermission")
    permission, _ = CrownPermission.objects.get_or_create(
        code="extended_care.edit",
        defaults={"description": "Create or modify extended-care records"},
    )
    for role_code in ("HEAD_OF_SCHOOL", "head_of_school", "school_admin"):
        RolePermission.objects.get_or_create(role_code=role_code, permission=permission)


def unseed_extended_care_edit(apps, schema_editor):
    CrownPermission = apps.get_model("core", "CrownPermission")
    RolePermission = apps.get_model("core", "RolePermission")
    permission = CrownPermission.objects.filter(code="extended_care.edit").first()
    if permission is None:
        return
    RolePermission.objects.filter(
        role_code__in=("HEAD_OF_SCHOOL", "head_of_school", "school_admin"),
        permission=permission,
    ).delete()
    permission.delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0015_curriculum_governance_permissions")]
    operations = [migrations.RunPython(seed_extended_care_edit, unseed_extended_care_edit)]
