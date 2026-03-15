from django.db import models


class DashboardSnapshot(models.Model):
    school_id = models.CharField(max_length=64, db_index=True)
    dashboard_key = models.SlugField(max_length=120, db_index=True)
    payload = models.JSONField(default=dict)
    source = models.CharField(max_length=32, default='manual')
    notes = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dashboard_snapshots'
        unique_together = ('school_id', 'dashboard_key')
        indexes = [
            models.Index(fields=['school_id', 'dashboard_key'], name='dashboard_s_school__f05431_idx'),
        ]
        ordering = ['school_id', 'dashboard_key']

    def __str__(self):
        return f'{self.school_id}:{self.dashboard_key}'
