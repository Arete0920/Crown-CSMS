"""
Append these settings to backend/crown_api/settings.py if not already present.

Required middleware entry:
core.observability.middleware.RequestCorrelationMiddleware

Recommended position:
after authentication middleware and before tenant isolation middleware.
"""

import os
import pathlib
import stat

repo_root = pathlib.Path(__file__).resolve().parents[2]
settings_dir = repo_root / "backend" / "crown_api"
settings_path = settings_dir / "settings.py"
if (
    (repo_root / "backend").is_symlink()
    or settings_dir.is_symlink()
    or settings_path.is_symlink()
    or not settings_path.is_file()
    or settings_path.resolve().parent != settings_dir
):
    raise SystemExit("Refusing unsafe observability settings path")
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

flags = os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
fd = os.open(settings_path, flags)
try:
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise SystemExit("Refusing unsafe observability settings target")
    os.ftruncate(fd, 0)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        fd = -1
        output.write(text)
finally:
    if fd >= 0:
        os.close(fd)
print("observability settings patched")
