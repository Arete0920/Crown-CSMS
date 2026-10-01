import hashlib
import json
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from households.scoping import get_request_school_id
from .experience_access import classroom_scope
from .family_views import text
from .models import Section
from .planning_models import ClassroomSectionPlanning, ClassroomPlanningEvent
from .submission_workflow_views import _uuid


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def classroom_planning(request):
    school = get_request_school_id(request, required=True)
    sections, _ = classroom_scope(request.user, school, 'admin')
    data = request.data
    if not isinstance(data, dict): raise ValidationError('Request must be an object.')
    section = get_object_or_404(sections, id=_uuid(data.get('section_id'), 'section_id'))
    size = data.get('target_size')
    if type(size) is not int or not 1 <= size <= 500: raise ValidationError('Planning target must be an integer from 1 to 500.')
    version = data.get('version')
    if type(version) is not int or version < 0: raise ValidationError('Planning version must be a non-negative integer.')
    note = text(data, 'planning_note')
    key = _uuid(data.get('request_key'), 'request_key')
    fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    with transaction.atomic():
        get_user_model().objects.select_for_update().get(id=request.user.id)
        Section.objects.select_for_update().get(id=section.id)
        previous = ClassroomPlanningEvent.objects.filter(school_id=school, actor=request.user, request_key=key).first()
        if previous:
            return Response(previous.result) if previous.fingerprint == fingerprint else Response({'detail':'Retry key conflict.'}, status=409)
        plan = ClassroomSectionPlanning.objects.filter(school_id=school, section=section).first()
        if version != (plan.version if plan else 0): return Response({'detail':'Planning changed; refresh before saving.'}, status=409)
        if plan:
            plan.target_size=size; plan.planning_note=note; plan.updated_by=request.user; plan.version+=1; plan.save()
        else:
            plan=ClassroomSectionPlanning.objects.create(school_id=school, section=section, target_size=size, planning_note=note, updated_by=request.user)
        result={'saved':True, 'version':plan.version}
        ClassroomPlanningEvent.objects.create(school_id=school, section=section, actor=request.user, request_key=key, fingerprint=fingerprint, payload=data, result=result)
        return Response(result)
