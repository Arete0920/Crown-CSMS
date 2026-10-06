from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from core.permissions import CrownModulePermission, user_has_permission
from households.scoping import get_request_school_id

from .governance import clone_version, create_new_draft, transition_version
from .models import CurriculumMap, CurriculumMapVersion, Lesson, Unit
from .serializers import (
    CurriculumMapSerializer,
    CurriculumMapVersionSerializer,
    LessonSerializer,
    UnitSerializer,
)


def _school_id(request):
    return get_request_school_id(request, required=True)


def _require_permission(request, code, message):
    school = getattr(request, "school", None)
    if school is None or not user_has_permission(request.user, code, school=school):
        raise PermissionDenied(message)
    return school.id


def _raise_drf_validation(exc: DjangoValidationError):
    if hasattr(exc, "message_dict"):
        raise ValidationError(exc.message_dict) from exc
    raise ValidationError(getattr(exc, "messages", [str(exc)])) from exc


class CurriculumMapViewSet(viewsets.ModelViewSet):
    serializer_class = CurriculumMapSerializer
    permission_classes = [CrownModulePermission("curriculum.view", write_code="curriculum.edit")]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CurriculumMap.objects.none()
        school_id = _school_id(self.request)
        qs = CurriculumMap.objects.filter(school_id=school_id)
        course_id = self.request.query_params.get("course_id")
        active = self.request.query_params.get("active")
        if course_id:
            qs = qs.filter(course_id=course_id)
        if active in {"true", "false"}:
            qs = qs.filter(active=(active == "true"))
        return qs.select_related("course").prefetch_related("versions").order_by("course__code", "title")

    def create(self, request, *args, **kwargs):
        school_id = _require_permission(request, "curriculum.edit", "Curriculum map creation requires curriculum.edit.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                curriculum_map = serializer.save(school_id=school_id)
                version = create_new_draft(
                    curriculum_map=curriculum_map,
                    actor=request.user,
                    change_summary=request.data.get("change_summary", ""),
                )
        except DjangoValidationError as exc:
            _raise_drf_validation(exc)
        data = self.get_serializer(curriculum_map).data
        data["initial_version"] = CurriculumMapVersionSerializer(version).data
        return Response(data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        school_id = _require_permission(self.request, "curriculum.edit", "Curriculum map updates require curriculum.edit.")
        try:
            serializer.save(school_id=school_id)
        except DjangoValidationError as exc:
            _raise_drf_validation(exc)

    def perform_destroy(self, instance):
        _require_permission(self.request, "curriculum.edit", "Curriculum map deletion requires curriculum.edit.")
        try:
            instance.delete()
        except DjangoValidationError as exc:
            _raise_drf_validation(exc)

    @action(detail=True, methods=["get", "post"], url_path="versions")
    def versions(self, request, pk=None):
        curriculum_map = self.get_object()
        school_id = _school_id(request)
        if request.method == "GET":
            versions = (
                curriculum_map.versions.filter(school_id=school_id)
                .select_related("submitted_by", "approved_by")
                .prefetch_related("events")
            )
            return Response(CurriculumMapVersionSerializer(versions, many=True).data)

        _require_permission(request, "curriculum.edit", "Curriculum version creation requires curriculum.edit.")
        try:
            version = create_new_draft(
                curriculum_map=curriculum_map,
                actor=request.user,
                change_summary=request.data.get("change_summary", ""),
            )
        except DjangoValidationError as exc:
            _raise_drf_validation(exc)
        return Response(CurriculumMapVersionSerializer(version).data, status=status.HTTP_201_CREATED)


class CurriculumMapVersionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CurriculumMapVersionSerializer
    permission_classes = [CrownModulePermission("curriculum.view", write_code="curriculum.edit")]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CurriculumMapVersion.objects.none()
        school_id = _school_id(self.request)
        qs = CurriculumMapVersion.objects.filter(school_id=school_id)
        curriculum_map_id = self.request.query_params.get("curriculum_map_id")
        version_status = self.request.query_params.get("status")
        if curriculum_map_id:
            qs = qs.filter(curriculum_map_id=curriculum_map_id)
        if version_status:
            qs = qs.filter(status=version_status)
        return qs.select_related("curriculum_map", "submitted_by", "approved_by").prefetch_related("events")

    @action(detail=True, methods=["post"], url_path="transition")
    def transition(self, request, pk=None):
        version = self.get_object()
        target = request.data.get("status", "")
        permission_code = (
            "curriculum.publish"
            if target in {
                CurriculumMapVersion.Status.APPROVED,
                CurriculumMapVersion.Status.PUBLISHED,
                CurriculumMapVersion.Status.RETIRED,
            }
            else "curriculum.edit"
        )
        _require_permission(request, permission_code, f"Curriculum transition to {target or 'unknown'} requires {permission_code}.")
        try:
            updated = transition_version(
                version=version,
                target_status=target,
                actor=request.user,
                notes=request.data.get("notes", ""),
            )
        except DjangoValidationError as exc:
            _raise_drf_validation(exc)
        return Response(CurriculumMapVersionSerializer(updated).data)

    @action(detail=True, methods=["post"], url_path="clone")
    def clone(self, request, pk=None):
        _require_permission(request, "curriculum.edit", "Curriculum version cloning requires curriculum.edit.")
        source = self.get_object()
        try:
            cloned = clone_version(
                source=source,
                actor=request.user,
                change_summary=request.data.get("change_summary", ""),
            )
        except DjangoValidationError as exc:
            _raise_drf_validation(exc)
        return Response(CurriculumMapVersionSerializer(cloned).data, status=status.HTTP_201_CREATED)


class UnitViewSet(viewsets.ModelViewSet):
    serializer_class = UnitSerializer
    permission_classes = [CrownModulePermission("curriculum.view", write_code="curriculum.edit")]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Unit.objects.none()
        school_id = _school_id(self.request)
        qs = Unit.objects.filter(school_id=school_id)
        curriculum_map_id = self.request.query_params.get("curriculum_map_id")
        curriculum_version_id = self.request.query_params.get("curriculum_version_id")
        if curriculum_map_id:
            qs = qs.filter(curriculum_map_id=curriculum_map_id)
        if curriculum_version_id:
            qs = qs.filter(curriculum_version_id=curriculum_version_id)
        return qs.select_related("curriculum_map", "curriculum_version").order_by("curriculum_map", "sequence")

    def perform_create(self, serializer):
        school_id = _require_permission(self.request, "curriculum.edit", "Curriculum unit creation requires curriculum.edit.")
        try:
            serializer.save(school_id=school_id)
        except DjangoValidationError as exc:
            _raise_drf_validation(exc)

    perform_update = perform_create

    def perform_destroy(self, instance):
        _require_permission(self.request, "curriculum.edit", "Curriculum unit deletion requires curriculum.edit.")
        try:
            instance.delete()
        except DjangoValidationError as exc:
            _raise_drf_validation(exc)


class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    permission_classes = [CrownModulePermission("curriculum.view", write_code="curriculum.edit")]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Lesson.objects.none()
        school_id = _school_id(self.request)
        qs = Lesson.objects.filter(school_id=school_id)
        unit_id = self.request.query_params.get("unit_id")
        curriculum_version_id = self.request.query_params.get("curriculum_version_id")
        if unit_id:
            qs = qs.filter(unit_id=unit_id)
        if curriculum_version_id:
            qs = qs.filter(unit__curriculum_version_id=curriculum_version_id)
        return qs.select_related("unit", "unit__curriculum_map", "unit__curriculum_version").order_by("unit", "sequence")

    def perform_create(self, serializer):
        school_id = _require_permission(self.request, "curriculum.edit", "Curriculum lesson creation requires curriculum.edit.")
        try:
            serializer.save(school_id=school_id)
        except DjangoValidationError as exc:
            _raise_drf_validation(exc)

    perform_update = perform_create

    def perform_destroy(self, instance):
        _require_permission(self.request, "curriculum.edit", "Curriculum lesson deletion requires curriculum.edit.")
        try:
            instance.delete()
        except DjangoValidationError as exc:
            _raise_drf_validation(exc)
