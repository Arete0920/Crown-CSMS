from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_COMMAND_ROOT = REPOSITORY_ROOT / "backend" / "sandbox_demo" / "management" / "commands"
SHADOW_COMMAND_ROOT = REPOSITORY_ROOT / "backend" / "sandbox_demo" / "sandbox_demo" / "management" / "commands"
CONTROLLED_COMMANDS = {
    "sandbox_create_invite.py",
    "sandbox_proof_gate.py",
    "sandbox_seed_flagship.py",
}


def test_sandbox_commands_have_one_canonical_source_path() -> None:
    missing = sorted(name for name in CONTROLLED_COMMANDS if not (CANONICAL_COMMAND_ROOT / name).is_file())
    shadowed = sorted(name for name in CONTROLLED_COMMANDS if (SHADOW_COMMAND_ROOT / name).exists())

    assert missing == [], f"Missing canonical sandbox commands: {missing}"
    assert shadowed == [], f"Shadow sandbox command copies are forbidden: {shadowed}"
