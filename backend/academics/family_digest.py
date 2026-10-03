"""Read-only weekly homework agenda from scoped enrollments and approved deadlines."""
from django.db.models import F, OuterRef, Subquery
from django.db.models.functions import Coalesce

from .instruction_models import ClassroomDeadlineAdjustment
from .models import Assignment, Submission


def weekly_agenda(school, sections, students, start, end, *, limit=100):
    # Each row is one published assignment for one authorized, enrolled child.
    adjustments = ClassroomDeadlineAdjustment.objects.filter(
        school_id=school, assignment_id=OuterRef('pk'),
        student_id=OuterRef('section__enrollments__student_id'),
    )
    tasks = Assignment.objects.filter(
        school_id=school, section__in=sections, is_published=True,
        category__school_id=school, category__section_id=F('section_id'),
        section__enrollments__school_id=school,
        section__enrollments__student__in=students,
    ).annotate(
        student_key=F('section__enrollments__student_id'),
        enrollment_key=F('section__enrollments__id'),
        first_name=F('section__enrollments__student__first_name'),
        last_name=F('section__enrollments__student__last_name'),
        effective_due=Coalesce(Subquery(adjustments.values('due_date')[:1]), F('due_date')),
        makeup_instructions=Subquery(adjustments.values('instructions')[:1]),
    ).filter(effective_due__range=(start, end)).select_related('section__course').order_by(
        'effective_due', 'last_name', 'first_name', 'student_key', 'name', 'id',
    )
    total = tasks.count()
    rows = list(tasks[:limit])
    submissions = Submission.objects.filter(
        school_id=school, assignment__school_id=school,
        assignment__is_published=True, assignment__category__school_id=school,
        assignment__category__section_id=F('assignment__section_id'),
        enrollment__school_id=school, enrollment__student__in=students,
        enrollment__section__in=sections,
        assignment__section_id=F('enrollment__section_id'),
    )
    # Count the full window, even when the visible assignment list is capped.
    receipt_deadlines = ClassroomDeadlineAdjustment.objects.filter(
        school_id=school, assignment_id=OuterRef('assignment_id'),
        student_id=OuterRef('enrollment__student_id'),
    )
    recorded = submissions.annotate(effective_due=Coalesce(
        Subquery(receipt_deadlines.values('due_date')[:1]), F('assignment__due_date'),
    )).filter(effective_due__range=(start, end), submitted_at__isnull=False).count()
    visible = submissions.filter(
        assignment_id__in=[row.id for row in rows],
        enrollment_id__in=[row.enrollment_key for row in rows],
    )
    receipts = {(row.assignment_id, row.enrollment_id): row for row in visible}
    agenda = []
    for row in rows:
        receipt = receipts.get((row.id, row.enrollment_key))
        agenda.append({
            'id': row.id, 'section_id': row.section_id, 'name': row.name,
            'student_id': row.student_key, 'student_name': f'{row.first_name} {row.last_name}',
            'course': row.section.course.name, 'due_date': row.effective_due,
            'original_due_date': row.due_date, 'home_support': row.home_support,
            'makeup_instructions': row.makeup_instructions or '',
            'submission_state': receipt.status if receipt else 'assigned',
            'submitted_at': receipt.submitted_at if receipt else None,
        })
    return {'assignments': agenda, 'assignments_total': total,
            'truncated': total > limit, 'recorded_submissions': recorded}
