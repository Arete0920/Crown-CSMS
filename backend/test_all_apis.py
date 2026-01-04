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

print('\n' + '='*60)
print('✅ TESTING ALL 6 PERSONA-SPECIFIC ENDPOINTS')
print('='*60 + '\n')

passed = 0
failed = 0

for ep in endpoints:
    url = f'http://127.0.0.1:8000{ep}'
    try:
        r = requests.get(url, params={'school_id': school, 'year_id': year}, timeout=5)
        print(f'{ep}')
        if r.status_code == 200:
            data = r.json()
            print(f'  ✅ Status: 200')
            print(f'  Persona: {data["meta"]["persona"]}')
            print(f'  Keys: {list(data.keys())}')
            passed += 1
        else:
            print(f'  ❌ Status: {r.status_code}')
            failed += 1
        print()
    except Exception as e:
        print(f'{ep}')
        print(f'  ❌ Error: {e}')
        print()
        failed += 1

print('='*60)
print(f'RESULTS: {passed} passed, {failed} failed')
print('='*60)
