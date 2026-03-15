from __future__ import annotations

from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from households.scoping import get_request_school_id
from households.models import Student
from academics.models import Enrollment, Section, Course
from .models import GradeEntry


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_grades_summary(request, student_id):
    """
    GET /api/v1/gradebook/students/{student_id}/grades/ 
    
    Returns all grades for a specific student across all their enrolled sections.
    Designed for parent portal views.
    """
    school_id = get_request_school_id(request, required=True)
    
    # Verify student exists and is in scope
    try:
        student = Student.objects.get(pk=student_id, school_id=school_id)
    except Student.DoesNotExist:
        return Response({"detail": "Student not found"}, status=404)
    
    # Get all enrollments for this student
    enrollments = (
        Enrollment.objects
        .filter(student=student, section__school_id=school_id)
        .select_related("section", "section__course")
    )
    
    if not enrollments:
        return Response({
            "student_id": str(student.id),
            "student_name": f"{student.first_name} {student.last_name}",
            "courses": []
        })
    
    courses = []
    
    for enrollment in enrollments:
        section = enrollment.section
        
        # Get all grade entries for this student in this section
        grade_entries = (
            GradeEntry.objects
            .filter(
                student=student,
                section=section,
                school_id=school_id
            )
            .select_related("assignment")
            .order_by("assignment__name", "assignment_name")
        )
        
        # Calculate grade statistics
        total_points_possible = 0
        total_points_earned = 0
        assignments = []
        
        for entry in grade_entries:
            assignment_name = entry.assignment.name if entry.assignment else entry.assignment_name
            points_possible = entry.assignment.points_possible if entry.assignment else entry.points_possible
            points_earned = entry.points_earned
            
            assignments.append({
                "assignment_name": assignment_name or "Unknown Assignment",
                "points_possible": str(points_possible) if points_possible else "0.00",
                "points_earned": str(points_earned) if points_earned is not None else None,
                "percentage": round((points_earned / points_possible * 100), 1) if points_earned is not None and points_possible and points_possible > 0 else None,
                "date_assigned": entry.created_at.isoformat() if entry.created_at else None,
            })
            
            if points_possible and points_earned is not None:
                total_points_possible += float(points_possible)
                total_points_earned += float(points_earned)
        
        # Calculate overall course grade
        overall_percentage = None
        letter_grade = None
        if total_points_possible > 0:
            overall_percentage = round((total_points_earned / total_points_possible * 100), 1)
            # Simple letter grade calculation
            if overall_percentage >= 90:
                letter_grade = "A"
            elif overall_percentage >= 80:
                letter_grade = "B"
            elif overall_percentage >= 70:
                letter_grade = "C"
            elif overall_percentage >= 60:
                letter_grade = "D"
            else:
                letter_grade = "F"
        
        courses.append({
            "course_code": section.course.code if section.course else "Unknown",
            "course_name": section.course.name if section.course else "Unknown Course",
            "section_id": str(section.id),
            "term": section.term,
            "overall_percentage": overall_percentage,
            "letter_grade": letter_grade,
            "total_points_possible": total_points_possible,
            "total_points_earned": total_points_earned,
            "assignments_count": len(assignments),
            "assignments": assignments
        })
    
    return Response({
        "student_id": str(student.id),
        "student_name": f"{student.first_name} {student.last_name}", 
        "grade_level": student.grade_level or "Unknown",
        "courses": courses
    })