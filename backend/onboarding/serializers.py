from rest_framework import serializers
from .models import ImportSession


class ImportSessionSerializer(serializers.ModelSerializer):
	class Meta:
		model = ImportSession
		fields = [
			"id", "school", "created_by", "mode", "status",
			"filename", "rows_total", "students_detected",
			"guardians_detected", "households_detected",
			"validate_result", "commit_result",
			"created_at", "updated_at",
		]
		read_only_fields = [
			"id", "rows_total", "students_detected",
			"guardians_detected", "households_detected",
			"validate_result", "commit_result",
			"created_at", "updated_at",
		]



class OnboardingTaskSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    task_name = serializers.CharField()
    status = serializers.CharField()
    order = serializers.IntegerField()
    completed_at = serializers.DateTimeField(allow_null=True)


class OnboardingProgressResponseSerializer(serializers.Serializer):
    school_id = serializers.CharField()
    total_tasks = serializers.IntegerField()
    completed = serializers.IntegerField()
    percent_complete = serializers.FloatField()
    tasks = OnboardingTaskSummarySerializer(many=True)
    parent_enrollment_guidance = serializers.DictField(required=False)


class OnboardingTaskCompleteResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.CharField()
    completed_at = serializers.DateTimeField()


class OnboardingActivationResponseSerializer(serializers.Serializer):
    school_id = serializers.CharField()
    can_activate = serializers.BooleanField()
    pending_tasks = serializers.ListField(child=serializers.CharField())


class SolomonArticleResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    slug = serializers.SlugField()
    title = serializers.CharField()
    summary = serializers.CharField(allow_blank=True)
    content = serializers.CharField(allow_blank=True)
    module = serializers.CharField()
    article_type = serializers.CharField()
    visibility = serializers.CharField()
    state = serializers.CharField()
    route_path = serializers.CharField(allow_blank=True)
    published = serializers.BooleanField()


class SolomonPlaybookResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    slug = serializers.SlugField()
    title = serializers.CharField()
    summary = serializers.CharField(allow_blank=True)
    module = serializers.CharField()


class SolomonSearchResponseSerializer(serializers.Serializer):
    results = SolomonArticleResponseSerializer(many=True)
    count = serializers.IntegerField()
    query = serializers.CharField(allow_blank=True)
    module = serializers.CharField(allow_blank=True)
    audience = serializers.CharField(allow_blank=True)
    categories = serializers.ListField(child=serializers.CharField())
    playbooks = SolomonPlaybookResponseSerializer(many=True)


class SolomonContextResponseSerializer(serializers.Serializer):
    primary_article = SolomonArticleResponseSerializer(allow_null=True)
    related_articles = SolomonArticleResponseSerializer(many=True)
    playbooks = SolomonPlaybookResponseSerializer(many=True)


class SolomonArticleAuthorResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    slug = serializers.SlugField()
    title = serializers.CharField()
    state = serializers.CharField()
    published = serializers.BooleanField()


class SolomonCategoriesResponseSerializer(serializers.Serializer):
    categories = serializers.ListField(child=serializers.CharField())


class SolomonPlaybooksResponseSerializer(serializers.Serializer):
    playbooks = SolomonPlaybookResponseSerializer(many=True)
