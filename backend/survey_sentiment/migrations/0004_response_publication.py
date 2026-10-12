from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("survey_sentiment", "0003_publication_snapshots")]

    operations = [
        migrations.AddField(
            model_name="surveyresponse",
            name="publication",
            field=models.ForeignKey(
                to="survey_sentiment.surveypublication",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="responses",
                null=True,
                blank=True,
            ),
        ),
    ]
