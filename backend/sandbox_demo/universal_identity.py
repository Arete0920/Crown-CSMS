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


def presenter_username(persona_key, school_id=UNIVERSAL_SCHOOL_ID):
    return f"presenter.{UUID(str(school_id)).hex}.{persona_key}@fictional.crown.invalid"


MAX_GENERATION = 4  # Five retained schools total; no unbounded automatic storage growth.
GENERATION_EVENT = "universal_presenter_generation_created_v1"


def generation_school(generation):
    from uuid import uuid5
    if type(generation) is not int or not 0 <= generation <= MAX_GENERATION:
        raise ValueError("Presenter generation is outside the reviewed retention limit.")
    if generation == 0:
        return UNIVERSAL_SCHOOL
    school_id = uuid5(UNIVERSAL_SCHOOL_ID, f"owned-presenter-generation:{generation}:v1")
    return replace(UNIVERSAL_SCHOOL, id=str(school_id), key=f"arete-universal-g{generation}",
                   name=f"{UNIVERSAL_SCHOOL.name} (generation {generation})")


def generation_number(school_id):
    for number in range(MAX_GENERATION + 1):
        if generation_school(number).id == str(school_id):
            return number
    raise ValueError("Unregistered presenter school identity.")
