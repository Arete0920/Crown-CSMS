from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
import threading

# Thread-local storage for current request school
_thread_locals = threading.local()


def set_current_school(school):
    _thread_locals.school = school


def get_current_school():
    return getattr(_thread_locals, "school", None)


class TenantQuerySet(models.QuerySet):
    def _filter_by_school(self):
        school = get_current_school()
        if school is None:
            return self
        return self.filter(school=school)

    def all(self):
        return self._filter_by_school()

    def filter(self, *args, **kwargs):
        return super().filter(*args, **kwargs)

    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)


class TenantManager(models.Manager):
    """Manager that auto-scopes queries to current tenant (fail-closed)."""
    def get_queryset(self):
        qs = TenantQuerySet(self.model, using=self._db)
        school = get_current_school()
        if school:
            return qs.filter(school=school)
        # FAIL-CLOSED: No school context = empty queryset (prevents data leaks)
        return qs.none()


class TenantScopedModel(models.Model):
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="%(class)ss"
    )

    objects = TenantManager()

    class Meta:
        abstract = True
