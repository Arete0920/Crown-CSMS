"""Stable, fictional Golden Path applicant identities.

Fixture identifiers are scoped to a school UUID. They are not student records,
external contacts, or production account identifiers.
"""

from __future__ import annotations

import uuid


GIVEN_NAMES = (
    "Abigail", "Adrian", "Amelia", "Andrew", "Anika", "Benjamin",
    "Caleb", "Camila", "Charlotte", "Daniel", "David", "Elijah",
    "Elise", "Emma", "Ethan", "Gabriel", "Grace", "Hannah",
    "Isaac", "Isabella", "James", "Jasmine", "Jonah", "Jordan",
    "Josiah", "Julian", "Kayla", "Leah", "Liam", "Lucas",
    "Madeline", "Mateo", "Micah", "Naomi", "Nathan", "Noah",
    "Olivia", "Owen", "Rachel", "Samuel", "Sarah", "Sophia",
    "Thomas", "Victoria", "William", "Zoe",
)

SURNAMES = (
    "Anderson", "Bennett", "Caldwell", "Donovan", "Ellis", "Foster",
    "Gibson", "Hernandez", "Ingram", "Jackson", "Kim", "Lawson",
    "Mitchell", "Nguyen", "Owens", "Patel", "Quintero", "Ramirez",
    "Sullivan", "Thompson", "Underwood", "Vasquez", "Walker", "Young",
    "Zimmerman", "Brooks", "Campbell", "Diaz", "Evans", "Fleming",
    "Garcia", "Harrison", "Ibrahim", "Jenkins", "Keller", "Lopez",
    "Morales", "Nelson", "Ortiz", "Parker", "Reyes", "Sanders",
    "Turner", "Valdez", "Williams", "Adams", "Bishop", "Chavez",
    "Daniels", "Edwards", "Fisher", "Gonzalez", "Hayes",
)

GOLDEN_PATH_FUNNEL_SIZE = 94


def applicant_identity(index: int) -> tuple[str, str]:
    """Return deterministic non-generic fictional names for applicant #index."""
    if not 0 <= index < GOLDEN_PATH_FUNNEL_SIZE:
        raise ValueError("Fictional applicant index must be within the funnel")
    return (
        GIVEN_NAMES[(index * 19 + index // len(GIVEN_NAMES)) % len(GIVEN_NAMES)],
        SURNAMES[(index * 17 + index // len(SURNAMES)) % len(SURNAMES)],
    )


def fixture_uuid(school_id: uuid.UUID | str, record_type: str, index: int) -> uuid.UUID:
    """Namespace one repeatable fixture ID under the authorized school."""
    if not record_type or not record_type.isascii() or not record_type.replace("-", "").replace(":", "").isalnum():
        raise ValueError("Unsupported Golden Path fixture record type")
    if not 0 <= index <= 1000:
        raise ValueError("Unsupported Golden Path fixture index")
    return uuid.uuid5(
        uuid.UUID(str(school_id)),
        f"crown:golden-path:v2:{record_type}:{index:04d}",
    )
