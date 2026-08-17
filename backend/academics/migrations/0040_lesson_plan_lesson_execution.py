# Generated for CROWN curriculum consolidation.

import uuid
from django.db import migrations, models
import django.db.models.deletion


def backfill_lesson_plan_links(apps, schema_editor):
    LessonPlan = apps.get_model("academics", "LessonPlan")
    Lesson = apps.get_model("academics", "Lesson")
    LessonPlanLesson = apps.get_model("academics", "LessonPlanLesson")

    for plan in LessonPlan.objects.all().iterator():
        raw_ids = plan.lesson_ids or []
        if not isinstance(raw_ids, list):
            continue

        normalized = []
        for position, raw_id in enumerate(raw_ids, start=1):
            try:
                lesson_id = uuid.UUID(str(raw_id))
            except (TypeError, ValueError, AttributeError):
                continue
            normalized.append((position, lesson_id))

        if not normalized:
            continue

        valid_lessons = {
            lesson.id: lesson
            for lesson in Lesson.objects.filter(
                id__in=[lesson_id for _, lesson_id in normalized],
                school_id=plan.school_id,
                unit__course_id=plan.section.course_id,
            )
        }
        for position, lesson_id in normalized:
            lesson = valid_lessons.get(lesson_id)
            if lesson is None:
                continue
            LessonPlanLesson.objects.get_or_create(
                lesson_plan_id=plan.id,
                lesson_id=lesson.id,
                defaults={
                    "school_id": plan.school_id,
                    "sequence_order": position,
                    "delivery_status": "planned",
                },
            )


class Migration(migrations.Migration):
    dependencies = [
        ("academics", "0039_term_uniq_term_year_code"),
    ]

    operations = [
        migrations.CreateModel(
            name="LessonPlanLesson",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("school_id", models.UUIDField(db_index=True)),
                ("sequence_order", models.PositiveSmallIntegerField(default=1)),
                ("delivery_status", models.CharField(choices=[("planned", "Planned"), ("in_progress", "In progress"), ("taught", "Taught"), ("partial", "Partially taught"), ("skipped", "Skipped"), ("rescheduled", "Rescheduled")], db_index=True, default="planned", max_length=16)),
                ("planned_minutes", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("actual_minutes", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("actual_started_at", models.DateTimeField(blank=True, null=True)),
                ("actual_completed_at", models.DateTimeField(blank=True, null=True)),
                ("completion_notes", models.TextField(blank=True, default="")),
                ("lesson", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lesson_plan_links", to="academics.lesson")),
                ("lesson_plan", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lesson_links", to="academics.lessonplan")),
            ],
            options={
                "db_table": "lesson_plan_lesson",
                "ordering": ["sequence_order", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="lessonplanlesson",
            constraint=models.UniqueConstraint(fields=("lesson_plan", "lesson"), name="uniq_lesson_plan_lesson"),
        ),
        migrations.AddIndex(
            model_name="lessonplanlesson",
            index=models.Index(fields=["school_id", "lesson_plan", "delivery_status"], name="lesson_plan_school__220497_idx"),
        ),
        migrations.AddIndex(
            model_name="lessonplanlesson",
            index=models.Index(fields=["school_id", "lesson"], name="lesson_plan_school__0f2b0d_idx"),
        ),
        migrations.RunPython(backfill_lesson_plan_links, migrations.RunPython.noop),
    ]
