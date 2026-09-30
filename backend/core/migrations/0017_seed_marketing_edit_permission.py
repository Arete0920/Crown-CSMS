from django.db import migrations


def seed_marketing_edit(apps, schema_editor):
    CrownPermission = apps.get_model("core", "CrownPermission")
    RolePermission = apps.get_model("core", "RolePermission")
    permission, _ = CrownPermission.objects.get_or_create(
        code="marketing.edit",
        defaults={"description": "Create and manage marketing campaigns and touchpoints"},
    )
    for role_code in (
        "HEAD_OF_SCHOOL",
        "head_of_school",
        "school_admin",
        "marketing",
        "admissions_manager",
    ):
        RolePermission.objects.get_or_create(role_code=role_code, permission=permission)


def unseed_marketing_edit(apps, schema_editor):
    CrownPermission = apps.get_model("core", "CrownPermission")
    RolePermission = apps.get_model("core", "RolePermission")
    permission = CrownPermission.objects.filter(code="marketing.edit").first()
    if permission is not None:
        RolePermission.objects.filter(permission=permission).delete()
        permission.delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0016_seed_extended_care_edit_permission")]

    operations = [migrations.RunPython(seed_marketing_edit, unseed_marketing_edit)]
