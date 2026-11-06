"""Dry-run contracts for the guarded, operator-only Entra OIDC repair helper.

The fake ``az`` is always first in PATH. Tests never contact or mutate Azure.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/execution/repair_entra_github_oidc_federation.sh"
ISSUER = "https://token.actions.githubusercontent.com"
AUDIENCE = "api://AzureADTokenExchange"
PREFIX = "repo:Arete0920@318664923/Crown-CSMS@1339719218"


def fic(name: str, subject: str, issuer: str = ISSUER) -> dict:
    return {
        "name": name,
        "id": f"id-{name}",
        "issuer": issuer,
        "subject": subject,
        "audiences": [AUDIENCE],
    }


SAFE_CREDENTIALS = [
    fic("github-crown-csms-main", PREFIX + ":ref:refs/heads/main"),
    fic("crown-csms-production", PREFIX + ":environment:production"),
    fic("github-env-dev", PREFIX + ":environment:dev"),
]
HISTORICAL_PREFIX = "repo:" + "/".join(("tcmegahan", "Crown2026"))
HISTORICAL = [
    fic("github-main-oidc", HISTORICAL_PREFIX + ":ref:refs/heads/main"),
    fic("github-env-prod", HISTORICAL_PREFIX + ":environment:prod"),
]


FAKE_AZ = r'''#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys

args = sys.argv[1:]
state = Path(os.environ["FAKE_AZ_STATE"])
trace = Path(os.environ["FAKE_AZ_TRACE"])
def record(action):
    with trace.open("a", encoding="utf8") as f:
        f.write(action + "\n")
if args[:2] == ["account", "show"]:
    print("{}")
elif args[:3] == ["ad", "app", "show"]:
    print("test-application-object-id")
elif args[:4] == ["ad", "app", "federated-credential", "list"]:
    fixture = Path(os.environ.get("FAKE_AZ_SECOND_STATE", ""))
    counter = Path(os.environ["FAKE_AZ_LIST_COUNTER"])
    n = int(counter.read_text()) if counter.exists() else 0
    counter.write_text(str(n + 1))
    if n > 0 and fixture.exists() and fixture.is_file():
        print(fixture.read_text())
    else:
        print(state.read_text())
elif args[:4] == ["ad", "app", "federated-credential", "create"]:
    record("CREATE")
    ind = args.index("--parameters")
    payload = json.loads(Path(args[ind + 1][1:]).read_text())
    data = json.loads(state.read_text())
    data.append(payload)
    state.write_text(json.dumps(data))
elif args[:4] == ["ad", "app", "federated-credential", "delete"]:
    record("DELETE")
    ind = args.index("--federated-credential-id")
    which = args[ind + 1]
    data = json.loads(state.read_text())
    new = [r for r in data if r.get("id") != which and r.get("name") != which]
    if len(new) == len(data):
        print("not found", file=sys.stderr)
        sys.exit(1)
    state.write_text(json.dumps(new))
else:
    print("unknown fake az command: " + " ".join(args), file=sys.stderr)
    sys.exit(7)
'''


@unittest.skipUnless(shutil.which("bash") and shutil.which("jq"), "requires bash and jq")
class HistoricalRepositoryOIDCGuardTests(unittest.TestCase):
    def run_helper(self, credentials: list[dict], *, apply: bool = False,
                   second_credentials: list[dict] | None = None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            fake = bin_dir / "az"
            fake.write_text(FAKE_AZ, encoding="utf8")
            fake.chmod(0o755)
            state = root / "state.json"
            state.write_text(json.dumps(credentials), encoding="utf8")
            trace = root / "trace.log"
            counter = root / "list-count.txt"
            second = root / "second.json"
            if second_credentials is not None:
                second.write_text(json.dumps(second_credentials), encoding="utf8")
            env = dict(os.environ,
                       PATH=str(bin_dir) + os.pathsep + os.environ.get("PATH", ""),
                       AZURE_CLIENT_ID="test-only-guid",
                       FAKE_AZ_STATE=str(state), FAKE_AZ_TRACE=str(trace),
                       FAKE_AZ_LIST_COUNTER=str(counter),
                       FAKE_AZ_SECOND_STATE=str(second))
            cmd = ["bash", str(SCRIPT)] + (["--apply"] if apply else [])
            completed = subprocess.run(cmd, env=env, text=True, capture_output=True,
                                       timeout=15, check=False)
            return (completed, trace.read_text() if trace.exists() else "",
                    json.loads(state.read_text()), int(counter.read_text()) if counter.exists() else 0)

    def test_current_legacy_names_block_audit_without_azure_writes(self):
        result, writes, unchanged, reads = self.run_helper(
            SAFE_CREDENTIALS[1:] + HISTORICAL,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("BLOCK: historical cross-repository OIDC trusts", result.stderr)
        self.assertIn("github-main-oidc", result.stderr)
        self.assertIn("github-env-prod", result.stderr)
        self.assertEqual(writes, "")
        self.assertEqual(unchanged, SAFE_CREDENTIALS[1:] + HISTORICAL)
        self.assertEqual(reads, 1)

    def test_apply_does_not_create_main_or_delete_anything_when_historic_trust_exists(self):
        result, writes, unchanged, reads = self.run_helper(
            SAFE_CREDENTIALS[1:] + HISTORICAL, apply=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No --apply changes made", result.stderr)
        self.assertEqual(writes, "")
        self.assertEqual(unchanged, SAFE_CREDENTIALS[1:] + HISTORICAL)
        self.assertEqual(reads, 1)

    def test_historic_subject_is_detected_even_if_credential_renamed(self):
        renamed = fic("renamed-unexpectedly", HISTORICAL[0]["subject"])
        result, writes, _unchanged, _reads = self.run_helper(SAFE_CREDENTIALS + [renamed])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("renamed-unexpectedly", result.stderr)
        self.assertEqual(writes, "")

    def test_normal_current_immutable_subjects_remain_read_only(self):
        result, writes, same, reads = self.run_helper(SAFE_CREDENTIALS)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("RESULT: all required immutable federated credentials are present", result.stdout)
        self.assertEqual(writes, "")
        self.assertEqual(same, SAFE_CREDENTIALS)
        self.assertEqual(reads, 1)

    def test_second_read_detects_historic_trust_before_apply_prune(self):
        result, writes, _same, reads = self.run_helper(
            SAFE_CREDENTIALS, apply=True,
            second_credentials=SAFE_CREDENTIALS + HISTORICAL,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("BLOCK: historical cross-repository OIDC trusts", result.stderr)
        self.assertEqual(writes, "")
        self.assertEqual(reads, 2)

    def test_existing_clean_apply_prunes_only_same_repo_superseded_subject(self):
        old = fic("crown-old-current-repo", "repo:Arete0920/Crown-CSMS:environment:dev")
        result, writes, after, reads = self.run_helper(SAFE_CREDENTIALS + [old], apply=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(writes.strip(), "DELETE")
        self.assertEqual(after, SAFE_CREDENTIALS)
        self.assertEqual(reads, 3)
        self.assertIn("RESULT: Entra federation cleanup complete", result.stdout)

    def test_wrong_issuer_historic_subject_cannot_trigger_the_guard(self):
        forged = fic("not-github", HISTORICAL[0]["subject"], issuer="https://example.invalid")
        result, writes, _same, _reads = self.run_helper(SAFE_CREDENTIALS + [forged])
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(writes, "")


if __name__ == "__main__":
    unittest.main()
