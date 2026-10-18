#!/usr/bin/env python3
"""Guard repository identity and reference language across every tracked file."""

from __future__ import annotations

import ast
import codecs
import hashlib
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]

EXCLUDED_PARTS = {
    ".git", ".venv", "venv", "node_modules", "dist", "build", "coverage",
    "__pycache__", ".pytest_cache", "audit-artifacts",
}

HISTORICAL_PREFIXES = (
    "archive/",
    "docs/archive/",
    "docs/release/",
    "docs/certification/",
    "docs/demo-proof/",
    "docs/instruction-ledger/",
    "solomon_governance_c1/governance/c1/runtime/audit_pack/",
)

HISTORICAL_EXACT = {
    "docs/PROOF_LOG_2026-02-24.md",
    "docs/PROOF_DEPLOY_INTEGRITY_2026-02-21.md",
}

TEXT_EXTENSIONS = {
    ".md", ".txt", ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".yml", ".yaml",
    ".csv", ".ps1", ".sh", ".html", ".css", ".toml", ".ini", ".cfg", ".cmd",
}

FORBIDDEN = {
    "tcmegahan/Crown2026": "obsolete predecessor repository URL",
    "Arete-Advisory-Group/Crown-CSMS": "obsolete repository owner path",
    "Crown2026!": "retired hard-coded demo password",
    "Little Lambs Daycare": "retired daycare display name",
}

# Readable control vocabulary is a technical exception under PUBLIC_LANGUAGE_POLICY.
# Only string literals in the named definitions are exempt in this file; comments,
# other expressions and filenames are scanned. Tests obtain examples from this vocabulary.
REFERENCE_WORDS = (
    "openai", "open ai", "chatgpt", "chat gpt", "anthropic", "claude", "copilot",
    "co pilot", "codex", "gemini", "bard", "deepseek", "deep seek", "grok", "perplexity",
    "llama", "mistral", "huggingface", "hugging face", "ollama", "langchain",
    "lang chain", "langgraph", "lang graph", "llamaindex", "llama index", "midjourney", "dall e", "stable diffusion",
    "vertex ai", "amazon bedrock", "aider", "tabnine", "windsurf", "cursor ai",
    "cursor.com", "cursor.sh", ".cursorrules", ".cursor/", "gpt", "ai", "a.i", "a.i.",
    "llm", "llms", "artificial intelligence", "machine learning", "deep learning",
    "neural network", "neural networks", "large language model", "large language models",
    "generative", "chatbot", "chatbots", "agentic", "model memory",
)
EXACT_REFERENCE_EXCEPTIONS = {
    # Applied schema history: preserve the original field creation and removal.
    ("backend/spiritual_life/migrations/0002_alter_prayerrequest_visibility_and_more.py", 278):
        "                ('generated_by_ai', models.BooleanField(default=False)),",
    ("backend/spiritual_life/migrations/0003_remove_devotionalcontent_generation_metadata.py", 13):
        '            name="generated_by_ai",',
    # Authentic prior cleanup record; this is a retired optional funding URL.
    ("docs/governance/REFERENCE_LANGUAGE_SWEEP_2026-10-12.md", 25):
        "| `frontend/dashboards/package-lock.json` | Five funding URLs ending in `/sponsors/ai`; third-party maintainer attribution, not product language. |",
    # Frozen source is hash-bound by the existing C1 golden/evidence registers.
    ("solomon_governance_c1/c1_candidate_sources/CROWN_SOLOMON_CANON.md", 70):
        "- a chatbot oracle",
}

GUARD_PATH = "scripts/ci/repository_identity_hygiene.py"
CONTROL_ASSIGNMENTS = {"REFERENCE_WORDS", "EXACT_REFERENCE_EXCEPTIONS", "VERSIONED_MODEL_RE"}
# Admission requires metadata/text extraction and rendered-content review recorded
# in the current sweep evidence. A changed file or a new path requires new review.
REVIEWED_BINARY_SHA256 = {
    'frontend/dashboards/public/brand/crown-logo-transparent.svg': '17b6bf92e59392b1afe73579ff317666e4b7c2f81da552f40c353605fd3453e0',
    'frontend/dashboards/public/brand/crown-mark-transparent.svg': 'a381001144cc0efbd8733265f82288eb1e416f52f8206e8d5e7467836bc69eba',
    'frontend/dashboards/public/brand/crown/logo/crown-logo-compact-full-color.svg': 'ded33d0cb3e6894eae65df240e9939f373e534327c0437a554e13fbf55f68f02',
    'frontend/dashboards/public/brand/crown/logo/crown-logo-horizontal-full-color.svg': 'bc5a2421283c0310d16458de13aec4309d754a5d4b900e42148a9ac64c392fc9',
    'frontend/dashboards/public/brand/crown/logo/crown-logo-mark-crown-only.svg': 'dab0df65e7473b9e8bf4afe0d37e7deb810b234e22371dd24c1dedf6e8b8dde7',
    'frontend/dashboards/public/brand/crown/logo/crown-logo-mark-shield.svg': 'cf3fa57e739deb25940a9732bb5aacc59d52bdce85672bb4e9bbf45726185453',
    'frontend/dashboards/public/brand/crown/logo/crown-logo-mark-square.svg': 'e3e891d230dedfb31f9403bf290630bc99ffd89429e801645b2132d3b507322f',
    'frontend/dashboards/public/brand/crown/logo/crown-logo-monochrome-royal.svg': '2a60092631f22961801c56bb8c62ca2fa33ded4fb932e631de203b03963b1f68',
    'frontend/dashboards/public/brand/crown/logo/crown-logo-monochrome-white.svg': '62de63413d97ddc8dd071a70ac8a3beb56d615e13c593e2c6b1d9943fff4ba62',
    'frontend/dashboards/public/brand/crown/logo/crown-logo-primary-stacked-full-color.svg': 'd31d3cf69e04821d1101bce68916e75ffeefa8d2031e95bd0a90f664edd29466',
    'frontend/dashboards/public/brand/crown/logo/crown-logo-wordmark-full-color.svg': '7082c7fe2607bdfb765c9d194e06fa4d9ce46893853696d62e875bb53f5d7e92',
    'frontend/dashboards/public/brand/crown/ui/crown-dashboard-hero-logo.svg': '17b6bf92e59392b1afe73579ff317666e4b7c2f81da552f40c353605fd3453e0',
    'frontend/dashboards/public/brand/crown/ui/crown-email-header-logo.svg': '17b6bf92e59392b1afe73579ff317666e4b7c2f81da552f40c353605fd3453e0',
    'frontend/dashboards/public/brand/crown/ui/crown-login-brand.svg': '17b6bf92e59392b1afe73579ff317666e4b7c2f81da552f40c353605fd3453e0',
    'frontend/dashboards/public/brand/crown/ui/crown-print-header-logo.svg': '17b6bf92e59392b1afe73579ff317666e4b7c2f81da552f40c353605fd3453e0',
    'frontend/dashboards/public/brand/crown/ui/crown-report-cover-logo.svg': '17b6bf92e59392b1afe73579ff317666e4b7c2f81da552f40c353605fd3453e0',
    'frontend/dashboards/public/brand/crown/ui/crown-sidebar-collapsed.svg': 'a381001144cc0efbd8733265f82288eb1e416f52f8206e8d5e7467836bc69eba',
    'frontend/dashboards/public/brand/crown/ui/crown-sidebar-expanded.svg': '17b6bf92e59392b1afe73579ff317666e4b7c2f81da552f40c353605fd3453e0',
    'frontend/dashboards/public/brand/crown/ui/crown-topnav-horizontal.svg': '17b6bf92e59392b1afe73579ff317666e4b7c2f81da552f40c353605fd3453e0',
    'frontend/dashboards/public/brand/kairos.svg': 'fa0d80f259dc3dbadb1feafed011df8f52a5b8618fc9f96b014f82e08d373ccf',
    'frontend/dashboards/src/assets/solomon/caution.webp': 'eea6249a2d75a46aa29574961b75dcafa93fc073879e0a2a2f2bea260f66dc09',
    'frontend/dashboards/src/assets/solomon/explain.webp': 'a34afb99b27b13ae94161e27aad96d3deb3cad78b6f7137cdff80d0431b508f6',
    'frontend/dashboards/src/assets/solomon/guide.webp': 'e9e4aac2dcb3082b81356cd4d1f84f90b4bbb294aa825ad2b819fa2160487664',
    'frontend/dashboards/src/assets/solomon/review.webp': '6b0d7a139a1856787502a79c6d09187c068e95d9b3f4b2e183a17e98821bbe66',
    'frontend/dashboards/src/assets/solomon/success.webp': 'f3d1f500b4e4412a6d2ccd6bc82f6ef02c0a62034e55c25ad1dba7e1519481bd',
    'sites/jireh/images/crown/family-billing.webp': '9717c686609fa7ddbe64798f813943ada8ad8f8d37628c07abd4536560666aa1',
    'sites/jireh/images/jireh-sgo/logo.png': '6d0be7312bfb08c4118e163930230ccde50218dd0625bc981400cf99c5617ca7',
    'sites/jireh/resources/jireh-sgo-overview.pdf': '0135d707767459375319a5a8e7366483fb49a794f2a9e6aa92c93f0af168cb45',
}
BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".pdf", ".ico", ".zip",
    ".docx", ".pptx", ".xlsx", ".xls", ".jar", ".gz", ".7z", ".pyc",
}
REFERENCE_RE = re.compile(
    r"(?<![a-z0-9])(?:" + "|".join(
        re.escape(word).replace(r"\ ", r"[\s_-]+") + ("" if word.endswith("/") else r"(?![a-z0-9])")
        for word in REFERENCE_WORDS
    ) + r")", re.IGNORECASE,
)
VERSIONED_MODEL_RE = re.compile(r"(?<![a-z0-9])gpt[ _-]?\d[\w.-]*", re.IGNORECASE)
OPAQUE_DIGEST_RE = re.compile(
    r"\bsha256-[A-Za-z0-9+/]{43}=|\bsha384-[A-Za-z0-9+/]{64}(?![A-Za-z0-9+/])|\bsha512-[A-Za-z0-9+/]{86}=="
)
OPAQUE_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9_-])eyJ[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+|\.{3})(?![A-Za-z0-9_.-])"
)
ENCODED_MEDIA_RE = re.compile(
    r"(data:(?:[a-z][a-z0-9.+-]*/[a-z0-9.+-]+)?(?:;[^,\s\"'<>]*)*,)([^\s\"')]+)", re.IGNORECASE,
)


def reference_found(value: str) -> bool:
    # Canonically sized dependency digests and complete/redacted JSON-header
    # tokens are opaque bytes. Surrounding text remains subject to the same rules.
    value = OPAQUE_TOKEN_RE.sub("", OPAQUE_DIGEST_RE.sub("", value))
    if REFERENCE_RE.search(value) or VERSIONED_MODEL_RE.search(value):
        return True
    # Include versioned source identifiers as well as ordinary CamelCase names.
    def split_identifier(match):
        word = re.sub(r"([A-Z])([A-Z][a-z])", r"\1_\2", match.group())
        word = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", word)
        return re.sub(r"([A-Za-z])([0-9])|([0-9])([A-Za-z])", r"\1\3_\2\4", word)
    value = re.sub(r"[A-Za-z0-9_]+", split_identifier, value)
    return bool(REFERENCE_RE.search(value) or VERSIONED_MODEL_RE.search(value))


def _mask_control_literals(relative: str, text: str) -> str:
    if relative != GUARD_PATH:
        return text
    try:
        nodes = ast.parse(text).body
    except SyntaxError:
        return text
    # AST columns count UTF-8 bytes. Mask only literal spans, retaining comments
    # and other statements even when they share a definition's physical line.
    lines = [bytearray(line) for line in text.encode("utf-8").split(b"\n")]
    for node in nodes:
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id in CONTROL_ASSIGNMENTS):
            continue
        for literal in ast.walk(node.value):
            if isinstance(literal, ast.Constant) and isinstance(literal.value, str):
                for number in range(literal.lineno, literal.end_lineno + 1):
                    start = literal.col_offset if number == literal.lineno else 0
                    end = literal.end_col_offset if number == literal.end_lineno else len(lines[number - 1])
                    lines[number - 1][start:end] = b" " * (end - start)
    return b"\n".join(lines).decode("utf-8")


def _decode_text(data: bytes) -> str | None:
    encoding = "utf-8-sig"
    if data.startswith((codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)):
        encoding = "utf-32"
    elif data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        encoding = "utf-16"
    try:
        text = data.decode(encoding)
    except UnicodeError:
        return None
    return None if any(ord(char) < 32 and char not in "\t\r\n\f" for char in text) else text


def scan_references(root: Path) -> tuple[list[tuple[str, int, str]], dict[str, int]]:
    findings: list[tuple[str, int, str]] = []
    counts = {"tracked": 0, "text": 0, "reviewed_binary": 0, "reviewed_svg": 0, "reviewed_embedded_media": 0, "exact_exceptions": 0}
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=True, capture_output=True,
        )
        paths = [path for path in result.stdout.decode("utf-8").split("\0") if path]
    except (OSError, UnicodeError, subprocess.CalledProcessError) as exc:
        return [("<repository>", 0, f"cannot enumerate Git-tracked files: {exc}")], counts
    if not paths:
        return [("<repository>", 0, "Git index contains no tracked files")], counts
    for relative in paths:
        counts["tracked"] += 1
        if reference_found(relative):
            findings.append((relative, 0, "prohibited reference in tracked filename"))
        path = root / relative
        try:
            if path.is_symlink():
                raise OSError("tracked symlink requires explicit review")
            data = path.read_bytes()
        except OSError as exc:
            findings.append((relative, 0, f"cannot read tracked file: {exc}"))
            continue
        binary = path.suffix.lower() in BINARY_SUFFIXES or data.startswith(
            (b"%PDF-", b"\x89PNG\r\n", b"\xff\xd8\xff", b"RIFF", b"GIF87a", b"GIF89a", b"PK\x03\x04")
        )
        text = None if binary else _decode_text(data)
        if text is None:
            if REVIEWED_BINARY_SHA256.get(relative) != hashlib.sha256(data).hexdigest():
                findings.append((relative, 0, "binary is new, renamed or changed; content review and hash admission required"))
            else:
                counts["reviewed_binary"] += 1
            continue
        counts["text"] += 1
        svg = path.suffix.lower() == ".svg"
        embedded = bool(ENCODED_MEDIA_RE.search(text))
        if svg or embedded:
            if REVIEWED_BINARY_SHA256.get(relative) != hashlib.sha256(data).hexdigest():
                findings.append((relative, 0, "vector/embedded media is new, renamed or changed; rendered/decoded-content review and hash admission required"))
            else:
                counts["reviewed_svg"] += int(svg)
                counts["reviewed_embedded_media"] += int(embedded)
        if embedded:
            # Retain surrounding markup and line positions. The hash gate above
            # covers every encoded payload, including metadata and rendered pixels.
            text = ENCODED_MEDIA_RE.sub(
                lambda match: match.group(1) + re.sub(r"[^\r\n]", " ", match.group(2)), text,
            )
        text = _mask_control_literals(relative, text)
        lines = text.splitlines()
        for number, line in enumerate(lines, 1):
            if not reference_found(line):
                continue
            if EXACT_REFERENCE_EXCEPTIONS.get((relative, number)) == line:
                counts["exact_exceptions"] += 1
                lines[number - 1] = ""
                continue
            findings.append((relative, number, "prohibited authoring/provider or method branding"))
        joined = "\n".join(lines)
        for match in REFERENCE_RE.finditer(joined):
            if "\n" in match.group():
                findings.append((relative, joined.count("\n", 0, match.start()) + 1, "prohibited wrapped reference branding"))
    return findings, counts


def first_party_text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in rel.parts):
            continue
        rel_text = rel.as_posix()
        if rel_text in HISTORICAL_EXACT or rel_text.startswith(HISTORICAL_PREFIXES):
            continue
        if "/migrations/" in f"/{rel_text}/":
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        yield rel, path


def main() -> int:
    findings, counts = scan_references(ROOT)
    self_rel = Path(__file__).resolve().relative_to(ROOT)

    for rel, path in first_party_text_files():
        if rel == self_rel:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for token, reason in FORBIDDEN.items():
                if token in line:
                    findings.append((rel.as_posix(), lineno, reason))

    print("Tracked reference coverage: " + ", ".join(f"{key}={value}" for key, value in counts.items()))
    if findings:
        print("Repository identity/naming hygiene violations:")
        for rel, lineno, reason in findings:
            print(f"- {rel}:{lineno} ({reason})")
        return 1

    print("Repository identity/naming hygiene: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
