from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Student
from core.permissions import user_has_permission
from spiritual_life.api.serializers import PastoralNoteSerializer, PrayerRequestSerializer
from spiritual_life.models import PastoralNote, PrayerRequest

from .views import _get_school


PASTORAL_ROLE_CODES = {"HEAD_OF_SCHOOL", "head_of_school", "chaplain", "spiritual_life"}


def _is_pastoral_for_school(user, school) -> bool:
    if not user_has_permission(user, "spiritual_life.view", school=school):
        return False
    return user.roles.filter(school=school, role_code__in=PASTORAL_ROLE_CODES).exists()


class SecurePrayerRequestListCreate(APIView):
    serializer_class = PrayerRequestSerializer

    def get(self, request):
        school = _get_school(request)
        pastoral = _is_pastoral_for_school(request.user, school)
        qs = PrayerRequest.objects.filter(school=school)
        if not pastoral:
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
        pastoral = _is_pastoral_for_school(request.user, school)
        title = request.data.get("title", "").strip()
        body = request.data.get("body", "").strip()
        if not title or not body:
            return Response(
                {"error": "title and body are required."}, status=status.HTTP_400_BAD_REQUEST
            )

        visibility = request.data.get("visibility", "staff")
        if visibility == "private" and not pastoral:
            return Response(
                {"error": "Only tenant-authorized pastoral staff may create private prayer requests."},
                status=status.HTTP_403_FORBIDDEN,
            )

        student = None
        student_id = request.data.get("student_id")
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
        return Response(PrayerRequestSerializer(obj).data, status=status.HTTP_201_CREATED)


class SecurePrayerRequestDetail(APIView):
    serializer_class = PrayerRequestSerializer

    def _get(self, pr_id, school):
        return get_object_or_404(PrayerRequest, id=pr_id, school=school)

    def get(self, request, pr_id):
        school = _get_school(request)
        pr = self._get(pr_id, school)
        if pr.visibility == "private" and not _is_pastoral_for_school(request.user, school):
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(PrayerRequestSerializer(pr).data)

    def patch(self, request, pr_id):
        school = _get_school(request)
        pr = self._get(pr_id, school)
        pastoral = _is_pastoral_for_school(request.user, school)
        owns_request = pr.submitted_by_id == request.user.id
        if not pastoral and not owns_request:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if pr.visibility == "private" and not pastoral:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if request.data.get("visibility") == "private" and not pastoral:
            return Response(status=status.HTTP_403_FORBIDDEN)

        for field in ["title", "body", "visibility", "status"]:
            if field in request.data:
                setattr(pr, field, request.data[field])
        pr.save()
        return Response(PrayerRequestSerializer(pr).data)


class SecurePastoralNoteListCreate(APIView):
    serializer_class = PastoralNoteSerializer

    def get(self, request):
        school = _get_school(request)
        if not _is_pastoral_for_school(request.user, school):
            return Response(status=status.HTTP_403_FORBIDDEN)
        qs = PastoralNote.objects.filter(school=school)
        student_id = request.query_params.get("student_id")
        if student_id:
            qs = qs.filter(student__id=student_id)
        return Response(PastoralNoteSerializer(qs[:500], many=True).data)

    def post(self, request):
        school = _get_school(request)
        if not _is_pastoral_for_school(request.user, school):
            return Response(status=status.HTTP_403_FORBIDDEN)
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


class SecurePastoralNoteDetail(APIView):
    serializer_class = PastoralNoteSerializer

    def _authorized(self, request, school):
        return _is_pastoral_for_school(request.user, school)

    def get(self, request, note_id):
        school = _get_school(request)
        if not self._authorized(request, school):
            return Response(status=status.HTTP_403_FORBIDDEN)
        note = get_object_or_404(PastoralNote, id=note_id, school=school)
        return Response(PastoralNoteSerializer(note).data)

    def patch(self, request, note_id):
        school = _get_school(request)
        if not self._authorized(request, school):
            return Response(status=status.HTTP_403_FORBIDDEN)
        note = get_object_or_404(PastoralNote, id=note_id, school=school)
        for field in ["note_date", "body", "is_sensitive"]:
            if field in request.data:
                setattr(note, field, request.data[field])
        note.save()
        return Response(PastoralNoteSerializer(note).data)

    def delete(self, request, note_id):
        school = _get_school(request)
        if not self._authorized(request, school):
            return Response(status=status.HTTP_403_FORBIDDEN)
        note = get_object_or_404(PastoralNote, id=note_id, school=school)
        note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
