from rest_framework import serializers
from .models import GLAccount, JournalEntry, JournalLine


class GLAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = GLAccount
        fields = ["id", "school", "code", "name", "account_type", "parent", "active"]
        read_only_fields = ["id"]


class JournalLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalLine
        fields = [
            "id", "entry", "account", "debit", "credit",
            "fund_code", "department_code", "program_code", "campus_code", "project_code",
        ]
        read_only_fields = ["id"]


class JournalEntrySerializer(serializers.ModelSerializer):
    lines = JournalLineSerializer(many=True, read_only=True)

    class Meta:
        model = JournalEntry
        fields = [
            "id", "school", "created_at", "created_by", "memo",
            "locked", "reference_type", "reference_id", "reversal_of",
            "lines",
        ]
        read_only_fields = ["id", "created_at"]

