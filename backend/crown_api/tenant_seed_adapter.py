import uuid

from django.apps import apps
from django.db import models
from django.utils import timezone


def _default_value_for_field(field, unique):
    if isinstance(field, (models.CharField, models.TextField, models.SlugField)):
        max_length = getattr(field, "max_length", 64) or 64
        base = f"probe_{unique}"
        return base[:max_length]

    if isinstance(field, models.EmailField):
        return f"probe_{unique}@example.com"

    if isinstance(field, models.BooleanField):
        return True

    if isinstance(field, (models.IntegerField, models.BigIntegerField, models.PositiveIntegerField)):
        return 1

    if isinstance(field, models.DateTimeField):
        return timezone.now()

    if isinstance(field, models.DateField):
        return timezone.now().date()

    if isinstance(field, models.TimeField):
        return timezone.now().time()

    return None


def _candidate_school_models():
    candidates = []

    for model in apps.get_models():
        meta = model._meta
        field_names = {field.name for field in meta.concrete_fields}
        score = 0

        if meta.object_name == "School":
            score += 100
        elif "School" in meta.object_name:
            score += 50

        if "name" in field_names:
            score += 10
        if "code" in field_names:
            score += 5
        if "slug" in field_names:
            score += 3

        if score > 0:
            candidates.append((score, model))

    candidates.sort(key=lambda item: item[0], reverse=True)
    return [model for _, model in candidates]


def find_school_model():
    models_found = _candidate_school_models()
    return models_found[0] if models_found else None


def _build_create_kwargs(model, unique):
    kwargs = {}

    for field in model._meta.concrete_fields:
        if getattr(field, "auto_created", False):
            continue
        if getattr(field, "primary_key", False):
            continue
        if getattr(field, "has_default", lambda: False)():
            continue
        if getattr(field, "null", False):
            continue
        if getattr(field, "blank", False) and isinstance(field, (models.CharField, models.TextField)):
            continue

        if isinstance(field, models.ForeignKey):
            related = field.related_model._default_manager.order_by("pk").first()
            if related is None:
                raise RuntimeError(
                    f"cannot create {model._meta.label}; required related object missing for field '{field.name}'"
                )
            kwargs[field.name] = related
            continue

        value = _default_value_for_field(field, unique)
        if value is None:
            raise RuntimeError(
                f"cannot infer default value for required field '{field.name}' on {model._meta.label}"
            )
        kwargs[field.name] = value

    return kwargs


def resolve_probe_school_context(default_school_id="1"):
    model = find_school_model()
    if model is None:
        return {
            "schoolId": str(default_school_id),
            "schoolObj": None,
            "schoolModel": None,
            "schoolModelLabel": "",
            "seedMode": "fallback",
            "reason": "no candidate school model found",
        }

    existing = model._default_manager.order_by("pk").first()
    if existing is not None:
        return {
            "schoolId": str(existing.pk),
            "schoolObj": existing,
            "schoolModel": model,
            "schoolModelLabel": model._meta.label,
            "seedMode": "existing",
            "reason": "",
        }

    unique = uuid.uuid4().hex[:10]

    try:
        kwargs = _build_create_kwargs(model, unique)
        created = model._default_manager.create(**kwargs)
    except Exception as exc:
        return {
            "schoolId": str(default_school_id),
            "schoolObj": None,
            "schoolModel": model,
            "schoolModelLabel": model._meta.label,
            "seedMode": "fallback",
            "reason": str(exc),
        }

    return {
        "schoolId": str(created.pk),
        "schoolObj": created,
        "schoolModel": model,
        "schoolModelLabel": model._meta.label,
        "seedMode": "created",
        "reason": "",
    }


def attach_user_to_school_if_possible(user, school_context):
    if not user:
        return []

    school_obj = school_context.get("schoolObj")
    school_model = school_context.get("schoolModel")
    if school_obj is None or school_model is None:
        return []

    changed_fields = []

    for field in user._meta.concrete_fields:
        if isinstance(field, models.ForeignKey) and field.related_model == school_model:
            setattr(user, field.name, school_obj)
            changed_fields.append(field.name)

    if hasattr(user, "school_id"):
        setattr(user, "school_id", school_obj.pk)
        changed_fields.append("school_id")
    elif hasattr(user, "school"):
        setattr(user, "school", school_obj)
        changed_fields.append("school")

    if hasattr(user, "tenant_id"):
        setattr(user, "tenant_id", school_obj.pk)
        changed_fields.append("tenant_id")
    elif hasattr(user, "tenant"):
        setattr(user, "tenant", school_obj)
        changed_fields.append("tenant")

    if hasattr(user, "organization_id"):
        setattr(user, "organization_id", school_obj.pk)
        changed_fields.append("organization_id")
    elif hasattr(user, "organization"):
        setattr(user, "organization", school_obj)
        changed_fields.append("organization")

    if changed_fields:
        user.save()

    return sorted(set(changed_fields))
