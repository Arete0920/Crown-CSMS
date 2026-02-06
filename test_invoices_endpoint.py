import requests
import json

session = requests.Session()
invoices_url = 'http://127.0.0.1:8000/api/billing/invoices/'
school_id = 'a5351136-98fe-4d48-add0-fa8f62d9ceff'

try:
    resp = session.get(
        invoices_url,
        headers={'X-School-ID': school_id}
    )
    print(f'Status: {resp.status_code}')
    
    if resp.status_code == 200:
        try:
            data = resp.json()
            print(f'Response (pretty): {json.dumps(data, indent=2)}')
        except Exception as je:
            print(f'JSON error: {je}')
            print(f'Raw text (first 500): {resp.text[:500]}')
    else:
        print(f'Error: {resp.text[:300]}')
except Exception as e:
    print(f'Exception: {e}')
