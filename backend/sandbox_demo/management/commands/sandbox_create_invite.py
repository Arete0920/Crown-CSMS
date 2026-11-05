from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from sandbox_demo.catalog import (
    DEFAULT_SANDBOX_INVITE_ROLES, SANDBOX_PERSONAS, SANDBOX_SCHOOLS, SANDBOX_TRACKS,
)
from sandbox_demo.models import SandboxInvite


class Command(BaseCommand):
    help = "Create a CROWN sandbox invite link."

    def add_arguments(self, parser):
        parser.add_argument("--organization", required=True)
        parser.add_argument("--track", default="school")
        parser.add_argument("--roles", default=",".join(DEFAULT_SANDBOX_INVITE_ROLES))
        parser.add_argument("--seed-packs", default="heritage-core")
        parser.add_argument("--days", type=int, default=14)
        parser.add_argument("--base-url", required=True)

    def handle(self, *args, **opts):
        roles = [item.strip() for item in opts["roles"].split(",") if item.strip()]
        seed_packs = [item.strip() for item in opts["seed_packs"].split(",") if item.strip()]
        if (
            opts["track"] not in SANDBOX_TRACKS
            or not roles
            or len(roles) != len(set(roles))
            or any(role not in SANDBOX_PERSONAS for role in roles)
            or seed_packs != ["heritage-core"]
            or any(pack not in SANDBOX_SCHOOLS for pack in seed_packs)
        ):
            raise CommandError("Invalid sandbox invite scope.")
        invite = SandboxInvite.objects.create(
            organization_label=opts["organization"],
            track=opts["track"],
            allowed_roles=roles,
            allowed_seed_packs=seed_packs,
            default_guidance="guided",
            expires_at=timezone.now() + timedelta(days=opts["days"]),
        )
        url = opts["base_url"].rstrip("/") + f"/sandbox?invite={invite.id}"
        self.stdout.write(self.style.SUCCESS(f"Invite created: {invite.id}"))
        self.stdout.write(url)
