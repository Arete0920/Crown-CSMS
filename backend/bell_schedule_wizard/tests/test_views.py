import uuid
from datetime import date, time as dtime

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient

from bell_schedule_wizard.models import (
    BellSchedule,
    BellScheduleWizardSession,
    DayTemplate,
    PeriodBlock,
)
from core.models import School

User = get_user_model()

BASE_URL = "/api/v1/bell-schedule-wizard/sessions/"
AY_START = "2027-08-01"
AY_END   = "2028-05-31"

GOOD_SINGLE_DAY_TEMPLATES = [
    {
        "template_code": "DEFAULT",
        "blocks": [
            {"code": "P1",    "label": "Period 1", "start_time": "08:00", "end_time": "08:55", "is_instructional": True},
            {"code": "P2",    "label": "Period 2", "start_time": "09:00", "end_time": "09:55", "is_instructional": True},
            {"code": "LUNCH", "label": "Lunch",    "start_time": "12:00", "end_time": "12:30", "is_lunch": True},
        ],
    }
]

GOOD_AB_TEMPLATES = [
    {
        "template_code": "A",
        "blocks": [
            {"code": "P1", "label": "Period 1", "start_time": "08:00", "end_time": "09:00"},
            {"code": "P2", "label": "Period 2", "start_time": "09:05", "end_time": "10:05"},
        ],
    },
    {
        "template_code": "B",
        "blocks": [
            {"code": "P1", "label": "Period 1", "start_time": "08:00", "end_time": "09:00"},
            {"code": "P3", "label": "Period 3", "start_time": "09:05", "end_time": "10:05"},
        ],
    },
]

GOOD_WEEKDAY_TEMPLATES = [
    {"template_code": "MON", "blocks": [{"code": "P1", "label": "Period 1", "start_time": "08:00", "end_time": "09:00"}]},
    {"template_code": "TUE", "blocks": [{"code": "P1", "label": "Period 1", "start_time": "08:00", "end_time": "09:00"}]},
    {"template_code": "WED", "blocks": [{"code": "P1", "label": "Period 1", "start_time": "08:00", "end_time": "09:00"}]},
]


def _make_school(name=None):
    name = name or f"BSW {uuid.uuid4().hex[:6]}"
    return School.objects.create(name=name, timezone="America/Chicago", is_active=True)


def _make_user():
    return User.objects.create_user(username=f"u{uuid.uuid4().hex[:8]}", password="pw")


def _make_ay(school, start=AY_START, end=AY_END):
    from core.models import AcademicYear
    return AcademicYear.objects.create(
        school=school,
        name=f"AY {uuid.uuid4().hex[:4]}",
        start_date=date.fromisoformat(start),
        end_date=date.fromisoformat(end),
    )


def _headers(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


def _authed_client():
    c = APIClient()
    c.force_authenticate(user=_make_user())
    return c


def _advance_to_configured(client, school, ay, mode="SINGLE_DAY", name="Standard"):
    r = client.post(BASE_URL, **_headers(school.id))
    sid = r.data["session_id"]
    client.post(
        f"{BASE_URL}{sid}/configure/",
        {"schedule_name": name, "schedule_mode": mode, "academic_year_id": str(ay.id)},
        format="json",
        **_headers(school.id),
    )
    return sid


def _advance_to_blocks_set(client, school, ay, templates=None, mode="SINGLE_DAY", name="Standard"):
    templates = templates or GOOD_SINGLE_DAY_TEMPLATES
    sid = _advance_to_configured(client, school, ay, mode=mode, name=name)
    client.post(
        f"{BASE_URL}{sid}/blocks/",
        {"templates": templates},
        format="json",
        **_headers(school.id),
    )
    return sid


def _advance_to_committed(client, school, ay, templates=None, mode="SINGLE_DAY", name="Standard"):
    templates = templates or GOOD_SINGLE_DAY_TEMPLATES
    sid = _advance_to_blocks_set(client, school, ay, templates=templates, mode=mode, name=name)
    client.post(f"{BASE_URL}{sid}/commit/", format="json", **_headers(school.id))
    return sid


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class BellScheduleAuthTest(TestCase):
    def test_create_requires_auth(self):
        school = _make_school()
        r = APIClient().post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 401)

    def test_configure_requires_auth(self):
        school = _make_school()
        c = _authed_client()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = APIClient().post(f"{BASE_URL}{sid}/configure/", **_headers(school.id))
        self.assertEqual(r2.status_code, 401)


# ---------------------------------------------------------------------------
# Tenant
# ---------------------------------------------------------------------------

class BellScheduleTenantTest(TestCase):
    def test_missing_school_header_returns_400(self):
        c = _authed_client()
        r = c.post(BASE_URL)
        self.assertEqual(r.status_code, 400)

    def test_school_mismatch_returns_404(self):
        school_a = _make_school()
        school_b = _make_school()
        ay = _make_ay(school_a)
        c = _authed_client()
        r = c.post(BASE_URL, **_headers(school_a.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"schedule_name": "X", "schedule_mode": "SINGLE_DAY", "academic_year_id": str(ay.id)},
            format="json",
            **_headers(school_b.id),
        )
        self.assertEqual(r2.status_code, 404)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

class BellScheduleCreateTest(TestCase):
    def test_create_returns_201_and_draft(self):
        school = _make_school()
        c = _authed_client()
        r = c.post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["status"], "draft")
        self.assertIn("session_id", r.data)

    def test_create_persists_session(self):
        school = _make_school()
        c = _authed_client()
        r = c.post(BASE_URL, **_headers(school.id))
        self.assertTrue(BellScheduleWizardSession.objects.filter(pk=r.data["session_id"]).exists())


# ---------------------------------------------------------------------------
# Configure
# ---------------------------------------------------------------------------

class BellScheduleConfigureTest(TestCase):
    def test_configure_single_day_happy(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"schedule_name": "Standard", "schedule_mode": "SINGLE_DAY", "academic_year_id": str(ay.id)},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["status"], "configured")
        self.assertEqual(r2.data["schedule_mode"], "SINGLE_DAY")

    def test_configure_day_templates_happy(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"schedule_name": "A/B Day", "schedule_mode": "DAY_TEMPLATES", "academic_year_id": str(ay.id)},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["schedule_mode"], "DAY_TEMPLATES")

    def test_configure_missing_name(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"schedule_mode": "SINGLE_DAY", "academic_year_id": str(ay.id)},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)

    def test_configure_missing_academic_year(self):
        school = _make_school()
        c = _authed_client()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"schedule_name": "Standard", "schedule_mode": "SINGLE_DAY"},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)

    def test_configure_bad_schedule_mode(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"schedule_name": "Standard", "schedule_mode": "WEEKLY", "academic_year_id": str(ay.id)},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)

    def test_configure_ay_not_in_school(self):
        school_a = _make_school()
        school_b = _make_school()
        ay_b = _make_ay(school_b)
        c = _authed_client()
        r = c.post(BASE_URL, **_headers(school_a.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"schedule_name": "Standard", "schedule_mode": "SINGLE_DAY", "academic_year_id": str(ay_b.id)},
            format="json",
            **_headers(school_a.id),
        )
        self.assertEqual(r2.status_code, 404)


# ---------------------------------------------------------------------------
# Set Blocks
# ---------------------------------------------------------------------------

class BellScheduleBlocksTest(TestCase):
    def test_draft_guard(self):
        school = _make_school()
        c = _authed_client()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/blocks/",
            {"templates": GOOD_SINGLE_DAY_TEMPLATES},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)

    def test_happy_single_day(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        sid = _advance_to_configured(c, school, ay, mode="SINGLE_DAY")
        r = c.post(
            f"{BASE_URL}{sid}/blocks/",
            {"templates": GOOD_SINGLE_DAY_TEMPLATES},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "blocks_set")
        self.assertEqual(r.data["template_count"], 1)

    def test_happy_day_templates_ab(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        sid = _advance_to_configured(c, school, ay, mode="DAY_TEMPLATES")
        r = c.post(
            f"{BASE_URL}{sid}/blocks/",
            {"templates": GOOD_AB_TEMPLATES},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["template_count"], 2)

    def test_happy_weekday_templates(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        sid = _advance_to_configured(c, school, ay, mode="DAY_TEMPLATES")
        r = c.post(
            f"{BASE_URL}{sid}/blocks/",
            {"templates": GOOD_WEEKDAY_TEMPLATES},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["template_count"], 3)

    def test_missing_block_code(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        sid = _advance_to_configured(c, school, ay, mode="SINGLE_DAY")
        bad = [{"template_code": "DEFAULT", "blocks": [
            {"label": "P1", "start_time": "08:00", "end_time": "09:00"}
        ]}]
        r = c.post(f"{BASE_URL}{sid}/blocks/", {"templates": bad}, format="json", **_headers(school.id))
        self.assertEqual(r.status_code, 400)

    def test_start_gte_end_rejected(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        sid = _advance_to_configured(c, school, ay, mode="SINGLE_DAY")
        bad = [{"template_code": "DEFAULT", "blocks": [
            {"code": "P1", "label": "Period 1", "start_time": "09:00", "end_time": "08:00"}
        ]}]
        r = c.post(f"{BASE_URL}{sid}/blocks/", {"templates": bad}, format="json", **_headers(school.id))
        self.assertEqual(r.status_code, 400)

    def test_overlap_rejected(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        sid = _advance_to_configured(c, school, ay, mode="SINGLE_DAY")
        bad = [{"template_code": "DEFAULT", "blocks": [
            {"code": "P1", "label": "Period 1", "start_time": "08:00", "end_time": "09:30"},
            {"code": "P2", "label": "Period 2", "start_time": "09:00", "end_time": "10:00"},
        ]}]
        r = c.post(f"{BASE_URL}{sid}/blocks/", {"templates": bad}, format="json", **_headers(school.id))
        self.assertEqual(r.status_code, 400)

    def test_single_day_wrong_template_count(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        sid = _advance_to_configured(c, school, ay, mode="SINGLE_DAY")
        r = c.post(
            f"{BASE_URL}{sid}/blocks/",
            {"templates": GOOD_AB_TEMPLATES},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_single_day_wrong_template_code(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        sid = _advance_to_configured(c, school, ay, mode="SINGLE_DAY")
        bad = [{"template_code": "A", "blocks": [
            {"code": "P1", "label": "Period 1", "start_time": "08:00", "end_time": "09:00"}
        ]}]
        r = c.post(f"{BASE_URL}{sid}/blocks/", {"templates": bad}, format="json", **_headers(school.id))
        self.assertEqual(r.status_code, 400)

    def test_duplicate_template_code_rejected(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        sid = _advance_to_configured(c, school, ay, mode="DAY_TEMPLATES")
        bad = [
            {"template_code": "A", "blocks": [{"code": "P1", "label": "P1", "start_time": "08:00", "end_time": "09:00"}]},
            {"template_code": "A", "blocks": [{"code": "P1", "label": "P1", "start_time": "08:00", "end_time": "09:00"}]},
        ]
        r = c.post(f"{BASE_URL}{sid}/blocks/", {"templates": bad}, format="json", **_headers(school.id))
        self.assertEqual(r.status_code, 400)


# ---------------------------------------------------------------------------
# Commit
# ---------------------------------------------------------------------------

class BellScheduleCommitTest(TestCase):
    def test_commit_creates_schedule(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        sid = _advance_to_blocks_set(c, school, ay)
        r = c.post(f"{BASE_URL}{sid}/commit/", format="json", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertIn("schedule_id", r.data)
        self.assertTrue(BellSchedule.objects.filter(pk=r.data["schedule_id"]).exists())

    def test_commit_creates_day_templates(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        sid = _advance_to_blocks_set(c, school, ay, templates=GOOD_AB_TEMPLATES, mode="DAY_TEMPLATES")
        r = c.post(f"{BASE_URL}{sid}/commit/", format="json", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        sched = BellSchedule.objects.get(pk=r.data["schedule_id"])
        self.assertEqual(DayTemplate.objects.filter(schedule=sched).count(), 2)

    def test_commit_creates_period_blocks(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        sid = _advance_to_blocks_set(c, school, ay)
        r = c.post(f"{BASE_URL}{sid}/commit/", format="json", **_headers(school.id))
        sched = BellSchedule.objects.get(pk=r.data["schedule_id"])
        tpl = DayTemplate.objects.get(schedule=sched, template_code="DEFAULT")
        self.assertEqual(PeriodBlock.objects.filter(template=tpl).count(), 3)

    def test_commit_returns_schedule_id_and_templates(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        sid = _advance_to_blocks_set(c, school, ay)
        r = c.post(f"{BASE_URL}{sid}/commit/", format="json", **_headers(school.id))
        self.assertIn("schedule_id", r.data)
        self.assertIn("templates", r.data)

    def test_draft_guard(self):
        school = _make_school()
        c = _authed_client()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(f"{BASE_URL}{sid}/commit/", format="json", **_headers(school.id))
        self.assertEqual(r2.status_code, 400)

    def test_configured_guard(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        sid = _advance_to_configured(c, school, ay, mode="SINGLE_DAY")
        r2 = c.post(f"{BASE_URL}{sid}/commit/", format="json", **_headers(school.id))
        self.assertEqual(r2.status_code, 400)

    def test_idempotent_commit_replaces_blocks(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        # First commit: 3 blocks
        sid = _advance_to_blocks_set(c, school, ay)
        c.post(f"{BASE_URL}{sid}/commit/", format="json", **_headers(school.id))
        # Second commit: same name, 1 block � blocks replaced
        sid2 = _advance_to_blocks_set(c, school, ay, templates=[{
            "template_code": "DEFAULT",
            "blocks": [{"code": "P1", "label": "P1 Updated", "start_time": "08:00", "end_time": "09:00"}],
        }])
        r2 = c.post(f"{BASE_URL}{sid2}/commit/", format="json", **_headers(school.id))
        sched = BellSchedule.objects.get(pk=r2.data["schedule_id"])
        tpl = DayTemplate.objects.get(schedule=sched, template_code="DEFAULT")
        self.assertEqual(PeriodBlock.objects.filter(template=tpl).count(), 1)


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

class BellScheduleVerifyTest(TestCase):
    def test_verify_returns_snapshot(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        sid = _advance_to_committed(c, school, ay)
        r = c.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["template_count"], 1)
        self.assertIn("snapshot", r.data)
        self.assertEqual(r.data["snapshot"][0]["template_code"], "DEFAULT")

    def test_verify_before_commit_rejected(self):
        school = _make_school()
        c = _authed_client()
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r2.status_code, 400)


# ---------------------------------------------------------------------------
# Single-active
# ---------------------------------------------------------------------------

class BellScheduleSingleActiveTest(TestCase):
    def test_committed_schedule_is_active(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        sid = _advance_to_committed(c, school, ay)
        sess = BellScheduleWizardSession.objects.get(pk=sid)
        sched = BellSchedule.objects.get(pk=sess.commit_result["schedule_id"])
        self.assertTrue(sched.is_active)

    def test_second_commit_flips_first_inactive(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        # First commit: Standard (3 blocks)
        sid1 = _advance_to_committed(c, school, ay, name="Standard")
        sess1 = BellScheduleWizardSession.objects.get(pk=sid1)
        sched1_id = sess1.commit_result["schedule_id"]
        # Second commit: different name -> new schedule object
        sid2 = _advance_to_committed(c, school, ay, templates=[{
            "template_code": "DEFAULT",
            "blocks": [{"code": "P1", "label": "P1", "start_time": "08:00", "end_time": "09:00"}],
        }], name="Chapel Day")
        # First schedule now inactive
        sched1 = BellSchedule.objects.get(pk=sched1_id)
        self.assertFalse(sched1.is_active)


# ---------------------------------------------------------------------------
# Snapshot (integration hook for Wizard #20 section scheduler)
# ---------------------------------------------------------------------------

class BellScheduleSnapshotTest(TestCase):
    def test_verify_snapshot_block_fields(self):
        school = _make_school()
        ay = _make_ay(school)
        c = _authed_client()
        sid = _advance_to_committed(c, school, ay)
        r = c.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        tpl = r.data["snapshot"][0]
        self.assertEqual(tpl["template_code"], "DEFAULT")
        block = tpl["blocks"][0]
        for field in ("code", "start_time", "end_time", "ordering"):
            self.assertIn(field, block)

    def test_cross_tenant_isolation(self):
        school_a = _make_school()
        school_b = _make_school()
        ay_a = _make_ay(school_a)
        c = _authed_client()
        r = c.post(BASE_URL, **_headers(school_a.id))
        sid = r.data["session_id"]
        r2 = c.get(f"{BASE_URL}{sid}/verify/", **_headers(school_b.id))
        self.assertEqual(r2.status_code, 404)


# ---------------------------------------------------------------------------
# DB constraints
# ---------------------------------------------------------------------------

class BellScheduleDBConstraintTest(TestCase):
    def test_unique_period_block_code_enforced(self):
        school = _make_school()
        ay = _make_ay(school)
        sched = BellSchedule.objects.create(
            school=school,
            academic_year=ay,
            name="DBTest",
            schedule_mode="SINGLE_DAY",
            is_active=True,
        )
        tpl = DayTemplate.objects.create(schedule=sched, template_code="DEFAULT", ordering=0)
        PeriodBlock.objects.create(
            template=tpl, code="P1", label="Period 1",
            start_time=dtime(8, 0), end_time=dtime(9, 0),
        )
        with self.assertRaises(IntegrityError):
            PeriodBlock.objects.create(
                template=tpl, code="P1", label="Duplicate",
                start_time=dtime(9, 5), end_time=dtime(10, 0),
            )
