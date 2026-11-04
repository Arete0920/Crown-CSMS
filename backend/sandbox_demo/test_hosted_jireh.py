"""Source-level hosted Jireh acceptance with isolated synthetic SQLite.

Only runtime-check functions are mocked to run these isolated DB cases.
Actual Azure DEV PostgreSQL and browser acceptance remain separate NO-GO gates.
"""
from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from uuid import uuid4

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from aid.models import AidApplication, AidFinancialProfile
from core.models import School, UserAccount, UserRole
from jireh_sgo.models import (
    SGOApplication, SGOFamilyIntake, SGOFamilyGrant, SGOProcessorAssignment,
)
from sandbox_demo.buyer_workspace import buyer_username
from sandbox_demo.models import SandboxBuyerWorkspace, SandboxInvite

SHA = "e" * 40
SEED = "sandbox_demo.management.commands.seed_hosted_jireh_buyer"
AID = "/api/v1/buyer-demo/jireh/aid/family/"
SGO = "/api/v1/buyer-demo/jireh/sgo/"


@override_settings(
    CROWN_ENV="dev", DEBUG=False, BUILD_SHA=SHA,
    CROWN_SANDBOX_ALLOW_OPEN_SESSION=False,
    CROWN_HOSTED_JIREH_DEMO_ENABLED=True,
    ALLOWED_HOSTS=["testserver"],
)
class HostedJirehContract(TestCase):
    def setUp(self):
        self.bindings = [self.make_buyer(), self.make_buyer()]

    def make_buyer(self):
        school = School.objects.create(name="Fictional school", is_active=True)
        roles = ("parent", "finance_director")
        invite = SandboxInvite.objects.create(
            organization_label="Invented buyer organization",
            allowed_roles=list(roles), allowed_seed_packs=["heritage-core"],
            track="school", expires_at=timezone.now() + timedelta(hours=1),
        )
        ws = SandboxBuyerWorkspace.objects.create(
            invite=invite, school=school, source_sha=SHA,
            provisioned_at=timezone.now(),
        )
        users = {}
        for key, role in (("parent", "PARENT"), ("finance_director", "FINANCE_DIRECTOR")):
            username = buyer_username(school.id, key)
            user = UserAccount.objects.create(
                username=username, email=username, school=school,
                is_active=True, is_staff=False, is_superuser=False,
            )
            user.set_unusable_password()
            user.save(update_fields=["password"])
            UserRole.objects.create(school=school, user=user, role_code=role)
            users[key] = user
        with patch(SEED + "._require_existing_dev_runtime"):
            with patch("sys.stdin", StringIO(invite.pk + "\n")):
                call_command(
                    "seed_hosted_jireh_buyer", "--expected-sha", SHA,
                    "--invite-stdin", "--apply", stdout=StringIO(),
                )
        return ws, users

    def client_as(self, i=0, role="parent"):
        workspace, users = self.bindings[i]
        client = APIClient()
        client.force_login(users[role])
        # Use a canonical tenant header; foreign headers must not override it.
        return client, {"HTTP_X_SCHOOL_ID": str(workspace.school_id)}

    def aid_payload(self, i=0):
        client, h = self.client_as(i)
        data = client.get(AID, **h).json()
        return {
            "fictional_acknowledged": True,
            "scenario": "fictional_modest",
            "household_size": 3,
            "academic_year_id": data["academic_years"][0]["id"],
            "student_ids": [data["students"][0]["id"]],
        }

    def request(self, method, url, i=0, role="parent", payload=None, **extra_headers):
        client, headers = self.client_as(i, role=role)
        headers.update(extra_headers)
        with patch("sandbox_demo.hosted_jireh.hosted_jireh_runtime", return_value=True):
            if method == "GET":
                return client.get(url, **headers)
            return client.post(url, payload, format="json", **headers)

    def test_school_aid_submit_persists_then_readback_and_duplicate_conflict(self):
        with patch("sandbox_demo.hosted_jireh.hosted_jireh_runtime", return_value=True):
            payload = self.aid_payload(0)
        first = self.request("POST", AID, payload=payload)
        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(first.json()["application"]["status"], "SUBMITTED")
        duplicate = self.request("POST", AID, payload=payload)
        self.assertEqual(duplicate.status_code, 409)
        response = self.request("GET", AID)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["applications"]), 1)
        self.assertEqual(response.json()["applications"][0]["id"], first.json()["application"]["id"])
        self.assertEqual(AidApplication.objects.count(), 1)
        self.assertEqual(AidFinancialProfile.objects.count(), 1)
        self.assertEqual(self.request("GET", AID, role="finance_director").status_code, 404)

    def test_school_aid_two_buyers_and_foreign_students_cannot_mix(self):
        with patch("sandbox_demo.hosted_jireh.hosted_jireh_runtime", return_value=True):
            one = self.aid_payload(0)
            two = self.aid_payload(1)
        foreign = dict(one, student_ids=two["student_ids"])
        self.assertEqual(self.request("POST", AID, payload=foreign).status_code, 404)
        other = dict(one, academic_year_id=two["academic_year_id"])
        self.assertEqual(self.request("POST", AID, payload=other).status_code, 404)
        self.assertEqual(self.request("POST", AID, payload=one).status_code, 201)
        self.assertEqual(self.request("GET", AID, i=1).json()["applications"], [])
        self.assertEqual(self.request("GET", AID, HTTP_X_SCHOOL_ID=str(self.bindings[1][0].school_id)).status_code, 404)

    def test_rejects_extra_financial_fields_and_revoked_access(self):
        with patch("sandbox_demo.hosted_jireh.hosted_jireh_runtime", return_value=True):
            payload = self.aid_payload()
        self.assertEqual(self.request("POST", AID, payload={**payload, "actual_income": 999}).status_code, 400)
        self.assertEqual(self.request("POST", AID, payload={**payload, "fictional_acknowledged": False}).status_code, 400)
        self.assertFalse(AidApplication.objects.exists())
        workspace, _ = self.bindings[0]
        workspace.invite.revoked_at = timezone.now()
        workspace.invite.save(update_fields=["revoked_at"])
        self.assertEqual(self.request("GET", AID).status_code, 403)
        self.assertEqual(self.request("GET", SGO + "family/programs/").status_code, 403)

    def test_sgo_partner_submit_idempotent_and_readback(self):
        programs = self.request("GET", SGO + "family/programs/")
        self.assertEqual(programs.status_code, 200, programs.content)
        program = programs.json()["programs"][0]
        payload = {
            "program_id": program["id"], "grade_level": "7",
            "consent": True, "consent_version": program["consent_version"],
            "submission_key": str(uuid4()),
        }
        created = self.request("POST", SGO + "family/submit/", payload=payload)
        self.assertEqual(created.status_code, 201, created.content)
        same = self.request("POST", SGO + "family/submit/", payload=payload)
        self.assertEqual(same.status_code, 200, same.content)
        self.assertFalse(same.json()["created"])
        self.assertEqual(SGOApplication.objects.count(), 1)
        self.assertEqual(SGOFamilyIntake.objects.count(), 1)
        app_id = created.json()["application"]["id"]
        self.assertEqual(self.request("GET", SGO + "family/applications/" + app_id + "/").status_code, 200)
        queue = self.request("GET", SGO + "processor/programs/" + program["id"] + "/queue/", role="finance_director")
        self.assertEqual(queue.status_code, 200, queue.content)
        self.assertEqual(len(queue.json()["applications"]), 1)
        self.assertEqual(queue.json()["funds_status"], "NONCASH_ONLY")
        self.assertEqual(self.request("GET", SGO + "family/applications/" + app_id + "/", i=1).status_code, 403)

    def test_sgo_cross_partner_and_missing_grants_fail_closed(self):
        a = self.request("GET", SGO + "family/programs/").json()["programs"][0]
        b = self.request("GET", SGO + "family/programs/", i=1).json()["programs"][0]
        payload = {
            "program_id": b["id"], "grade_level": "7", "consent": True,
            "consent_version": b["consent_version"], "submission_key": str(uuid4()),
        }
        self.assertEqual(self.request("POST", SGO + "family/submit/", payload=payload).status_code, 404)
        self.assertEqual(self.request("GET", SGO + "processor/programs/" + b["id"] + "/queue/", role="finance_director").status_code, 404)
        self.assertEqual(self.request("GET", SGO + "processor/programs/" + a["id"] + "/queue/", role="parent").status_code, 404)
        grant = SGOFamilyGrant.objects.get(program_id=a["id"])
        grant.active = False
        grant.save(update_fields=["active"])
        self.assertEqual(self.request("GET", SGO + "family/programs/").json()["programs"], [])
        self.assertFalse(SGOApplication.objects.exists())

    def test_sgo_no_implicit_processor_authority_and_correction_revision(self):
        program = self.request("GET", SGO + "family/programs/").json()["programs"][0]
        payload = {
            "program_id": program["id"], "grade_level": "7",
            "consent": True, "consent_version": program["consent_version"],
            "submission_key": str(uuid4()),
        }
        app_id = self.request("POST", SGO + "family/submit/", payload=payload).json()["application"]["id"]
        assignment = SGOProcessorAssignment.objects.get(program_id=program["id"])
        assignment.active = False
        assignment.save(update_fields=["active"])
        queue = SGO + "processor/programs/" + program["id"] + "/queue/"
        self.assertEqual(self.request("GET", queue, role="finance_director").status_code, 404)
        assignment.active = True
        assignment.save(update_fields=["active"])
        corrected = self.request(
            "POST", SGO + "processor/applications/" + app_id + "/request-correction/",
            role="finance_director",
            payload={"expected_revision": 1, "reason": "GRADE_UNVERIFIED", "request_key": str(uuid4())},
        )
        self.assertEqual(corrected.status_code, 200, corrected.content)
        self.assertEqual(corrected.json()["application"]["revision"], 2)
        resubmitted = self.request(
            "POST", SGO + "family/applications/" + app_id + "/correct/",
            payload={"expected_revision": 2, "grade_level": "8", "correction_key": str(uuid4())},
        )
        self.assertEqual(resubmitted.status_code, 200, resubmitted.content)
        self.assertEqual(resubmitted.json()["application"]["status"], "RESUBMITTED")

    def test_local_guards_remain_closed_on_hosted_runtime(self):
        self.assertEqual(self.request("GET", "/api/v1/aid/family/demo-intake/").status_code, 404)
        # The legacy standalone SGO guard rejects untrusted school selector
        # headers before reaching the local-only runtime check.
        self.assertEqual(self.request("GET", "/api/v1/jireh-sgo/family/programs/").status_code, 400)
        client, _ = self.client_as()
        self.assertEqual(client.get("/api/v1/jireh-sgo/family/programs/").status_code, 404)

    @override_settings(CROWN_HOSTED_JIREH_DEMO_ENABLED=False)
    def test_hosted_endpoints_disabled_by_default(self):
        client, headers = self.client_as()
        response = client.get(AID, **headers)
        self.assertEqual(response.status_code, 404)
        from sandbox_demo.hosted_jireh import hosted_jireh_runtime
        self.assertFalse(hosted_jireh_runtime())
