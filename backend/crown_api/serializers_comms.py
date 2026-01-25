from rest_framework import serializers

from crown_api.models import Message, MessageThread, Person


class PersonMiniSerializer(serializers.ModelSerializer):
    person_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = Person
        fields = (
            "person_id",
            "first_name",
            "last_name",
        )


class ThreadListSerializer(serializers.ModelSerializer):
    thread_id = serializers.UUIDField(source="id", read_only=True)

    household_id = serializers.UUIDField(source="household.id", read_only=True)
    household_name = serializers.CharField(source="household.household_name", read_only=True)

    student_id = serializers.SerializerMethodField()
    student_first_name = serializers.SerializerMethodField()
    student_last_name = serializers.SerializerMethodField()

    class Meta:
        model = MessageThread
        fields = (
            "thread_id",
            "household_id",
            "household_name",
            "student_id",
            "student_first_name",
            "student_last_name",
            "subject",
            "thread_type",
            "last_message_at",
        )

    def get_student_id(self, obj):
        student = getattr(obj, "student", None)
        return str(student.id) if student else None

    def get_student_first_name(self, obj):
        student = getattr(obj, "student", None)
        person = getattr(student, "person", None) if student else None
        return getattr(person, "first_name", None) if person else None

    def get_student_last_name(self, obj):
        student = getattr(obj, "student", None)
        person = getattr(student, "person", None) if student else None
        return getattr(person, "last_name", None) if person else None


class MessageReadSerializer(serializers.ModelSerializer):
    sender_person = PersonMiniSerializer(allow_null=True)

    class Meta:
        model = Message
        fields = (
            "sender_person",
            "body",
            "sent_at",
        )


class ThreadDetailSerializer(serializers.ModelSerializer):
    thread_id = serializers.UUIDField(source="id", read_only=True)

    household_id = serializers.UUIDField(source="household.id", read_only=True)
    household_name = serializers.CharField(source="household.household_name", read_only=True)

    student_id = serializers.SerializerMethodField()
    student_first_name = serializers.SerializerMethodField()
    student_last_name = serializers.SerializerMethodField()

    messages = serializers.SerializerMethodField()

    class Meta:
        model = MessageThread
        fields = (
            "thread_id",
            "household_id",
            "household_name",
            "student_id",
            "student_first_name",
            "student_last_name",
            "subject",
            "thread_type",
            "last_message_at",
            "messages",
        )

    def get_student_id(self, obj):
        student = getattr(obj, "student", None)
        return str(student.id) if student else None

    def get_student_first_name(self, obj):
        student = getattr(obj, "student", None)
        person = getattr(student, "person", None) if student else None
        return getattr(person, "first_name", None) if person else None

    def get_student_last_name(self, obj):
        student = getattr(obj, "student", None)
        person = getattr(student, "person", None) if student else None
        return getattr(person, "last_name", None) if person else None

    def get_messages(self, obj):
        messages = self.context.get("messages") or []
        return MessageReadSerializer(messages, many=True).data
