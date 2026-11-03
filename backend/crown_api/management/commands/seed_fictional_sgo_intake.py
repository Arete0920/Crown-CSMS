"""Seed two strictly fictional partner SGOs into the isolated local Heritage database."""
import secrets
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from jireh_sgo.family_intake_api import fictional_intake_enabled
from jireh_sgo.models import ( SGOFamilyGrant, SGOMembership, SGOOrganization, SGOProcessorAssignment, )
from jireh_sgo.services import create_program
from sandbox_demo.management.commands.five_module_demo_preflight import ( _require_isolated_local_database, )
PARTNERS = ( ("de", "Fictional Delaware SGO (demo)", "DE"), ("pa", "Fictional Pennsylvania SGO (demo)", "PA"), )
def _make_user(username):
    User = get_user_model()
    email = f"{username}@example.test"
    user = User.objects.filter(username=username).first()
    if user and user.email != email:
        raise CommandError("A local account conflicts with a reserved fictional demo username.")
    if user is None:
        user = User.objects.create_user(username=username, email=email)
    if not user.is_active:
        raise CommandError("A reserved fictional demo user is inactive; do not override.")
    secret = secrets.token_urlsafe(20)
    user.set_password(secret)
    user.save(update_fields=["password"])
    return user, secret
class Command(BaseCommand):
    help = "Local-only: seed synthetic SGO partner programs and per-program family/processor grants."
    def add_arguments(self, parser):
        parser.add_argument("--credentials-file", required=True, help="Write rotating demo-only credentials to a private local file.")
    @transaction.atomic
    def handle(self, *args, **options):
        if not fictional_intake_enabled():
            raise CommandError("Fictional intake seeding requires explicitly enabled, nonhosted local mode.")
        # Local environment flags alone do not prove a database is disposable.
        # Validate the exact isolated Heritage SQLite target before any writes.
        _require_isolated_local_database()
        lines = [ "# CROWN fictional SGO local demo accounts. Never use for live families or partners.", "# Regenerated when the Heritage demo is prepared. No public partner registration exists.", ]
        for code, legal_name, state in PARTNERS:
            partner, partner_secret = _make_user(f"sgo_demo_{code}_partner")
            family, family_secret = _make_user(f"sgo_demo_{code}_family")
            processor, processor_secret = _make_user(f"sgo_demo_{code}_processor")
            org, _ = SGOOrganization.objects.get_or_create( legal_name=legal_name, state_of_domicile=state, defaults={"active": True}, )
            if not org.active:
                raise CommandError("Inactive fictional partner requires manual reconciliation.")
            member, _ = SGOMembership.objects.get_or_create( organization=org, user=partner, defaults={"role": SGOMembership.ADMIN, "active": True}, )
            if member.role != SGOMembership.ADMIN:
                raise CommandError("Fictional partner membership role mismatch.")
            if not member.active:
                raise CommandError("Inactive fictional partner membership requires manual reconciliation.")
            program = create_program( user=partner, organization_id=org.id, name=f"{state} Synthetic Scholarship Intake 2027", code=f"fictional-{code}-2027", calendar_year=2027,
                funding_source="PRIVATE", rule_version="DEMO_POLICY_2027_V1",
            )
            student = uuid5(NAMESPACE_URL, f"crown-fictional-sgo-{code}-student")
            school = uuid5(NAMESPACE_URL, f"crown-fictional-sgo-{code}-school")
            grant, _ = SGOFamilyGrant.objects.get_or_create( program=program, student_key=student, defaults={ "user": family, "school_key": school,
                    "consent_version": "DEMO_CONSENT_V1", "active": True,
                },
            )
            if (grant.user_id != family.id or grant.school_key != school or grant.consent_version != "DEMO_CONSENT_V1"):
                raise CommandError("Existing fictional applicant grant differs; manual reconciliation required.")
            if not grant.active:
                raise CommandError("Revoked fictional family grant requires manual reconciliation.")
            assignment, _ = SGOProcessorAssignment.objects.get_or_create( program=program, user=processor, defaults={"active": True}, )
            if not assignment.active:
                raise CommandError("Revoked fictional processor assignment requires manual reconciliation.")
            lines.extend([ f"", f"[{legal_name}]", f"Family login: {family.username} / {family_secret}", f"Processor login: {processor.username} / {processor_secret}",
                f"Partner SGO admin (no automatic processor rights): {partner.username} / {partner_secret}",
                f"Fictional program: {program.id}",
            ])
        path = Path(options["credentials_file"]).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        path.chmod(0o600)
        self.stdout.write(self.style.SUCCESS( "Two fictional partner SGO programs, applicant grants and processor assignments ready. " f"Local-only credentials file: {path}" ))
