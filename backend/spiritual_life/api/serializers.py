from __future__ import annotations

from rest_framework import serializers

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


class StudentSpiritualProfileSerializer(serializers.ModelSerializer):
    school_id = serializers.UUIDField(source="school.id", read_only=True)
    student_id = serializers.UUIDField(source="student.id", read_only=True)
    updated_by_id = serializers.UUIDField(
        source="updated_by.id", read_only=True, allow_null=True
    )

    class Meta:
        model = StudentSpiritualProfile
        fields = [
            "id",
            "school_id",
            "student_id",
            "faith_background",
            "baptized",
            "baptism_date",
            "spiritual_gifts",
            "notes",
            "updated_by_id",
            "created_at",
            "updated_at",
        ]


class SpiritualAssessmentSerializer(serializers.ModelSerializer):
    school_id = serializers.UUIDField(source="school.id", read_only=True)
    student_id = serializers.UUIDField(source="student.id", read_only=True)
    administered_by_id = serializers.UUIDField(
        source="administered_by.id", read_only=True, allow_null=True
    )

    class Meta:
        model = SpiritualAssessment
        fields = [
            "id",
            "school_id",
            "student_id",
            "administered_by_id",
            "assessment_title",
            "assessment_date",
            "score",
            "max_score",
            "notes",
            "created_at",
        ]


class ChapelEventSerializer(serializers.ModelSerializer):
    school_id = serializers.UUIDField(source="school.id", read_only=True)
    created_by_id = serializers.UUIDField(
        source="created_by.id", read_only=True, allow_null=True
    )

    class Meta:
        model = ChapelEvent
        fields = [
            "id",
            "school_id",
            "title",
            "speaker",
            "event_date",
            "start_time",
            "end_time",
            "location",
            "theme",
            "scripture_reference",
            "notes",
            "created_by_id",
            "created_at",
        ]


class ChapelAttendanceSerializer(serializers.ModelSerializer):
    school_id = serializers.UUIDField(source="school.id", read_only=True)
    event_id = serializers.UUIDField(source="event.id", read_only=True)
    student_id = serializers.UUIDField(source="student.id", read_only=True)
    recorded_by_id = serializers.UUIDField(
        source="recorded_by.id", read_only=True, allow_null=True
    )

    class Meta:
        model = ChapelAttendance
        fields = [
            "id",
            "school_id",
            "event_id",
            "student_id",
            "status",
            "recorded_by_id",
            "created_at",
        ]


class SmallGroupSerializer(serializers.ModelSerializer):
    school_id = serializers.UUIDField(source="school.id", read_only=True)
    leader_id = serializers.UUIDField(source="leader.id", read_only=True, allow_null=True)

    class Meta:
        model = SmallGroup
        fields = [
            "id",
            "school_id",
            "name",
            "leader_id",
            "description",
            "is_active",
            "created_at",
        ]


class SmallGroupMemberSerializer(serializers.ModelSerializer):
    school_id = serializers.UUIDField(source="school.id", read_only=True)
    group_id = serializers.UUIDField(source="group.id", read_only=True)
    student_id = serializers.UUIDField(source="student.id", read_only=True)

    class Meta:
        model = SmallGroupMember
        fields = ["id", "school_id", "group_id", "student_id", "joined_at"]


class SmallGroupSessionSerializer(serializers.ModelSerializer):
    school_id = serializers.UUIDField(source="school.id", read_only=True)
    group_id = serializers.UUIDField(source="group.id", read_only=True)

    class Meta:
        model = SmallGroupSession
        fields = [
            "id",
            "school_id",
            "group_id",
            "session_date",
            "topic",
            "scripture_reference",
            "notes",
            "created_at",
        ]


class SmallGroupAttendanceSerializer(serializers.ModelSerializer):
    school_id = serializers.UUIDField(source="school.id", read_only=True)
    session_id = serializers.UUIDField(source="session.id", read_only=True)
    member_id = serializers.UUIDField(source="member.id", read_only=True)

    class Meta:
        model = SmallGroupAttendance
        fields = ["id", "school_id", "session_id", "member_id", "status", "created_at"]


class PrayerRequestSerializer(serializers.ModelSerializer):
    school_id = serializers.UUIDField(source="school.id", read_only=True)
    student_id = serializers.UUIDField(
        source="student.id", read_only=True, allow_null=True
    )
    submitted_by_id = serializers.UUIDField(
        source="submitted_by.id", read_only=True, allow_null=True
    )

    class Meta:
        model = PrayerRequest
        fields = [
            "id",
            "school_id",
            "student_id",
            "submitted_by_id",
            "title",
            "body",
            "visibility",
            "status",
            "created_at",
            "updated_at",
        ]


class PastoralNoteSerializer(serializers.ModelSerializer):
    """Full serializer — only served to staff/HEAD_OF_SCHOOL users."""

    school_id = serializers.UUIDField(source="school.id", read_only=True)
    student_id = serializers.UUIDField(source="student.id", read_only=True)
    author_id = serializers.UUIDField(source="author.id", read_only=True)

    class Meta:
        model = PastoralNote
        fields = [
            "id",
            "school_id",
            "student_id",
            "author_id",
            "note_date",
            "body",
            "is_sensitive",
            "created_at",
            "updated_at",
        ]
