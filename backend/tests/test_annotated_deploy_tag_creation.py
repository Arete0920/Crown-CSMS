"""Exercise annotated candidate creation against a real local bare remote."""
from pathlib import Path
import subprocess

import pytest

from scripts.release.create_annotated_deploy_tag import TagCreationBlocked, create_tag, validate_checks


def run(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def git_repo(tmp_path):
    origin = tmp_path / "origin.git"
    repo = tmp_path / "work"
    subprocess.run(["git", "init", "--bare", "--initial-branch=main", str(origin)], check=True, capture_output=True)
    subprocess.run(["git", "clone", str(origin), str(repo)], check=True, capture_output=True)
    run(repo, "config", "user.name", "Test release workflow")
    run(repo, "config", "user.email", "release@example.test")
    (repo / "source.txt").write_text("verified source")
    run(repo, "add", "source.txt")
    run(repo, "commit", "-m", "Initial source")
    run(repo, "push", "origin", "main")
    sha = run(repo, "rev-parse", "HEAD")
    checks = {"check_runs": [{"id": n, "name": name, "head_sha": sha,
                             "status": "completed", "conclusion": "success"}
                            for n, name in enumerate(["Release authority gates", "pytest-internal", "source-contracts"], 1)]}
    return repo, origin, sha, "prod-deploy-20261012-" + sha[:7], checks


def test_published_tag_is_annotated_and_remote_identity_matches(git_repo):
    repo, origin, sha, tag, checks = git_repo
    result = create_tag(repo, sha, tag, checks, publish=True)
    assert result["remote_verified"] is True and result["tag_created"] is True
    assert run(origin, "cat-file", "-t", "refs/tags/" + tag) == "tag"
    assert run(origin, "rev-parse", tag + "^{commit}") == sha
    before = run(origin, "rev-parse", "refs/tags/" + tag)
    with pytest.raises(TagCreationBlocked, match="already exists"):
        create_tag(repo, sha, tag, checks, publish=True)
    assert run(origin, "rev-parse", "refs/tags/" + tag) == before


def test_preview_does_not_create_a_ref(git_repo):
    repo, origin, sha, tag, checks = git_repo
    assert create_tag(repo, sha, tag, checks)["tag_created"] is False
    assert run(origin, "tag", "--list") == ""


@pytest.mark.parametrize("change", ["pending", "failed", "wrong_sha", "missing"])
def test_unverified_checks_cannot_publish(git_repo, change):
    repo, origin, sha, tag, checks = git_repo
    if change == "pending":
        checks["check_runs"][0].update(status="in_progress", conclusion=None)
    elif change == "failed":
        checks["check_runs"][0]["conclusion"] = "failure"
    elif change == "wrong_sha":
        checks["check_runs"][0]["head_sha"] = "0" * 40
    else:
        checks["check_runs"].pop()
    with pytest.raises(TagCreationBlocked):
        create_tag(repo, sha, tag, checks, publish=True)
    assert run(origin, "tag", "--list") == ""


def test_non_main_source_is_rejected(git_repo):
    repo, origin, sha, tag, checks = git_repo
    (repo / "source.txt").write_text("unpublished change")
    run(repo, "add", "source.txt")
    run(repo, "commit", "-m", "Unverified local source")
    new_sha = run(repo, "rev-parse", "HEAD")
    with pytest.raises(TagCreationBlocked, match="remote main"):
        create_tag(repo, new_sha, "prod-deploy-20261012-" + new_sha[:7], checks, publish=True)
    assert run(origin, "tag", "--list") == ""


def test_only_current_tag_workflow_may_be_excluded_from_terminal_checks(git_repo):
    repo, origin, sha, tag, checks = git_repo
    checks["check_runs"].append({"id": 10, "name": "create-annotated-tag", "head_sha": sha,
                                "status": "in_progress", "conclusion": None,
                                "details_url": "https://github.com/Arete0920/Crown-CSMS/actions/runs/123/job/456"})
    assert validate_checks(checks, sha, "123") == 3
    with pytest.raises(TagCreationBlocked):
        validate_checks(checks, sha, "999")


@pytest.mark.parametrize("bad_tag", ["prod-deploy-20261312-aaaaaaa", "prod-deploy-20261012-aaaaaaa", "prod-deploy-20261012-a;echo bad"])
def test_invalid_tag_inputs_are_rejected(git_repo, bad_tag):
    repo, origin, sha, tag, checks = git_repo
    with pytest.raises(TagCreationBlocked):
        create_tag(repo, sha, bad_tag, checks, publish=True)
    assert run(origin, "tag", "--list") == ""
