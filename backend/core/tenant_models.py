from django.db import models, router
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from contextlib import contextmanager
import threading
import logging

logger = logging.getLogger(__name__)

# Thread-local storage for current request school
_thread_locals = threading.local()


def set_current_school(school):
    _thread_locals.school = school


def get_current_school():
    return getattr(_thread_locals, "school", None)


def clear_current_school():
    set_current_school(None)


def _log_tenant_violation(*, violation_type, tenant_school_id=None, model=None, operation=None, extra=None):
    payload = {
        "event": "TENANT_VIOLATION",
        "violation_type": violation_type,
        "tenant_school_id": str(tenant_school_id) if tenant_school_id else None,
        "model": model,
        "operation": operation,
    }
    if extra:
        payload.update(extra)
    logger.warning("TENANT_VIOLATION", extra=payload)


def require_tenant_context():
    """Require tenant context to be set - raises if missing."""
    current = get_current_school()
    if current is None:
        _log_tenant_violation(violation_type='context_required', tenant_school_id=None, model=None, operation='require_tenant_context')
        raise TenantContextRequired("TENANT_CONTEXT_REQUIRED")
    return current


@contextmanager
def tenant_context(school):
    """Context manager for explicit tenant scoping (supports nesting)."""
    # Save prior (supports nesting)
    prior = get_current_school()
    try:
        set_current_school(school)
        yield school
    finally:
        # Restore prior (or clear)
        set_current_school(prior)


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

    def update(self, **kwargs):
        """Guard bulk update - require tenant context (fail-closed)."""
        current = get_current_school()
        if current is None:
            _log_tenant_violation(violation_type='bulk_update', tenant_school_id=None, model=getattr(self.model,'__name__',None), operation='update')
            raise TenantBulkOpViolation('TENANT_CONTEXT_MISSING_BULK_UPDATE')
        # Tenant ownership is immutable; expressions cannot reparent rows.
        if 'school' in kwargs or 'school_id' in kwargs:
            raise TenantWriteViolation('TENANT_OWNERSHIP_IMMUTABLE')
        # Ensure we are tenant-scoped before bulk update
        if hasattr(self.model, 'school'):
            qs = self.filter(school=current)
            return super(TenantQuerySet, qs).update(**kwargs)
        return super().update(**kwargs)

    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False,
                    update_conflicts=False, update_fields=None, unique_fields=None):
        current = require_tenant_context()
        objs = list(objs)
        if {'school', 'school_id'} & set(update_fields or ()):
            raise TenantWriteViolation('TENANT_OWNERSHIP_IMMUTABLE')
        using = self._db or router.db_for_write(self.model)
        for obj in objs:
            obj._assert_tenant_ownership(current, using=using)
        return super().bulk_create(
            objs, batch_size=batch_size, ignore_conflicts=ignore_conflicts,
            update_conflicts=update_conflicts, update_fields=update_fields,
            unique_fields=unique_fields,
        )

    def bulk_update(self, objs, fields, *args, **kwargs):
        current = require_tenant_context()
        fields = tuple(fields)
        if {'school', 'school_id'} & set(fields):
            raise TenantWriteViolation('TENANT_OWNERSHIP_IMMUTABLE')
        objs = tuple(objs)
        for obj in objs:
            obj._assert_tenant_ownership(current, using=self._db or router.db_for_write(self.model))
        return super().bulk_update(objs, fields, *args, **kwargs)

    def delete(self):
        """Guard bulk delete - require tenant context (fail-closed)."""
        current = get_current_school()
        if current is None:
            _log_tenant_violation(violation_type='bulk_delete', tenant_school_id=None, model=getattr(self.model,'__name__',None), operation='delete')
            raise TenantBulkOpViolation('TENANT_CONTEXT_MISSING_BULK_DELETE')
        # Ensure we are tenant-scoped before bulk delete
        if hasattr(self.model, 'school'):
            qs = self.filter(school=current)
            return super(TenantQuerySet, qs).delete()
        return super().delete()


class TenantWriteViolation(Exception):
    """Raised when attempting cross-tenant write operation."""
    pass


class TenantBulkOpViolation(Exception):
    """Raised when attempting bulk operation without tenant context."""
    pass


class TenantContextRequired(Exception):
    """Raised when tenant context is required but missing."""
    pass


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

    def _assert_tenant_ownership(self, current, *, using):
        if self.school_id is None:
            self.school_id = current.id
        if self.school_id != current.id:
            _log_tenant_violation(
                violation_type='write', tenant_school_id=current.id,
                model=self.__class__.__name__, operation='write',
                extra={'target_school_id': str(self.school_id)},
            )
            raise TenantWriteViolation('CROSS_TENANT_WRITE_BLOCKED')
        if self.pk is not None:
            stored_school_id = (
                self.__class__._base_manager.using(using).filter(pk=self.pk)
                .values_list('school_id', flat=True).first()
            )
            if stored_school_id is not None and stored_school_id != current.id:
                _log_tenant_violation(
                    violation_type='write', tenant_school_id=current.id,
                    model=self.__class__.__name__, operation='reparent',
                )
                raise TenantWriteViolation('TENANT_OWNERSHIP_IMMUTABLE')

    def save(self, *args, **kwargs):
        """Require explicit scope for creates and updates; never reparent records."""
        current = require_tenant_context()
        using = kwargs.get('using') or (args[2] if len(args) > 2 else None) or router.db_for_write(self.__class__, instance=self)
        self._assert_tenant_ownership(current, using=using)
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        current = require_tenant_context()
        using = kwargs.get('using') or (args[0] if args else None) or router.db_for_write(self.__class__, instance=self)
        self._assert_tenant_ownership(current, using=using)
        return super().delete(*args, **kwargs)

    class Meta:
        abstract = True
