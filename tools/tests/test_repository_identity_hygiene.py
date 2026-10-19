"""Negative proofs for complete tracked-file reference and media review coverage."""
import base64
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("identity_policy", ROOT / "scripts/ci/repository_identity_hygiene.py")
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)
TOKEN = policy.REFERENCE_WORDS[0]


class ReferencePolicyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.git("init", "-q")

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)

    def track(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value.encode("utf-8") if isinstance(value, str) else value)
        self.git("add", "-f", "--", name)
        return path

    def findings(self):
        return policy.scan_references(self.root)[0]

    def test_vocabulary_identifier_boundaries_and_ordinary_language(self):
        for word in policy.REFERENCE_WORDS:
            with self.subTest(word=word):
                self.assertTrue(policy.reference_found(word))
                self.assertTrue(policy.reference_found("before_" + word + "_after"))
                self.assertTrue(policy.reference_found(word.replace(" ", "_")))
                self.assertTrue(policy.reference_found(word.replace(" ", "-")))
        self.assertTrue(policy.reference_found(TOKEN.title() + "Client"))
        short = next(word for word in policy.REFERENCE_WORDS if len(word) == 2)
        self.assertTrue(policy.reference_found("generateWith" + short.title()))
        for value in (TOKEN.title() + "ClientV2", "v2" + TOKEN.title() + "Client",
                      "2" + TOKEN.title() + "Client", "generateWith" + short.upper() + "2",
                      "create" + short.title() + "Response2", TOKEN.title() + "2"):
            self.assertTrue(policy.reference_found(value), value)
        for value in ("said", "available", "chair", "email", "User-Agent", "cursor.execute", "model.objects"):
            self.assertFalse(policy.reference_found(value), value)

    def test_opaque_tokens_do_not_exempt_surrounding_language(self):
        short = next(word for word in policy.REFERENCE_WORDS if len(word) == 2)
        digest = "sha512-" + "A" * 43 + short.title() + "A" * 41 + "=="
        token = "eyJ0eX" + short.title() + "OiJKV1QiLCJhbGc..."
        for value in (digest, token):
            self.assertFalse(policy.reference_found(value))
            self.assertTrue(policy.reference_found(value + " " + TOKEN))

    def test_wrapped_prose_phrases_are_scanned_with_original_line_numbers(self):
        for word in policy.REFERENCE_WORDS:
            if " " in word:
                with self.subTest(word=word):
                    self.track("wrapped.notes", "Neutral introduction.\n" + word.replace(" ", "\n"))
                    self.assertTrue(any(row[1] == 2 and "branding" in row[2] for row in self.findings()))

    def test_hidden_ignored_tracked_and_unusual_extension_are_scanned(self):
        self.track(".gitignore", ".cache/\n")
        self.track(".cache/.hidden.unusual", TOKEN)
        findings, counts = policy.scan_references(self.root)
        self.assertEqual(counts["tracked"], 2)
        self.assertTrue(any(row[0] == ".cache/.hidden.unusual" for row in findings))

    def test_unicode_encodings_are_scanned_without_extension_filter(self):
        for encoding in ("utf-8-sig", "utf-16", "utf-32"):
            self.track("encoded-" + encoding + ".data", TOKEN.encode(encoding))
        self.assertEqual(len(self.findings()), 3)

    def test_tracked_filename_is_checked(self):
        name = "docs/" + TOKEN + "_notes.md"
        self.track(name, "ordinary content")
        self.assertIn((name, 0, "prohibited reference in tracked filename"), self.findings())

    def test_missing_and_unreadable_tracked_files_fail(self):
        path = self.track("missing.txt", "ordinary")
        path.unlink()
        self.assertIn("cannot read tracked file", self.findings()[0][2])
        path.write_text("ordinary")
        with patch.object(Path, "read_bytes", side_effect=PermissionError("denied")):
            self.assertIn("cannot read tracked file", self.findings()[0][2])

    def test_no_repository_and_empty_index_fail_closed(self):
        self.assertIn("no tracked files", self.findings()[0][2])
        with tempfile.TemporaryDirectory() as directory:
            self.assertIn("cannot enumerate", policy.scan_references(Path(directory))[0][0][2])

    def test_exact_exceptions_never_cover_appended_or_rewritten_content(self):
        for (name, number), line in policy.EXACT_REFERENCE_EXCEPTIONS.items():
            with self.subTest(name=name):
                text = "\n" * (number - 1) + line + "\n"
                path = self.track(name, text)
                self.assertFalse(self.findings())
                path.write_text(text + TOKEN + "\n", encoding="utf-8")
                self.assertTrue(self.findings())
                path.write_text(text.rstrip("\n") + " " + TOKEN + "\n", encoding="utf-8")
                self.assertTrue(self.findings())
                path.write_text(text, encoding="utf-8")

    def test_reviewed_binary_cannot_change_or_move(self):
        name = "assets/reviewed.webp"
        data = b"RIFF\x00\xff\x80reviewed-image"
        path = self.track(name, data)
        admitted = {name: hashlib.sha256(data).hexdigest()}
        self.assertTrue(self.findings())
        with patch.object(policy, "REVIEWED_BINARY_SHA256", admitted):
            self.assertFalse(self.findings())
            path.write_bytes(data + b"drift")
            self.assertTrue(self.findings())
            path.write_bytes(data)
            self.git("mv", name, "assets/renamed.webp")
            self.assertTrue(self.findings())

    def test_text_encoded_document_still_requires_media_review(self):
        for name in ("document.pdf", "document.unusual"):
            self.track(name, "%PDF-1.7\nplain encoded document\n")
        self.assertEqual(len(self.findings()), 2)
        self.assertTrue(all("hash admission" in row[2] for row in self.findings()))

    def test_embedded_media_requires_review_and_surrounding_text_is_scanned(self):
        name = "assets/wrapper.svg"
        payload = base64.b64encode(b"\x89PNG\r\n\xff\x00").decode()
        content = '<svg><image href="data:image/png;base64,' + payload + '"/></svg>'
        path = self.track(name, content)
        self.assertTrue(self.findings())
        admitted = {name: hashlib.sha256(content.encode()).hexdigest()}
        with patch.object(policy, "REVIEWED_BINARY_SHA256", admitted):
            self.assertFalse(self.findings())
            path.write_text(content + "\n<!-- " + TOKEN + " -->", encoding="utf-8")
            findings = self.findings()
            self.assertTrue(any("embedded media" in row[2] for row in findings))
            self.assertTrue(any(row[1] == 2 and "branding" in row[2] for row in findings))

    def test_control_vocabulary_exempts_only_its_definitions(self):
        content = (ROOT / policy.GUARD_PATH).read_text(encoding="utf-8")
        path = self.track(policy.GUARD_PATH, content)
        self.assertFalse(self.findings())
        path.write_text(content + "\n# " + TOKEN + "\n", encoding="utf-8")
        self.assertTrue(self.findings())
        definition = next(line for line in content.splitlines() if line.startswith("VERSIONED_MODEL_RE ="))
        for tail in ("; CURRENT_LABEL = " + repr(TOKEN + " powered"), " # " + TOKEN):
            path.write_text(content.replace(definition, definition + tail), encoding="utf-8")
            self.assertTrue(self.findings())

    def test_vector_paths_and_percent_encoded_media_require_review(self):
        payload = "".join("%" + format(byte, "02x") for byte in b"<svg><path d='M0 0'/></svg>")
        for name, content in (("vector.svg", '<svg><path d="M0 0"/></svg>'),
                              ("page.html", '<img src="data:image/svg+xml,' + payload + '">'),
                              ("style.css", 'image: url(data:image/svg+xml,' + payload + ');')):
            path = self.track(name, content)
            self.assertTrue(self.findings())
            with patch.object(policy, "REVIEWED_BINARY_SHA256", {name: hashlib.sha256(content.encode()).hexdigest()}):
                self.assertFalse(self.findings())
                path.write_text(content + "\n" + TOKEN, encoding="utf-8")
                self.assertTrue(any(row[1] == 2 and "branding" in row[2] for row in self.findings()))
                path.write_text(content, encoding="utf-8")
                self.git("mv", name, "renamed-" + name)
                self.assertTrue(self.findings())
            self.git("rm", "-f", "renamed-" + name)

    def test_style_review_reports_line_column_and_markdown_specific_pattern(self):
        self.track("docs/overview.md", "School registration instructions.\n")
        self.track("docs/notes.md",
                   "Current guidance.\n" + "Here is " + "the code\n" +
                   "## " + "Key Takeaways\n")
        self.track("backend/scheduling/tasks.py", "status = 'complete'\n")
        findings, errors = policy.scan_style_signatures(self.root)
        self.assertEqual(errors, [])
        self.assertEqual(
            [(item[0], item[1], item[2], item[3], item[4]) for item in findings],
            [("docs/notes.md", 2, 1, "generic-code-introduction", "medium"),
             ("docs/notes.md", 3, 1, "generic-markdown-heading", "low")],
        )

    def test_style_review_detects_disclosure_without_false_framework_attribution(self):
        disclosure = "As an " + "A" + "I" + " language model"
        self.track("docs/disclosure.md", "Preface\n  " + disclosure + "\n")
        self.track("backend/core/migrations/0001_initial.py",
                   "# Generated by Django 5.2.17 on 2026-10-01\n")
        findings, errors = policy.scan_style_signatures(self.root)
        self.assertEqual(errors, [])
        self.assertEqual(
            [(item[0], item[1], item[2], item[4]) for item in findings],
            [("docs/disclosure.md", 2, 3, "high")],
        )

    def test_style_review_reports_read_failures(self):
        path = self.track("docs/missing.md", "ordinary documentation\n")
        path.unlink()
        findings, errors = policy.scan_style_signatures(self.root)
        self.assertEqual(findings, [])
        self.assertEqual(len(errors), 1)
        self.assertIn("docs/missing.md", errors[0])


    def test_existing_identity_control_and_historical_scope_are_preserved(self):
        content = (ROOT / policy.GUARD_PATH).read_text(encoding="utf-8")
        script = self.track(policy.GUARD_PATH, content)
        retired_identity = next(iter(policy.FORBIDDEN))
        current = self.track("README.md", retired_identity)
        result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn(policy.FORBIDDEN[retired_identity], result.stdout)
        current.write_text("Current repository overview", encoding="utf-8")
        self.track("docs/release/history.md", retired_identity)
        self.track("AGENTS.md", "Current execution instructions")
        result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
