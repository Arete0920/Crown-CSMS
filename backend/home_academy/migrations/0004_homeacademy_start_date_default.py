from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ("home_academy", "0003_uuid_identity_spine"),
    ]

    operations = [
        migrations.AlterField(
            model_name="homeacademyenrollment",
            name="start_date",
            field=models.DateField(default=timezone.localdate),
        ),
    ]
