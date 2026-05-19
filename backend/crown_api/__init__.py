# Expose Celery app so `celery -A crown_api` works.
from .celery_app import app as celery_app  # noqa: F401

# Register drf-spectacular schema extensions.
from . import spectacular_extensions  # noqa: F401

__all__ = ("celery_app",)
