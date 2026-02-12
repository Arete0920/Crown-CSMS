# Generated manually on 2026-02-12
# Data migration: Auto-create missing assignments and link GradeEntry FK

from django.db import migrations
from django.db.models import Min


def forwards(apps, schema_editor):
    """
    Populate GradeEntry.assignment FK by:
    1. Matching existing Assignment records (section + name)
    2. Auto-creating missing Assignment records for orphan GradeEntry rows
    3. Linking all GradeEntry records to their Assignment
    
    For auto-created assignments, we:
    - Get or create a "Gradebook" category per section
    - Use MIN(points_possible) from GradeEntry for deterministic values
    - Copy school_id from GradeEntry
    """
    GradeEntry = apps.get_model("gradebook", "GradeEntry")
    Assignment = apps.get_model("academics", "Assignment")
    AssignmentCategory = apps.get_model("academics", "AssignmentCategory")

    db_alias = schema_editor.connection.alias

    # Only deal with rows that have a legacy name but no FK yet
    qs = (
        GradeEntry.objects.using(db_alias)
        .filter(assignment__isnull=True)
        .exclude(assignment_name__isnull=True)
        .exclude(assignment_name__exact="")
    )

    # Build a map of existing Assignments by (section_id, name) for quick lookup
    existing = Assignment.objects.using(db_alias).values_list("section_id", "name", "id")
    assignment_id_by_key = {(section_id, name): a_id for section_id, name, a_id in existing}

    # Build or cache "Gradebook" categories by section_id
    category_by_section = {}

    # Find distinct (section_id, assignment_name) pairs present in GradeEntry
    pairs = (
        qs.values("section_id", "assignment_name")
        .distinct()
    )

    created_categories = 0
    created_assignments = 0
    linked = 0

    for p in pairs.iterator():
        section_id = p["section_id"]
        name = p["assignment_name"].strip()

        key = (section_id, name)
        a_id = assignment_id_by_key.get(key)

        if a_id is None:
            # Get school_id from first GradeEntry with this section
            sample_ge = (
                GradeEntry.objects.using(db_alias)
                .filter(section_id=section_id)
                .values("school_id")
                .first()
            )
            school_id = sample_ge["school_id"]

            # Get or create "Gradebook" category for this section
            if section_id not in category_by_section:
                category, created = AssignmentCategory.objects.using(db_alias).get_or_create(
                    section_id=section_id,
                    name="Gradebook",
                    defaults={
                        "school_id": school_id,
                        "weight_percent": 0,
                        "sort_order": 999,
                        "is_active": True,
                    }
                )
                category_by_section[section_id] = category.id
                if created:
                    created_categories += 1
            
            category_id = category_by_section[section_id]

            # Use a deterministic points_possible: MIN(points_possible) across matching GradeEntry rows
            agg = (
                GradeEntry.objects.using(db_alias)
                .filter(section_id=section_id, assignment_name=p["assignment_name"])
                .aggregate(pp=Min("points_possible"))
            )
            points_possible = agg["pp"] or 0

            # Create the Assignment
            a = Assignment.objects.using(db_alias).create(
                school_id=school_id,
                section_id=section_id,
                category_id=category_id,
                name=name,
                points_possible=points_possible,
                is_published=True,
            )
            a_id = a.id
            assignment_id_by_key[key] = a_id
            created_assignments += 1

        # Link all GradeEntry rows for this pair
        updated = (
            GradeEntry.objects.using(db_alias)
            .filter(section_id=section_id, assignment_name=p["assignment_name"], assignment__isnull=True)
            .update(assignment_id=a_id)
        )
        linked += updated

    print(f"[gradebook 0003] created categories: {created_categories}, created assignments: {created_assignments}, linked GradeEntry rows: {linked}")


def backwards(apps, schema_editor):
    """
    Reverse: unlink GradeEntry FKs (don't delete Assignments - they may be referenced elsewhere)
    """
    GradeEntry = apps.get_model("gradebook", "GradeEntry")
    db_alias = schema_editor.connection.alias
    GradeEntry.objects.using(db_alias).update(assignment=None)


class Migration(migrations.Migration):
    dependencies = [
        ('gradebook', '0002_gradeentry_assignment'),
        ('academics', '0036_remove_section_teacher_id_section_teacher'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
