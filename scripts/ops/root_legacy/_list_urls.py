import os, sys, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'crown_api.settings'
sys.path.insert(0, 'backend')
django.setup()
from django.urls import get_resolver

def walk(resolver, prefix=''):
    for pattern in resolver.url_patterns:
        p = prefix + str(pattern.pattern)
        if hasattr(pattern, 'url_patterns'):
            yield from walk(pattern, p)
        else:
            yield p

urls = sorted(set(u for u in walk(get_resolver()) if '/api/' in u))
for u in urls:
    print(u)
