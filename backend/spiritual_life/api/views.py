from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import School, Student
from households.scoping import get_request_school_id
from spiritual_life.models import (
    StudentSpiritualProfile,
    SpiritualAssessment,
    ChapelEvent,
    ChapelAttendance,
    SmallGroup,
    SmallGroupMember,
    SmallGroupSession,
    SmallGroupAttendance,
    PrayerRequest,
    PastoralNote,
)
from spiritual_life.api.serializers import (
    StudentSpiritualProfileSerializer,
    SpiritualAssessmentSerializer,
    ChapelEventSerializer,
    ChapelAttendanceSerializer,
    SmallGroupSerializer,
    SmallGroupMemberSerializer,
    SmallGroupSessionSerializer,
    SmallGroupAttendanceSerializer,
    PrayerRequestSerializer,
    PastoralNoteSerializer,
)


def _get_school(request) -> School:
    """
    Canonical tenant resolver for spiritual_life views.

    - Missing / invalid X-School-Id header → MissingSchoolContext (400)
    - Non-staff user pointing at wrong school → NotFound (404)
    - Staff users → pass-through
    """
    sid = get_request_school_id(request, required=True)
    return School.objects.get(pk=sid)


def _is_pastoral_staff(user) -> bool:
    """
    Pastoral / admin gate for PastoralNote access.
    Returns True for Django staff users, superusers, and HEAD_OF_SCHOOL role holders.
    """
    if user.is_staff or user.is_superuser:
        return True
    return user.roles.filter(role_code="HEAD_OF_SCHOOL").exists()


# ---------------------------------------------------------------------------
# Student Spiritual Profiles
# ---------------------------------------------------------------------------

class SpiritualProfileView(APIView):
    """
    GET  spiritual-life/profiles/          → list all profiles for school
    POST spiritual-life/profiles/          → create / upsert profile
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school = _get_school(request)
        qs = StudentSpiritualProfile.objects.filter(school=school).select_related(
            "student", "updated_by"
        )
        return Response(StudentSpiritualProfileSerializer(qs, many=True).data)

    def post(self, request):
        school = _get_school(request)
        student_id = request.data.get("student_id")
        if not student_id:
            return Response(
                {"error": "student_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        student = get_object_or_404(Student, id=student_id, school=school)
        profile, _ = StudentSpiritualProfile.objects.get_or_create(
            school=school, student=student
        )
        writable = [
            "faith_background",
            "baptized",
            "baptism_date",
            "spiritual_gifts",
            "notes",
        ]
        for field in writable:
            if field in request.data:
                setattr(profile, field, request.data[field])
        profile.updated_by = request.user
        profile.save()
        return Response(
            StudentSpiritualProfileSerializer(profile).data, status=status.HTTP_200_OK
        )


class SpiritualProfileDetailView(APIView):
    """
    GET   spiritual-life/profiles/<id>/   → retrieve
    PATCH spiritual-life/profiles/<id>/   → update
    """

    permission_classes = [permissions.IsAuthenticated]

    def _get(self, profile_id, school):
        return get_object_or_404(StudentSpiritualProfile, id=profile_id, school=school)

    def get(self, request, profile_id):
        school = _get_school(request)
        profile = self._get(profile_id, school)
        return Response(StudentSpiritualProfileSerializer(profile).data)

    def patch(self, request, profile_id):
        school = _get_school(request)
        profile = self._get(profile_id, school)
        writable = [
            "faith_background",
            "baptized",
            "baptism_date",
            "spiritual_gifts",
            "notes",
        ]
        for field in writable:
            if field in request.data:
                setattr(profile, field, request.data[field])
        profile.updated_by = request.user
        profile.save()
        return Response(StudentSpiritualProfileSerializer(profile).data)


# ---------------------------------------------------------------------------
# Spiritual Assessments
# ---------------------------------------------------------------------------

class SpiritualAssessmentListCreate(APIView):
    """
    GET  spiritual-life/assessments/   → list (filter: ?student_id=)
    POST spiritual-life/assessments/   → create
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school = _get_school(request)
        qs = SpiritualAssessment.objects.filter(school=school)
        student_id = request.query_params.get("student_id")
        if student_id:
            qs = qs.filter(student__id=student_id)
        return Response(SpiritualAssessmentSerializer(qs[:500], many=True).data)

    def post(self, request):
        school = _get_school(request)
        student_id = request.data.get("student_id")
        if not student_id:
            return Response(
                {"error": "student_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        assessment_title = request.data.get("assessment_title", "").strip()
        if not assessment_title:
            return Response(
                {"error": "assessment_title is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        assessment_date = request.data.get("assessment_date")
        if not assessment_date:
            return Response(
                {"error": "assessment_date is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        student = get_object_or_404(Student, id=student_id, school=school)
        obj = SpiritualAssessment.objects.create(
            school=school,
            student=student,
            administered_by=request.user,
            assessment_title=assessment_title,
            assessment_date=assessment_date,
            score=request.data.get("score"),
            max_score=request.data.get("max_score"),
            notes=request.data.get("notes", ""),
        )
        return Response(
            SpiritualAssessmentSerializer(obj).data, status=status.HTTP_201_CREATED
        )


# ---------------------------------------------------------------------------
# Chapel Events
# ---------------------------------------------------------------------------

class ChapelEventListCreate(APIView):
    """
    GET  spiritual-life/chapel-events/   → list (filter: ?date_from=, ?date_to=)
    POST spiritual-life/chapel-events/   → create
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school = _get_school(request)
        qs = ChapelEvent.objects.filter(school=school)
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        if date_from:
            qs = qs.filter(event_date__gte=date_from)
        if date_to:
            qs = qs.filter(event_date__lte=date_to)
        return Response(ChapelEventSerializer(qs[:500], many=True).data)

    def post(self, request):
        school = _get_school(request)
        title = request.data.get("title", "").strip()
        if not title:
            return Response(
                {"error": "title is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        event_date = request.data.get("event_date")
        if not event_date:
            return Response(
                {"error": "event_date is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        obj = ChapelEvent.objects.create(
            school=school,
            title=title,
            speaker=request.data.get("speaker", ""),
            event_date=event_date,
            start_time=request.data.get("start_time") or None,
            end_time=request.data.get("end_time") or None,
            location=request.data.get("location", ""),
            theme=request.data.get("theme", ""),
            scripture_reference=request.data.get("scripture_reference", ""),
            notes=request.data.get("notes", ""),
            created_by=request.user,
        )
        return Response(ChapelEventSerializer(obj).data, status=status.HTTP_201_CREATED)


class ChapelEventDetail(APIView):
    """GET / PATCH for a single ChapelEvent."""

    permission_classes = [permissions.IsAuthenticated]

    def _get(self, event_id, school):
        return get_object_or_404(ChapelEvent, id=event_id, school=school)

    def get(self, request, event_id):
        school = _get_school(request)
        return Response(ChapelEventSerializer(self._get(event_id, school)).data)

    def patch(self, request, event_id):
        school = _get_school(request)
        event = self._get(event_id, school)
        for field in ["title", "speaker", "event_date", "location", "theme",
                      "scripture_reference", "notes", "start_time", "end_time"]:
            if field in request.data:
                setattr(event, field, request.data[field] or None if field in ("start_time", "end_time") else request.data[field])
        event.save()
        return Response(ChapelEventSerializer(event).data)


class ChapelAttendanceListCreate(APIView):
    """
    GET  spiritual-life/chapel-events/<id>/attendance/  → list attendance
    POST spiritual-life/chapel-events/<id>/attendance/  → record attendance
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, event_id):
        school = _get_school(request)
        event = get_object_or_404(ChapelEvent, id=event_id, school=school)
        qs = ChapelAttendance.objects.filter(school=school, event=event)
        return Response(ChapelAttendanceSerializer(qs, many=True).data)

    def post(self, request, event_id):
        school = _get_school(request)
        event = get_object_or_404(ChapelEvent, id=event_id, school=school)
        student_id = request.data.get("student_id")
        if not student_id:
            return Response(
                {"error": "student_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        student = get_object_or_404(Student, id=student_id, school=school)
        att_status = request.data.get("status", "present")
        obj, created = ChapelAttendance.objects.get_or_create(
            school=school,
            event=event,
            student=student,
            defaults={"status": att_status, "recorded_by": request.user},
        )
        if not created:
            obj.status = att_status
            obj.recorded_by = request.user
            obj.save()
        resp_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(ChapelAttendanceSerializer(obj).data, status=resp_status)


# ---------------------------------------------------------------------------
# Small Groups
# ---------------------------------------------------------------------------

class SmallGroupListCreate(APIView):
    """
    GET  spiritual-life/small-groups/   → list active groups
    POST spiritual-life/small-groups/   → create group
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school = _get_school(request)
        qs = SmallGroup.objects.filter(school=school)
        active_only = request.query_params.get("active_only", "true").lower()
        if active_only != "false":
            qs = qs.filter(is_active=True)
        return Response(SmallGroupSerializer(qs[:200], many=True).data)

    def post(self, request):
        school = _get_school(request)
        name = request.data.get("name", "").strip()
        if not name:
            return Response(
                {"error": "name is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        obj = SmallGroup.objects.create(
            school=school,
            name=name,
            leader=request.user,
            description=request.data.get("description", ""),
        )
        return Response(SmallGroupSerializer(obj).data, status=status.HTTP_201_CREATED)


class SmallGroupMemberListCreate(APIView):
    """
    GET  spiritual-life/small-groups/<id>/members/   → list members
    POST spiritual-life/small-groups/<id>/members/   → add member
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, group_id):
        school = _get_school(request)
        group = get_object_or_404(SmallGroup, id=group_id, school=school)
        qs = SmallGroupMember.objects.filter(school=school, group=group)
        return Response(SmallGroupMemberSerializer(qs, many=True).data)

    def post(self, request, group_id):
        school = _get_school(request)
        group = get_object_or_404(SmallGroup, id=group_id, school=school)
        student_id = request.data.get("student_id")
        if not student_id:
            return Response(
                {"error": "student_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        student = get_object_or_404(Student, id=student_id, school=school)
        obj, created = SmallGroupMember.objects.get_or_create(
            school=school, group=group, student=student
        )
        resp_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(SmallGroupMemberSerializer(obj).data, status=resp_status)


class SmallGroupSessionListCreate(APIView):
    """
    GET  spiritual-life/small-groups/<id>/sessions/   → list sessions
    POST spiritual-life/small-groups/<id>/sessions/   → create session
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, group_id):
        school = _get_school(request)
        group = get_object_or_404(SmallGroup, id=group_id, school=school)
        qs = SmallGroupSession.objects.filter(school=school, group=group)
        return Response(SmallGroupSessionSerializer(qs[:200], many=True).data)

    def post(self, request, group_id):
        school = _get_school(request)
        group = get_object_or_404(SmallGroup, id=group_id, school=school)
        session_date = request.data.get("session_date")
        if not session_date:
            return Response(
                {"error": "session_date is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        obj = SmallGroupSession.objects.create(
            school=school,
            group=group,
            session_date=session_date,
            topic=request.data.get("topic", ""),
            scripture_reference=request.data.get("scripture_reference", ""),
            notes=request.data.get("notes", ""),
        )
        return Response(
            SmallGroupSessionSerializer(obj).data, status=status.HTTP_201_CREATED
        )


class SmallGroupSessionAttendanceView(APIView):
    """
    GET  spiritual-life/small-group-sessions/<id>/attendance/
    POST spiritual-life/small-group-sessions/<id>/attendance/
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, session_id):
        school = _get_school(request)
        session = get_object_or_404(SmallGroupSession, id=session_id, school=school)
        qs = SmallGroupAttendance.objects.filter(school=school, session=session)
        return Response(SmallGroupAttendanceSerializer(qs, many=True).data)

    def post(self, request, session_id):
        school = _get_school(request)
        session = get_object_or_404(SmallGroupSession, id=session_id, school=school)
        member_id = request.data.get("member_id")
        if not member_id:
            return Response(
                {"error": "member_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        member = get_object_or_404(
            SmallGroupMember, id=member_id, school=school, group=session.group
        )
        att_status = request.data.get("status", "present")
        obj, created = SmallGroupAttendance.objects.get_or_create(
            school=school,
            session=session,
            member=member,
            defaults={"status": att_status},
        )
        if not created:
            obj.status = att_status
            obj.save()
        resp_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(SmallGroupAttendanceSerializer(obj).data, status=resp_status)


# ---------------------------------------------------------------------------
# Prayer Requests
# ---------------------------------------------------------------------------

class PrayerRequestListCreate(APIView):
    """
    GET  spiritual-life/prayer-requests/   → list (filter: ?status=, ?visibility=)
    POST spiritual-life/prayer-requests/   → create
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school = _get_school(request)
        qs = PrayerRequest.objects.filter(school=school)

        # Non-staff users cannot see "private" visibility requests (pastoral-only)
        if not _is_pastoral_staff(request.user):
            qs = qs.exclude(visibility="private")

        status_q = request.query_params.get("status")
        if status_q:
            qs = qs.filter(status=status_q)
        visibility_q = request.query_params.get("visibility")
        if visibility_q:
            qs = qs.filter(visibility=visibility_q)

        return Response(PrayerRequestSerializer(qs[:500], many=True).data)

    def post(self, request):
        school = _get_school(request)
        title = request.data.get("title", "").strip()
        body = request.data.get("body", "").strip()
        if not title or not body:
            return Response(
                {"error": "title and body are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        visibility = request.data.get("visibility", "staff")
        # Only pastoral staff can create private visibility requests
        if visibility == "private" and not _is_pastoral_staff(request.user):
            return Response(
                {"error": "Only pastoral staff may create private prayer requests."},
                status=status.HTTP_403_FORBIDDEN,
            )
        student_id = request.data.get("student_id")
        student = None
        if student_id:
            student = get_object_or_404(Student, id=student_id, school=school)
        obj = PrayerRequest.objects.create(
            school=school,
            student=student,
            submitted_by=request.user,
            title=title,
            body=body,
            visibility=visibility,
            status=request.data.get("status", "open"),
        )
        return Response(
            PrayerRequestSerializer(obj).data, status=status.HTTP_201_CREATED
        )


class PrayerRequestDetail(APIView):
    """GET / PATCH a single PrayerRequest."""

    permission_classes = [permissions.IsAuthenticated]

    def _get(self, pr_id, school):
        return get_object_or_404(PrayerRequest, id=pr_id, school=school)

    def get(self, request, pr_id):
        school = _get_school(request)
        pr = self._get(pr_id, school)
        if pr.visibility == "private" and not _is_pastoral_staff(request.user):
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(PrayerRequestSerializer(pr).data)

    def patch(self, request, pr_id):
        school = _get_school(request)
        pr = self._get(pr_id, school)
        if pr.visibility == "private" and not _is_pastoral_staff(request.user):
            return Response(status=status.HTTP_403_FORBIDDEN)
        for field in ["title", "body", "visibility", "status"]:
            if field in request.data:
                setattr(pr, field, request.data[field])
        pr.save()
        return Response(PrayerRequestSerializer(pr).data)


# ---------------------------------------------------------------------------
# Pastoral Notes — Staff / HEAD_OF_SCHOOL ONLY
# ---------------------------------------------------------------------------

class PastoralNoteListCreate(APIView):
    """
    GET  spiritual-life/pastoral-notes/   → list (filter: ?student_id=)
    POST spiritual-life/pastoral-notes/   → create
    Staff / HEAD_OF_SCHOOL only.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not _is_pastoral_staff(request.user):
            return Response(status=status.HTTP_403_FORBIDDEN)
        school = _get_school(request)
        qs = PastoralNote.objects.filter(school=school)
        student_id = request.query_params.get("student_id")
        if student_id:
            qs = qs.filter(student__id=student_id)
        return Response(PastoralNoteSerializer(qs[:500], many=True).data)

    def post(self, request):
        if not _is_pastoral_staff(request.user):
            return Response(status=status.HTTP_403_FORBIDDEN)
        school = _get_school(request)
        student_id = request.data.get("student_id")
        body = request.data.get("body", "").strip()
        note_date = request.data.get("note_date")
        if not student_id or not body or not note_date:
            return Response(
                {"error": "student_id, body, and note_date are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        student = get_object_or_404(Student, id=student_id, school=school)
        obj = PastoralNote.objects.create(
            school=school,
            student=student,
            author=request.user,
            note_date=note_date,
            body=body,
            is_sensitive=request.data.get("is_sensitive", True),
        )
        return Response(PastoralNoteSerializer(obj).data, status=status.HTTP_201_CREATED)


class PastoralNoteDetail(APIView):
    """GET / PATCH / DELETE a single PastoralNote. Staff only."""

    permission_classes = [permissions.IsAuthenticated]

    def _require_pastoral(self, user):
        if not _is_pastoral_staff(user):
            return Response(status=status.HTTP_403_FORBIDDEN)
        return None

    def get(self, request, note_id):
        denied = self._require_pastoral(request.user)
        if denied:
            return denied
        school = _get_school(request)
        note = get_object_or_404(PastoralNote, id=note_id, school=school)
        return Response(PastoralNoteSerializer(note).data)

    def patch(self, request, note_id):
        denied = self._require_pastoral(request.user)
        if denied:
            return denied
        school = _get_school(request)
        note = get_object_or_404(PastoralNote, id=note_id, school=school)
        for field in ["note_date", "body", "is_sensitive"]:
            if field in request.data:
                setattr(note, field, request.data[field])
        note.save()
        return Response(PastoralNoteSerializer(note).data)

    def delete(self, request, note_id):
        denied = self._require_pastoral(request.user)
        if denied:
            return denied
        school = _get_school(request)
        note = get_object_or_404(PastoralNote, id=note_id, school=school)
        note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
