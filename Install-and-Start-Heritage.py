"""Download the pinned CROWN source and launch the local Heritage demo."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile

SOURCE_SHA = "a1bf22fc1e520eba149ce943edcd747dbf75c1e5"
# Only a separately source-stamped release candidate may enable guarded five-module mode.
FIVE_MODULE_LAUNCH = False
SOURCE_URL = f"https://api.github.com/repos/Arete0920/Crown-CSMS/zipball/{SOURCE_SHA}"
ROOT = Path(__file__).resolve().parent
DESTINATION = ROOT / f"Heritage-{SOURCE_SHA[:12]}"


def _source_token():
    """Use the owner's existing GitHub login or a short-lived CI token, never a ZIP credential."""
    token = (os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or "").strip()
    if not token:
        try:
            completed = subprocess.run(
                ["gh", "auth", "token"], check=True, capture_output=True,
                text=True, timeout=15,
            )
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            raise RuntimeError(
                "Private Heritage source requires read-only GitHub access. "
                "Sign in using 'gh auth login' or supply GH_TOKEN securely."
            ) from None
        token = completed.stdout.strip()
    if not token or any(char in token for char in ("\\r", "\\n")):
        raise RuntimeError("Valid GitHub source authorization is required")
    return token


class _ScopedArchiveRedirect(urllib.request.HTTPRedirectHandler):
    """Follow only the GitHub archive host and strip Authorization on redirect."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirect = urllib.parse.urlsplit(newurl)
        if (redirect.scheme != "https" or redirect.hostname != "codeload.github.com"
                or redirect.port not in (None, 443)):
            raise RuntimeError("Unexpected GitHub source archive redirect destination")
        request = super().redirect_request(req, fp, code, msg, headers, newurl)
        if request is not None:
            request.remove_header("Authorization")
        return request


def _download_source_archive(source_url, archive):
    if source_url != SOURCE_URL:
        raise RuntimeError("Unreviewed source URL override rejected")
    request = urllib.request.Request(
        SOURCE_URL,
        headers={
            "Authorization": "Bearer " + _source_token(),
            "Accept": "application/vnd.github+json",
            "User-Agent": "CROWN-Heritage-Local-Starter",
        },
    )
    opener = urllib.request.build_opener(_ScopedArchiveRedirect())
    try:
        with opener.open(request, timeout=120) as response, archive.open("wb") as output:
            shutil.copyfileobj(response, output)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"Private Heritage archive unavailable (HTTP {exc.code}); "
            "verify GitHub Contents:read access"
        ) from None


def _matches_pinned_root(directory_name):
    """GitHub zipball archives use an abbreviated owner-repository-SHA root."""
    if directory_name == f"Crown-CSMS-{SOURCE_SHA}":
        return True
    prefix = "Arete0920-Crown-CSMS-"
    if not directory_name.startswith(prefix):
        return False
    abbreviated = directory_name[len(prefix):]
    return bool(re.fullmatch(r"[0-9a-f]{7,40}", abbreviated)
                and SOURCE_SHA.startswith(abbreviated))


def install_source(destination=DESTINATION, source_url=SOURCE_URL):
    marker = destination / "HERITAGE_SOURCE_COMMIT.txt"
    if destination.exists():
        if not marker.is_file() or marker.read_text().strip() != SOURCE_SHA:
            raise RuntimeError("Existing Heritage folder has a different source identity. Move the starter to a new folder.")
        return destination
    with tempfile.TemporaryDirectory(prefix="heritage-source-", dir=ROOT) as work:
        archive = Path(work) / "source.zip"
        print("Downloading the tested Heritage source revision...", flush=True)
        _download_source_archive(source_url, archive)
        unpack = Path(work) / "source"
        unpack.mkdir()
        with zipfile.ZipFile(archive) as bundle:
            if bundle.testzip() is not None:
                raise RuntimeError("Heritage source ZIP failed integrity check")
            names = bundle.namelist()
            if len(names) != len(set(names)):
                raise RuntimeError("Heritage source ZIP contains duplicate paths")
            for member in bundle.infolist():
                target = (unpack / member.filename).resolve()
                if not target.is_relative_to(unpack.resolve()) or ((member.external_attr >> 16) & 0o170000) == 0o120000:
                    raise RuntimeError("The source archive contains an unsafe path.")
            bundle.extractall(unpack)
        roots = list(unpack.iterdir())
        if (len(roots) != 1 or not roots[0].is_dir()
                or not _matches_pinned_root(roots[0].name)
                or not (roots[0] / "scripts/demo/start_heritage_local.py").is_file()):
            raise RuntimeError("The download is not the expected CROWN source archive.")
        (roots[0] / "HERITAGE_SOURCE_COMMIT.txt").write_text(SOURCE_SHA + "\n")
        roots[0].rename(destination)
    return destination


def main():
    if sys.version_info < (3, 12):
        raise RuntimeError("Install Python 3.12 or newer; Python 3.12 is the Windows-certified runtime.")
    if not shutil.which("node"):
        raise RuntimeError("Install Node.js 24 with npm, then double-click the starter again.")
    source = install_source()
    command = [sys.executable, str(source / "scripts/demo/start_heritage_local.py")]
    if FIVE_MODULE_LAUNCH:
        command.append("--five-module-demo")
    return subprocess.call(command, cwd=source)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
        print(f"Heritage could not start: {exc}", file=sys.stderr)
        sys.exit(1)
