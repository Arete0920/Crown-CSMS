from __future__ import annotations

import os
from dataclasses import asdict, dataclass

DEMO_SCHOOL_ID = os.getenv(
    "CROWN_DEMO_SCHOOL_ID", "19801b59-8c05-4c84-9312-5d792e4e839d"
)


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class SandboxPersona:
    key: str
    label: str
    role_code: str
    route: str
    email: str
    first_name: str
    last_name: str
    track_keys: tuple[str, ...]
    tour_title: str
    promise: str
    steps: tuple[str, ...]


@dataclass(frozen=True)
class SandboxSchool:
    id: str
    key: str
    track: str
    name: str
    archetype: str
    enrollment: int
    best_for: str
    tour: str


SANDBOX_TRACKS = {
    "school": {
        "key": "school",
        "label": "School Demo",
        "headline": "Run a Christian school day from leadership to classroom to family.",
        "summary": "Best for K-12 Christian school leaders evaluating admissions, academics, finance, communications, and family access.",
        "primarySchoolKey": "heritage-core",
    },
    "daycare": {
        "key": "daycare",
        "label": "Daycare / Early Learning Demo",
        "headline": "Build parent trust and run daily care operations.",
        "summary": "Best for early learning centers, preschool programs, church daycares, and mixed PK-5 schools.",
        "primarySchoolKey": "emmanuel-early-learning",
    },
    "camp": {
        "key": "camp",
        "label": "Camp / Summer Program Demo",
        "headline": "Manage seasonal registration through daily roster operations.",
        "summary": "Best for summer camps, VBS-style programs, enrichment weeks, and school-run seasonal programs.",
        "primarySchoolKey": "cedar-summer-camp",
    },
}

SANDBOX_SCHOOLS = {
    "heritage-core": SandboxSchool(
        id=DEMO_SCHOOL_ID,
        key="heritage-core",
        track="school",
        name="Heritage Christian Academy",
        archetype="Flagship PK-12 Christian school with early learning and finance proof",
        enrollment=700,
        best_for="full CROWN operating proof across leadership, admissions, finance, classroom, parent, and student views",
        tour="flagship-school-operating-proof",
    ),
    "harvest-small-school": SandboxSchool(
        id="00000000-0000-0000-0000-000000000201",
        key="harvest-small-school",
        track="school",
        name="Harvest Christian School",
        archetype="Small school simplicity",
        enrollment=180,
        best_for="simple operations and fast implementation story",
        tour="small-school-simplicity",
    ),
    "faith-admissions": SandboxSchool(
        id="00000000-0000-0000-0000-000000000202",
        key="faith-admissions",
        track="school",
        name="Faith Christian Academy",
        archetype="Admissions growth school",
        enrollment=520,
        best_for="inquiry-to-enrollment growth and conversion workflow",
        tour="admissions-growth",
    ),
    "calvary-finance": SandboxSchool(
        id="00000000-0000-0000-0000-000000000203",
        key="calvary-finance",
        track="school",
        name="Calvary Christian School",
        archetype="Tuition and aid pressure school",
        enrollment=390,
        best_for="tuition, aid, billing, payment-risk, and family balance review",
        tour="finance-aid-billing-proof",
    ),
    "st-anne-family": SandboxSchool(
        id="00000000-0000-0000-0000-000000000204",
        key="st-anne-family",
        track="school",
        name="St. Anne Christian Academy",
        archetype="Parent communication and community school",
        enrollment=460,
        best_for="family engagement, communications, and parent clarity",
        tour="family-engagement-proof",
    ),
    "emmanuel-early-learning": SandboxSchool(
        id="00000000-0000-0000-0000-000000000301",
        key="emmanuel-early-learning",
        track="daycare",
        name="Emmanuel Early Learning Center",
        archetype="Church-based daycare and preschool",
        enrollment=168,
        best_for="check-in/out, care notes, billing, parent updates, and daily trust",
        tour="daycare-daily-care",
    ),
    "cedar-summer-camp": SandboxSchool(
        id="00000000-0000-0000-0000-000000000401",
        key="cedar-summer-camp",
        track="camp",
        name="Cedar Ridge Summer Camp",
        archetype="Seasonal camp and summer program",
        enrollment=260,
        best_for="registration, rosters, attendance, payments, safety notes, and family updates",
        tour="camp-session-operations",
    ),
}

SANDBOX_PERSONAS = {
    "school_admin": SandboxPersona(
        key="school_admin",
        label="Head of School",
        role_code="HEAD_OF_SCHOOL",
        route="/school-admin-dashboard",
        email="admin@heritage.example.org",
        first_name="Grace",
        last_name="Whitaker",
        track_keys=("school", "daycare", "camp"),
        tour_title="Daily operating picture",
        promise="See enrollment, attendance, finance, admissions, and communication health in one operating picture.",
        steps=(
            "Review the leadership dashboard.",
            "Check attendance and enrollment signals.",
            "Open admissions and enrollment indicators.",
            "Review finance risk and parent communication.",
            "Switch to a parent or teacher view to validate stakeholder context.",
        ),
    ),
    "admissions_director": SandboxPersona(
        key="admissions_director",
        label="Admissions Director",
        role_code="REGISTRAR",
        route="/admissions-dashboard",
        email="admissions@heritage.example.org",
        first_name="Caroline",
        last_name="Mercer",
        track_keys=("school", "daycare", "camp"),
        tour_title="Inquiry-to-enrollment proof path",
        promise="Walk an inquiry from first contact through decision, enrollment, and handoff.",
        steps=(
            "Open the admissions dashboard.",
            "Review inquiry volume and applicant stage mix.",
            "Open a fictional applicant record.",
            "Advance one applicant in the demo workflow.",
            "Confirm admissions metrics remain clear for leadership.",
        ),
    ),
    "finance_director": SandboxPersona(
        key="finance_director",
        label="Finance Director",
        role_code="FINANCE_DIRECTOR",
        route="/finance",
        email="finance@heritage.example.org",
        first_name="Daniel",
        last_name="Price",
        track_keys=("school", "daycare", "camp"),
        tour_title="Tuition, aid, receivables, and payment-risk proof",
        promise="Review tuition plans, financial aid impact, family balances, and payment follow-up.",
        steps=(
            "Open the finance dashboard.",
            "Review open balances and receivables risk.",
            "Inspect one family account.",
            "Review tuition and aid impact.",
            "Prepare a payment follow-up path.",
        ),
    ),
    "teacher": SandboxPersona(
        key="teacher",
        label="Teacher / Staff",
        role_code="TEACHER",
        route="/teacher",
        email="teacher.lower@heritage.example.org",
        first_name="Eleanor",
        last_name="Lower",
        track_keys=("school", "daycare", "camp"),
        tour_title="Staff daily workflow",
        promise="Take attendance, view student context, and move through daily classroom work quickly.",
        steps=(
            "Open the staff dashboard.",
            "Take attendance or check participants in.",
            "Review class, group, or roster context.",
            "Open student support details.",
            "Confirm administrative functions are not visible.",
        ),
    ),
    "parent": SandboxPersona(
        key="parent",
        label="Parent / Guardian",
        role_code="PARENT",
        route="/parent",
        email="parent.reed@heritage.example.org",
        first_name="Miriam",
        last_name="Reed",
        track_keys=("school", "daycare", "camp"),
        tour_title="Family experience proof path",
        promise="See child context, communication, application status, attendance, and family account information.",
        steps=(
            "Open the parent dashboard.",
            "Review student snapshot.",
            "Check attendance and communications.",
            "Review billing or statement context.",
            "Confirm the experience is clear for non-technical families.",
        ),
    ),
    "student": SandboxPersona(
        key="student",
        label="Student / Camper",
        role_code="STUDENT",
        route="/student",
        email="student.avery.reed11@heritage.example.org",
        first_name="Avery",
        last_name="Reed",
        track_keys=("school", "camp"),
        tour_title="Learner self-service proof path",
        promise="View schedule, assignments, activities, communications, and progress from a learner perspective.",
        steps=(
            "Open the learner dashboard.",
            "Review schedule and assignments.",
            "Inspect progress context.",
            "Check communications and next actions.",
            "Confirm no administrative functions are visible.",
        ),
    ),
    "board": SandboxPersona(
        key="board",
        label="School Board",
        role_code="HEAD_OF_SCHOOL",
        route="/board",
        email="board@heritage.example.org",
        first_name="Evelyn",
        last_name="Grant",
        track_keys=("school",),
        tour_title="Governance summary proof path",
        promise="Review governance-safe school health, finance, enrollment, and mission indicators from the board view.",
        steps=(
            "Open the board dashboard.",
            "Review mission, enrollment, and finance indicators.",
            "Open board packet or report links.",
            "Confirm governance-safe summaries without operational overreach.",
            "Validate board routes remain distinct from admin workflows.",
        ),
    ),
}


def _active_sandbox_tracks() -> dict:
    if _env_flag("CROWN_SANDBOX_EXPOSE_LEGACY_SCHOOLS", default=False):
        return SANDBOX_TRACKS
    return {"school": SANDBOX_TRACKS["school"]}


def _active_sandbox_schools() -> dict:
    if _env_flag("CROWN_SANDBOX_EXPOSE_LEGACY_SCHOOLS", default=False):
        return SANDBOX_SCHOOLS
    return {"heritage-core": SANDBOX_SCHOOLS["heritage-core"]}


def get_track(track_key: str | None) -> dict:
    return _active_sandbox_tracks().get(track_key or "") or SANDBOX_TRACKS["school"]


def get_school(school_key_or_id: str | None) -> SandboxSchool:
    aliases = {
        "heritage": "heritage-core",
    }
    if not school_key_or_id:
        return SANDBOX_SCHOOLS["heritage-core"]
    school_key_or_id = aliases.get(str(school_key_or_id).strip(), str(school_key_or_id).strip())
    active_schools = _active_sandbox_schools()
    if school_key_or_id in active_schools:
        return active_schools[school_key_or_id]
    for school in active_schools.values():
        if school.id == school_key_or_id:
            return school
    return SANDBOX_SCHOOLS["heritage-core"]


def get_persona(persona_key: str | None) -> SandboxPersona:
    return SANDBOX_PERSONAS.get(persona_key or "") or SANDBOX_PERSONAS["school_admin"]


def catalog_payload() -> dict:
    tracks = _active_sandbox_tracks()
    schools = _active_sandbox_schools()
    return {
        "tracks": list(tracks.values()),
        "schools": [asdict(school) for school in schools.values()],
        "personas": [asdict(persona) for persona in SANDBOX_PERSONAS.values()],
    }
