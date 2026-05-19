from rest_framework import serializers
from .models import (
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
	class Meta:
		model = StudentSpiritualProfile
		fields = [
			"id", "school", "student", "faith_background", "baptized",
			"baptism_date", "spiritual_gifts", "notes", "created_at", "updated_at",
		]
		read_only_fields = ["id", "created_at", "updated_at"]


class SpiritualAssessmentSerializer(serializers.ModelSerializer):
	class Meta:
		model = SpiritualAssessment
		fields = [
			"id", "school", "student", "administered_by",
			"assessment_title", "assessment_date", "score", "max_score",
			"notes", "created_at",
		]
		read_only_fields = ["id", "created_at"]


class ChapelAttendanceSerializer(serializers.ModelSerializer):
	class Meta:
		model = ChapelAttendance
		fields = [
			"id", "school", "event", "student", "status",
			"recorded_by", "created_at",
		]
		read_only_fields = ["id", "created_at"]


class ChapelEventSerializer(serializers.ModelSerializer):
	attendances = ChapelAttendanceSerializer(many=True, read_only=True)

	class Meta:
		model = ChapelEvent
		fields = [
			"id", "school", "title", "speaker", "event_date",
			"start_time", "end_time", "location", "theme",
			"scripture_reference", "notes", "created_at", "attendances",
		]
		read_only_fields = ["id", "created_at"]


class SmallGroupMemberSerializer(serializers.ModelSerializer):
	class Meta:
		model = SmallGroupMember
		fields = ["id", "school", "group", "student", "joined_at"]
		read_only_fields = ["id", "joined_at"]


class SmallGroupAttendanceSerializer(serializers.ModelSerializer):
	class Meta:
		model = SmallGroupAttendance
		fields = ["id", "school", "session", "member", "status", "created_at"]
		read_only_fields = ["id", "created_at"]


class SmallGroupSessionSerializer(serializers.ModelSerializer):
	attendances = SmallGroupAttendanceSerializer(many=True, read_only=True)

	class Meta:
		model = SmallGroupSession
		fields = [
			"id", "school", "group", "session_date", "topic",
			"scripture_reference", "notes", "created_at", "attendances",
		]
		read_only_fields = ["id", "created_at"]


class SmallGroupSerializer(serializers.ModelSerializer):
	members = SmallGroupMemberSerializer(many=True, read_only=True)

	class Meta:
		model = SmallGroup
		fields = [
			"id", "school", "name", "leader", "description",
			"is_active", "created_at", "members",
		]
		read_only_fields = ["id", "created_at"]


class PrayerRequestSerializer(serializers.ModelSerializer):
	class Meta:
		model = PrayerRequest
		fields = [
			"id", "school", "student", "submitted_by",
			"title", "body", "visibility", "status",
			"created_at", "updated_at",
		]
		read_only_fields = ["id", "created_at", "updated_at"]


class PastoralNoteSerializer(serializers.ModelSerializer):
	class Meta:
		model = PastoralNote
		fields = [
			"id", "school", "student", "author",
			"note_date", "body", "is_sensitive",
			"created_at", "updated_at",
		]
		read_only_fields = ["id", "created_at", "updated_at"]
