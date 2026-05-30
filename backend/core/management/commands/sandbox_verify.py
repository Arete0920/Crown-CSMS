from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


TRACK_PACKS = {
    "school": "heritage_core",
    "daycare": "emmanuel_early_learning",
    "camp": "cedar_ridge_summer_camp",
}


class Command(BaseCommand):
    help = "Verify CROWN sandbox seed-pack contracts and release-gate prerequisites."

    def add_arguments(self, parser):
        parser.add_argument("--track", choices=sorted(TRACK_PACKS.keys()), required=True)
        parser.add_argument("--pack", required=False, help="Seed pack name. Defaults to the canonical pack for the track.")
        parser.add_argument("--strict", action="store_true", help="Fail on implementation placeholders that are still scaffold-only.")

    def handle(self, *args, **opts):
        track = opts["track"]
        pack = opts.get("pack") or TRACK_PACKS[track]
        strict = bool(opts.get("strict"))
        manifest_path = self._manifest_path(track, pack)

        if not manifest_path.exists():
            raise CommandError(f"Sandbox manifest not found: {manifest_path}")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        findings = self._verify_manifest(manifest, track, pack)

        for finding in findings:
            level = finding["level"]
            message = finding["message"]
            if level == "PASS":
                self.stdout.write(self.style.SUCCESS(f"PASS {message}"))
            elif level == "WARN":
                self.stdout.write(self.style.WARNING(f"WARN {message}"))
            else:
                self.stdout.write(self.style.ERROR(f"FAIL {message}"))

        failures = [finding for finding in findings if finding["level"] == "FAIL"]
        warnings = [finding for finding in findings if finding["level"] == "WARN"]

        if failures:
            raise CommandError(f"Sandbox verification failed: {len(failures)} failure(s)")

        if strict and warnings:
            raise CommandError(f"Sandbox strict verification failed: {len(warnings)} warning(s)")

        self.stdout.write(self.style.SUCCESS(
            f"Sandbox verification complete: track={track} pack={pack} warnings={len(warnings)}"
        ))

    def _manifest_path(self, track: str, pack: str) -> Path:
        repo_root = Path(settings.BASE_DIR).parent
        return repo_root / "sandbox" / "seed_packs" / track / pack / "manifest.json"

    def _verify_manifest(self, manifest: dict, track: str, pack: str) -> list[dict[str, str]]:
        findings: list[dict[str, str]] = []

        def add(level: str, message: str) -> None:
            findings.append({"level": level, "message": message})

        add("PASS", "manifest file loaded")

        if manifest.get("track") == track:
            add("PASS", "track matches requested verification target")
        else:
            add("FAIL", f"track mismatch: expected {track}, found {manifest.get('track')}")

        if manifest.get("pack") == pack:
            add("PASS", "pack matches requested verification target")
        else:
            add("FAIL", f"pack mismatch: expected {pack}, found {manifest.get('pack')}")

        if manifest.get("demo_data_only") is True:
            add("PASS", "demo_data_only is explicitly true")
        else:
            add("FAIL", "demo_data_only must be true")

        if manifest.get("reset_required") is True:
            add("PASS", "reset_required is explicitly true")
        else:
            add("FAIL", "reset_required must be true")

        personas = manifest.get("personas") or []
        if personas:
            add("PASS", f"{len(personas)} persona(s) declared")
        else:
            add("FAIL", "no personas declared")

        invalid_personas = [persona for persona in personas if not all(k in persona for k in ["key", "label", "email", "route"])]
        if invalid_personas:
            add("FAIL", f"{len(invalid_personas)} persona(s) missing key, label, email, or route")
        else:
            add("PASS", "all personas include key, label, email, and route")

        story = manifest.get("guided_story") or []
        if len(story) >= 3:
            add("PASS", f"guided story contains {len(story)} step(s)")
        else:
            add("FAIL", "guided story must include at least three steps")

        metrics = manifest.get("expected_metrics") or {}
        if metrics:
            add("PASS", f"expected metrics declared: {', '.join(sorted(metrics.keys()))}")
        else:
            add("FAIL", "expected_metrics must be non-empty")

        add("WARN", "model-level data writes are scaffolded but not implemented")
        add("WARN", "dashboard metric assertions require seeded database implementation")
        add("WARN", "role permission proof requires authenticated test run")
        add("WARN", "cross-tenant proof requires runtime test run")

        return findings
