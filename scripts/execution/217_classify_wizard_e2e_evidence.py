from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC_ROOT = ROOT / "tests" / "e2e"
OUT_DIR = ROOT / "audit-artifacts" / "wizard-e2e-evidence" / "latest"

TRIVIAL_PATTERNS = [
    re.compile(r"expect\(\s*true\s*\)\.toBeTruthy\(\s*\)", re.I),
    re.compile(r"expect\(\s*1\s*\)\.toBe\(\s*1\s*\)", re.I),
    re.compile(r"expect\(\s*['\"]?ok['\"]?\s*\)\.toBeTruthy\(\s*\)", re.I),
]


def has_any(text: str, needles: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(needle.lower() in lower for needle in needles)


def classify(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    compact = re.sub(r"\s+", " ", text).strip()

    uses_page = has_any(text, ("page.goto(", "page.getby", "page.locator(", "page.click(", "page.fill("))
    uses_request = has_any(text, ("request.get(", "request.post(", "request.patch(", "request.put(", "request.delete("))
    uses_api_response = has_any(text, ("waitforresponse(", "response.status(", "/api/"))
    route_mocking = has_any(text, ("page.route(", "route.fulfill(", "route.continue("))
    persistence_signal = has_any(
        text,
        (
            "commit",
            "save",
            "submit",
            "persist",
            "reread",
            "verify",
            "created",
            "updated",
            "delete",
            "post(",
            "patch(",
            "put(",
        ),
    )
    rbac_tenant_signal = has_any(
        text,
        (
            "unauthorized",
            "forbidden",
            "403",
            "401",
            "tenant",
            "school-id",
            "x-school-id",
            "cross-school",
            "foreign school",
            "wrong school",
            "denied",
        ),
    )
    validation_signal = has_any(text, ("validation", "invalid", "required", "error", "400"))
    constant_assertion = any(pattern.search(text) for pattern in TRIVIAL_PATTERNS)
    tiny = len(compact) < 220
    no_app_interaction = not (uses_page or uses_request or uses_api_response)

    if constant_assertion and tiny and no_app_interaction:
        classification = "PLACEHOLDER"
    elif uses_page and not persistence_signal:
        classification = "ROUTE_ONLY"
    elif uses_page or uses_request or uses_api_response:
        classification = "REAL_FUNCTIONAL_CANDIDATE"
    else:
        classification = "NON_EVIDENTIARY"

    scaffold_ui = uses_page
    live_ui_api = bool((uses_page or uses_request or uses_api_response) and not route_mocking)
    backend_persistence = bool(live_ui_api and persistence_signal)
    rbac_tenant = bool(live_ui_api and rbac_tenant_signal)

    # A required production-capable wizard is not proof-backed unless live runtime,
    # persistence and RBAC/tenant evidence are all present. Validation is reported
    # separately because some read-only wizards may not have a mutation boundary.
    proof_backed = bool(
        classification == "REAL_FUNCTIONAL_CANDIDATE"
        and live_ui_api
        and backend_persistence
        and rbac_tenant
    )

    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "classification": classification,
        "SCAFFOLD_UI": scaffold_ui,
        "LIVE_UI_API": live_ui_api,
        "BACKEND_PERSISTENCE": backend_persistence,
        "RBAC_TENANT": rbac_tenant,
        "VALIDATION": validation_signal,
        "route_mocking": route_mocking,
        "constant_assertion": constant_assertion,
        "proof_backed": proof_backed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-on-placeholder", action="store_true")
    parser.add_argument("--fail-on-unverified", action="store_true")
    args = parser.parse_args()

    specs = sorted(SPEC_ROOT.glob("*_wizard_spec.ts"))
    rows = [classify(path) for path in specs]

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1

    placeholders = [row for row in rows if row["classification"] == "PLACEHOLDER"]
    unverified = [row for row in rows if not row["proof_backed"]]

    status = {
        "schema_version": 1,
        "spec_count": len(rows),
        "classification_counts": counts,
        "placeholder_count": len(placeholders),
        "proof_backed_count": len(rows) - len(unverified),
        "unverified_count": len(unverified),
        "all_specs_proof_backed": len(rows) > 0 and not unverified,
        "evidence_classes": [
            "SCAFFOLD_UI",
            "LIVE_UI_API",
            "BACKEND_PERSISTENCE",
            "RBAC_TENANT",
        ],
        "rows": rows,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "99_STATUS.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")

    summary = [
        "# Wizard E2E Evidence Classification",
        "",
        f"- Specs inventoried: {len(rows)}",
        f"- Placeholder: {len(placeholders)}",
        f"- Proof-backed: {status['proof_backed_count']}",
        f"- Not verified: {len(unverified)}",
        "",
        "| Spec | Classification | Scaffold UI | Live UI/API | Persistence | RBAC/Tenant | Proof-backed |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        summary.append(
            f"| `{row['path']}` | {row['classification']} | "
            f"{str(row['SCAFFOLD_UI']).upper()} | {str(row['LIVE_UI_API']).upper()} | "
            f"{str(row['BACKEND_PERSISTENCE']).upper()} | {str(row['RBAC_TENANT']).upper()} | "
            f"{str(row['proof_backed']).upper()} |"
        )
    (OUT_DIR / "00_SUMMARY.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    print(json.dumps({k: v for k, v in status.items() if k != "rows"}, indent=2))

    if args.fail_on_placeholder and placeholders:
        print("ERROR: placeholder wizard specs remain:")
        for row in placeholders:
            print(f" - {row['path']}")
        return 2
    if args.fail_on_unverified and unverified:
        print("ERROR: wizard specs remain without required live functional evidence")
        for row in unverified:
            print(f" - {row['path']}: {row['classification']}")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
