"""Reserved presenter identity; deliberately absent from the public catalog."""
from dataclasses import replace
from uuid import UUID

from .catalog import SANDBOX_SCHOOLS

UNIVERSAL_SCHOOL_ID = UUID("cd216908-b692-5fa7-997b-743f811f1ea9")
UNIVERSAL_SCHOOL = replace(
    SANDBOX_SCHOOLS["heritage-core"],
    id=str(UNIVERSAL_SCHOOL_ID), key="arete-universal",
    name="Heritage Christian Academy - Arete Fictional Presenter",
)


def presenter_username(persona_key):
    return f"presenter.{UNIVERSAL_SCHOOL_ID.hex}.{persona_key}@fictional.crown.invalid"
