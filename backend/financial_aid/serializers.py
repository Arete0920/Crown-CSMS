from rest_framework import serializers
from .models import FinancialAidApplication, AidAward, AidBucket

class AidAwardSerializer(serializers.ModelSerializer):
    class Meta:
        model = AidAward
        fields = ["id", "bucket", "amount", "rationale", "created_at", "updated_at"]

class FinancialAidApplicationSerializer(serializers.ModelSerializer):
    awards = AidAwardSerializer(many=True, read_only=True)
    class Meta:
        model = FinancialAidApplication
        fields = [
            "id", "school_id", "household_id", "academic_year",
            "submitted_at", "household_income", "household_size",
            "status", "awards"
        ]

class AidSummarySerializer(serializers.Serializer):
    academic_year = serializers.CharField()
    total_applications = serializers.IntegerField()
    total_awarded = serializers.DecimalField(max_digits=12, decimal_places=2)
    bucket_totals = serializers.DictField(child=serializers.DecimalField(max_digits=12, decimal_places=2))
    bucket_counts = serializers.DictField(child=serializers.IntegerField())
