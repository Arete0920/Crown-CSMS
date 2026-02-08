"""
Unmanaged adapter models for legacy academics tables.
Schema verified via PRAGMA table_info() on 2026-02-08.

DO NOT run makemigrations on this app.
These models are read-only adapters to existing tables.
"""
from django.db import models


class SectionRow(models.Model):
    """
    Unmanaged read-only adapter for 'section' table.
    
    Verified columns (2026-02-08):
    - created_at: datetime, notnull
    - updated_at: datetime, notnull
    - id: char(32), pk
    - school_id: char(32), notnull
    - term: varchar(24), notnull
    - teacher_name: varchar(120), notnull
    - grade_band: varchar(32), notnull
    - course_id: char(32), notnull
    - term_ref_id: char(32), nullable
    """
    id = models.CharField(max_length=32, primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    school_id = models.CharField(max_length=32, db_index=True)
    course_id = models.CharField(max_length=32)
    term_ref_id = models.CharField(max_length=32, null=True, blank=True)
    term = models.CharField(max_length=24)
    teacher_name = models.CharField(max_length=120)
    grade_band = models.CharField(max_length=32)
    
    class Meta:
        managed = False
        db_table = "section"
        
    def __str__(self):
        return f"SectionRow({self.id[:8]}, {self.term})"


class CourseRow(models.Model):
    """
    Unmanaged read-only adapter for 'course' table.
    
    Verified columns (2026-02-08):
    - created_at: datetime, notnull
    - updated_at: datetime, notnull
    - id: char(32), pk
    - school_id: char(32), notnull
    - code: varchar(32), notnull
    - name: varchar(160), notnull
    """
    id = models.CharField(max_length=32, primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    school_id = models.CharField(max_length=32, db_index=True)
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=160)
    
    class Meta:
        managed = False
        db_table = "course"
        
    def __str__(self):
        return f"{self.code}: {self.name}"
