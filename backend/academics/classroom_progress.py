"""Provisional category-weighted evidence preview, never report-card authority."""
from decimal import Decimal
from gradebook.models import GradeEntry
from .models import Assignment, AssignmentCategory, Enrollment, Grade, Submission


def progress_rows(school, sections, students):
    rows = []
    for enrollment in Enrollment.objects.filter(school_id=school, section__in=sections, student__in=students).select_related('section')[:200]:
        section = enrollment.section
        categories = list(AssignmentCategory.objects.filter(school_id=school, section=section, is_active=True))
        assignments = list(Assignment.objects.filter(school_id=school, section=section, is_published=True))
        entries = {e.assignment_id: e for e in GradeEntry.objects.filter(school_id=school, section=section, student=enrollment.student, assignment__in=assignments)}
        academic = {g.submission.assignment_id: g for g in Grade.objects.filter(school_id=school, submission__enrollment=enrollment, submission__assignment__in=assignments).select_related('submission')}
        buckets = {c.id: [Decimal('0'), Decimal('0'), 0] for c in categories}
        conflicts = []; sources = set()
        for a in assignments:
            entry, grade = entries.get(a.id), academic.get(a.id)
            if entry and entry.points_earned is not None and grade and (entry.points_earned != grade.numeric_score or entry.points_possible != a.points_possible):
                conflicts.append(str(a.id)); continue
            earned = entry.points_earned if entry and entry.points_earned is not None else grade.numeric_score if grade else None
            possible = entry.points_possible if entry and entry.points_earned is not None else a.points_possible
            if earned is None or possible is None or possible <= 0 or a.category_id not in buckets:
                continue
            sources.add('gradebook.GradeEntry' if entry and entry.points_earned is not None else 'academics.Grade')
            bucket = buckets[a.category_id]; bucket[0] += earned; bucket[1] += possible; bucket[2] += 1
        weight = sum((c.weight_percent for c in categories), Decimal('0'))
        complete = weight == Decimal('100') and all(0 <= c.weight_percent <= 100 for c in categories) and all(buckets[c.id][1] > 0 for c in categories if c.weight_percent > 0) and not conflicts
        percent = sum((buckets[c.id][0] / buckets[c.id][1] * c.weight_percent for c in categories if c.weight_percent > 0), Decimal('0')) if complete else None
        rows.append({'section_id': section.id, 'student_id': enrollment.student_id, 'weighted_preview_percent': percent,
            'policy_weight_total': weight, 'recorded_scored_assignments': sum(b[2] for b in buckets.values()), 'published_assignments': len(assignments),
            'grade_conflicts': conflicts, 'sources': sorted(sources), 'categories': [{'name': c.name, 'weight_percent': c.weight_percent, 'scored_assignments': buckets[c.id][2]} for c in categories],
            'limitation': 'Provisional recorded-evidence preview; incomplete categories, invalid weights or conflicts withhold the preview. Unscored work is not zero. This is not a report-card grade.'})
    return rows
