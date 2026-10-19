"""Fictional, stable identities for the Heritage demonstration school.

This module is deliberately isolated from production account creation and outreach.
Names, addresses, and numbers are fabricated. The example.org email domain and
reserved 555-01xx numbers must never be used to send messages or place calls.
"""

from __future__ import annotations

from dataclasses import dataclass

FAMILY_RECORD_COUNT = 286
STUDENT_RECORD_COUNT = 700
FIXTURE_EMAIL_DOMAIN = "heritage.example.org"

# Broad, ordinary surname and given-name pools; nothing is sourced from families.
SURNAMES = (
    "Anderson", "Bennett", "Caldwell", "Donovan", "Ellis", "Foster",
    "Gibson", "Hernandez", "Ingram", "Jackson", "Kim", "Lawson",
    "Mitchell", "Nguyen", "Owens", "Patel", "Quintero", "Ramirez",
    "Sullivan", "Thompson", "Underwood", "Vasquez", "Walker", "Young",
    "Zimmerman", "Brooks", "Campbell", "Diaz", "Evans", "Fleming",
    "Garcia", "Harrison", "Iqbal", "Jenkins", "Keller", "Lopez",
    "Morales", "Nelson", "Ortiz", "Parker", "Reyes", "Sanders",
    "Turner", "Valdez", "Williams", "Adams", "Bishop", "Chavez",
    "Daniels", "Edwards", "Fisher", "Gonzalez", "Hayes", "Ibrahim",
    "Jordan", "Kennedy", "Lewis", "Mendoza", "Nolan", "Ochoa",
    "Price", "Richards", "Santiago", "Taylor", "Vega", "Wright",
    "Ali", "Baker", "Chen", "Davis", "Farrell", "Grant",
    "Hughes", "Johnson", "Khan", "Martinez", "Newman", "Olsen",
    "Phillips", "Roberts", "Shah", "Torres", "Watson", "Yates",
    "Armstrong", "Barrett", "Cruz", "Delgado", "Escobar", "Fields",
    "Greene", "Howard", "James", "Kaur", "Miller", "Navarro",
    "Pierce", "Rogers", "Soto", "Warren", "Yu", "Zamora",
)

GUARDIAN_GIVEN_NAMES = (
    "Andrea", "Benjamin", "Caroline", "Daniel", "Elena", "Francis",
    "Grace", "Henry", "Isabel", "Jonathan", "Katherine", "Luis",
    "Miriam", "Nathan", "Olivia", "Peter", "Rachel", "Samuel",
    "Teresa", "Victor", "Wendy", "Abigail", "Christopher", "Diana",
    "Emmanuel", "Faith", "Gabriel", "Hannah", "Isaac", "Julia",
    "Leah", "Matthew", "Naomi", "Omar", "Priscilla", "Thomas",
)

STUDENT_GIVEN_NAMES = (
    "Amelia", "Aaron", "Aaliyah", "Adrian", "Alana", "Andrew",
    "Anika", "Benjamin", "Caleb", "Camila", "Charlotte", "Daniel",
    "David", "Elijah", "Elise", "Emma", "Ethan", "Eva",
    "Gabriel", "Grace", "Hannah", "Isaac", "Isabella", "James",
    "Jasmine", "Jonah", "Jordan", "Josiah", "Julian", "Kayla",
    "Leah", "Liam", "Lily", "Lucas", "Madeline", "Mateo",
    "Micah", "Mila", "Naomi", "Nathan", "Noah", "Olivia",
    "Owen", "Rachel", "Samuel", "Sarah", "Sophia", "Thomas",
    "Victoria", "William", "Zoe", "Zion", "Abigail",
)

# Local Mid-Atlantic patterns are plausible; street lines remain fabricated.
REGIONAL_LOCATIONS = (
    ("Newark", "DE", "19711", "302"),
    ("Elkton", "MD", "21921", "410"),
    ("West Chester", "PA", "19380", "610"),
)
STREET_NAMES = (
    "Cedar Ridge Way", "Oak Grove Lane", "Meadowcrest Drive",
    "Brookstone Court", "Maple Brook Road", "Stonebridge Way",
    "Willow Park Drive", "Providence Court", "Briarwood Place",
    "Kingsley Terrace", "Chapel Hill Lane",
)


@dataclass(frozen=True)
class FictionalFamilyIdentity:
    family_name: str
    surname: str
    guardian_first_name: str
    guardian_email: str
    phone: str
    address_line1: str
    city: str
    state: str
    zip_code: str


def family_identity(index: int) -> FictionalFamilyIdentity:
    """Return one stable fictitious family without touching a live database."""
    if not 1 <= index <= FAMILY_RECORD_COUNT:
        raise ValueError("Heritage fictional family index out of range")
    offset = index - 1
    surname_index = (offset * 37) % len(SURNAMES)
    cycle = offset // len(SURNAMES)
    surname = SURNAMES[surname_index]
    guardian_first_name = GUARDIAN_GIVEN_NAMES[
        (surname_index * 5 + cycle * 7) % len(GUARDIAN_GIVEN_NAMES)
    ]
    # Distinguish two unrelated families with the same surname as registrars do.
    family_name = (
        f"{surname} Family"
        if cycle == 0
        else f"{surname} Family ({guardian_first_name})"
    )
    city, state, zip_code, area_code = REGIONAL_LOCATIONS[offset // 100]
    street = STREET_NAMES[(offset * 11 + cycle) % len(STREET_NAMES)]
    return FictionalFamilyIdentity(
        family_name=family_name,
        surname=surname,
        guardian_first_name=guardian_first_name,
        guardian_email=(
            f"{guardian_first_name.lower()}.{surname.lower()}.{index:03d}"
            f"@{FIXTURE_EMAIL_DOMAIN}"
        ),
        phone=f"{area_code}-555-01{offset % 100:02d}",
        address_line1=f"{120 + (index * 37) % 870} {street}",
        city=city,
        state=state,
        zip_code=zip_code,
    )


def student_given_name(index: int) -> str:
    """Stable school-year-independent learner name, not an identity key."""
    if not 1 <= index <= STUDENT_RECORD_COUNT:
        raise ValueError("Heritage fictional student index out of range")
    return STUDENT_GIVEN_NAMES[
        ((index - 1) * 23 + (index // FAMILY_RECORD_COUNT) * 17)
        % len(STUDENT_GIVEN_NAMES)
    ]
