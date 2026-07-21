from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = REPO_ROOT / "backend"
EXCLUDED_PARTS = {"migrations", "tests", "__pycache__", ".venv", "venv"}

SENSITIVITY_RULES = {
    "restricted_health": {"medical", "medication", "allergy", "health", "diagnosis", "emergency"},
    "restricted_financial": {"income", "salary", "tuition", "balance", "award", "aid", "payment", "bank"},
    "restricted_counseling_discipline": {"discipline", "incident", "counsel", "pastoral", "behavior", "sanction"},
    "confidential_identity": {"first_name", "last_name", "email", "phone", "address", "birth", "guardian", "student"},
    "confidential_academic": {"grade", "attendance", "transcript", "course", "assessment", "gpa"},
    "confidential_authentication": {"password", "token", "secret", "credential", "mfa"},
}

KNOWN_DOMAIN_ANCHORS = {
    "backend/core/models.py",
    "backend/households/models.py",
    "backend/crown_api/models_households.py",
    "backend/applications/models.py",
}


def iter_model_files(repo_root: Path):
    backend = repo_root / "backend"
    for path in backend.rglob("*.py"):
        relative = path.relative_to(repo_root)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if path.name == "models.py" or path.name.startswith("models_"):
            yield path, relative.as_posix()


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{call_name(node.value)}.{node.attr}".strip(".")
    return ""


def classify_field(field_name: str, model_name: str, path: str) -> tuple[str, list[str]]:
    haystack = f"{field_name} {model_name} {path}".lower()
    matches = [category for category, terms in SENSITIVITY_RULES.items() if any(term in haystack for term in terms)]
    if not matches:
        return "internal_operational", ["automated_review_required"]
    order = [
        "restricted_health",
        "restricted_financial",
        "restricted_counseling_discipline",
        "confidential_authentication",
        "confidential_identity",
        "confidential_academic",
    ]
    primary = next(category for category in order if category in matches)
    flags = ["automated_classification_review_required"] if len(matches) > 1 else []
    return primary, flags


def build_inventory(repo_root: Path) -> dict:
    records = []
    observed_files = set()
    parse_failures = []

    for path, relative in iter_model_files(repo_root):
        observed_files.add(relative)
        try:
            source = path.read_text(encoding="utf-8-sig", errors="strict")
            tree = ast.parse(source, filename=relative)
        except (SyntaxError, UnicodeDecodeError) as exc:
            parse_failures.append({
                "path": relative,
                "line": getattr(exc, "lineno", None),
                "message": str(getattr(exc, "msg", exc)),
            })
            continue

        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            base_names = [call_name(base) for base in node.bases]
            if not any(name.endswith("Model") or name.endswith("models.Model") for name in base_names):
                continue
            for statement in node.body:
                if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
                    continue
                targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
                value = statement.value
                if not isinstance(value, ast.Call):
                    continue
                field_type = call_name(value.func)
                if "Field" not in field_type and not field_type.endswith(("ForeignKey", "OneToOneField", "ManyToManyField")):
                    continue
                for target in targets:
                    if not isinstance(target, ast.Name):
                        continue
                    sensitivity, flags = classify_field(target.id, node.name, relative)
                    records.append({
                        "path": relative,
                        "model": node.name,
                        "field": target.id,
                        "field_type": field_type,
                        "sensitivity": sensitivity,
                        "review_flags": flags,
                    })

    records.sort(key=lambda item: (item["path"], item["model"], item["field"]))
    sensitivity_counts = Counter(record["sensitivity"] for record in records)
    missing_anchors = sorted(KNOWN_DOMAIN_ANCHORS - observed_files)

    return {
        "schema_version": 1,
        "mode": "read_only_static_source_inventory",
        "legal_determination": False,
        "record_count": len(records),
        "sensitivity_counts": dict(sorted(sensitivity_counts.items())),
        "missing_known_domain_anchors": missing_anchors,
        "parse_failures": parse_failures,
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a deterministic static inventory of Django model fields and provisional sensitivity classes.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    inventory = build_inventory(repo_root)
    rendered = json.dumps(inventory, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = args.output if args.output.is_absolute() else repo_root / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    return 1 if inventory["missing_known_domain_anchors"] or inventory["parse_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
