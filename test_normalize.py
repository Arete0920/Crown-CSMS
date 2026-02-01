#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
django.setup()

from applications.views_admissions import _normalize_ay_name, _get_academic_year_window
from uuid import UUID

# Test normalization
print('✓ Normalize test:')
h1 = _normalize_ay_name('2026-2027')
h2 = _normalize_ay_name('2026–2027')
print(f'  2026-2027 -> "{h1}"')
print(f'  2026–2027 -> "{h2}"')
print(f'  Match: {h1 == h2}')

# Test window lookup
print('\n✓ Window lookup tests:')
sid = UUID('a5351136-98fe-4d48-add0-fa8f62d9ceff')

name, start, end, is_explicit = _get_academic_year_window(str(sid), None)
print(f'  No param (is_current): name={name}, is_explicit={is_explicit}')

name, start, end, is_explicit = _get_academic_year_window(str(sid), '2026-2027')
print(f'  2026-2027: name={name}, is_explicit={is_explicit}')
