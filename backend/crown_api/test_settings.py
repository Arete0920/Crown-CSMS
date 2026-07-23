"""Pytest-only settings that add an independent database alias for routing proof."""

from copy import deepcopy

from .settings import *  # noqa: F401,F403


_section_alias = deepcopy(DATABASES["default"])
_engine = str(_section_alias.get("ENGINE", ""))
_base_name = str(_section_alias.get("NAME") or "crown")

if _engine.endswith("sqlite3"):
    _section_alias["NAME"] = BASE_DIR / "section_alias.sqlite3"
else:
    _database_name = _base_name.rsplit("/", 1)[-1]
    _alias_name = f"{_database_name}_section_alias"[:63]
    _section_alias["NAME"] = _alias_name
    _section_alias.setdefault("TEST", {})["NAME"] = f"test_{_alias_name}"[:63]

_section_alias.setdefault("TEST", {})["MIRROR"] = None
_section_alias["CONN_MAX_AGE"] = 0
DATABASES["section_alias"] = _section_alias
