"""Private, first-release teacher-observation API. No ratings or implicit grants."""
import hashlib
import json
import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.cache import never_cache
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import AcademicYear, Staff, UserAccount
from core.permissions import user_has_permission

from .models import (
    TeacherEvaluationAssignment,
    TeacherEvaluationCycle,
    TeacherEvaluationEvent,
    TeacherObservation,
    TeacherObservationResponse,
)

MAX_PAGE = 100


def _school(request):
    """Require explicit and matching tenant context; never infer staff from email."""
    header = request.headers.get("X-School-Id")
    if not header:
        raise ValidationError("X-School-Id is required for confidential evaluations.")
    try:
        school_id = uuid.UUID(header)
    except (ValueError, TypeError):
        raise ValidationError("X-School-Id requires a UUID.")
    school = getattr(request, "school", None)
    if (
        school is None
        or school.id != school_id
        or not school.is_active
        or not request.user.is_active
        or request.user.school_id != school_id
    ):
        raise PermissionDenied("A current school-scoped account is required.")
    return school


def _grant(user, code, school):
    if not user_has_permission(user, code, school):
        raise PermissionDenied("Explicit teacher-evaluation permission required.")


def _uuid(value, name):
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError(f"{name} requires a UUID.")


def _text(value, name, limit, *, optional=False):
    if optional and value in (None, ""):
        return ""
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValidationError(f"{name} is required and limited to {limit} characters.")
    return value.strip()


def _payload(request, fields):
    if not isinstance(request.data, dict):
        raise ValidationError("Request must be an object.")
    if set(request.data) != set(fields):
        raise ValidationError("Request contains missing or unsupported fields.")
    return request.data


def _version(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValidationError("version requires a positive integer.")
    return value


def _fingerprint(action, data):
    raw = json.dumps({"action": action, "payload": data}, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _retry(school, actor, key, fingerprint):
    event = TeacherEvaluationEvent.objects.filter(
        school=school, actor=actor, request_key=key
    ).first()
    if event is None:
        return None
    if event.fingerprint != fingerprint:
        return Response({"detail": "Retry key conflict."}, status=409)
    return Response(event.after, status=200)


def _write_event(*, school, actor, key, fingerprint, action, cycle, after, before=None, observation=None):
    return TeacherEvaluationEvent.objects.create(
        school=school,
        cycle=cycle,
        observation=observation,
        actor=actor,
        request_key=key,
        fingerprint=fingerprint,
        action=action,
        before=before or {},
        after=after,
    )


def _subject(user, cycle):
    return bool(
        user.is_active
        and user.school_id == cycle.school_id
        and user.staff_id == cycle.staff_id
    )


def _evaluator(user, cycle):
    return bool(
        user.is_active
        and user.school_id == cycle.school_id
        and TeacherEvaluationAssignment.objects.filter(
            school_id=cycle.school_id, cycle=cycle, evaluator=user
        ).exists()
    )


def _can_read(user, cycle, school):
    return (
        (_subject(user, cycle) and user_has_permission(user, "evaluation.read_self", school))
        or (_evaluator(user, cycle) and user_has_permission(user, "evaluation.read_assigned", school))
    )


def _can_observe(user, cycle, school):
    return _evaluator(user, cycle) and user_has_permission(user, "evaluation.observe", school)


def _ensure_read(user, cycle, school):
    if not _can_read(user, cycle, school):
        raise NotFound()


def _cycle(school, cycle_id):
    return get_object_or_404(
        TeacherEvaluationCycle.objects.filter(school=school).select_related(
            "school", "staff", "academic_year"
        ), pk=cycle_id
    )


def _cycle_data(cycle):
    return {
        "id": str(cycle.pk),
        "staff_id": str(cycle.staff_id),
        "academic_year_id": str(cycle.academic_year_id),
        "title": cycle.title,
        "state": cycle.state,
        "created_at": cycle.created_at.isoformat(),
    }


def _observation_data(row, *, include_text=True):
    data = {
        "id": str(row.pk),
        "cycle_id": str(row.cycle_id),
        "observed_at": row.observed_at.isoformat(),
        "status": row.status,
        "version": row.version,
        "submitted_at": row.submitted_at.isoformat() if row.submitted_at else None,
    }
    if include_text:
        data["narrative"] = row.narrative
    return data


def _response_data(row):
    return {
        "id": str(row.pk),
        "observation_id": str(row.observation_id),
        "choice": row.choice,
        "comment": row.comment,
        "created_at": row.created_at.isoformat(),
    }


def _error(exc):
    if isinstance(exc, DjangoValidationError):
        raise ValidationError(exc.messages)
    raise exc


@never_cache
@extend_schema(methods=["GET"], responses=OpenApiTypes.OBJECT)
@extend_schema(methods=["POST"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def cycles(request):
    school = _school(request)
    if request.method == "GET":
        self_grant = user_has_permission(request.user, "evaluation.read_self", school)
        assigned_grant = user_has_permission(request.user, "evaluation.read_assigned", school)
        if not self_grant and not assigned_grant:
            raise PermissionDenied("Explicit teacher-evaluation read permission required.")
        queryset = TeacherEvaluationCycle.objects.filter(school=school)
        allowed = Q(pk__in=[])
        if self_grant and request.user.staff_id is not None:
            allowed |= Q(staff_id=request.user.staff_id)
        if assigned_grant:
            allowed |= Q(assignment__school=school, assignment__evaluator=request.user)
        queryset = queryset.filter(allowed).distinct()
        try:
            offset = int(request.query_params.get("offset", "0"))
        except (ValueError, TypeError):
            raise ValidationError("offset must be a nonnegative integer.")
        if offset < 0 or offset > 100000:
            raise ValidationError("offset out of range.")
        total = queryset.count()
        rows = queryset.select_related("staff", "academic_year").order_by("-created_at", "id")[offset:offset+MAX_PAGE]
        return Response({
            "source": "live",
            "cycles": [_cycle_data(row) for row in rows],
            "total": total,
            "next_offset": offset + MAX_PAGE if offset + MAX_PAGE < total else None,
        })

    school = _school(request)
    _grant(request.user, "evaluation.assign", school)
    data = _payload(request, ("request_key", "staff_id", "academic_year_id", "evaluator_id", "title"))
    key = _uuid(data["request_key"], "request_key")
    staff_id = _uuid(data["staff_id"], "staff_id")
    year_id = _uuid(data["academic_year_id"], "academic_year_id")
    evaluator_id = _uuid(data["evaluator_id"], "evaluator_id")
    title = _text(data["title"], "title", 160)
    fingerprint = _fingerprint("cycle_created", data)
    try:
        with transaction.atomic():
            actor = UserAccount.objects.select_for_update().get(pk=request.user.pk)
            _grant(actor, "evaluation.assign", school)
            replay = _retry(school, actor, key, fingerprint)
            if replay is not None:
                return replay
            staff = get_object_or_404(
                Staff.objects.select_for_update(), school=school, pk=staff_id,
                role_type="TEACHER", status="ACTIVE"
            )
            year = get_object_or_404(AcademicYear, school=school, pk=year_id)
            evaluator = get_object_or_404(
                UserAccount, school=school, pk=evaluator_id, is_active=True
            )
            if not user_has_permission(evaluator, "evaluation.observe", school):
                raise PermissionDenied("Evaluator must have explicit observation authority.")
            if actor.staff_id == staff.pk or evaluator.staff_id == staff.pk:
                raise PermissionDenied("Self-evaluation assignment is prohibited.")
            if TeacherEvaluationCycle.objects.filter(
                school=school, staff=staff, academic_year=year
            ).exists():
                return Response({"detail": "This teacher already has a cycle for the year."}, status=409)
            cycle = TeacherEvaluationCycle.objects.create(
                school=school, staff=staff, academic_year=year, created_by=actor, title=title
            )
            TeacherEvaluationAssignment.objects.create(
                school=school, cycle=cycle, evaluator=evaluator, assigned_by=actor
            )
            output = _cycle_data(cycle)
            output["evaluator_id"] = str(evaluator.pk)
            _write_event(
                school=school, actor=actor, key=key, fingerprint=fingerprint,
                action="cycle_created", cycle=cycle,
                after=output,
            )
            return Response(output, status=201)
    except (DjangoValidationError, IntegrityError) as exc:
        if isinstance(exc, IntegrityError):
            return Response({"detail": "Conflicting evaluation cycle or request."}, status=409)
        _error(exc)


@never_cache
@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cycle_detail(request, cycle_id):
    school = _school(request)
    cycle = _cycle(school, cycle_id)
    _ensure_read(request.user, cycle, school)
    is_evaluator = _evaluator(request.user, cycle) and user_has_permission(
        request.user, "evaluation.read_assigned", school
    )
    qs = TeacherObservation.objects.filter(school=school, cycle=cycle)
    if not is_evaluator:
        qs = qs.filter(status="submitted")
    rows = list(qs.order_by("-observed_at", "id")[:MAX_PAGE])
    response_by_id = {
        r.observation_id: _response_data(r)
        for r in TeacherObservationResponse.objects.filter(
            school=school, observation__in=rows
        )
    }
    return Response({
        "source": "live",
        "cycle": _cycle_data(cycle),
        "observations": [
            {**_observation_data(row), "teacher_response": response_by_id.get(row.pk)}
            for row in rows
        ],
        "observations_limit": MAX_PAGE,
    })


@never_cache
@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def observations(request, cycle_id):
    school = _school(request)
    data = _payload(request, ("request_key", "observed_at", "narrative"))
    key = _uuid(data["request_key"], "request_key")
    try:
        observed_at = parse_datetime(data["observed_at"]) if isinstance(data["observed_at"], str) else None
    except (ValueError, TypeError, OverflowError):
        observed_at = None
    if observed_at is None or timezone.is_naive(observed_at) or observed_at > timezone.now():
        raise ValidationError("observed_at requires a nonfuture timezone-aware ISO datetime.")
    narrative = _text(data["narrative"], "narrative", 8000)
    fingerprint = _fingerprint("observation_draft", {"cycle_id": str(cycle_id), **data})
    try:
        with transaction.atomic():
            actor = UserAccount.objects.select_for_update().get(pk=request.user.pk)
            replay = _retry(school, actor, key, fingerprint)
            if replay is not None:
                # An old retry must not restore visibility after permissions are revoked.
                cycle = _cycle(school, cycle_id)
                if not _can_observe(actor, cycle, school):
                    raise NotFound()
                if replay.status_code == 200:
                    original = get_object_or_404(
                        TeacherObservation, pk=replay.data["id"], school=school,
                        cycle=cycle, evaluator=actor,
                    )
                    return Response(_observation_data(original), status=200)
                return replay
            cycle = _cycle(school, cycle_id)
            if not _can_observe(actor, cycle, school):
                raise NotFound()
            try:
                observed_date = observed_at.astimezone(ZoneInfo(school.timezone)).date()
            except (ZoneInfoNotFoundError, ValueError, TypeError):
                raise ValidationError("School timezone must be valid.")
            if not cycle.academic_year.start_date <= observed_date <= cycle.academic_year.end_date:
                raise ValidationError("Observation must fall inside the evaluation academic year.")
            row = TeacherObservation.objects.create(
                school=school, cycle=cycle, evaluator=actor,
                observed_at=observed_at, narrative=narrative,
            )
            output = _observation_data(row, include_text=False)
            _write_event(
                school=school, actor=actor, key=key, fingerprint=fingerprint,
                action="observation_draft", cycle=cycle, observation=row, after=output,
            )
            return Response({**output, "narrative": row.narrative}, status=201)
    except DjangoValidationError as exc:
        _error(exc)
    except IntegrityError:
        return Response({"detail": "Conflicting request key."}, status=409)


@never_cache
@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_observation(request, observation_id):
    school = _school(request)
    data = _payload(request, ("request_key", "version"))
    key = _uuid(data["request_key"], "request_key")
    version = _version(data["version"])
    fingerprint = _fingerprint("observation_submitted", {"observation_id": str(observation_id), **data})
    try:
        with transaction.atomic():
            actor = UserAccount.objects.select_for_update().get(pk=request.user.pk)
            row = get_object_or_404(
                TeacherObservation.objects.select_for_update().select_related("cycle", "cycle__academic_year"),
                school=school, pk=observation_id
            )
            if not _can_observe(actor, row.cycle, school) or row.evaluator_id != actor.pk:
                raise NotFound()
            replay = _retry(school, actor, key, fingerprint)
            if replay is not None:
                return replay
            if row.status != "draft" or row.version != version:
                return Response({"detail": "Observation changed; refresh before submitting."}, status=409)
            previous = {"status": row.status, "version": row.version}
            row.status = "submitted"
            row.submitted_at = timezone.now()
            row.version += 1
            row.save()
            output = _observation_data(row, include_text=False)
            _write_event(
                school=school, actor=actor, key=key, fingerprint=fingerprint,
                action="observation_submitted", cycle=row.cycle,
                observation=row, before=previous, after=output,
            )
            return Response(output)
    except DjangoValidationError as exc:
        _error(exc)
    except IntegrityError:
        return Response({"detail": "Conflicting request key."}, status=409)


@never_cache
@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def observation_response(request, observation_id):
    school = _school(request)
    data = _payload(request, ("request_key", "choice", "comment"))
    key = _uuid(data["request_key"], "request_key")
    choice = data["choice"]
    if choice not in ("acknowledged_receipt", "disputed"):
        raise ValidationError("Response must acknowledge receipt or dispute the observation.")
    if not isinstance(data["comment"], str) or len(data["comment"]) > 2000:
        raise ValidationError("comment must be text at most 2000 characters.")
    comment = data["comment"].strip()
    if choice == "disputed" and not comment:
        raise ValidationError("Disputes require a written response.")
    fingerprint = _fingerprint("teacher_response", {"observation_id": str(observation_id), **data})
    try:
        with transaction.atomic():
            actor = UserAccount.objects.select_for_update().get(pk=request.user.pk)
            row = get_object_or_404(
                TeacherObservation.objects.select_for_update().select_related("cycle"),
                school=school, pk=observation_id, status="submitted"
            )
            if not _subject(actor, row.cycle) or not user_has_permission(
                actor, "evaluation.respond_self", school
            ):
                raise NotFound()
            replay = _retry(school, actor, key, fingerprint)
            if replay is not None:
                return replay
            if TeacherObservationResponse.objects.filter(
                school=school, observation=row
            ).exists():
                return Response({"detail": "Response already recorded."}, status=409)
            response = TeacherObservationResponse.objects.create(
                school=school, observation=row, teacher=actor, choice=choice, comment=comment
            )
            output = _response_data(response)
            _write_event(
                school=school, actor=actor, key=key, fingerprint=fingerprint,
                action="teacher_response", cycle=row.cycle, observation=row,
                after={"id": output["id"], "observation_id": output["observation_id"], "choice": choice},
            )
            return Response(output, status=201)
    except DjangoValidationError as exc:
        _error(exc)
    except IntegrityError:
        return Response({"detail": "Conflicting response or request key."}, status=409)
