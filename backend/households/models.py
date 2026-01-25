import uuid
from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
	"""
	Local lightweight base to avoid depending on any other app’s base classes.
	Spine rule: keep it boring, predictable, and testable.
	"""
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True


class Household(TimeStampedModel):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	# Multi-tenant scoping anchor
	school_id = models.UUIDField(db_index=True)

	name = models.CharField(max_length=160)

	# Address (minimal — expand later)
	address1 = models.CharField(max_length=160, blank=True, default="")
	address2 = models.CharField(max_length=160, blank=True, default="")
	city = models.CharField(max_length=80, blank=True, default="")
	state = models.CharField(max_length=40, blank=True, default="")
	postal_code = models.CharField(max_length=20, blank=True, default="")

	is_active = models.BooleanField(default=True)

	class Meta:
		db_table = "household"
		indexes = [
			models.Index(fields=["school_id", "is_active"]),
			models.Index(fields=["school_id", "name"]),
		]

	def __str__(self) -> str:
		return f"{self.name}"


class Guardian(TimeStampedModel):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	school_id = models.UUIDField(db_index=True)
	household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="guardians")

	first_name = models.CharField(max_length=80)
	last_name = models.CharField(max_length=80)
	email = models.EmailField(blank=True, default="")
	phone = models.CharField(max_length=30, blank=True, default="")

	# Spine: keep roles simple; expand later (custody, billing responsibility, etc.)
	is_primary = models.BooleanField(default=False)

	class Meta:
		db_table = "guardian"
		indexes = [
			models.Index(fields=["school_id", "household"]),
			models.Index(fields=["school_id", "last_name", "first_name"]),
		]

	def __str__(self) -> str:
		return f"{self.last_name}, {self.first_name}"


class Student(TimeStampedModel):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	school_id = models.UUIDField(db_index=True)
	household = models.ForeignKey(Household, on_delete=models.PROTECT, related_name="students")

	first_name = models.CharField(max_length=80)
	last_name = models.CharField(max_length=80)

	# Spine: grade as simple string for now (K, 1, 2, ... 12, PK)
	grade_level = models.CharField(max_length=16, blank=True, default="")

	is_active = models.BooleanField(default=True)

	class Meta:
		db_table = "student"
		indexes = [
			models.Index(fields=["school_id", "is_active"]),
			models.Index(fields=["school_id", "last_name", "first_name"]),
			models.Index(fields=["school_id", "grade_level"]),
		]

	def __str__(self) -> str:
		return f"{self.last_name}, {self.first_name}"
