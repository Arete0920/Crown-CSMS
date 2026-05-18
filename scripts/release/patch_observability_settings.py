"""
Append these settings to backend/crown_api/settings.py if not already present.

Required middleware entry:
core.observability.middleware.RequestCorrelationMiddleware

Recommended position:
after authentication middleware and before tenant isolation middleware.
"""

import pathlib

settings_path = pathlib.Path("backend/crown_api/settings.py")
text = settings_path.read_text(encoding="utf-8")

middleware = '"core.observability.middleware.RequestCorrelationMiddleware"'

if middleware not in text:
    # Insert after AuthenticationMiddleware and before TenantIsolationMiddleware
    text = text.replace(
        "'django.contrib.auth.middleware.AuthenticationMiddleware',\n",
        "'django.contrib.auth.middleware.AuthenticationMiddleware',\n    " + middleware + ",\n",
    )

if '"crown.request"' not in text:
    text += '''

# Crown structured request logging
LOGGING = globals().get("LOGGING", {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {},
})

LOGGING.setdefault("handlers", {}).setdefault("console", {"class": "logging.StreamHandler"})
LOGGING.setdefault("loggers", {})["crown.request"] = {
    "handlers": ["console"],
    "level": "INFO",
    "propagate": False,
}
'''

settings_path.write_text(text, encoding="utf-8")
print("observability settings patched")
