import requests

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

print('='*60)
print('API ACCURACY AUDIT')
print('='*60)

for ep in endpoints:
    url = f'http://127.0.0.1:8000{ep}'
    try:
        r = requests.get(url, params={'school_id': school, 'year_id': year}, timeout=5)
        status = 'PASS' if r.status_code == 200 else 'FAIL'
        print(f'{status} - {ep} - {r.status_code}')
        if r.status_code == 200:
            data = r.json()
            print(f'  Keys: {list(data.keys())}')
            print(f'  Persona: {data.get("meta", {}).get("persona")}')
    except Exception as e:
        print(f'FAIL - {ep} - ERROR: {e}')

print('='*60)
