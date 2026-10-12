#!/usr/bin/env python3
"""Create one annotated candidate tag from terminally verified main."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlparse


class TagCreationBlocked(ValueError):
    pass


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, check=check, capture_output=True, text=True)


def validate_source(repo: Path, sha: str, tag: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise TagCreationBlocked("A full lowercase source SHA is required.")
    match = re.fullmatch(r"prod-deploy-([0-9]{8})-([0-9a-f]{7})", tag)
    if not match or match.group(2) != sha[:7]:
        raise TagCreationBlocked("Tag must use prod-deploy-YYYYMMDD and the selected short SHA.")
    try:
        datetime.strptime(match.group(1), "%Y%m%d")
    except ValueError as exc:
        raise TagCreationBlocked("Tag date is invalid.") from exc
    if git(repo, "rev-parse", "HEAD").stdout.strip() != sha:
        raise TagCreationBlocked("Checked-out source does not match the selected SHA.")
    git(repo, "fetch", "--no-tags", "origin", "main")
    if git(repo, "rev-parse", "FETCH_HEAD").stdout.strip() != sha:
        raise TagCreationBlocked("Selected source is not the current remote main.")


def validate_checks(data, sha: str, ignore_run_id: str | None = None) -> int:
    pages = data if isinstance(data, list) else [data]
    latest = {}
    for page in pages:
        for row in page.get("check_runs", []):
            if row.get("head_sha") != sha:
                raise TagCreationBlocked("Check evidence is not for the selected SHA.")
            url = urlparse(row.get("details_url") or "")
            segments = url.path.split("/")
            if ignore_run_id and url.hostname == "github.com" and ["actions", "runs", str(ignore_run_id)] == segments[3:6]:
                # This workflow's own job is necessarily still running.
                continue
            key = row.get("name", "").casefold()
            if not key:
                raise TagCreationBlocked("Check evidence has no name.")
            if key not in latest or int(row["id"]) > int(latest[key]["id"]):
                latest[key] = row
    if not latest:
        raise TagCreationBlocked("Terminal source validation evidence is required.")
    for name, row in latest.items():
        if row.get("status") != "completed" or row.get("conclusion") not in {"success", "neutral", "skipped"}:
            raise TagCreationBlocked("Source checks have not passed: " + name)
    groups = [
        {"release authority gates", "current release authority"},
        {"pytest-internal", "backend-gate", "test"},
        {"tenant-tests", "source-contracts"},
    ]
    successful = {name for name, row in latest.items() if row.get("conclusion") == "success"}
    if any(not successful.intersection(group) for group in groups):
        raise TagCreationBlocked("Required release, backend and scope-validation evidence is missing.")
    return len(latest)


def create_tag(repo: Path, sha: str, tag: str, data, *, publish: bool = False,
               ignore_run_id: str | None = None) -> dict:
    validate_source(repo, sha, tag)
    checked = validate_checks(data, sha, ignore_run_id)
    remote = git(repo, "ls-remote", "--tags", "origin", "refs/tags/" + tag).stdout.strip()
    local = git(repo, "show-ref", "--verify", "--quiet", "refs/tags/" + tag, check=False)
    if remote or local.returncode == 0:
        raise TagCreationBlocked("Tag already exists; it must not be moved or recreated.")
    result = {"source_sha": sha, "tag": tag, "validated_checks": checked, "tag_created": False}
    if not publish:
        return result
    # Recheck main immediately before the first ref mutation.
    validate_source(repo, sha, tag)
    git(repo, "tag", "-a", tag, sha, "-m", "CROWN deployment candidate. Source: " + sha + ". No production certification is claimed.")
    if git(repo, "cat-file", "-t", "refs/tags/" + tag).stdout.strip() != "tag":
        raise TagCreationBlocked("Created ref is not an annotated tag.")
    object_sha = git(repo, "rev-parse", "refs/tags/" + tag).stdout.strip()
    git(repo, "push", "origin", "refs/tags/" + tag)
    refs = {}
    for line in git(repo, "ls-remote", "--tags", "origin", "refs/tags/" + tag, "refs/tags/" + tag + "^{}").stdout.splitlines():
        value, ref = line.split()
        refs[ref] = value
    if refs.get("refs/tags/" + tag) != object_sha or refs.get("refs/tags/" + tag + "^{}") != sha:
        raise TagCreationBlocked("Remote annotated tag identity did not verify.")
    result.update(tag_created=True, tag_object_sha=object_sha, remote_verified=True)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--checks-json", type=Path)
    parser.add_argument("--ignore-run-id")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--source-only", action="store_true")
    mode.add_argument("--publish", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        repo = Path.cwd()
        if args.source_only:
            validate_source(repo, args.expected_sha, args.tag)
            result = {"source_sha": args.expected_sha, "tag": args.tag, "source_validated": True, "tag_created": False}
        else:
            if not args.checks_json:
                parser.error("--checks-json is required before creating a tag")
            result = create_tag(repo, args.expected_sha, args.tag,
                                json.loads(args.checks_json.read_text()), publish=args.publish,
                                ignore_run_id=args.ignore_run_id)
        if args.output:
            args.output.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result))
        return 0
    except (TagCreationBlocked, subprocess.CalledProcessError, OSError, ValueError, KeyError) as exc:
        message = str(exc) if isinstance(exc, TagCreationBlocked) else type(exc).__name__
        print("Annotated candidate tag creation blocked: " + message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
