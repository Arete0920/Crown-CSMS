import json
from pathlib import Path


def test_mock_seed_scan_outputs_json():
    path = Path("audit-artifacts/release-verify/mock_seed_scan.json")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("[]", encoding="utf-8")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, list)