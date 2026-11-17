"""Owned fictional administration using the existing transactional workflow."""
from dataclasses import asdict
from uuid import uuid5
from django.core.management.base import CommandError
from django.db import transaction
from django.urls import path
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from core.models import Student, UserAccount
from core.permissions import user_has_permission
from crown_api.models_households import Household, Person
from .admin_operations import seed_admin_context, serialize_admin_student_state, resolve_admin_student_workflow
from .models import SandboxEvent
from .presenter_jireh import actor_scope
from .universal_demo import _owned_school
from .universal_identity import presenter_username
from .universal_runtime import require_presenter_runtime

STAGED = 'universal_presenter_admin_staged_v1'


def _context(school):
    student = Student.objects.select_related('family', 'current_grade_level').get(
        school=school, student_number='HCA-0001')
    return student, uuid5(school.pk, 'admin:communication:household:v1'), uuid5(school.pk, 'admin:communication:sender:v1')


def prepare_presenter_admin(*, apply=False):
    require_presenter_runtime()
    with transaction.atomic():
        school = _owned_school()
        if school is None:
            raise CommandError('Prepare the owned fictional presenter first.')
        admin = UserAccount.objects.get(school=school, username=presenter_username('school_admin', school.pk),
            is_active=True, is_staff=False, is_superuser=False)
        if not user_has_permission(admin, 'admin.view', school=school):
            raise CommandError('Existing approved administrator permissions required; no grants changed.')
        student, household_id, sender_id = _context(school)
        if (SandboxEvent.objects.filter(event=STAGED, school=str(school.pk)).exists()
                or Household.objects.filter(pk=household_id).exists() or Person.objects.filter(pk=sender_id).exists()):
            raise CommandError('Existing administrative scenario cannot be adopted or overwritten.')
        result = {'mode': 'PREFLIGHT', 'school_id': str(school.pk), 'release_certified': False}
        if not apply:
            return result
        Household.objects.create(id=household_id, household_name=f'Fictional presenter {school.pk} attendance household')
        Person.objects.create(id=sender_id, email=admin.email, first_name=admin.first_name, last_name=admin.last_name)
        result.update(seed_admin_context(student))
        SandboxEvent.objects.create(event=STAGED, school=str(school.pk), track='school', guidance='ops', persona='operator')
        return {**result, 'mode': 'STAGED'}


def _request_context(request, *, require_director_action=False):
    school = actor_scope(request, ('school_admin',))
    if (not user_has_permission(request.user, 'admin.view', school=school)
            or (require_director_action and not user_has_permission(request.user, 'director.actions', school=school))):
        from rest_framework.exceptions import NotFound
        raise NotFound('Not found.')
    if not SandboxEvent.objects.filter(event=STAGED, school=str(school.pk)).exists():
        raise ValidationError({'detail': 'Administrative scenario is not staged.'})
    return school, _context(school)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_state(request):
    _, (student, _, _) = _request_context(request)
    return Response(asdict(serialize_admin_student_state(student, request.user)))


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_resolve(request):
    if request.data:
        raise ValidationError({'detail': 'This fixed fictional workflow accepts no selectors.'})
    with transaction.atomic():
        # Root ownership lock serializes this mutation with generation rollover.
        _, (student, household_id, sender_id) = _request_context(request, require_director_action=True)
        household = Household.objects.get(pk=household_id)
        sender = Person.objects.get(pk=sender_id)
        return Response(resolve_admin_student_workflow(student, request.user, household=household, sender=sender))


urlpatterns = [path('state/', admin_state), path('resolve-operational-exception/', admin_resolve)]
