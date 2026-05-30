from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from sandbox_demo.catalog import SANDBOX_PERSONAS
from sandbox_demo.models import SandboxInvite


class Command(BaseCommand):
    help = "Create a CROWN sandbox invite link."

    def add_arguments(self, parser):
        parser.add_argument("--organization", required=True)
        parser.add_argument("--track", default="school")
        parser.add_argument("--roles", default=",".join(SANDBOX_PERSONAS.keys()))
        parser.add_argument("--seed-packs", default="heritage-core")
        parser.add_argument("--days", type=int, default=14)
        parser.add_argument("--base-url", required=True)

    def handle(self, *args, **opts):
        roles = [item.strip() for item in opts["roles"].split(",") if item.strip()]
        seed_packs = [item.strip() for item in opts["seed_packs"].split(",") if item.strip()]
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
