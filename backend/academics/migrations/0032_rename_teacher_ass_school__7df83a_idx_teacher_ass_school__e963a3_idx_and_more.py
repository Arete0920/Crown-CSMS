"""No-op migration.

The index names were aligned in 0031_academics_readonly.
This placeholder remains to avoid rename operations on fresh DBs.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("academics", "0031_academics_readonly"),
    ]

    operations = []
