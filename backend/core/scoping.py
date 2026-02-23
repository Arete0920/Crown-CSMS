"""
Layer C (Row + Field Scoping) — Central enforcement module.

Doctrine:
- Row scoping: which records can be seen (queryset filtering).
- Field scoping: which fields can be seen (serializer field pruning).
- No role-string checks in views. Views call this module.
- Safe defaults: deny-by-default (return empty queryset / remove sensitive fields).

Model wiring (as of 2026-02-22):
    Teacher → Student:
        academics.Section.teacher (FK → AUTH_USER_MODEL)
        academics.Enrollment.section + .student (FK → households.Student)
        Path on Student qs: .filter(enrollments__section__teacher=user).distinct()

    Parent → Student:
        households.Guardian.email matched against user.email
        households.Student.household → households.Household → households.Guardian
        Path: .filter(household__guardians__email__iexact=user.email).distinct()
        (mirrors the live pattern in households/views.py)

    Parent → FinancialAidApplication:
        financial_aid.FinancialAidApplication.household_id (bare UUID, no FK)
        Resolve via: Guardian.objects.filter(email__iexact=user.email).values_list('household_id', flat=True)
        Path: .filter(household_id__in=household_ids)

    Parent → LedgerEntry (financial domain):
        core.UserAccount.guardian (OneToOneField → core.Guardian → .family)
        Path: .filter(family=user.guardian.family)

Roles:
    UserRole.role_code values (stored in DB):
        HEAD_OF_SCHOOL, AID_DIRECTOR, FINANCE_DIRECTOR, REGISTRAR,
        TEACHER, PARENT, STUDENT, SUPPORT
    Mapped to canonical lowercase keys via _ROLE_CODE_TO_CANONICAL.
"""

# ===========================================================================
# SPINE CONTRACT — DO NOT VIOLATE
# ===========================================================================
#
# This is the ONLY place where role-based row scoping and field scoping
# may be defined. All other modules must call into this module.
#
# FORBIDDEN in views, viewsets, serializers, managers, or any other module:
#   - qs.filter(<role-based condition>)
#   - if request.user.role == "...": qs = qs.filter(...)
#   - hasattr(user, "guardian") / .email checks outside this module
#   - Any field hiding tied to role logic outside FIELD_SCOPE below
#
# If a new scoping rule is needed:
#   1. Add the relationship to the correct _scope_<domain>() function here.
#   2. Add or update the FieldScope entry in FIELD_SCOPE below.
#   3. Add a test in backend/core/tests/test_scoping.py.
#   4. Update docs/CROWN_LAYER_C_SCOPING_MATRIX.md (row + implementation status).
#
# Public API (the only surface views should call):
#   scope_queryset(user, qs, domain, *, school_id=None)  → filtered QuerySet
#   scope_serializer_fields(user, serializer, *, school_id=None)  → mutates in-place
#   apply_scope(user, qs, serializer_cls, domain, *, ...)  → (qs, serializer)
#   scoped_serializer_context(domain, base=None)  → dict
#   Domain constants: DOMAIN_STUDENTS, DOMAIN_FINANCIAL, DOMAIN_FINANCIAL_AID,
#                     DOMAIN_DISCIPLINE, DOMAIN_FORMATION, DOMAIN_REFERRALS
# ===========================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Set, Type, Union

from django.db.models import QuerySet


# ---------------------------------------------------------------------------
# Domains (canonical)
# ---------------------------------------------------------------------------

DOMAIN_STUDENTS = "students"
DOMAIN_FINANCIAL = "financial"
DOMAIN_FINANCIAL_AID = "financial_aid"
DOMAIN_DISCIPLINE = "discipline"
DOMAIN_FORMATION = "formation"
DOMAIN_REFERRALS = "referrals"

ALL_DOMAINS: Set[str] = {
    DOMAIN_STUDENTS,
    DOMAIN_FINANCIAL,
    DOMAIN_FINANCIAL_AID,
    DOMAIN_DISCIPLINE,
    DOMAIN_FORMATION,
    DOMAIN_REFERRALS,
}


# ---------------------------------------------------------------------------
# Role resolution
# ---------------------------------------------------------------------------

# Maps UserRole.role_code → canonical scoping key used in FIELD_SCOPE / _scope_* functions.
_ROLE_CODE_TO_CANONICAL: dict[str, str] = {
    "HEAD_OF_SCHOOL": "head",
    "AID_DIRECTOR": "aid_officer",
    "FINANCE_DIRECTOR": "finance",
    "REGISTRAR": "registrar",
    "TEACHER": "teacher",
    "COUNSELOR": "counselor",
    "PARENT": "parent",
    "STUDENT": "student",
    "SUPPORT": "support",
}

# Priority for multi-role resolution (first match wins, most privileged first).
_ROLE_PRIORITY: list[str] = [
    "HEAD_OF_SCHOOL",
    "AID_DIRECTOR",
    "FINANCE_DIRECTOR",
    "REGISTRAR",
    "COUNSELOR",
    "TEACHER",
    "PARENT",
    "STUDENT",
    "SUPPORT",
]


def resolve_role(user, school_id=None) -> str:
    """
    Resolve the active Crown scope-role for a user.

    Priority: UserRole queryset (most privileged first) → fallback to 'unknown'.

    school_id: if provided, restricts role lookup to that school.
    """
    roles_qs = getattr(user, "roles", None)
    if roles_qs is not None:
        try:
            qs = roles_qs.all()
            if school_id:
                qs = qs.filter(school_id=school_id)
            active_codes: Set[str] = set(qs.values_list("role_code", flat=True))
            for code in _ROLE_PRIORITY:
                if code in active_codes:
                    return _ROLE_CODE_TO_CANONICAL.get(code, code.lower())
        except Exception:
            pass

    # Fallback: direct .role attribute (dev/test convenience)
    direct = getattr(user, "role", None)
    if direct:
        return _ROLE_CODE_TO_CANONICAL.get(str(direct).upper(), str(direct).lower())

    # Fallback: Django is_superuser / is_staff → admin scope (no UserRole assigned)
    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return "admin"

    return "unknown"


# ---------------------------------------------------------------------------
# Row scope (queryset filtering)
# ---------------------------------------------------------------------------

def _empty(qs: QuerySet) -> QuerySet:
    return qs.none()


def scope_queryset(user, qs: QuerySet, domain: str, *, school_id=None) -> QuerySet:
    """
    Apply row-level scoping to a queryset for a given domain.

    The view MUST already restrict to tenant (e.g., filter school_id=school_id)
    before calling this. This function further limits within-tenant visibility
    by the caller's Crown role.

    Usage:
        qs = Student.objects.filter(school_id=school_id)
        qs = scope_queryset(request.user, qs, DOMAIN_STUDENTS)

    school_id: optional — if provided used to tighten role resolution to
               a single school when the user holds roles at multiple schools.
    """
    if domain not in ALL_DOMAINS:
        return _empty(qs)

    role = resolve_role(user, school_id=school_id)

    dispatch = {
        DOMAIN_STUDENTS: _scope_students,
        DOMAIN_FINANCIAL: _scope_financial,
        DOMAIN_FINANCIAL_AID: _scope_financial_aid,
        DOMAIN_DISCIPLINE: _scope_discipline,
        DOMAIN_FORMATION: _scope_formation,
        DOMAIN_REFERRALS: _scope_referrals,
    }
    fn = dispatch.get(domain)
    if fn is None:
        return _empty(qs)
    return fn(user, qs, role)


# ---------------------------------------------------------------------------
# Domain row-scope implementations
# ---------------------------------------------------------------------------

def _scope_students(user, qs: QuerySet, role: str) -> QuerySet:
    """
    Row scoping for households.Student querysets.

    Relationships:
    - teacher: academics.Enrollment.section.teacher (FK → AUTH_USER_MODEL)
               Student reverse: .enrollments (related_name on academics.Enrollment.student)
    - parent:  households.Student.household → households.Household
               households.Guardian.email matched against user.email
    - student: no user FK on Student yet (Phase 3); deny for now
    """
    if role in {"head", "director", "registrar", "admin"}:
        return qs

    if role == "teacher":
        # academics.Enrollment links Section (via section.teacher) and Student.
        # related_name="enrollments" is on academics.Enrollment.student FK.
        return qs.filter(enrollments__section__teacher=user).distinct()

    if role == "parent":
        email = getattr(user, "email", None)
        if not email:
            return _empty(qs)
        # households.Student.household → Household.guardians → Guardian.email
        return qs.filter(household__guardians__email__iexact=email).distinct()

    if role == "student":
        # Phase 3: Student.user FK not yet migrated. Deny until wired.
        return _empty(qs)

    if role == "counselor":
        # TODO: wire once counselor assignment model exists
        return _empty(qs)

    if role == "board":
        return _empty(qs)

    return _empty(qs)


def _scope_financial(user, qs: QuerySet, role: str) -> QuerySet:
    """
    Row scoping for core.LedgerEntry querysets.

    LedgerEntry.family (FK → core.Family).
    For parent users: core.UserAccount.guardian (OneToOneField → core.Guardian → .family).
    """
    if role in {"head", "director", "finance"}:
        return qs

    if role == "parent":
        # core.UserAccount.guardian → core.Guardian.family
        guardian = getattr(user, "guardian", None)
        if guardian is None:
            return _empty(qs)
        family = getattr(guardian, "family", None)
        if family is None:
            return _empty(qs)
        return qs.filter(family=family)

    return _empty(qs)


def _scope_financial_aid(user, qs: QuerySet, role: str) -> QuerySet:
    """
    Row scoping for financial_aid.FinancialAidApplication querysets.

    FinancialAidApplication.household_id is a bare UUID field (no FK).
    Parent resolution: households.Guardian.household_id matched by user.email.
    """
    if role in {"head", "director", "finance", "aid_officer"}:
        return qs

    if role == "parent":
        email = getattr(user, "email", None)
        if not email:
            return _empty(qs)
        # Lazy import to avoid circular dependency.
        from households.models import Guardian as HouseholdsGuardian  # noqa: PLC0415
        household_ids = HouseholdsGuardian.objects.filter(
            email__iexact=email
        ).values_list("household_id", flat=True)
        return qs.filter(household_id__in=household_ids)

    return _empty(qs)


def _scope_discipline(user, qs: QuerySet, role: str) -> QuerySet:
    """
    Row scoping for discipline incident querysets.

    No discipline model defined yet. All non-privileged roles return empty.
    TODO: wire once discipline.Incident model exists.
    """
    if role in {"head", "director"}:
        return qs

    if role == "counselor":
        # TODO: filter to assigned students once assignment model exists
        return _empty(qs)

    if role == "teacher":
        # TODO: filter to incidents for teacher's students/sections
        return _empty(qs)

    if role in {"parent", "student"}:
        return _empty(qs)

    return _empty(qs)


def _scope_formation(user, qs: QuerySet, role: str) -> QuerySet:
    """
    Row scoping for Barnabas / Formation domain querysets.

    No formation model defined yet.
    TODO: wire once formation model exists.
    """
    if role in {"head", "director", "spiritual_life"}:
        return qs

    # counselor / parent / student / teacher — all deny until wired
    return _empty(qs)


def _scope_referrals(user, qs: QuerySet, role: str) -> QuerySet:
    """
    Row scoping for Operation Andrew referral querysets.

    No referral model defined yet.
    TODO: wire once admissions.Referral model exists.
    """
    if role in {"head", "director", "admissions"}:
        return qs

    if role == "parent":
        # TODO: filter to own referrals once model has submitter FK
        return _empty(qs)

    if role == "finance":
        # TODO: referral reward records only
        return _empty(qs)

    return _empty(qs)


# ---------------------------------------------------------------------------
# Field scope (serializer pruning)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FieldScope:
    """
    Field scoping rule.

    allow: "__all__" or an explicit set of allowed field names.
    deny: fields always removed, even when allow="__all__".
    """
    allow: Union[Set[str], str]
    deny: Set[str]


FIELD_SCOPE: dict[str, dict[str, FieldScope]] = {
    DOMAIN_STUDENTS: {
        "head": FieldScope(allow="__all__", deny=set()),
        "director": FieldScope(allow="__all__", deny=set()),
        "registrar": FieldScope(allow="__all__", deny=set()),
        "teacher": FieldScope(
            allow={"id", "first_name", "last_name", "grade_level", "homeroom", "attendance_summary"},
            deny={"ssn", "counseling_notes", "internal_staff_notes", "financial_aid_details"},
        ),
        "parent": FieldScope(
            allow={"id", "first_name", "last_name", "grade_level", "attendance_summary", "schedule"},
            deny={"ssn", "counseling_notes", "internal_staff_notes", "financial_aid_details"},
        ),
        "student": FieldScope(
            allow={"id", "first_name", "last_name", "grade_level", "attendance_summary", "schedule"},
            deny={"ssn", "counseling_notes", "internal_staff_notes", "financial_aid_details"},
        ),
        "board": FieldScope(allow=set(), deny=set()),
        "unknown": FieldScope(allow=set(), deny=set()),
    },
    DOMAIN_FINANCIAL: {
        "head": FieldScope(allow="__all__", deny=set()),
        "director": FieldScope(allow="__all__", deny=set()),
        "finance": FieldScope(allow="__all__", deny=set()),
        "parent": FieldScope(
            allow={"id", "statement_period", "balance_cents", "charges", "payments"},
            deny={"collection_notes", "processor_metadata", "bank_account"},
        ),
        "unknown": FieldScope(allow=set(), deny=set()),
    },
    DOMAIN_FINANCIAL_AID: {
        "head": FieldScope(allow="__all__", deny=set()),
        "director": FieldScope(allow="__all__", deny=set()),
        "finance": FieldScope(allow="__all__", deny=set()),
        "aid_officer": FieldScope(allow="__all__", deny=set()),
        "parent": FieldScope(
            allow={"id", "status", "submitted_at", "requested_cents", "decision_status"},
            deny={"review_notes", "committee_comments", "internal_score"},
        ),
        "unknown": FieldScope(allow=set(), deny=set()),
    },
    DOMAIN_DISCIPLINE: {
        "head": FieldScope(allow="__all__", deny=set()),
        "director": FieldScope(allow="__all__", deny=set()),
        "counselor": FieldScope(allow="__all__", deny={"financial_fields", "donor_giving"}),
        "teacher": FieldScope(
            allow={"id", "incident_date", "category", "summary", "actions_taken"},
            deny={"confidential_notes", "counseling_notes"},
        ),
        "parent": FieldScope(
            allow={"id", "incident_date", "category", "summary", "actions_taken"},
            deny={"confidential_notes", "counseling_notes", "internal_staff_notes"},
        ),
        "student": FieldScope(
            allow={"id", "incident_date", "category", "summary", "actions_taken"},
            deny={"confidential_notes", "counseling_notes", "internal_staff_notes"},
        ),
        "unknown": FieldScope(allow=set(), deny=set()),
    },
    DOMAIN_FORMATION: {
        "head": FieldScope(allow="__all__", deny={"confidential_counseling_notes"}),
        "director": FieldScope(allow="__all__", deny={"confidential_counseling_notes"}),
        "spiritual_life": FieldScope(allow="__all__", deny={"confidential_counseling_notes"}),
        "counselor": FieldScope(allow="__all__", deny=set()),
        "parent": FieldScope(
            allow={"id", "devotion_date", "prompt", "student_response", "milestones"},
            deny={"mentor_private_notes", "risk_assessment"},
        ),
        "student": FieldScope(
            allow={"id", "devotion_date", "prompt", "student_response", "milestones"},
            deny={"mentor_private_notes", "risk_assessment"},
        ),
        "teacher": FieldScope(
            allow={"id", "devotion_date", "prompt"},
            deny={"student_response", "mentor_private_notes", "risk_assessment"},
        ),
        "unknown": FieldScope(allow=set(), deny=set()),
    },
    DOMAIN_REFERRALS: {
        "head": FieldScope(allow="__all__", deny=set()),
        "director": FieldScope(allow="__all__", deny=set()),
        "admissions": FieldScope(allow="__all__", deny=set()),
        "finance": FieldScope(
            allow={"id", "reward_amount_cents", "reward_type", "issued_at", "status"},
            deny={"applicant_private_data"},
        ),
        "parent": FieldScope(
            allow={"id", "status", "created_at", "reward_status"},
            deny={"internal_notes", "other_family_private_data"},
        ),
        "unknown": FieldScope(allow=set(), deny=set()),
    },
}


def get_field_scope(user, domain: str, *, school_id=None) -> FieldScope:
    role = resolve_role(user, school_id=school_id)
    domain_map = FIELD_SCOPE.get(domain, {})
    return (
        domain_map.get(role)
        or domain_map.get("unknown")
        or FieldScope(allow=set(), deny=set())
    )


def scope_serializer_fields(user, serializer, *, school_id=None) -> None:
    """
    Mutate a DRF serializer instance in-place to remove disallowed fields.

    Requires `crown_domain` in serializer.context (set via scoped_serializer_context).
    Defaults to deny-all if domain is absent.

    Usage:
        ser = StudentSerializer(qs, many=True, context=scoped_serializer_context(DOMAIN_STUDENTS, {"request": request}))
        scope_serializer_fields(request.user, ser)
        return Response(ser.data)
    """
    domain = getattr(serializer, "context", {}).get("crown_domain")
    if not domain:
        serializer.fields.clear()
        return

    rule = get_field_scope(user, domain, school_id=school_id)
    current_fields = set(serializer.fields.keys())

    if rule.allow != "__all__":
        allowed = set(rule.allow)
        for name in list(current_fields):
            if name not in allowed:
                serializer.fields.pop(name, None)

    for name in rule.deny:
        serializer.fields.pop(name, None)


def scoped_serializer_context(domain: str, base: Optional[dict] = None) -> dict:
    """
    Build a serializer context dict that includes `crown_domain`.

    Every view that uses scope_serializer_fields must pass this as context.
    Forgetting crown_domain causes deny-all (safe default).
    """
    ctx = dict(base or {})
    ctx["crown_domain"] = domain
    return ctx


# ---------------------------------------------------------------------------
# Convenience wrapper
# ---------------------------------------------------------------------------

def apply_scope(
    user,
    qs: QuerySet,
    serializer_cls: Type,
    domain: str,
    *,
    many: bool = True,
    context: Optional[dict] = None,
    school_id=None,
):
    """
    One-call helper:
    1. scope_queryset (row filtering)
    2. instantiate serializer with crown_domain context
    3. scope_serializer_fields (field pruning)

    Returns (scoped_qs, serializer_instance).

    Example:
        scoped_qs, ser = apply_scope(
            request.user,
            Student.objects.filter(school_id=school_id),
            StudentSerializer,
            DOMAIN_STUDENTS,
            context={"request": request},
            school_id=school_id,
        )
        return Response(ser.data)
    """
    scoped_qs = scope_queryset(user, qs, domain, school_id=school_id)
    ser = serializer_cls(
        scoped_qs,
        many=many,
        context=scoped_serializer_context(domain, context),
    )
    scope_serializer_fields(user, ser, school_id=school_id)
    return scoped_qs, ser
