from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from admissions.models import AdmissionsApplication


def get_priority_queue(user, school_id, academic_year):
    '''
    Build priority queue for Admissions Director.
    Returns list of dicts ready for template rendering.
    '''
    if not academic_year:
        return []

    # Get applications needing attention
    applications = AdmissionsApplication.objects.filter(
        school_id=school_id,
        academic_year=academic_year,
        status__in=[
            AdmissionsApplication.STATUS_SUBMITTED,
            AdmissionsApplication.STATUS_UNDER_REVIEW,
            AdmissionsApplication.STATUS_NEEDS_INFO,
        ]
    ).select_related('family', 'student', 'academic_year').order_by('-submitted_at')

    now = timezone.now()
    rows = []

    for app in applications:
        # Calculate days waiting
        if app.submitted_at:
            days_waiting = (now - app.submitted_at).days
        else:
            days_waiting = 0

        # Determine priority reason
        priority_reason = ''
        if app.status == AdmissionsApplication.STATUS_NEEDS_INFO:
            priority_reason = 'Needs Additional Info'
        elif not app.transcript_received:
            priority_reason = 'Missing Transcript'
        elif not app.essay_received:
            priority_reason = 'Missing Essay'
        elif app.recommendations_received < 2:
            priority_reason = f'Needs {2 - app.recommendations_received} More Recommendation(s)'
        elif days_waiting > 14:
            priority_reason = 'Waiting > 2 Weeks'
        elif app.status == AdmissionsApplication.STATUS_UNDER_REVIEW:
            priority_reason = 'Under Review'
        else:
            priority_reason = 'Recently Submitted'

        # Next action
        next_action_label = 'Review Application'
        next_action_url = f'/admissions/applications/{app.id}/'

        rows.append({
            'id': str(app.id),
            'family_name': app.family.family_name,
            'grade_applying': app.student.grade_level.name if app.student else 'N/A',
            'submitted_date': app.submitted_at.strftime('%Y-%m-%d') if app.submitted_at else 'Not Submitted',
            'days_waiting': days_waiting,
            'status_label': app.get_status_display(),
            'priority_reason': priority_reason,
            'next_action_label': next_action_label,
            'next_action_url': next_action_url,
            'gpa': f'{app.gpa:.2f}' if app.gpa else 'N/A',
            'test_score': app.test_score or 'N/A',
        })

    return rows


def dashboard(request):
    '''
    Admissions Director Dashboard - mirrors Financial Aid structure
    '''
    # For now, use hardcoded school/year (will wire persona resolver later)
    from core.models import School, AcademicYear
    
    school = School.objects.first()
    academic_year = AcademicYear.objects.filter(school=school, is_current=True).first()

    priority_queue = get_priority_queue(request.user, school.id if school else None, academic_year)

    context = {
        'page_title': 'Admissions Director',
        'school': school,
        'academic_year': academic_year,
        'priority_queue': priority_queue,
    }

    return render(request, 'admissions/dashboard.html', context)


def applications_list(request):
    '''Placeholder for applications list view'''
    return render(request, 'admissions/applications_list.html', {})


def application_detail(request, id):
    '''Placeholder for application detail view'''
    return render(request, 'admissions/application_detail.html', {'id': id})
