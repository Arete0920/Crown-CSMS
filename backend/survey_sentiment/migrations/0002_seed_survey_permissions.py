from django.db import migrations


SURVEY_PERMISSIONS = (
    ("survey.view", "View school survey definitions and questions"),
    ("survey.edit", "Create and edit school survey drafts"),
)
SURVEY_ADMIN_ROLES = ("HEAD_OF_SCHOOL", "head_of_school", "school_admin")


def seed_survey_permissions(apps, schema_editor):
    CrownPermission = apps.get_model("core", "CrownPermission")
    RolePermission = apps.get_model("core", "RolePermission")
    for code, description in SURVEY_PERMISSIONS:
        permission, _ = CrownPermission.objects.get_or_create(
            code=code, defaults={"description": description},
        )
        for role in SURVEY_ADMIN_ROLES:
            RolePermission.objects.get_or_create(role_code=role, permission=permission)


def unseed_survey_permissions(apps, schema_editor):
    CrownPermission = apps.get_model("core", "CrownPermission")
    RolePermission = apps.get_model("core", "RolePermission")
    for code, _ in SURVEY_PERMISSIONS:
        permission = CrownPermission.objects.filter(code=code).first()
        if permission is not None:
            RolePermission.objects.filter(permission=permission, role_code__in=SURVEY_ADMIN_ROLES).delete()
            if not RolePermission.objects.filter(permission=permission).exists():
                permission.delete()


class Migration(migrations.Migration):
    dependencies = [("survey_sentiment", "0001_initial")]

    operations = [migrations.RunPython(seed_survey_permissions, unseed_survey_permissions)]
