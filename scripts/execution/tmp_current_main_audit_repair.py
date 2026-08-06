from __future__ import annotations

import json
from pathlib import Path


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Expected {label} anchor not found in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


settings = Path("backend/crown_api/settings.py")
replace_once(
    settings,
    '''if DATABASE_URL and _env_is_prod():
    DATABASES["default"].setdefault("OPTIONS", {})
    DATABASES["default"]["OPTIONS"]["sslmode"] = "require"
''',
    '''if (
    DATABASE_URL
    and _env_is_prod()
    and DATABASES["default"].get("ENGINE")
    in {
        "django.db.backends.postgresql",
        "django.db.backends.postgresql_psycopg2",
    }
):
    DATABASES["default"].setdefault("OPTIONS", {})
    DATABASES["default"]["OPTIONS"]["sslmode"] = "require"
''',
    "database SSL",
)

workflow = Path(".github/workflows/current-main-audit.yml")
text = workflow.read_text(encoding="utf-8")
for source, target in {
    "DJANGO_SECRET_KEY: ci-current-main-not-secret": "DJANGO_SECRET_KEY: ci-current-main-audit-secret-7L9m2Q4v8X1p5R0s6T3u9W2y7Z4a8B1c",
    "SECRET_KEY: ci-current-main-not-secret": "SECRET_KEY: ci-current-main-audit-secret-7L9m2Q4v8X1p5R0s6T3u9W2y7Z4a8B1c",
    "DJANGO_ENV: production": "DJANGO_ENV: ci",
    "CROWN_ENV: prod": "CROWN_ENV: ci",
}.items():
    if source not in text:
        raise SystemExit(f"Expected workflow value not found: {source}")
    text = text.replace(source, target, 1)

install_anchor = '''      - name: Install frontend dependencies
        working-directory: frontend/dashboards
        shell: bash
        run: npm ci
'''
install_replacement = install_anchor + '''
      - name: Install Playwright Chromium
        working-directory: frontend/dashboards
        shell: bash
        run: npx playwright install --with-deps chromium
'''
if install_anchor not in text:
    raise SystemExit("Frontend dependency step anchor not found")
text = text.replace(install_anchor, install_replacement, 1)

deploy_old = "run_check django_deploy_check advisory bash -lc 'cd backend && python manage.py check --deploy'"
deploy_new = "run_check django_deploy_check advisory env DJANGO_ENV=production CROWN_ENV=prod DJANGO_SECRET_KEY=ci-current-main-audit-deploy-secret-9N4q7V2x5M8r1T6y3P0s4K7d2F9h6J1c DATABASE_URL=sqlite:///./ci_current_main.sqlite3 bash -lc 'cd backend && python manage.py check --deploy'"
if deploy_old not in text:
    raise SystemExit("Deploy check command not found")
workflow.write_text(text.replace(deploy_old, deploy_new, 1), encoding="utf-8")

package = Path("frontend/dashboards/package.json")
data = json.loads(package.read_text(encoding="utf-8"))
data.setdefault("overrides", {})["postcss"] = "8.5.23"
package.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

print("Current Main audit source repairs applied")
