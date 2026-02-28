from django.db import models


class BoardReportSnapshot(models.Model):
    """Board-safe snapshot of key metrics at a point in time.
    Avoid raw detail; store pre-aggregated values and summary JSON."""
    school_id = models.UUIDField(db_index=True)

    as_of_date = models.DateField(db_index=True)
    period_label = models.CharField(max_length=64, default="")
    payload = models.JSONField(default=dict)  # board-safe summary payload

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("school_id", "as_of_date", "period_label")
        ordering = ["-as_of_date", "-created_at"]

    def __str__(self):
        return f"BoardReportSnapshot({self.school_id}, {self.as_of_date}, {self.period_label})"


class BoardPacket(models.Model):
    """A board packet is a curated set of snapshot references + documents.
    Mode A: read-only distribution container."""
    school_id = models.UUIDField(db_index=True)

    title = models.CharField(max_length=200)
    meeting_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True, default="")

    snapshots = models.ManyToManyField(BoardReportSnapshot, blank=True)
    documents = models.JSONField(default=list, blank=True)  # [{name, url, kind}]

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-meeting_date", "-created_at"]

    def __str__(self):
        return f"BoardPacket({self.school_id}, {self.title})"
