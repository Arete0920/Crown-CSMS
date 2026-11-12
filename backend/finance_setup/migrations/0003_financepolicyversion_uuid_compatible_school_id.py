# Preserve legacy integer school identifiers as inert text while permitting
# canonical UUID school identifiers on all authenticated Finance Setup requests.
# Historical integer rows are never silently assigned to a UUID school.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("finance_setup", "0002_alter_discountpolicy_max_discount_percent_bp_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="financepolicyversion",
            name="school_id",
            field=models.CharField(db_index=True, max_length=36),
        ),
    ]
