"""Download the pinned CROWN source and launch the local Heritage demo."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

SOURCE_SHA = "5e49157f440c549b9394f3cea7259c09d409b6bd"
SOURCE_URL = f"https://github.com/Arete0920/Crown-CSMS/archive/{SOURCE_SHA}.zip"
ROOT = Path(__file__).resolve().parent
DESTINATION = ROOT / f"Heritage-{SOURCE_SHA[:12]}"


def install_source(destination=DESTINATION, source_url=SOURCE_URL):
    marker = destination / "HERITAGE_SOURCE_COMMIT.txt"
    if destination.exists():
        if not marker.is_file() or marker.read_text().strip() != SOURCE_SHA:
            raise RuntimeError("Existing Heritage folder has a different source identity. Move the starter to a new folder.")
        return destination
    with tempfile.TemporaryDirectory(prefix="heritage-source-", dir=ROOT) as work:
        archive = Path(work) / "source.zip"
        print("Downloading the tested Heritage source revision...", flush=True)
        request = urllib.request.Request(source_url, headers={"User-Agent": "CROWN-Heritage-Local-Starter"})
        with urllib.request.urlopen(request, timeout=120) as response, archive.open("wb") as output:
            shutil.copyfileobj(response, output)
        unpack = Path(work) / "source"
        unpack.mkdir()
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                target = (unpack / member.filename).resolve()
                if not target.is_relative_to(unpack.resolve()) or ((member.external_attr >> 16) & 0o170000) == 0o120000:
                    raise RuntimeError("The source archive contains an unsafe path.")
            bundle.extractall(unpack)
        roots = list(unpack.iterdir())
        if len(roots) != 1 or not (roots[0] / "scripts/demo/start_heritage_local.py").is_file():
            raise RuntimeError("The download is not the expected CROWN source archive.")
        (roots[0] / "HERITAGE_SOURCE_COMMIT.txt").write_text(SOURCE_SHA + "\n")
        roots[0].rename(destination)
    return destination


def main():
    if sys.version_info < (3, 11):
        raise RuntimeError("Install Python 3.11 or newer. Python 3.12 was used for this rehearsal.")
    if not shutil.which("node"):
        raise RuntimeError("Install Node.js 22.12+ with npm, then double-click the starter again.")
    source = install_source()
    return subprocess.call([sys.executable, str(source / "scripts/demo/start_heritage_local.py")], cwd=source)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
        print(f"Heritage could not start: {exc}", file=sys.stderr)
        sys.exit(1)
