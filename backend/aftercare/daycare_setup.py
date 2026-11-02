"""Inactive director configuration; never approves licensing or admits children."""
from datetime import date
from django.db import transaction
from rest_framework.exceptions import NotFound, PermissionDenied
from core.models import School, UserAccount, UserRole
from core.permissions import user_has_permission
from audit.models import AuditLog
from .daycare_checkin import require_entitlement
from .daycare_models import DaycareSite, DaycareRoom


class ConfigurationConflict(Exception):
    pass


def require_configuration(school_id, actor_id):
    """Called inside the operation's transaction; no legacy/superuser role bypass."""
    school = School.objects.filter(pk=school_id, is_active=True).first()
    # Preserve the custody engine's lock order: entitlement, then staff identity.
    require_entitlement(school_id)
    actor = UserAccount.objects.select_for_update().filter(
        pk=actor_id, school_id=school_id, is_active=True,
    ).first()
    if school is None or actor is None:
        raise PermissionDenied("Active school-bound director required.")
    role = UserRole.objects.select_for_update().filter(
        user=actor, school=school, role_code="DAYCARE_DIRECTOR",
    ).first()
    if role is None or not user_has_permission(actor, "diadem.daycare.configure", school=school):
        raise PermissionDenied("Explicit Diadem configuration permission required.")
    return school, actor


def create_configuration(*, school_id, actor_id, values, site_id=None):
    """Tenant-local natural keys make identical retries safe, conflicts explicit.

    The per-school entitlement row lock serializes configuration creation;
    existing canonical unique constraints remain the final database guard.
    Values originate from the strict API serializer, not arbitrary model fields.
    """
    with transaction.atomic():
        school, actor = require_configuration(school_id, actor_id)
        model = DaycareSite if site_id is None else DaycareRoom
        identity = {"school": school, "code": values["code"]}
        if site_id is not None:
            site = DaycareSite.objects.select_for_update().filter(
                pk=site_id, school=school,
            ).first()
            if site is None:
                raise NotFound()
            identity["site"] = site
        existing = model.objects.filter(**identity).first()
        if existing is not None:
            if existing.is_active or any(getattr(existing, key) != val for key, val in values.items()):
                raise ConfigurationConflict("Configuration code already has different settings.")
            return existing, False
        record = model.objects.create(**identity, **{
            key: val for key, val in values.items() if key != "code"
        }, is_active=False)
        AuditLog.objects.create(
            user_id=actor.pk, action="diadem.daycare.configuration.created",
            model=model.__name__, object_id=str(record.pk),
            metadata={"school_id": str(school.pk), "site_id": str(site_id or record.pk),
                      "code": record.code, "is_active": False,
                      "policy_approval": "NOT_VERIFIED",
                      "configuration": {key: val.isoformat() if isinstance(val, date) else val
                                        for key, val in values.items()}},
        )
        return record, True
