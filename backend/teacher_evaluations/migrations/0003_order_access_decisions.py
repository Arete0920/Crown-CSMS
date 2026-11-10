"""Order school-scoped evaluation access decisions without trusting clock or UUID."""

import django.db.models
from django.db import migrations, models


def reject_unreviewed_legacy_history(apps, schema_editor):
    access = apps.get_model("teacher_evaluations", "TeacherEvaluationAccessEvent")
    if access.objects.using(schema_editor.connection.alias).exists():
        raise RuntimeError(
            "Existing teacher-evaluation access events require an independently "
            "reviewed decision-order conversion. Refusing to guess their order."
        )


class Migration(migrations.Migration):
    dependencies = [
        ("teacher_evaluations", "0002_access_events"),
    ]

    operations = [
        migrations.RunPython(
            reject_unreviewed_legacy_history,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AddField(
            model_name="teacherevaluationaccessevent",
            name="decision_version",
            field=models.PositiveBigIntegerField(default=0, editable=False),
        ),
        migrations.AlterModelOptions(
            name="teacherevaluationaccessevent",
            options={"ordering": ["-decision_version"]},
        ),
        migrations.RemoveIndex(
            model_name="teacherevaluationaccessevent",
            name="te_access_scope_idx",
        ),
        migrations.AddConstraint(
            model_name="teacherevaluationaccessevent",
            constraint=models.UniqueConstraint(
                fields=("school", "user", "permission_code", "decision_version"),
                name="te_access_version_once",
            ),
        ),
        migrations.AddConstraint(
            model_name="teacherevaluationaccessevent",
            constraint=models.CheckConstraint(
                condition=models.Q(decision_version__gte=1),
                name="te_access_version_positive",
            ),
        ),
    ]
