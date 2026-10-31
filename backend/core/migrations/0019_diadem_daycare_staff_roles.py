"""Declare explicit standalone childcare roles and permissions; no legacy access grant.

A HEAD_OF_SCHOOL or Extended Care grant never silently authorizes Diadem
check-in. Permissions are explicit and tenant-scoped via existing UserRole.
"""
from django.db import migrations, models


def seed_diadem_roles(apps, schema_editor):
    Permission = apps.get_model("core", "CrownPermission")
    RolePermission = apps.get_model("core", "RolePermission")
    rules = {
        "diadem.daycare.view": ("DAYCARE_DIRECTOR", "DAYCARE_STAFF"),
        "diadem.daycare.checkin": ("DAYCARE_DIRECTOR", "DAYCARE_STAFF"),
    }
    for code, roles in rules.items():
        permission, _ = Permission.objects.get_or_create(
            code=code, defaults={"description": "Tenant-scoped standalone Diadem childcare operations"},
        )
        for role in roles:
            RolePermission.objects.get_or_create(role_code=role, permission=permission)


class Migration(migrations.Migration):
    dependencies = [("core", "0018_student_health_permissions")]
    operations = [
        migrations.AlterField(
            model_name="userrole", name="role_code",
            field=models.CharField(max_length=50, choices=[
                ("HEAD_OF_SCHOOL", "Head of School"),
                ("AID_DIRECTOR", "Aid Director"),
                ("FINANCE_DIRECTOR", "Finance Director"),
                ("REGISTRAR", "Registrar"),
                ("TEACHER", "Teacher"),
                ("PARENT", "Parent"),
                ("STUDENT", "Student"),
                ("SUPPORT", "Support"),
                ("DAYCARE_DIRECTOR", "Diadem Daycare Director"),
                ("DAYCARE_STAFF", "Diadem Daycare Staff"),
            ]),
        ),
        migrations.RunPython(seed_diadem_roles, migrations.RunPython.noop),
    ]
