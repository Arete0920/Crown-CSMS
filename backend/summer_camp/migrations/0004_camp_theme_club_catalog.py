"""Camp theme weeks and reusable club/elective scheduling."""

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("summer_camp", "0003_staff_credential_review_evidence"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="summercampsession",
            name="theme_title",
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name="summercampsession",
            name="theme_story",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="summercampsession",
            name="scripture_reference",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="summercampsession",
            name="virtue_focus",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="summercampsession",
            name="special_event",
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.CreateModel(
            name="SummerCampClub",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.SlugField(max_length=72)),
                ("name", models.CharField(max_length=160)),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("STEM", "STEM"),
                            ("ARTS", "Arts"),
                            ("SPORTS", "Sports"),
                            ("COOKING", "Cooking"),
                            ("LEADERSHIP", "Leadership"),
                            ("SERVICE", "Service"),
                            ("FAITH", "Faith"),
                            ("READING", "Reading"),
                            ("OTHER", "Other"),
                        ],
                        default="OTHER",
                        max_length=24,
                    ),
                ),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "school",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="summer_camp_clubs",
                        to="core.school",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SummerCampClubOffering",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("weekdays", models.JSONField(default=list)),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
                ("location", models.CharField(blank=True, max_length=120)),
                ("capacity", models.PositiveIntegerField(default=0)),
                ("waitlist_capacity", models.PositiveIntegerField(default=0)),
                ("optional_charge_cents", models.PositiveIntegerField(default=0)),
                (
                    "status",
                    models.CharField(
                        choices=[("DRAFT", "Draft"), ("PUBLISHED", "Published")],
                        default="DRAFT",
                        max_length=16,
                    ),
                ),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "club",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="offerings",
                        to="summer_camp.summercampclub",
                    ),
                ),
                (
                    "instructor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="summer_camp_club_offerings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "school",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="summer_camp_club_offerings",
                        to="core.school",
                    ),
                ),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="club_offerings",
                        to="summer_camp.summercampsession",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SummerCampClubSelection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ENROLLED", "Enrolled"),
                            ("WAITLISTED", "Waitlisted"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        default="ENROLLED",
                        max_length=16,
                    ),
                ),
                ("waitlist_position", models.PositiveIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "enrollment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="club_selections",
                        to="summer_camp.summercampenrollment",
                    ),
                ),
                (
                    "offering",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="selections",
                        to="summer_camp.summercampcluboffering",
                    ),
                ),
                (
                    "school",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="summer_camp_club_selections",
                        to="core.school",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="summercampclub",
            constraint=models.UniqueConstraint(fields=("school", "code"), name="camp_club_school_code_uq"),
        ),
        migrations.AddIndex(
            model_name="summercampclub",
            index=models.Index(fields=["school", "is_active"], name="camp_club_school_active_idx"),
        ),
        migrations.AddConstraint(
            model_name="summercampcluboffering",
            constraint=models.UniqueConstraint(
                fields=("session", "club", "start_time"),
                name="camp_club_offering_session_time_uq",
            ),
        ),
        migrations.AddIndex(
            model_name="summercampcluboffering",
            index=models.Index(
                fields=["school", "session", "status"],
                name="camp_offer_school_session_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="summercampclubselection",
            constraint=models.UniqueConstraint(
                fields=("offering", "enrollment"),
                name="camp_club_selection_uq",
            ),
        ),
        migrations.AddIndex(
            model_name="summercampclubselection",
            index=models.Index(
                fields=["school", "offering", "status"],
                name="camp_select_school_offer_idx",
            ),
        ),
    ]
