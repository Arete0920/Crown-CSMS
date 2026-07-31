from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("households", "0008_households_guardians_students"),
    ]

    operations = [
        migrations.AddField(
            model_name="guardian",
            name="account",
            field=models.OneToOneField(
                blank=True,
                help_text="Canonical authenticated account for Parent360 access. Email is not authorization.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="households_guardian",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
