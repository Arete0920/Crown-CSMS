from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admissions", "0003_alter_admissionsapplication_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="admissionsauditevent",
            name="entity_id",
            field=models.CharField(max_length=64),
        ),
    ]
