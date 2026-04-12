from decimal import Decimal

from rest_framework import serializers

from .models import (
    AdmissionsPoGRecord,
    PoGDomain,
    PoGDomainScore,
    PoGRubricLevel,
    PortraitConfig,
    RECOMMENDATION_CHOICES,
)
from .services import normalize_weights, validate_config


class PoGRubricLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PoGRubricLevel
        fields = ["id", "level", "label", "descriptor"]


class PoGRubricLevelWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PoGRubricLevel
        fields = ["level", "label", "descriptor"]

    def validate_level(self, value):
        if value not in range(1, 6):
            raise serializers.ValidationError("Level must be between 1 and 5.")
        return value


class PoGDomainSerializer(serializers.ModelSerializer):
    rubric_levels = PoGRubricLevelSerializer(many=True, read_only=True)
    weight_percentage = serializers.ReadOnlyField()

    class Meta:
        model = PoGDomain
        fields = [
            "id",
            "name",
            "domain_type",
            "description",
            "scripture_reference",
            "weight",
            "weight_percentage",
            "is_faith_anchor",
            "is_active",
            "order",
            "rubric_levels",
        ]


class PoGDomainWriteSerializer(serializers.ModelSerializer):
    rubric_levels = PoGRubricLevelWriteSerializer(many=True)

    class Meta:
        model = PoGDomain
        fields = [
            "id",
            "name",
            "domain_type",
            "description",
            "scripture_reference",
            "weight",
            "is_faith_anchor",
            "is_active",
            "order",
            "rubric_levels",
        ]

    def validate_rubric_levels(self, value):
        levels = sorted(row["level"] for row in value)
        if levels != [1, 2, 3, 4, 5]:
            raise serializers.ValidationError(
                "Exactly 5 rubric levels are required, one for each score 1–5."
            )
        return value

    def validate_weight(self, value):
        if value <= 0 or value > 1:
            raise serializers.ValidationError("Weight must be between 0.0001 and 1.0000.")
        return value

    def create(self, validated_data):
        rubric_data = validated_data.pop("rubric_levels", [])
        domain = PoGDomain.objects.create(**validated_data)
        for row in rubric_data:
            PoGRubricLevel.objects.create(domain=domain, school=domain.school, **row)
        return domain

    def update(self, instance, validated_data):
        rubric_data = validated_data.pop("rubric_levels", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if rubric_data is not None:
            instance.rubric_levels.all().delete()
            for row in rubric_data:
                PoGRubricLevel.objects.create(domain=instance, school=instance.school, **row)
        return instance


class PortraitConfigSerializer(serializers.ModelSerializer):
    domains = PoGDomainSerializer(many=True, read_only=True)
    domain_weights_valid = serializers.ReadOnlyField()
    config_errors = serializers.SerializerMethodField()

    class Meta:
        model = PortraitConfig
        fields = [
            "id",
            "name",
            "version",
            "is_active",
            "preamble",
            "covenant_text",
            "scripture_anchor",
            "threshold_strong_accept",
            "threshold_accept",
            "threshold_accept_review",
            "threshold_hold",
            "require_faith_formation_minimum",
            "faith_minimum_score",
            "domain_weights_valid",
            "config_errors",
            "domains",
            "created_at",
            "updated_at",
        ]

    def get_config_errors(self, obj):
        return validate_config(obj)


class PortraitConfigWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortraitConfig
        fields = [
            "name",
            "version",
            "is_active",
            "preamble",
            "covenant_text",
            "scripture_anchor",
            "threshold_strong_accept",
            "threshold_accept",
            "threshold_accept_review",
            "threshold_hold",
            "require_faith_formation_minimum",
            "faith_minimum_score",
        ]

    def validate(self, attrs):
        strong = Decimal(str(attrs.get("threshold_strong_accept", Decimal("80.00"))))
        accept = Decimal(str(attrs.get("threshold_accept", Decimal("65.00"))))
        review = Decimal(str(attrs.get("threshold_accept_review", Decimal("50.00"))))
        hold = Decimal(str(attrs.get("threshold_hold", Decimal("35.00"))))
        if not (hold < review <= accept <= strong):
            raise serializers.ValidationError(
                "Thresholds must satisfy: Hold < Accept with Review <= Accept <= Strong Accept."
            )
        return attrs


class NormalizeWeightsSerializer(serializers.Serializer):
    weights = serializers.DictField(child=serializers.FloatField(min_value=0.0001))

    def validate_weights(self, value):
        if not value:
            raise serializers.ValidationError("At least one domain weight is required.")
        _ = normalize_weights(value)
        return value


class PoGDomainScoreWriteSerializer(serializers.ModelSerializer):
    rubric_level_id = serializers.PrimaryKeyRelatedField(
        queryset=PoGRubricLevel._base_manager.all(),
        source="rubric_level",
        required=False,
        allow_null=True,
    )

    class Meta:
        model = PoGDomainScore
        fields = ["id", "domain", "score", "rubric_level_id", "notes"]

    def validate(self, attrs):
        score = attrs.get("score", getattr(self.instance, "score", None))
        rubric_level = attrs.get("rubric_level", getattr(self.instance, "rubric_level", None))
        domain = attrs.get("domain", getattr(self.instance, "domain", None))

        if score and rubric_level and rubric_level.level != score:
            raise serializers.ValidationError(
                f"Score ({score}) does not match rubric level ({rubric_level.level}: {rubric_level.label})."
            )
        if domain and rubric_level and rubric_level.domain_id != domain.id:
            raise serializers.ValidationError("Selected rubric level does not belong to the chosen domain.")
        return attrs


class PoGDomainScoreReadSerializer(serializers.ModelSerializer):
    domain_name = serializers.CharField(source="domain.name", read_only=True)
    domain_weight = serializers.DecimalField(source="domain.weight", max_digits=5, decimal_places=4, read_only=True)
    domain_weight_percentage = serializers.FloatField(source="domain.weight_percentage", read_only=True)
    is_faith_anchor = serializers.BooleanField(source="domain.is_faith_anchor", read_only=True)
    rubric_level_detail = PoGRubricLevelSerializer(source="rubric_level", read_only=True)
    weighted_score = serializers.ReadOnlyField()

    class Meta:
        model = PoGDomainScore
        fields = [
            "id",
            "domain",
            "domain_name",
            "domain_weight",
            "domain_weight_percentage",
            "is_faith_anchor",
            "score",
            "rubric_level_detail",
            "notes",
            "weighted_score",
        ]


class AdmissionsPoGRecordCreateSerializer(serializers.ModelSerializer):
    config = serializers.PrimaryKeyRelatedField(
        queryset=PortraitConfig._base_manager.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = AdmissionsPoGRecord
        fields = ["applicant_id", "config", "context"]

    def validate_config(self, config):
        if config is None:
            return config
        errors = validate_config(config)
        if errors:
            raise serializers.ValidationError(
                f"Selected PoG config is not valid for scoring: {'; '.join(errors)}"
            )
        return config


class AdmissionsPoGRecordUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionsPoGRecord
        fields = [
            "context",
            "family_faith_statement",
            "church_attendance",
            "church_name",
            "student_faith_notes",
            "general_interview_notes",
        ]


class AdmissionsPoGRecordSerializer(serializers.ModelSerializer):
    domain_scores = PoGDomainScoreReadSerializer(many=True, read_only=True)
    scored_by_name = serializers.SerializerMethodField()
    recommendation_display = serializers.SerializerMethodField()
    recommendation_color = serializers.SerializerMethodField()
    scored_domains_count = serializers.ReadOnlyField()
    required_domains_count = serializers.ReadOnlyField()
    config_name = serializers.CharField(source="config.name", read_only=True)
    config_version = serializers.CharField(source="config.version", read_only=True)
    faith_minimum_score = serializers.IntegerField(source="config.faith_minimum_score", read_only=True)

    class Meta:
        model = AdmissionsPoGRecord
        fields = [
            "id",
            "applicant_id",
            "config",
            "config_name",
            "config_version",
            "context",
            "scored_by",
            "scored_by_name",
            "scored_at",
            "family_faith_statement",
            "church_attendance",
            "church_name",
            "student_faith_notes",
            "general_interview_notes",
            "composite_score",
            "composite_percentage",
            "recommendation",
            "recommendation_display",
            "recommendation_color",
            "faith_gate_triggered",
            "faith_minimum_score",
            "is_complete",
            "scored_domains_count",
            "required_domains_count",
            "domain_scores",
            "created_at",
            "updated_at",
        ]

    def get_scored_by_name(self, obj):
        if not obj.scored_by:
            return None
        full_name = f"{obj.scored_by.first_name} {obj.scored_by.last_name}".strip()
        return full_name or getattr(obj.scored_by, "username", None) or getattr(obj.scored_by, "email", None)

    def get_recommendation_display(self, obj):
        return dict(RECOMMENDATION_CHOICES).get(obj.recommendation, obj.recommendation)

    def get_recommendation_color(self, obj):
        mapping = {
            "strong_accept": "success",
            "accept": "success",
            "accept_review": "warning",
            "hold": "caution",
            "decline": "danger",
            "": "neutral",
        }
        return mapping.get(obj.recommendation or "", "neutral")


class BatchScoreItemSerializer(serializers.Serializer):
    domain = serializers.PrimaryKeyRelatedField(queryset=PoGDomain._base_manager.all())
    score = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=5)
    rubric_level_id = serializers.IntegerField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class BatchDomainScoreSerializer(serializers.Serializer):
    scores = BatchScoreItemSerializer(many=True, min_length=1)
    run_engine = serializers.BooleanField(default=True)


class DryRunPreviewSerializer(serializers.Serializer):
    config_id = serializers.IntegerField()
    domain_scores = serializers.DictField(
        child=serializers.IntegerField(min_value=1, max_value=5),
        help_text="Dict of {domain_id: score (1-5)}",
    )

    def validate_domain_scores(self, value):
        return {str(key): score for key, score in value.items()}
