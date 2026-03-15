import requests
import logging


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

school = '852e31bc-d953-48c5-b081-98d27469d634'
year = 'a3e4bc0c-f0db-481b-b5e4-9ec86d45f50a'

endpoints = [
    '/api/aid/priority-queue/',
    '/api/aid/metrics/',
    '/api/aid/timeline/',
    '/api/admissions/priority-queue/',
    '/api/admissions/metrics/',
    '/api/admissions/timeline/'
]

logger.info('=' * 60)
logger.info('API ACCURACY AUDIT')
logger.info('=' * 60)

for ep in endpoints:
    url = f'http://127.0.0.1:8000{ep}'
    try:
        r = requests.get(url, params={'school_id': school, 'year_id': year}, timeout=5)
        status = 'PASS' if r.status_code == 200 else 'FAIL'
        logger.info('%s - %s - %s', status, ep, r.status_code)
        if r.status_code == 200:
            data = r.json()
            logger.info('  Keys: %s', list(data.keys()))
            logger.info('  Persona: %s', data.get("meta", {}).get("persona"))
    except Exception as e:
        logger.info('FAIL - %s - ERROR: %s', ep, e)

    logger.info('=' * 60)
