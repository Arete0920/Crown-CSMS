import uuid
from django.core.management.base import BaseCommand
from django.db import connection
from datetime import datetime

# UUID without hyphens (32 chars) to match DB char(32) columns
DEMO_SCHOOL_ID  = "00000000000000000000000000000001"


def _run_sql(cursor, sql: str, params=None):
    exec_fn = getattr(cursor, "execute")
    return exec_fn(sql, [] if params is None else params)

def db_column_names(table_name):
    """Get actual column names from the database table."""
    with connection.cursor() as cursor:
        _run_sql(cursor, f"PRAGMA table_info({table_name})")
        return {row[1] for row in cursor.fetchall()}


class Command(BaseCommand):
    help = "Seed demo Sections using raw SQL (bypasses ORM to avoid schema drift)."

    def add_arguments(self, parser):
        parser.add_argument("--wipe", action="store_true")
        parser.add_argument("--term", default="2025-26 S1")

    def handle(self, *args, **opts):
        term = opts["term"]
        now = datetime.now().isoformat()

        with connection.cursor() as cursor:
            course_cols = db_column_names("course")
            section_cols = db_column_names("section")

            if opts["wipe"]:
                # Wipe sections first (FK constraint)
                if "school_id" in section_cols:
                    _run_sql(cursor, "DELETE FROM section WHERE school_id = %s", [DEMO_SCHOOL_ID])
                else:
                    _run_sql(cursor, "DELETE FROM section")

                # Wipe demo courses
                if "school_id" in course_cols:
                    _run_sql(cursor, "DELETE FROM course WHERE school_id = %s AND code LIKE %s", [DEMO_SCHOOL_ID, "DEMO-%"])

                self.stdout.write(self.style.WARNING("Wiped existing demo data."))

            # Create courses with meaningful names
            courses = [
                ("DEMO-ALG1", "Algebra I"),
                ("DEMO-ENG9", "English 9"),
                ("DEMO-BIO", "Biology"),
            ]

            course_map = {}
            for code, name in courses:
                course_id = str(uuid.uuid4()).replace("-", "")
                cols = ["id", "school_id", "code", "name"]
                vals = [course_id, DEMO_SCHOOL_ID, code, name]

                if "created_at" in course_cols:
                    cols.append("created_at")
                    vals.append(now)
                if "updated_at" in course_cols:
                    cols.append("updated_at")
                    vals.append(now)

                placeholders = ", ".join(["%s"] * len(cols))
                _run_sql(cursor, f"INSERT INTO course ({', '.join(cols)}) VALUES ({placeholders})", vals)
                course_map[code] = course_id
                self.stdout.write(f"Created course: {name} ({code})")

            # Create sections linked to courses
            specs = [
                ("DEMO-ALG1", "Algebra I"),
                ("DEMO-ENG9", "English 9"),
                ("DEMO-BIO", "Biology"),
            ]

            created = 0
            for course_code, course_name in specs:
                section_id = str(uuid.uuid4()).replace("-", "")
                course_id = course_map[course_code]

                cols = ["id", "school_id", "course_id", "term"]
                vals = [section_id, DEMO_SCHOOL_ID, course_id, term]

                if "created_at" in section_cols:
                    cols.append("created_at")
                    vals.append(now)
                if "updated_at" in section_cols:
                    cols.append("updated_at")
                    vals.append(now)
                if "teacher_name" in section_cols:
                    cols.append("teacher_name")
                    vals.append(f"Ms. {course_name.split()[0]} Teacher")
                if "grade_band" in section_cols:
                    cols.append("grade_band")
                    vals.append("9-12")

                placeholders = ", ".join(["%s"] * len(cols))
                _run_sql(cursor, f"INSERT INTO section ({', '.join(cols)}) VALUES ({placeholders})", vals)
                created += 1

            self.stdout.write(self.style.SUCCESS(f"Seeded {created} Section rows with meaningful course names."))
