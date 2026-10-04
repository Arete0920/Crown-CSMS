from django.db import migrations


def clinical_permissions(apps, schema_editor):
    Permission = apps.get_model('core', 'CrownPermission')
    RolePermission = apps.get_model('core', 'RolePermission')
    for code in ('student_health.view', 'student_health.edit'):
        permission, _ = Permission.objects.get_or_create(code=code, defaults={'description': 'Restricted school clinical record access'})
        for role in ('nurse', 'health', 'health_office', 'NURSE', 'HEALTH_OFFICE'):
            RolePermission.objects.get_or_create(role_code=role, permission=permission)


class Migration(migrations.Migration):
    dependencies = [('core', '0017_seed_marketing_edit_permission')]
    operations = [migrations.RunPython(clinical_permissions, migrations.RunPython.noop)]
