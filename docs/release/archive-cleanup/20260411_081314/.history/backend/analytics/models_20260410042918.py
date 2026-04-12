from django.db import models

from core.models import School

from .models_customer_health import CustomerHealth


class PredictiveModelRun(models.Model):
    """Auditable record of a predictive analytics run for a school."""

    model_name = models.CharField(max_length=100)
    run_date = models.DateTimeField(auto_now_add=True)
    # `core.School` is the authoritative tenant root in this codebase.
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="predictive_model_runs",
    )
    input_snapshot_date = models.DateField()
    output_json = models.JSONField()
    confidence_interval_low = models.FloatField(null=True, blank=True)
    confidence_interval_high = models.FloatField(null=True, blank=True)
    feature_importance = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["-run_date"]

    def __str__(self):
        return f"{self.model_name} for {self.school} on {self.run_date.date()}"


__all__ = ["CustomerHealth", "PredictiveModelRun"]
