"""The Solomon governance guard must accept only the current CROWN repository."""

from pathlib import Path

import pytest

from solomon_governance_c1 import env_guard


@pytest.mark.parametrize(
    ("remote_url", "accepted"),
    [
        ("https://github.com/Arete0920/Crown-CSMS.git", True),
        ("https://github.com/Arete0920/Crown-CSMS", True),
        ("git@github.com:Arete0920/Crown-CSMS.git", True),
        ("ssh://git@github.com/Arete0920/Crown-CSMS.git", True),
        ("git://github.com/Arete0920/Crown-CSMS.git", True),
        ("https://github.com/" + "tcmegahan" + "/" + "Crown2026.git", False),
        ("https://github.com/Arete0920/Crown-CSMS-test.git", False),
        ("https://github.com/other/Crown-CSMS.git", False),
        ("https://example.com/Arete0920/Crown-CSMS.git", False),
        ("https://github.com/Arete0920/Crown-CSMS.git?ref=main", False),
        ("", False),
    ],
)
def test_origin_acceptance_is_exact(remote_url: str, accepted: bool) -> None:
    assert env_guard.is_authoritative_remote(remote_url) is accepted


@pytest.mark.parametrize("valid", [True, False])
def test_repo_root_enforces_current_origin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid: bool
) -> None:
    repository = tmp_path / "Crown-CSMS"
    repository.mkdir()
    (repository / ".git").write_text("gitdir: /fake/worktree\\n", encoding="utf-8")
    (repository / "README.md").write_text("# CROWN\\n", encoding="utf-8")
    nested = repository / "solomon_governance_c1"
    nested.mkdir()
    monkeypatch.chdir(nested)

    remote = (
        "git@github.com:Arete0920/Crown-CSMS.git"
        if valid
        else "git@github.com:" + "tcmegahan" + "/" + "Crown2026.git"
    )
    monkeypatch.setattr(
        env_guard,
        "run_cmd",
        lambda argv, cwd=None: (0, remote, ""),
    )

    assert env_guard.find_repo_root() == (repository if valid else None)
