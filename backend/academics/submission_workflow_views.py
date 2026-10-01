import hashlib
import json
from uuid import UUID
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from households.scoping import get_request_school_id
from .experience_access import classroom_scope, is_leader, taught_sections
from .models import Assignment, Enrollment, Submission, SubmissionRevision


def _uuid(value, field):
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        raise ValidationError(f'{field} must be a UUID.')


def _serialize(submission, audience):
    result = {'id': submission.id, 'version': submission.version, 'state': submission.status,
            'content': submission.draft_content, 'submitted_at': submission.submitted_at,
            'revisions': list(submission.revisions.values('id', 'sequence', 'action', 'content', 'feedback', 'created_at'))}
    if audience != 'student':
        result['revisions'] = [r for r in result['revisions'] if r['action'] != 'save_draft']
        if submission.status in {'draft', 'returned'}:
            result['content'] = ''
    return result


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def assignment_work(request, assignment_id):
    school_id = get_request_school_id(request, required=True)
    assignment = get_object_or_404(Assignment, id=assignment_id, school_id=school_id, section__school_id=school_id)
    manager = is_leader(request.user, school_id) or taught_sections(request.user, school_id).filter(id=assignment.section_id).exists()
    audience = request.query_params.get('audience', 'student')
    sections, students = classroom_scope(request.user, school_id, audience)
    if audience == 'board' or not sections.filter(id=assignment.section_id).exists():
        raise PermissionDenied('No access to this assignment.')
    if not manager and not assignment.is_published:
        raise PermissionDenied('Assignment is unpublished.')
    data = request.data if request.method == 'POST' else request.query_params
    student_id = _uuid(data.get('student_id'), 'student_id')
    enrollment = get_object_or_404(Enrollment, school_id=school_id, section=assignment.section,
                                   student_id=student_id, student__in=students)
    if request.method == 'GET':
        submission = Submission.objects.filter(school_id=school_id, assignment=assignment, enrollment=enrollment).first()
        result = _serialize(submission, audience) if submission else {'version': 0, 'state': 'assigned', 'content': '', 'revisions': [], 'submitted_at': None}
        return Response(result)
    action = data.get('action')
    if action not in {'save_draft', 'submit', 'return', 'feedback'}:
        raise ValidationError('Invalid work action.')
    owner = enrollment.student.account_id == request.user.id
    if action in {'save_draft', 'submit'} and not owner:
        raise PermissionDenied('Only the student may save or submit their own work.')
    if action in {'return', 'feedback'} and not manager:
        raise PermissionDenied('Only an assigned teacher or school leader may return work.')
    key = _uuid(data.get('request_key'), 'request_key')
    version = data.get('version')
    if isinstance(version, bool) or not isinstance(version, int) or version < 0:
        raise ValidationError('version must be a non-negative integer.')
    content = data.get('content', '')
    feedback = data.get('feedback', '')
    if not isinstance(content, str) or not isinstance(feedback, str) or max(len(content), len(feedback)) > 100000:
        raise ValidationError('Content and feedback must be text of at most 100000 characters.')
    if action == 'submit' and not content.strip():
        raise ValidationError('Write your work before submitting.')
    if action == 'return' and not feedback.strip():
        raise ValidationError('Return instructions are required.')
    fingerprint = hashlib.sha256(json.dumps([str(request.user.id), action, content, feedback, version]).encode()).hexdigest()
    with transaction.atomic():
        Enrollment.objects.select_for_update().get(id=enrollment.id)
        submission, _ = Submission.objects.get_or_create(school_id=school_id, assignment=assignment, enrollment=enrollment)
        replay = submission.revisions.filter(request_key=key).first()
        if replay:
            if replay.fingerprint != fingerprint:
                return Response({'detail': 'Retry key conflicts with an earlier action.'}, status=409)
            return Response(_serialize(submission, audience))
        if version != submission.version:
            return Response({'detail': 'Work changed elsewhere. Reload before saving.'}, status=409)
        if action in {'save_draft', 'submit'} and submission.status in {'submitted', 'late', 'graded'}:
            return Response({'detail': 'Teacher must return submitted work before revision.'}, status=409)
        if action == 'return' and submission.status not in {'submitted', 'late', 'graded'}:
            return Response({'detail': 'Only submitted work can be returned.'}, status=409)
        if action == 'save_draft':
            submission.draft_content = content
            submission.status = 'draft' if not submission.submitted_at else 'returned'
        elif action == 'submit':
            submission.draft_content = content
            submission.submitted_at = timezone.now()
            from .instruction_models import ClassroomDeadlineAdjustment
            adjustment = ClassroomDeadlineAdjustment.objects.filter(school_id=school_id, assignment=assignment, student=enrollment.student).first()
            effective_due = adjustment.due_date if adjustment else assignment.due_date
            submission.status = 'late' if effective_due and effective_due < timezone.localdate() else 'submitted'
        elif action == 'return':
            submission.status = 'returned'
        submission.version += 1
        submission.save()
        SubmissionRevision.objects.create(submission=submission, actor=request.user, sequence=submission.version,
                                           action=action, content=submission.draft_content if action in {'save_draft', 'submit'} else (submission.revisions.filter(action='submit').order_by('-sequence').values_list('content', flat=True).first() or ''), feedback=feedback,
                                           request_key=key, fingerprint=fingerprint)
        return Response(_serialize(submission, audience))
