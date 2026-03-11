import os
import sys
import logging
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from households.models import Household
from core.models import School


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

logger.info("Schools: %s", School.objects.count())
logger.info("Households: %s", Household.objects.count())

if Household.objects.exists():
    h = Household.objects.first()
    logger.info("Sample household school_id: %s", h.school_id)
    logger.info("Students in first household: %s", h.students.count())
else:
    if School.objects.exists():
        s = School.objects.first()
        logger.info("First school ID: %s", s.id)
