"""Aggregate classroom oversight with explicit source and date definitions."""
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from households.scoping import get_request_school_id
from gradebook.models import GradeEntry
from signals.models import InterventionCase
from .experience_access import classroom_scope
from .experience_views import reporting_window, report_sections
from .models import Enrollment, Assignment, Submission, LessonPlan, TeacherAssignment
from .lesson_execution_models import LessonPlanLesson
from .instruction_models import ClassroomMasteryEvidence
from .collaboration_models import ClassroomRecord, ClassroomResponse
from .family_models import ClassroomFamilyThread
from .support_models import ClassroomInterventionLink, ClassroomRestorativeLink
from .experience_access import taught_sections
from .classroom_reporting import attendance_summary, coverage_rows, instructional_time_summary


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def classroom_leadership(request):
    school = get_request_school_id(request, required=True)
    audience = request.query_params.get('audience', 'admin')
    if audience not in {'admin', 'board'}:
        raise PermissionDenied('School leadership or board role required.')
    sections, _ = classroom_scope(request.user, school, audience)
    if request.query_params.get('section_id') or request.query_params.get('student_id'):
        raise ValidationError('Use term and date filters for this aggregate report.')
    start, end = reporting_window(request)
    target = request.query_params.get('target_class_size')
    if target is not None:
        if not isinstance(target, str) or not target.isascii() or not target.isdigit() or not 1 <= int(target) <= 1000:
            raise ValidationError('target_class_size must be an integer from 1 through 1000.')
        target = int(target)
    terms = list(sections.order_by('term').values_list('term', flat=True).distinct())
    if request.query_params.get('term'): sections = sections.filter(term=request.query_params['term'])
    enrollments = Enrollment.objects.filter(school_id=school, section__in=sections, student__school_id=school)
    assignments = Assignment.objects.filter(school_id=school, section__in=sections, due_date__range=(start, end))
    plans = LessonPlan.objects.filter(school_id=school, section__in=sections, plan_date__range=(start, end))
    lessons = LessonPlanLesson.objects.filter(school_id=school, lesson_plan__in=plans)
    records = ClassroomRecord.objects.filter(school_id=school, section__in=sections)
    activity = records.filter(created_at__date__range=(start, end))
    links = ClassroomInterventionLink.objects.filter(school_id=school, section__in=sections, case__school_id=school)
    cases = InterventionCase.objects.filter(school_id=school, id__in=links.values('case_id'))
    open_cases = cases.exclude(status='CLOSED')
    responses = ClassroomResponse.objects.filter(record__in=activity, created_at__date__range=(start, end))
    graded_pairs = set(GradeEntry.objects.filter(school_id=school, section__in=sections, points_earned__isnull=False).values_list('assignment_id', 'student_id'))
    pending = [s for s in Submission.objects.filter(school_id=school, assignment__in=assignments, enrollment__in=enrollments, submitted_at__isnull=False).select_related('grade', 'enrollment')
               if not hasattr(s, 'grade') and (s.assignment_id, s.enrollment.student_id) not in graded_pairs]
    summary = report_sections(school, sections, start, end)
    from django.contrib.auth import get_user_model
    from django.db.models import Q
    from core.models import UserRole
    section_rows = list(sections.select_related('course').order_by('term', 'id'))
    primary = {s.teacher_id for s in section_rows if s.teacher_id}
    staff_ids = TeacherAssignment.objects.filter(school_id=school, section__in=sections, staff__school_id=school).values('staff_id')
    teacher_roles = UserRole.objects.filter(school_id=school, role_code__in=['TEACHER', 'teacher']).values('user_id')
    teachers = get_user_model().objects.filter(Q(id__in=primary) | Q(staff_id__in=staff_ids),
        id__in=teacher_roles, is_active=True, staff__school_id=school, staff__status='ACTIVE', staff__role_type='TEACHER').select_related('staff').distinct()
    assigned = {teacher.id: set(taught_sections(teacher, school).filter(id__in=sections.values('id')).values_list('id', flat=True)) for teacher in teachers}
    sizes = dict(enrollments.values('section_id').annotate(n=Count('id')).values_list('section_id', 'n'))
    planning = [{'id': s.id, 'course': s.course.name, 'term': s.term, 'roster_size': sizes.get(s.id, 0),
                 'verified_teachers': sum(s.id in ids for ids in assigned.values())} for s in section_rows]
    coverage = coverage_rows(school, section_rows, lessons, start, end)
    summary.update(attendance_summary(school, sections, start, end))
    summary.update(instructional_time_summary(lessons))
    summary.update({'known_objective_section_pairs': sum(row['known_objectives'] for row in coverage),
                    'planned_objective_section_pairs': sum(row['planned_objectives'] for row in coverage),
                    'confirmed_taught_objective_section_pairs': sum(row['confirmed_taught_objectives'] for row in coverage),
                    'curriculum_alignment_issues': sum(row['alignment_issues'] for row in coverage),
                    'sections_without_objective_inventory': sum(row['known_objectives'] == 0 for row in coverage)})
    summary.update({'sections_without_verified_teacher': sum(row['verified_teachers'] == 0 for row in planning),
                    'largest_recorded_section': max(sizes.values(), default=0),
                    'target_class_size': target,
                    'sections_above_target': sum(row['roster_size'] > target for row in planning) if target else None,
                    'additional_sections_for_target': sum(max((row['roster_size'] + target - 1) // target - 1, 0) for row in planning) if target else None})
    summary.update({
        'unique_students': enrollments.values('student_id').distinct().count(),
        'pending_grading': len(pending),
        'planned_lesson_links': lessons.count(),
        'confirmed_taught_lessons': lessons.filter(delivery_status='taught', actual_completed_at__isnull=False).count(),
        'recorded_planned_minutes': lessons.aggregate(v=Sum('planned_minutes'))['v'],
        'recorded_actual_minutes': lessons.aggregate(v=Sum('actual_minutes'))['v'],
        'mastery_observations': ClassroomMasteryEvidence.objects.filter(school_id=school, assignment__section__in=sections, created_at__date__range=(start, end)).count(),
        'open_linked_support_cases': open_cases.count(),
        'overdue_linked_support_reviews': open_cases.filter(review_at__lt=timezone.now()).count(),
        'linked_cases_without_verified_owner': open_cases.filter(owner_account__isnull=True).count(),
        'unlinked_school_support_cases': InterventionCase.objects.filter(school_id=school).exclude(id__in=ClassroomInterventionLink.objects.filter(school_id=school).values('case_id')).exclude(status='CLOSED').count(),
        'overdue_accommodation_reviews': records.filter(kind__in=['accommodation', 'support_plan'], state='open', due_at__lt=timezone.now()).count(),
        'open_family_concerns': ClassroomFamilyThread.objects.filter(school_id=school, section__in=sections, kind='conversation', state='open').count(),
        'restorative_plans_created': ClassroomRestorativeLink.objects.filter(school_id=school, section__in=sections, incident__school_id=school, incident__occurred_at__date__range=(start, end)).count(),
        'service_opportunities': activity.filter(kind='service').count(),
        'family_service_participation': activity.filter(kind='family_service').count(),
        'portrait_linked_service': activity.filter(kind__in=['service', 'family_service'], metadata__has_key='portrait_domain_id').count(),
        'worldview_linked_service': activity.filter(kind__in=['service', 'family_service'], metadata__has_key='worldview_priority_id').count(),
        'service_responses': responses.filter(record__kind='service').count(),
        'resource_reflections': responses.filter(record__kind='resource').count(),
    })
    resource_costs = [r.metadata.get('cost_cents') for r in activity.filter(kind='resource')]
    valid_costs = [v for v in resource_costs if type(v) is int and v >= 0]
    summary['recorded_resource_cost_cents'] = sum(valid_costs) if valid_costs else None
    summary['recorded_interruption_minutes'] = sum(r.metadata.get('minutes', 0) for r in activity.filter(kind='interruption'))
    summary['definitions'].update({
        'window': 'Due assignments, scheduled plans and created activity use the selected dates. Open cases, reviews and concerns are current snapshots.',
        'pending_grading': 'Timestamped submissions for assignments due in the window, without a recorded grade in either grade store.',
        'minutes': 'Sums of recorded values only. Missing minutes remain unknown; a recorded zero is preserved.',
        'support': 'Linked cases follow the selected term. Unlinked cases are a separate school-wide current inventory.',
        'formation': 'Service opportunities and responses are participation evidence, not a measure of personal faith.',
        'resources': 'Recorded resource costs are declared planning costs, not purchases. Reflections do not prove resource effectiveness.',
        'curriculum': 'Planned links and confirmed taught lessons are distinct; neither count proves mastery.',
        'coverage': 'Coverage uses the current recorded course objective inventory per section. Repeated teaching links count once. Delivery is confirmed taught evidence within the selected plan dates. An empty objective inventory withholds the percentage; recorded inventory does not establish external curriculum completeness.',
        'attendance': 'Presence percentage is PRESENT plus TARDY divided by the frozen expected rosters of audited section-day sessions; ABSENT and EXCUSED remain in the denominator. Missing roster, identity or status evidence withholds the percentage. This is not a schoolwide attendance rate or a count of every scheduled school day.',
        'instructional_time': 'Actual/planned minutes for dated lesson links only. Any missing value or zero planned total withholds the ratio. The ratio can exceed 100 and is not an effectiveness score.',
        'planning': 'Roster sizes and verified staffing are current snapshots. Target class size is a planning scenario, not an approved room capacity. Additional sections assume current rosters can be divided evenly; no timetable, hiring or budget feasibility is inferred.',
    })
    result = {'source': 'live', 'audience': audience, 'generated_at': timezone.now(), 'from': start, 'to': end, 'terms': terms, 'summary': summary,
              'provenance': ['academics.Enrollment', 'academics.Assignment', 'academics.Submission', 'gradebook.GradeEntry', 'academics.LessonPlanLesson', 'academics.PublisherObjective', 'academics.ClassroomAttendanceSession', 'core.StudentIdentityLink', 'crown_api.AttendanceRecord', 'academics.ClassroomMasteryEvidence', 'signals.InterventionCase', 'academics.ClassroomRecord', 'academics.ClassroomFamilyThread'],
              'limitations': ['Operational counts do not establish classroom quality, instructional effectiveness or a spiritual score.', 'No attendance rate is inferred without a verified expected attendance denominator.', 'No teacher ranking or report-card policy is inferred.']}
    if audience == 'admin':
        result['curriculum_coverage'] = coverage
        result['sections'] = [{**row,
                              'plans': plans.filter(section=s).count(), 'planned_lessons': lessons.filter(lesson_plan__section=s).count(),
                              'confirmed_taught_lessons': lessons.filter(lesson_plan__section=s, delivery_status='taught', actual_completed_at__isnull=False).count()} for s, row in zip(section_rows, planning)]
        workloads = []
        for teacher in teachers:
            ids = assigned[teacher.id]
            seats = enrollments.filter(section_id__in=ids)
            workloads.append({'teacher_id': teacher.id, 'teacher': teacher.get_full_name() or teacher.username, 'sections': len(ids),
                              'section_enrollments': seats.count(), 'unique_students': seats.values('student_id').distinct().count(),
                              'assignments_due': assignments.filter(section_id__in=ids).count(),
                              'pending_grading': sum(s.enrollment.section_id in ids for s in pending),
                              'planned_minutes': lessons.filter(lesson_plan__section_id__in=ids).aggregate(v=Sum('planned_minutes'))['v']})
        result['teacher_workload'] = workloads
    return Response(result)
