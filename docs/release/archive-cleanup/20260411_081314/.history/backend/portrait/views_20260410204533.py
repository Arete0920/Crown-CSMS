from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from core.audit import audit_event
from core.models import School
from core.permissions import CrownModulePermission

from .models import AdmissionsPoGRecord, PoGDomain, PoGDomainScore, PoGRubricLevel, PortraitConfig
from .serializers import (
    AdmissionsPoGRecordCreateSerializer,
    AdmissionsPoGRecordSerializer,
    AdmissionsPoGRecordUpdateSerializer,
    BatchDomainScoreSerializer,
    DryRunPreviewSerializer,
    NormalizeWeightsSerializer,
    PoGDomainSerializer,
    PoGDomainWriteSerializer,
    PoGDomainScoreWriteSerializer,
    PortraitConfigSerializer,
    PortraitConfigWriteSerializer,
)
from .services import (
    WeightEngine,
    build_portrait_record_summary,
    initialize_domain_scores,
    normalize_weights,
    validate_config,
)


def _current_school(request):
    school = getattr(request, "school", None)
    if school is not None:
        return school
    school_id = request.headers.get("X-School-Id") or request.query_params.get("school_id")
    if not school_id:
        return None
    return School.objects.filter(pk=school_id).first()


def _audit_portrait(request, event, **extra):
    audit_event(
        event,
        user=getattr(request, "user", None),
        school=_current_school(request),
        extra=extra or None,
    )


class PortraitConfigViewSet(viewsets.ModelViewSet):
    permission_classes = [CrownModulePermission("admissions.view", write_code="admissions.edit")]

    def get_queryset(self):
        school = _current_school(self.request)
        if school is None:
            return PortraitConfig.objects.none()
        return (
            PortraitConfig.objects.filter(school=school)
            .prefetch_related("domains__rubric_levels")
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return PortraitConfigWriteSerializer
        return PortraitConfigSerializer

    def perform_create(self, serializer):
        school = _current_school(self.request)
        if school is None:
            raise ValidationError({"detail": "Missing school context."})
        config = serializer.save(school=school)
        _audit_portrait(self.request, "portrait.config.created", config_id=str(config.id), active=config.is_active)

    def perform_update(self, serializer):
        config = serializer.save()
        _audit_portrait(self.request, "portrait.config.updated", config_id=str(config.id), active=config.is_active)

    def perform_destroy(self, instance):
        config_id = str(instance.id)
        instance.delete()
        _audit_portrait(self.request, "portrait.config.deleted", config_id=config_id)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        config = self.get_object()
        PortraitConfig.objects.filter(school=config.school, is_active=True).exclude(pk=config.pk).update(is_active=False)
        config.is_active = True
        config.save(update_fields=["is_active", "updated_at"])
        _audit_portrait(request, "portrait.config.activated", config_id=str(config.id))
        return Response({"status": "ok", "active_config_id": str(config.id)})

    @action(detail=True, methods=["get"])
    def validate(self, request, pk=None):
        config = self.get_object()
        errors = validate_config(config)
        return Response({"valid": not errors, "errors": errors})

    @action(detail=True, methods=["post"], url_path="normalize-weights")
    def normalize_weights_action(self, request, pk=None):
        config = self.get_object()
        payload = request.data or {}
        if not payload.get("weights"):
            payload = {
                "weights": {
                    str(domain.id): float(domain.weight)
                    for domain in config.domains.filter(is_active=True)
                }
            }
        serializer = NormalizeWeightsSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        normalized = normalize_weights(serializer.validated_data["weights"])

        for domain in config.domains.filter(pk__in=list(normalized.keys())):
            domain.weight = normalized[str(domain.id)]
            domain.save(update_fields=["weight", "updated_at"])

        return Response({"weights": {key: str(value) for key, value in normalized.items()}})

    @action(detail=True, methods=["post"], url_path="dry-run")
    def dry_run(self, request, pk=None):
        config = self.get_object()
        serializer = DryRunPreviewSerializer(
            data={
                "config_id": str(config.id),
                "domain_scores": request.data.get("domain_scores", {}),
            }
        )
        serializer.is_valid(raise_exception=True)

        class _PreviewRecord:
            def __init__(self, cfg):
                self.config = cfg

        result = WeightEngine(_PreviewRecord(config)).dry_run(serializer.validated_data["domain_scores"])
        return Response(result.to_dict())


class PoGDomainListCreateView(APIView):
    permission_classes = [CrownModulePermission("admissions.view", write_code="admissions.edit")]

    def _get_config(self, request, config_pk):
        school = _current_school(request)
        return get_object_or_404(PortraitConfig, pk=config_pk, school=school)

    def get(self, request, config_pk):
        config = self._get_config(request, config_pk)
        domains = config.domains.prefetch_related("rubric_levels").all().order_by("order")
        return Response(PoGDomainSerializer(domains, many=True).data)

    def post(self, request, config_pk):
        config = self._get_config(request, config_pk)
        serializer = PoGDomainWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        domain = serializer.save(
            config=config,
            school=config.school,
            order=serializer.validated_data.get("order", config.domains.count()),
        )
        _audit_portrait(request, "portrait.domain.created", config_id=str(config.id), domain_id=str(domain.id))
        return Response(PoGDomainSerializer(domain).data, status=status.HTTP_201_CREATED)


class PoGDomainDetailView(APIView):
    permission_classes = [CrownModulePermission("admissions.view", write_code="admissions.edit")]

    def _get_domain(self, request, config_pk, pk):
        school = _current_school(request)
        return get_object_or_404(PoGDomain, pk=pk, config_id=config_pk, school=school)

    def get(self, request, config_pk, pk):
        domain = self._get_domain(request, config_pk, pk)
        return Response(PoGDomainSerializer(domain).data)

    def patch(self, request, config_pk, pk):
        domain = self._get_domain(request, config_pk, pk)
        serializer = PoGDomainWriteSerializer(domain, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        domain = serializer.save()
        _audit_portrait(request, "portrait.domain.updated", config_id=str(domain.config_id), domain_id=str(domain.id))
        return Response(PoGDomainSerializer(domain).data)

    def delete(self, request, config_pk, pk):
        domain = self._get_domain(request, config_pk, pk)
        domain_id = str(domain.id)
        domain.delete()
        _audit_portrait(request, "portrait.domain.deleted", config_id=str(config_pk), domain_id=domain_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PoGDomainReorderView(APIView):
    permission_classes = [CrownModulePermission("admissions.view", write_code="admissions.edit")]

    def post(self, request, config_pk):
        school = _current_school(request)
        config = get_object_or_404(PortraitConfig, pk=config_pk, school=school)
        ordered_ids = request.data.get("domain_ids") or request.data.get("ordered_ids") or []
        domain_lookup = {str(domain.id): domain for domain in config.domains.all()}

        for index, domain_id in enumerate(ordered_ids):
            domain = domain_lookup.get(str(domain_id))
            if domain is None:
                continue
            domain.order = index
            domain.save(update_fields=["order", "updated_at"])

        refreshed = config.domains.prefetch_related("rubric_levels").all().order_by("order")
        _audit_portrait(request, "portrait.domain.reordered", config_id=str(config.id), count=len(ordered_ids))
        return Response(PoGDomainSerializer(refreshed, many=True).data)


class AdmissionsPoGRecordViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [CrownModulePermission("admissions.view", write_code="admissions.edit")]

    def get_queryset(self):
        school = _current_school(self.request)
        if school is None:
            return AdmissionsPoGRecord.objects.none()
        queryset = (
            AdmissionsPoGRecord.objects.filter(school=school)
            .select_related("config", "scored_by")
            .prefetch_related("domain_scores__domain", "domain_scores__rubric_level")
            .order_by("-scored_at")
        )
        applicant_id = self.request.query_params.get("applicant_id")
        if applicant_id:
            queryset = queryset.filter(applicant_id=str(applicant_id))
        recommendation = self.request.query_params.get("recommendation")
        if recommendation:
            queryset = queryset.filter(recommendation=recommendation)
        context = self.request.query_params.get("context")
        if context:
            queryset = queryset.filter(context=context)
        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return AdmissionsPoGRecordCreateSerializer
        if self.action in {"update", "partial_update"}:
            return AdmissionsPoGRecordUpdateSerializer
        return AdmissionsPoGRecordSerializer

    def create(self, request, *args, **kwargs):
        school = _current_school(request)
        if school is None:
            return Response({"detail": "Missing school context."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        config = serializer.validated_data.get("config")
        if config is None:
            config = PortraitConfig.objects.filter(school=school, is_active=True).order_by("-created_at").first()
        elif config.school_id != school.id:
            return Response(
                {"detail": "Selected Portrait config does not belong to this school."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if config is None:
            return Response(
                {"detail": "No active Portrait config exists for this school."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        errors = validate_config(config)
        if errors:
            return Response({"detail": "Config is not ready for scoring.", "errors": errors}, status=400)

        record = AdmissionsPoGRecord.objects.create(
            school=school,
            applicant_id=serializer.validated_data["applicant_id"],
            config=config,
            context=serializer.validated_data.get("context", "interview"),
            scored_by=request.user if request.user.is_authenticated else None,
        )
        initialize_domain_scores(record)
        record.refresh_from_db()
        _audit_portrait(request, "portrait.record.created", record_id=str(record.id), applicant_id=record.applicant_id)
        return Response(AdmissionsPoGRecordSerializer(record).data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        record = serializer.save()
        _audit_portrait(
            self.request,
            "portrait.record.updated",
            record_id=str(record.id),
            applicant_id=record.applicant_id,
            recommendation=record.recommendation or "",
        )

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        school = _current_school(request)
        if school is None:
            return Response({"detail": "Missing school context."}, status=status.HTTP_400_BAD_REQUEST)
        limit = request.query_params.get("limit")
        try:
            parsed_limit = int(limit) if limit else 6
        except ValueError:
            parsed_limit = 6
        parsed_limit = max(1, min(parsed_limit, 20))
        _audit_portrait(request, "portrait.summary.viewed", limit=parsed_limit)
        return Response(build_portrait_record_summary(school, limit=parsed_limit))

    @action(detail=True, methods=["post"], url_path="score-domain")
    def score_domain(self, request, pk=None):
        record = self.get_object()
        serializer = PoGDomainScoreWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        domain = serializer.validated_data["domain"]
        if domain.config_id != record.config_id:
            return Response({"detail": "Domain does not belong to the record's active config."}, status=400)

        score_row, _ = PoGDomainScore.objects.get_or_create(
            record=record,
            domain=domain,
            defaults={"school": record.school},
        )
        for attr, value in serializer.validated_data.items():
            setattr(score_row, attr, value)
        score_row.school = record.school
        score_row.save()

        result = WeightEngine(record).compute()
        record.refresh_from_db()
        _audit_portrait(
            request,
            "portrait.record.scored_domain",
            record_id=str(record.id),
            applicant_id=record.applicant_id,
            recommendation=result.recommendation,
        )
        return Response({"record": AdmissionsPoGRecordSerializer(record).data, "compute": result.to_dict()})

    @action(detail=True, methods=["post"], url_path="score-batch")
    def score_batch(self, request, pk=None):
        record = self.get_object()
        serializer = BatchDomainScoreSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        for item in serializer.validated_data["scores"]:
            domain_ref = item["domain"]
            domain = get_object_or_404(PoGDomain, pk=domain_ref.pk, config=record.config, school=record.school)
            score_row, _ = PoGDomainScore.objects.get_or_create(
                record=record,
                domain=domain,
                defaults={"school": record.school},
            )
            score_row.score = item.get("score")
            score_row.notes = item.get("notes", score_row.notes or "")
            rubric_level_id = item.get("rubric_level_id")
            if rubric_level_id:
                score_row.rubric_level = get_object_or_404(PoGRubricLevel, pk=rubric_level_id, domain=domain)
            elif "rubric_level_id" in item:
                score_row.rubric_level = None
            score_row.save()

        result = None
        if serializer.validated_data.get("run_engine", True):
            result = WeightEngine(record).compute()
        record.refresh_from_db()
        _audit_portrait(
            request,
            "portrait.record.scored_batch",
            record_id=str(record.id),
            applicant_id=record.applicant_id,
            recommendation=(result.recommendation if result else (record.recommendation or "")),
        )
        return Response(
            {
                "record": AdmissionsPoGRecordSerializer(record).data,
                "compute": result.to_dict() if result else None,
            }
        )

    @action(detail=True, methods=["post"])
    def compute(self, request, pk=None):
        record = self.get_object()
        result = WeightEngine(record).compute()
        record.refresh_from_db()
        _audit_portrait(
            request,
            "portrait.record.computed",
            record_id=str(record.id),
            applicant_id=record.applicant_id,
            recommendation=result.recommendation,
        )
        return Response({"record": AdmissionsPoGRecordSerializer(record).data, "compute": result.to_dict()})


class ApplicantPoGView(APIView):
    permission_classes = [CrownModulePermission("admissions.view", write_code="admissions.edit")]

    def get(self, request, applicant_id):
        school = _current_school(request)
        if school is None:
            return Response({"exists": False, "detail": "Missing school context."}, status=400)

        record = (
            AdmissionsPoGRecord.objects.filter(school=school, applicant_id=str(applicant_id))
            .select_related("config", "scored_by")
            .prefetch_related("domain_scores__domain", "domain_scores__rubric_level")
            .order_by("-scored_at")
            .first()
        )
        if record is None:
            return Response({"exists": False}, status=404)
        return Response({"exists": True, "record": AdmissionsPoGRecordSerializer(record).data})
