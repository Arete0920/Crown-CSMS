from rest_framework import serializers

from crown_api.models import Invoice


class InvoiceMiniSerializer(serializers.ModelSerializer):
    invoice_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = Invoice
        fields = (
            "invoice_id",
            "invoice_number",
            "amount_cents",
            "status",
            "due_date",
        )
