CROWN_AUTHORITY_RULES = [
    {
        "rule": "CROWN owns process truth",
        "detail": (
            "Remote learning activation, teacher readiness, parent visibility, "
            "student actions, curriculum maps, interventions, dual enrollment, "
            "and transcript impact originate in CROWN."
        ),
    },
    {
        "rule": "CROWN owns SIS truth",
        "detail": (
            "Students, households, guardians, staff, courses, sections, rosters, "
            "attendance, grades, transcript records, and intervention records "
            "remain authoritative in CROWN."
        ),
    },
    {
        "rule": "Microsoft executes and collaborates",
        "detail": (
            "Teams, Microsoft 365, Microsoft Education, Assignments, Classwork, "
            "SDS, Insights, Reflect, OneDrive, and SharePoint support execution "
            "and collaboration but do not replace CROWN record truth."
        ),
    },
    {
        "rule": "External systems report sync state",
        "detail": (
            "Microsoft and provider systems return sync status, errors, timestamps, "
            "launch status, assignment status, and engagement signals for CROWN review."
        ),
    },
    {
        "rule": "CROWN resolves conflicts",
        "detail": (
            "If CROWN and an external system disagree, CROWN shows an exception "
            "and requires authorized review instead of silently accepting external state."
        ),
    },
]


def _metric(label, value, helper, tone="royal"):
    return {"label": label, "value": value, "helper": helper, "tone": tone}


def _record(record_id, record_type, state, crown_truth, external_role, sync_state, next_action):
    return {
        "crownRecordId": record_id,
        "recordType": record_type,
        "state": state,
        "crownTruth": crown_truth,
        "microsoftRole": external_role,
        "syncState": sync_state,
        "nextAction": next_action,
    }


LEARNING_CONTINUITY_PAGES = {
    "onlineCommand": {
        "pageKey": "onlineCommand",
        "eyebrow": "CROWN source of truth",
        "title": "Online Learning Command Center",
        "subtitle": (
            "CROWN-owned activation, monitoring, communication, attendance, "
            "assignment, and evidence control for remote or closure learning."
        ),
        "crownOwner": "School Administrator / Principal",
        "authorityStatement": (
            "Remote-learning days are created, governed, closed, and archived in CROWN. "
            "Teams and Microsoft services execute class collaboration and return status back to CROWN."
        ),
        "primarySource": "CROWN",
        "externalSystems": ["Microsoft Teams", "Microsoft 365", "Microsoft Graph"],
        "metrics": [
            _metric("Remote day state", "Configured", "CROWN workflow shell is ready for activation state wiring.", "royal"),
            _metric("Class readiness", "91%", "CROWN readiness score from lesson, Teams, attendance, assignment, and roster checks.", "emerald"),
            _metric("Family notice gap", "31", "Families that have not opened required notice.", "amber"),
            _metric("Evidence state", "Draft", "Closure-day audit packet is defined but not yet backed by live export.", "violet"),
        ],
        "records": [
            _record(
                "RLD-2026-0001",
                "RemoteLearningDay",
                "Configured",
                "Remote day activation, scope, reason, dates, affected classes, and closeout belong to CROWN.",
                "Receives class meeting/channel activation and returns launch/completion status.",
                "Pending",
                "Wire backend RemoteLearningDay model and activation endpoint.",
            ),
            _record(
                "CLR-2026-0001",
                "ClassLearningReadiness",
                "Watch",
                "CROWN calculates readiness from roster, lesson, assignment, attendance method, and Teams verification.",
                "Returns class team, channel, meeting, and assignment availability.",
                "Warning",
                "Create readiness API that aggregates CROWN and Microsoft status.",
            ),
        ],
        "workflow": [
            "Create remote-learning day in CROWN.",
            "Select closure reason, affected dates, grades, classes, and operating rules.",
            "Generate CROWN announcements and required acknowledgements.",
            "Verify Teams/class/channel/assignment readiness.",
            "Monitor live class launch, attendance, and family access.",
            "Close day and export evidence packet.",
        ],
    },
    "teacherCockpit": {
        "pageKey": "teacherCockpit",
        "eyebrow": "CROWN teacher truth",
        "title": "Teacher Daily Cockpit",
        "subtitle": "CROWN-owned teacher operating page for the class day.",
        "crownOwner": "Teacher / Academic Leadership",
        "authorityStatement": (
            "The teacher's class obligations, lesson expectations, attendance state, "
            "grading queue, and student-support responsibilities originate in CROWN."
        ),
        "primarySource": "CROWN",
        "externalSystems": ["Microsoft Teams", "Microsoft 365", "Microsoft Graph"],
        "metrics": [
            _metric("Next class", "10:05", "CROWN schedule and section roster determine the next teaching obligation.", "royal"),
            _metric("Attendance open", "1", "Attendance state belongs to CROWN SIS/attendance workflow.", "amber"),
            _metric("Ungraded work", "23", "CROWN gradebook owns grading obligations and final grade truth.", "rose"),
            _metric("Lesson state", "Ready", "Publisher baseline and teacher edits available for today.", "emerald"),
        ],
        "records": [
            _record(
                "CLS-ENG8B-2026-05-27",
                "ClassSession",
                "Ready",
                "CROWN owns section, roster, class time, attendance requirement, and completion state.",
                "Hosts Teams class meeting or class channel if remote/hybrid.",
                "Pending",
                "Connect ClassSession state to schedule, attendance, and Teams launch status.",
            ),
            _record(
                "LP-ENG8B-U04-L12",
                "LessonPlan",
                "Ready",
                "CROWN owns lesson objective, curriculum map position, teacher edits, and actual-taught state.",
                "May receive files, links, resources, or assignment shells.",
                "Manual review",
                "Build lesson-plan API and version history.",
            ),
        ],
        "workflow": [
            "Open next class from CROWN schedule.",
            "Review roster and support flags.",
            "Open CROWN lesson plan and Teams resources.",
            "Take attendance in CROWN.",
            "Post or confirm assignment obligation.",
            "Update actual-taught status and grading queue.",
        ],
    },
    "parentStatus": {
        "pageKey": "parentStatus",
        "eyebrow": "CROWN family truth",
        "title": "Parent Learning Status",
        "subtitle": "CROWN-owned family view of child schedule, attendance, missing work, messages, grades, and school actions.",
        "crownOwner": "Parent / Guardian, constrained by CROWN family-scope permissions",
        "authorityStatement": (
            "CROWN determines what each parent can see based on household/guardian relationships, "
            "student enrollment, role permissions, and school policy."
        ),
        "primarySource": "CROWN",
        "externalSystems": ["Microsoft Teams", "Microsoft 365", "Microsoft School Data Sync"],
        "metrics": [
            _metric("Family tasks", "4", "CROWN family action queue.", "amber"),
            _metric("Child learning status", "Watch", "One child has missing work or access risk.", "rose"),
            _metric("Unread school messages", "3", "CROWN communications remain family-scoped.", "violet"),
            _metric("Class links ready", "6", "Teams/Microsoft links surfaced through CROWN.", "emerald"),
        ],
        "records": [
            _record(
                "FAM-0042-STUDENT-LEARNING-DAY",
                "ParentLearningDigest",
                "Watch",
                "CROWN owns family-scoped digest, school actions, child status, and communication visibility.",
                "May supply Teams assignment or guardian digest metadata where available.",
                "Pending",
                "Create parent digest endpoint from CROWN SIS, communications, gradebook, and attendance.",
            )
        ],
        "workflow": [
            "Identify current parent/guardian household in CROWN.",
            "Load only that family's students.",
            "Show today's schedule, attendance, missing work, messages, and actions.",
            "Surface Teams links without exposing unrelated class data.",
            "Record required acknowledgements in CROWN.",
        ],
    },
}


ALIASES = {
    "studentToday": "parentStatus",
    "curriculumImport": "teacherCockpit",
    "microsoftHealth": "onlineCommand",
    "dualEnrollment": "teacherCockpit",
    "interventions": "teacherCockpit",
}


def get_learning_continuity_page(page_key: str) -> dict | None:
    canonical_key = page_key if page_key in LEARNING_CONTINUITY_PAGES else ALIASES.get(page_key)
    if canonical_key is None:
        return None

    page = dict(LEARNING_CONTINUITY_PAGES[canonical_key])
    page["pageKey"] = page_key
    return page
