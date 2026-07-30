from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_PACKAGE_ROOT = REPOSITORY_ROOT / "backend" / "sandbox_demo"
SHADOW_PACKAGE_ROOT = CANONICAL_PACKAGE_ROOT / "sandbox_demo"
CANONICAL_REQUIRED_FILES = {
    "__init__.py",
    "admin.py",
    "apps.py",
    "catalog.py",
    "models.py",
    "services.py",
    "urls.py",
    "views.py",
    "migrations/0001_initial.py",
    "management/commands/sandbox_create_invite.py",
    "management/commands/sandbox_proof_gate.py",
    "management/commands/sandbox_seed_flagship.py",
}


def test_sandbox_package_has_one_canonical_source_path() -> None:
    missing = sorted(
        relative_path
        for relative_path in CANONICAL_REQUIRED_FILES
        if not (CANONICAL_PACKAGE_ROOT / relative_path).is_file()
    )
    shadow_files = (
        sorted(
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for path in SHADOW_PACKAGE_ROOT.rglob("*")
            if path.is_file()
        )
        if SHADOW_PACKAGE_ROOT.exists()
        else []
    )

    assert missing == [], f"Missing canonical sandbox package files: {missing}"
    assert not SHADOW_PACKAGE_ROOT.exists(), (
        "Shadow sandbox package is forbidden; remaining files: "
        f"{shadow_files}"
    )
