from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


TRACK_PACKS = {
    "school": "heritage_core",
    "daycare": "emmanuel_early_learning",
    "camp": "cedar_ridge_summer_camp",
}


class Command(BaseCommand):
    help = "Validate and prepare deterministic CROWN sandbox seed packs. Does not import real data."

    def add_arguments(self, parser):
        parser.add_argument("--track", choices=sorted(TRACK_PACKS.keys()), required=True)
        parser.add_argument("--pack", required=False, help="Seed pack name. Defaults to the canonical pack for the track.")
        parser.add_argument("--reset", action="store_true", help="Allow reset semantics for future seed implementation.")
        parser.add_argument("--dry-run", action="store_true", help="Validate the manifest without writing data.")

    def handle(self, *args, **opts):
        track = opts["track"]
        pack = opts.get("pack") or TRACK_PACKS[track]
        manifest_path = self._manifest_path(track, pack)

        if not manifest_path.exists():
            raise CommandError(f"Sandbox manifest not found: {manifest_path}")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self._validate_manifest(manifest, track, pack)

        mode = "dry-run" if opts.get("dry_run") else "prepare"
        reset_state = "reset requested" if opts.get("reset") else "no reset requested"

        self.stdout.write(self.style.SUCCESS(
            f"Sandbox seed manifest validated: track={track} pack={pack} mode={mode} {reset_state}"
        ))
        self.stdout.write(
            "This command currently enforces the seed-pack contract only. "
            "Add model-specific, tenant-scoped writes after sandbox_verify and role-proof gates are in place."
        )

    def _manifest_path(self, track: str, pack: str) -> Path:
        repo_root = Path(settings.BASE_DIR).parent
        return repo_root / "sandbox" / "seed_packs" / track / pack / "manifest.json"

    def _validate_manifest(self, manifest: dict, track: str, pack: str) -> None:
        required_fields = [
            "track",
            "pack",
            "display_name",
            "status",
            "description",
            "default_mode",
            "personas",
            "guided_story",
            "expected_metrics",
            "reset_required",
            "demo_data_only",
        ]
        missing = [field for field in required_fields if field not in manifest]
        if missing:
            raise CommandError(f"Manifest missing required fields: {', '.join(missing)}")

        if manifest["track"] != track:
            raise CommandError(f"Manifest track mismatch: expected {track}, found {manifest['track']}")

        if manifest["pack"] != pack:
            raise CommandError(f"Manifest pack mismatch: expected {pack}, found {manifest['pack']}")

        if manifest["demo_data_only"] is not True:
            raise CommandError("Manifest must explicitly set demo_data_only=true")

        if manifest["reset_required"] is not True:
            raise CommandError("Manifest must explicitly set reset_required=true")

        if not isinstance(manifest["personas"], list) or not manifest["personas"]:
            raise CommandError("Manifest must define at least one sandbox persona")

        if not isinstance(manifest["guided_story"], list) or len(manifest["guided_story"]) < 3:
            raise CommandError("Manifest guided_story must include at least three steps")

        if not isinstance(manifest["expected_metrics"], dict) or not manifest["expected_metrics"]:
            raise CommandError("Manifest expected_metrics must be a non-empty object")
