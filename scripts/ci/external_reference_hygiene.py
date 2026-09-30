#!/usr/bin/env python3
"""Fail when prohibited external-reference fingerprints appear in committed first-party content."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EXCLUDED_PARTS = {
    ".git", ".venv", "venv", "node_modules", "dist", "build", "coverage",
    "__pycache__", ".pytest_cache", "audit-artifacts", "migrations",
}

EXCLUDED_FILENAMES = {
    "package-lock.json",
    "npm-shrinkwrap.json",
}

TEXT_EXTENSIONS = {
    ".md", ".txt", ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".yml", ".yaml",
    ".csv", ".ps1", ".sh", ".html", ".css", ".toml", ".ini", ".cfg",
}

# SHA-256 fingerprints of prohibited external product, provider, and model/tool terminology.
# The underlying terms are intentionally not stored in repository source.
PROHIBITED_FINGERPRINTS = {
    "7d3194f79e645c42e4396dda38be04766810ec6a00d00aced3ffc2a0a1f1a9ef",
    "60965168ce762e949600281ba6d01fee136e5b6e8257b1f216f9025ed324474c",
    "053ea4804ef1bb33d4a3d6fb024a614b6d257cebc2bc7cd915da9c9522f37ffc",
    "c857d09db23e6822e3600bc06ad8d58f92ed62bc8efd81c753f77048662cb97d",
    "5d72436256ada53828b51895a94bb8489e9f1ac4fe937a8024ef1594e7045ff6",
    "3ea125d0bff386e6754b3782b300016fc79a9cf8f8669c0a5c3db64467ddb681",
    "c70eca6b0f88f44d81a41311647e50fda1ac454ec04ffd442b0eb4743a993131",
    "920510199770f4d65cb8aaa2cd12bdb2b8c37f5b3907c50a734a0e3409da2823",
    "fc5a1047f5919892fcdf8aa79ea5d6bb6531b5c176939ef0110906cb225941c1",
    "add92b9cde2bdbf3daaf65a0db79e9b1a7fa428b71b4d6ce38c742eb6dca0c1c",
    "45d780f82c9247fc1142f8b60c12b6c6cd3d9f23dd836cfa6e84c498d2f83292",
    "9058f79c893a1d7e20b13009b95b9cf3211478a91a47e2ad65bdfedad6fc98f4",
    "487b91042c7cf27a19e23ea8699f5f354b1a0c3af9e418138dc6150d830f970d",
    "803b3eb2b6af027151950019f2d5ede506a6636a9eafd262b27c23e3f834056f",
    "7dd9d5f010e8a9a74e0d40763f82735105cdac542ed9b1cf493498d650af161e",
    "dcaa8e5ecb8d70ad4ededfab010e9ac8894d61070d561e97e84cd68d6f1ff0c9",
    "746d1113c358e1c93874b12761fba6298d99d01aec38a47f13df47b94d129b37",
    "764c17e66b9976d235358361e4ef4165b047178180812a6804a3247e11bf8d51",
    "45779bc98fc51729fc67b37e4cc28396fd9285ac756beceb22aa790dd3d3267d",
    "32e83e92d45d71f69dcf9d214688f0375542108631b45d344e5df2eb91c11566",
    "f1cfd278701d1a5a1020ff7f3cb047c969510ea022b1ee25d1874a5a685c07b3",
    "fe40a3861f8cfb6316fe5b44dfb9971115f98f016b1408392230305e4c9cf381",
    "e8b7be4471f8d3b0ef91f4f3b6f33f08d31052d56ff9bf9b7c70d35b1baa92cf",
    "e993761c2b9c919be2d142e719aa475f59b41dce9a016bb8fddc3428c0191975",
    "f9d473f53f88d30d1a40bbcdd4afd5c73cd3f1db78e64aa0ebde627717f744f1",
    "0f7be90decd9a97f2558d0a7706f908fbf4a567d10f57e6a8e9f233d1aa403de",
    "c9b5ab6ae4041ceb0ee5e0dcdc5e810e34ff1a1839754a7b2c49259efe15cca6",
    "d1d287b865b8c23f5536574cfac8e74a5c206253b54df5245ffc9c54e54b6f45",
    "b02f82c06ea89a02be8a1a38c1dc962b50649c38bd51fbd5f042167d0290318d",
    "adb968959b7cc311473530e3988e7ae55137971f8b13d50ee5984e5f011539ba",
    "08184088fdfeb897bfca1ba8ffa75a1a5317e8649a5127a88b86e0b674af87ed",
    "ff6028ab0c85d104e106546a8a6fc9da364b5d555c82893d02eec2307719e36b",
    "03f114723904795a6131420e7563e92a1e3cbc7987a4ab2b24185dc3efb157b3",
    "458a0ed08c0c263949deb4f80529c58e257fcd550692944706d88accf9e71aa1",
    "442075b0d966ceff7a6f2740f4bdb365dc94dc9a64d49a049ccc04b3fc377c4c",
    "26bc222d9daba9bedb029aba3cd2339e74b866002bf0bb198ceed189e2a8cdea",
    "ae29cb43c1270325b5c51357d62444409c7218e8c199f2a3d5fd3e21a462a146",
    "2bebf6a02d468c561181415b40613695e47befebaf153bdb15aba61ec05d0f31",
    "168e03b77aae9a3e3d1bee49e2cd10f7f7bd858872f963ad0bc06fbcd2a04627",
    "aab1e15cf87f81381fa5bc7761b4c4d7a654111c6ac81c17b161f9fb19ea7689",
    "665a50d830952d1cede097794f1035e408836e366d8a5b8c244816f9d44e4d14",
    "7b466c9ac3be81715be14f3b89b172b43c7ae98630b8f6e1dba5e5a31f301d72",
    "66530f1020a52465a68263b16ba7e9382c86b191feab3ac241016e71b1091ef7",
    "6984ae5b618c0f1ccf56b548aea8afc581dc4d364a69db7bd163187c72526b77",
    "41b48b722295a63cd22c7c1dcd687e06a755e5716343d6b9775f8a26cd4b137b",
    "7b6474c8b495de3f5569068f8d0e910a7b02f36de27fc87ec8e291f9b8258e2b",
    "0da5cfc978e594f5a1fe7b6e15dac1c175a6779daea50c7e85650524cd03d395",
    "2f99472d6173eab94c5a1c42c4d44320a933ecaea53ba08a5c7e73f8e9c834c7",
    "be61f19bc5c91a43f6f62bc4bcb6828aaf22215587ed46aa1377260a3637e8ec",
    "470cff317e59dac29d7ae60614a2dcdf50ec9be26343e59b30298f8f1635c9db",
    "25be854040b6cebc7a9a4eaf9110b93462b584cb82936cc6783797d94de6f575",
}

WORD_RE = re.compile(r"[A-Za-z0-9]+")
MAX_WORDS = 3
CASE_SENSITIVE_FINGERPRINTS = {
    "c73e2d5f781dd728da917445472992925aec69318557b5c9734a01fff7a4434d",
}



def digest(value: str) -> str:
    return hashlib.sha256(value.lower().encode("utf-8")).hexdigest()


def first_party_text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in rel.parts):
            continue
        if path.name in EXCLUDED_FILENAMES:
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        yield rel, path


def line_contains_prohibited_reference(line: str) -> bool:
    words = WORD_RE.findall(line)
    for word in words:
        if hashlib.sha256(word.encode("utf-8")).hexdigest() in CASE_SENSITIVE_FINGERPRINTS:
            return True
    for width in range(1, MAX_WORDS + 1):
        for start in range(0, len(words) - width + 1):
            candidate = " ".join(words[start:start + width])
            if digest(candidate) in PROHIBITED_FINGERPRINTS:
                return True
    return False


def main() -> int:
    findings: list[tuple[str, int]] = []
    self_rel = Path(__file__).resolve().relative_to(ROOT)

    for rel, path in first_party_text_files():
        if rel == self_rel:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if line_contains_prohibited_reference(line):
                findings.append((rel.as_posix(), lineno))

    if findings:
        print("Prohibited external references found in first-party repository content:")
        for rel, lineno in findings:
            print(f"- {rel}:{lineno}")
        return 1

    print("External-reference hygiene: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
