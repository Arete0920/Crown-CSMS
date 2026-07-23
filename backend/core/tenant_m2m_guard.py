from __future__ import annotations

from functools import wraps

from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import DEFAULT_DB_ALIAS, models
from django.db.models.signals import m2m_changed


SUPPORTED_TENANT_FIELDS = ("school_id", "school", "tenant_id", "tenant")


def _tenant_field(model: type[models.Model]) -> models.Field | None:
    for name in SUPPORTED_TENANT_FIELDS:
        try:
            field = model._meta.get_field(name)
        except FieldDoesNotExist:
            continue
        if name in {"school", "tenant"} and not isinstance(
            field, (models.ForeignKey, models.OneToOneField)
        ):
            continue
        return field
    return None


def _tenant_lookup(field: models.Field) -> str:
    return getattr(field, "attname", field.name)


def _tenant_anchor(field: models.Field) -> str:
    lookup = _tenant_lookup(field)
    return lookup[:-3] if lookup.endswith("_id") else field.name


def _tenant_type(field: models.Field) -> str:
    target = getattr(field, "target_field", None)
    return (target or field).get_internal_type()


def _through_fields(
    through_model: type[models.Model],
) -> tuple[models.ForeignKey, models.ForeignKey] | None:
    if not through_model._meta.auto_created or not through_model._meta.managed:
        return None
    relation_fields = [
        field
        for field in through_model._meta.fields
        if isinstance(field, models.ForeignKey)
    ]
    if len(relation_fields) != 2:
        return None
    left_tenant = _tenant_field(relation_fields[0].remote_field.model)
    right_tenant = _tenant_field(relation_fields[1].remote_field.model)
    if left_tenant is None or right_tenant is None:
        return None
    return relation_fields[0], relation_fields[1]


def _endpoint_names(through_fields) -> set[str]:
    if not through_fields:
        return set()
    return {field.name for field in through_fields} | {
        field.attname for field in through_fields
    }


def _require_complete_endpoint_update(through_fields, fields) -> None:
    if not through_fields or fields is None:
        return
    requested = set(fields)
    endpoint_groups = [{field.name, field.attname} for field in through_fields]
    touched = [bool(group & requested) for group in endpoint_groups]
    if any(touched) and not all(touched):
        raise ValidationError(
            "Implicit M2M endpoint updates must include both endpoints."
        )


def _verified_endpoint_authority(
    left_field: models.ForeignKey,
    right_field: models.ForeignKey,
) -> tuple[models.Field, models.Field]:
    left_tenant = _tenant_field(left_field.remote_field.model)
    right_tenant = _tenant_field(right_field.remote_field.model)
    if left_tenant is None or right_tenant is None:
        raise ValidationError(
            "Implicit M2M endpoints do not expose two tenant authorities."
        )
    if (
        _tenant_anchor(left_tenant) != _tenant_anchor(right_tenant)
        or _tenant_type(left_tenant) != _tenant_type(right_tenant)
    ):
        raise ValidationError(
            "Implicit M2M endpoints do not share a verified tenant authority."
        )
    return left_tenant, right_tenant


def _tenant_map(model, tenant_field, primary_keys, using):
    return dict(
        model._default_manager.using(using)
        .filter(pk__in=primary_keys)
        .values_list("pk", _tenant_lookup(tenant_field))
    )


def _validate_through_objects(through_model, objects, using):
    through_fields = _through_fields(through_model)
    if through_fields is None or not objects:
        return
    left_field, right_field = through_fields
    left_tenant, right_tenant = _verified_endpoint_authority(
        left_field,
        right_field,
    )

    left_ids = {getattr(obj, left_field.attname) for obj in objects}
    right_ids = {getattr(obj, right_field.attname) for obj in objects}
    if None in left_ids or None in right_ids:
        raise ValidationError("Implicit M2M through rows require both endpoints.")

    left_tenants = _tenant_map(
        left_field.remote_field.model,
        left_tenant,
        left_ids,
        using,
    )
    right_tenants = _tenant_map(
        right_field.remote_field.model,
        right_tenant,
        right_ids,
        using,
    )
    if len(left_tenants) != len(left_ids) or len(right_tenants) != len(right_ids):
        raise ValidationError("One or more implicit M2M endpoint records do not exist.")

    for obj in objects:
        left_id = getattr(obj, left_field.attname)
        right_id = getattr(obj, right_field.attname)
        if left_tenants[left_id] != right_tenants[right_id]:
            raise ValidationError(
                "Implicit M2M records must belong to the same tenant."
            )


def reject_cross_tenant_m2m(
    sender,
    instance,
    action,
    reverse,
    model,
    pk_set,
    using,
    **kwargs,
):
    if action != "pre_add" or not pk_set or _through_fields(sender) is None:
        return

    instance_tenant_field = _tenant_field(type(instance))
    related_tenant_field = _tenant_field(model)
    if instance_tenant_field is None or related_tenant_field is None:
        return
    if (
        _tenant_anchor(instance_tenant_field) != _tenant_anchor(related_tenant_field)
        or _tenant_type(instance_tenant_field) != _tenant_type(related_tenant_field)
    ):
        raise ValidationError(
            "Implicit M2M endpoints do not share a verified tenant authority."
        )

    instance_tenant = getattr(instance, _tenant_lookup(instance_tenant_field))
    related_lookup = _tenant_lookup(related_tenant_field)
    related_values = list(
        model._default_manager.using(using)
        .filter(pk__in=pk_set)
        .values_list(related_lookup, flat=True)
    )
    if len(related_values) != len(pk_set):
        raise ValidationError("One or more related M2M records do not exist.")
    if set(related_values) != {instance_tenant}:
        raise ValidationError(
            "Implicit M2M records must belong to the same tenant as the owner."
        )


def _install_model_save_base_guard() -> None:
    if getattr(models.Model.save_base, "_crown_tenant_guard", False):
        return

    original_save_base = models.Model.save_base

    @wraps(original_save_base)
    def guarded_save_base(
        self,
        raw=False,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        through_fields = _through_fields(type(self))
        if through_fields is not None:
            _require_complete_endpoint_update(through_fields, update_fields)
            database = using or self._state.db or DEFAULT_DB_ALIAS
            _validate_through_objects(type(self), [self], database)
        return original_save_base(
            self,
            raw=raw,
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

    guarded_save_base._crown_tenant_guard = True
    models.Model.save_base = guarded_save_base


def _install_queryset_guards() -> None:
    if getattr(models.QuerySet.bulk_create, "_crown_tenant_guard", False):
        return

    original_bulk_create = models.QuerySet.bulk_create
    original_bulk_update = models.QuerySet.bulk_update
    original_update = models.QuerySet.update

    @wraps(original_bulk_create)
    def guarded_bulk_create(self, objs, *args, **kwargs):
        object_list = list(objs)
        _validate_through_objects(self.model, object_list, self.db)
        return original_bulk_create(self, object_list, *args, **kwargs)

    @wraps(original_bulk_update)
    def guarded_bulk_update(self, objs, fields, *args, **kwargs):
        object_list = list(objs)
        through_fields = _through_fields(self.model)
        _require_complete_endpoint_update(through_fields, fields)
        if _endpoint_names(through_fields).intersection(fields):
            _validate_through_objects(self.model, object_list, self.db)
        return original_bulk_update(self, object_list, fields, *args, **kwargs)

    @wraps(original_update)
    def guarded_update(self, **kwargs):
        through_fields = _through_fields(self.model)
        if _endpoint_names(through_fields).intersection(kwargs):
            raise ValidationError(
                "Implicit M2M endpoint columns cannot be changed with QuerySet.update()."
            )
        return original_update(self, **kwargs)

    guarded_bulk_create._crown_tenant_guard = True
    guarded_bulk_update._crown_tenant_guard = True
    guarded_update._crown_tenant_guard = True
    models.QuerySet.bulk_create = guarded_bulk_create
    models.QuerySet.bulk_update = guarded_bulk_update
    models.QuerySet.update = guarded_update


def install_tenant_m2m_guards() -> None:
    m2m_changed.connect(
        reject_cross_tenant_m2m,
        dispatch_uid="core.reject_cross_tenant_implicit_m2m",
        weak=False,
    )
    _install_model_save_base_guard()
    _install_queryset_guards()
