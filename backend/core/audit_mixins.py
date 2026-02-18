from rest_framework.viewsets import ModelViewSet

class AuditMutationMixin:
    """
    Stamps last_modified_by on create/update if field exists.
    Safe: does nothing if model has no such field.
    """

    def perform_create(self, serializer):
        instance = serializer.save()
        if hasattr(instance, "last_modified_by_id"):
            instance.last_modified_by_id = getattr(self.request.user, "id", None)
            instance.save(update_fields=["last_modified_by"])

    def perform_update(self, serializer):
        instance = serializer.save()
        if hasattr(instance, "last_modified_by_id"):
            instance.last_modified_by_id = getattr(self.request.user, "id", None)
            instance.save(update_fields=["last_modified_by"])
