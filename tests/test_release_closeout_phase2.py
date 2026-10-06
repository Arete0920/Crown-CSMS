from pathlib import Path


def test_release_closeout_runtime_package_is_retired():
    assert not Path("release_closeout").exists()


def test_release_closeout_is_not_wired_into_runtime():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    settings = Path("backend/crown_api/settings.py").read_text(encoding="utf-8")
    urls = Path("backend/crown_api/urls.py").read_text(encoding="utf-8")

    assert "COPY release_closeout" not in dockerfile
    assert "release_closeout" not in settings
    assert "release_closeout" not in urls
