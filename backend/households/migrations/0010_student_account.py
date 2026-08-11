from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("households", "0009_guardian_account"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="account",
            field=models.OneToOneField(
                blank=True,
                help_text="Canonical authenticated account for Student self-service. Email is not authorization.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="households_student",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
