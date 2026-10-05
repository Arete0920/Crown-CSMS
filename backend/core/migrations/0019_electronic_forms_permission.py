from django.db import migrations


FORM_MANAGER_ROLES = (
    "HEAD_OF_SCHOOL",
    "head_of_school",
    "school_admin",
    "REGISTRAR",
    "registrar",
    "admissions_manager",
)


def seed_forms_manage(apps, schema_editor):
    CrownPermission = apps.get_model("core", "CrownPermission")
    RolePermission = apps.get_model("core", "RolePermission")
    permission, _ = CrownPermission.objects.get_or_create(
        code="forms.manage",
        defaults={"description": "Create, issue, and manage electronic forms and signature envelopes"},
    )
    for role_code in FORM_MANAGER_ROLES:
        RolePermission.objects.get_or_create(role_code=role_code, permission=permission)


def unseed_forms_manage(apps, schema_editor):
    CrownPermission = apps.get_model("core", "CrownPermission")
    RolePermission = apps.get_model("core", "RolePermission")
    permission = CrownPermission.objects.filter(code="forms.manage").first()
    if permission is None:
        return
    RolePermission.objects.filter(role_code__in=FORM_MANAGER_ROLES, permission=permission).delete()
    permission.delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0018_student_health_permissions")]
    operations = [migrations.RunPython(seed_forms_manage, unseed_forms_manage)]
