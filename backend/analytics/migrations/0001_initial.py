from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='CustomerHealth',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('school_id', models.UUIDField(db_index=True, unique=True)),
                ('login_frequency_score', models.IntegerField(default=0)),
                ('payment_failure_score', models.IntegerField(default=0)),
                ('support_ticket_score', models.IntegerField(default=0)),
                ('overall_score', models.IntegerField(default=0)),
                ('computed_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['school_id']},
        ),
    ]
