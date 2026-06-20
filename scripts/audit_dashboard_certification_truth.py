#!/usr/bin/env python3
import csv
import datetime as dt
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "audit-artifacts" / "dashboard-certification-truth"

REGISTRY_FILE = (
    REPO_ROOT / "frontend" / "dashboards" / "src" / "config" / "dashboardRegistry.js"
)
PATHS_FILE = REPO_ROOT / "frontend" / "dashboards" / "src" / "routes" / "paths.js"
DATA_REG_FILE = (
    REPO_ROOT
    / "frontend"
    / "dashboards"
    / "src"
    / "config"
    / "dashboardDataRegistry.js"
)
CERT_REG_FILE = (
    REPO_ROOT
    / "frontend"
    / "dashboards"
    / "src"
    / "config"
    / "dashboardCertificationRegistry.js"
)
TEMPLATE_INDEX_FILE = (
    REPO_ROOT
    / "frontend"
    / "dashboards"
    / "src"
    / "config"
    / "dashboardTemplates"
    / "index.js"
)
MATRIX_FILE = (
    REPO_ROOT
    / "docs"
    / "dashboard-completion"
    / "DASHBOARD_CERTIFICATION_MATRIX_V2.csv"
)
STATE_FILE = (
    REPO_ROOT
    / "audit-artifacts"
    / "dashboard-completion"
    / "state"
    / "dashboard-certification-state.json"
)

RELEVANT_PRS = [1115, 1116, 1117, 1118, 1119, 1121, 1122, 1123, 1124, 1125, 1126]
PR_SEARCH = (
    "dashboard certification OR dashboard control OR dashboard registry "
    "OR readiness OR release reliability OR compliance audit"
)

TODAY = dt.date.today()


def run(cmd: List[str], cwd: Optional[Path] = None) -> Tuple[bool, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd or REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        return proc.returncode == 0, proc.stdout.strip(), proc.stderr.strip()
    except Exception as exc:
        return False, "", str(exc)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def slugify(value: str) -> str:
    v = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", value)
    v = re.sub(r"[^a-zA-Z0-9]+", "-", v)
    return re.sub(r"-+", "-", v).strip("-").lower()


def parse_paths() -> Dict[str, str]:
    text = read_text(PATHS_FILE)
    out: Dict[str, str] = {}
    for k, v in re.findall(r"([A-Z0-9_]+)\s*:\s*'([^']+)'", text):
        out[k] = v
    return out


def parse_imports(js_text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for sym, path in re.findall(
        r"import\s+([A-Za-z0-9_]+)\s+from\s+'([^']+)'", js_text
    ):
        out[sym] = path
    return out


def parse_create_dashboard_blocks(text: str) -> List[str]:
    blocks: List[str] = []
    start = 0
    token = "createDashboard({"
    while True:
        i = text.find(token, start)
        if i < 0:
            break
        j = i + len("createDashboard(")
        depth = 1
        in_quote = False
        quote_ch = ""
        esc = False
        while j < len(text):
            ch = text[j]
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif in_quote:
                if ch == quote_ch:
                    in_quote = False
            elif ch in ("'", '"'):
                in_quote = True
                quote_ch = ch
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    blocks.append(text[i : j + 1])
                    start = j + 1
                    break
            j += 1
        else:
            break
    return blocks


def parse_field(block: str, field: str) -> Optional[str]:
    m = re.search(rf"\b{re.escape(field)}\s*:\s*'([^']*)'", block)
    if m:
        return m.group(1)
    m = re.search(rf"\b{re.escape(field)}\s*:\s*([A-Za-z0-9_\.\-]+)", block)
    if m:
        return m.group(1)
    return None


def parse_registry(paths_map: Dict[str, str]) -> List[Dict[str, Any]]:
    text = read_text(REGISTRY_FILE)
    imports = parse_imports(text)
    blocks = parse_create_dashboard_blocks(text)
    dashboards: List[Dict[str, Any]] = []
    for b in blocks:
        key = parse_field(b, "key")
        if not key:
            continue
        label = parse_field(b, "label") or key
        path_raw = parse_field(b, "path") or ""
        route = path_raw
        if route.startswith("PATHS."):
            route = paths_map.get(route.split(".", 1)[1], route)
        component = parse_field(b, "component") or ""
        release_state = parse_field(b, "releaseState") or "draft"
        tier_raw = parse_field(b, "tier") or ""
        section = parse_field(b, "section") or ""
        page_path = ""
        if component in imports:
            page_path = str(
                (REGISTRY_FILE.parent / imports[component])
                .resolve()
                .relative_to(REPO_ROOT)
            ).replace("\\", "/")
        dashboards.append(
            {
                "dashboard_key": key,
                "label": label,
                "route": route,
                "tier": int(tier_raw) if str(tier_raw).isdigit() else None,
                "section": section,
                "component": component,
                "page_component_file": page_path,
                "release_state": release_state,
            }
        )
    return dashboards


def parse_matrix() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    if not MATRIX_FILE.exists():
        return out
    with MATRIX_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            key = row.get("dashboard_key", "").strip()
            if key:
                out[key] = row
    return out


def parse_state_register() -> Dict[str, Any]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(read_text(STATE_FILE))
    except Exception:
        return {}


def extract_call(text: str, start_paren: int) -> str:
    depth = 0
    in_quote = False
    quote = ""
    esc = False
    i = start_paren
    while i < len(text):
        ch = text[i]
        if esc:
            esc = False
        elif ch == "\\":
            esc = True
        elif in_quote:
            if ch == quote:
                in_quote = False
        elif ch in ("'", '"'):
            in_quote = True
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[start_paren : i + 1]
        i += 1
    return ""


def parse_data_registry() -> Dict[str, Dict[str, Any]]:
    text = read_text(DATA_REG_FILE)
    out: Dict[str, Dict[str, Any]] = {}
    pat = re.compile(
        r"^\s*(?:'([^']+)'|([a-z][a-z0-9\-]*)):\s*createDataConfig\(", re.M
    )
    for m in pat.finditer(text):
        key = m.group(1) or m.group(2)
        open_idx = text.find("(", m.end() - 1)
        call = extract_call(text, open_idx)
        endpoint = ""
        slug_match = re.search(r"dashboardSummaryPath\('([^']+)'\)", call)
        if slug_match:
            endpoint = f"/api/v1/dashboards/{slug_match.group(1)}/summary"
        else:
            lit = re.search(r"^\((?:\s*)'([^']+)'", call)
            if lit:
                endpoint = lit.group(1)
        allow_fallback = "allowScaffoldFallback: true" in call
        has_fallback_data = "fallbackData:" in call
        if has_fallback_data and re.search(r"served_from\s*:\s*'sample'", call):
            source_type = "sample"
        elif has_fallback_data:
            source_type = "fallback"
        elif allow_fallback:
            source_type = "snapshot"
        elif endpoint:
            source_type = "live"
        else:
            source_type = "unknown"
        out[key] = {
            "summary_api": endpoint,
            "allow_scaffold_fallback": allow_fallback,
            "has_fallback_data": has_fallback_data,
            "data_source_type": source_type,
        }
    return out


def parse_cert_registry() -> Dict[str, Dict[str, str]]:
    text = read_text(CERT_REG_FILE)
    out: Dict[str, Dict[str, str]] = {}
    for m in re.finditer(
        r"(?:'([^']+)'|([a-z][a-z0-9\-]*)):\s*createCertification\('([^']+)'\s*,\s*'([^']+)'",
        text,
    ):
        key = m.group(1) or m.group(2)
        out[key] = {
            "cert_registry_status": m.group(3),
            "cert_registry_owner": m.group(4),
        }
    return out


def parse_template_index() -> Tuple[Dict[str, str], Dict[str, str]]:
    text = read_text(TEMPLATE_INDEX_FILE)
    imports = parse_imports(text)
    key_to_file: Dict[str, str] = {}
    for m in re.finditer(r"([A-Za-z0-9_]+)\s*:\s*([A-Za-z0-9_]+)", text):
        key = m.group(1)
        var = m.group(2)
        if key in ("dataSource",):
            continue
        if var in imports:
            f = (TEMPLATE_INDEX_FILE.parent / imports[var]).resolve()
            if f.exists():
                key_to_file[slugify(key)] = str(f.relative_to(REPO_ROOT)).replace(
                    "\\", "/"
                )
    var_to_file: Dict[str, str] = {}
    for var, rel in imports.items():
        f = (TEMPLATE_INDEX_FILE.parent / rel).resolve()
        if f.exists():
            var_to_file[var] = str(f.relative_to(REPO_ROOT)).replace("\\", "/")
    return key_to_file, var_to_file


def category_near(text: str, pos: int) -> str:
    window = text[max(0, pos - 600) : pos]
    best = ("unknown", -1)
    for cat in [
        "metrics",
        "alerts",
        "priorities",
        "quickActions",
        "statuses",
        "commandModules",
        "trendPanels",
        "activities",
        "queue",
    ]:
        i = window.rfind(cat + ":")
        if i > best[1]:
            best = (cat, i)
    return best[0]


def extract_widgets_from_template(path: Path) -> List[Dict[str, str]]:
    text = read_text(path)
    widgets: List[Dict[str, str]] = []
    for m in re.finditer(r"(label|title)\s*:\s*'([^']+)'", text):
        nm = m.group(2).strip()
        if not nm:
            continue
        widgets.append(
            {
                "widget_name": nm,
                "widget_key": slugify(nm),
                "widget_type": category_near(text, m.start()),
            }
        )
    if not widgets:
        widgets.append(
            {
                "widget_name": "NO_TEMPLATE_WIDGETS_FOUND",
                "widget_key": "no-template-widgets-found",
                "widget_type": "unknown",
            }
        )
    return widgets


def parse_date_from_text(s: str) -> Optional[dt.date]:
    for rx in [r"(20\d{2})(\d{2})(\d{2})", r"(20\d{2})-(\d{2})-(\d{2})"]:
        m = re.search(rx, s)
        if m:
            try:
                return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                return None
    return None


def classify_evidence(path: Path, text: str) -> Tuple[str, bool, str]:
    p = str(path).lower().replace("\\", "/")
    t = text.lower()
    if any(
        x in p
        for x in [
            "independent-review",
            "independent_review",
            "workaround",
            "authority",
            "approval",
        ]
    ):
        return "independent review record", False, "No direct technical proof"
    if "certification-state" in p or "certification_decision" in t:
        return "certification decision", False, "Decision register, not proof"
    if any(x in p for x in ["failed", "failure", "error"]):
        return "failed proof", False, "Contains failure markers"
    if any(x in p for x in ["scaffold", "template", "intake", "placeholder"]):
        return "scaffold/intake placeholder", False, "Scaffold/template markers"
    if "partial" in p or "not_verified" in t or "pending" in t:
        return "partial proof", False, "Proof incomplete"
    if any(
        x in p for x in ["proof", "evidence", "runtime", "browser", "pytest", "test"]
    ):
        supports = (
            ("pass" in t or "passed" in t)
            and "not_verified" not in t
            and "pending" not in t
            and "fail" not in t
        )
        if supports:
            return "real proof", True, "Pass markers present"
        return "real proof", False, "Missing full-pass markers"
    return "unknown", False, "Unclassified evidence"


def evidence_inventory(keys: List[str]) -> List[Dict[str, Any]]:
    roots = [
        REPO_ROOT / "docs" / "dashboard-completion",
        REPO_ROOT / "audit-artifacts" / "dashboard-completion",
        REPO_ROOT / "docs" / "release",
        REPO_ROOT / "frontend" / "dashboards" / "src",
        REPO_ROOT / "backend",
    ]
    suffixes = {".md", ".json", ".txt", ".csv", ".py", ".js"}
    inventory: List[Dict[str, Any]] = []
    key_l = [k.lower() for k in keys]
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in suffixes:
                continue
            lp = str(path).lower().replace("\\", "/")
            if (
                "dashboard" not in lp
                and "certification" not in lp
                and "release-reliability" not in lp
                and "compliance-audit" not in lp
            ):
                continue
            rel = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
            txt = read_text(path)[:4000]
            ev_type, supports, caveat = classify_evidence(path, txt)
            mapped = None
            for k in key_l:
                key_pat = rf"(?<![a-z0-9]){re.escape(k)}(?![a-z0-9])"
                if re.search(key_pat, lp) or re.search(key_pat, txt.lower()):
                    mapped = k
                    break
            d = parse_date_from_text(lp) or parse_date_from_text(txt)
            freshness = d.isoformat() if d else "unknown"
            if d and (TODAY - d).days > 60:
                if ev_type == "real proof":
                    ev_type = "stale proof"
                    supports = False
                    caveat = "Proof date older than 60 days"
            claims = []
            for token in [
                "pass",
                "passed",
                "pending",
                "not_verified",
                "certified",
                "not_certified",
                "mapped",
                "live",
            ]:
                if token in txt.lower():
                    claims.append(token)
            inventory.append(
                {
                    "path": rel,
                    "dashboard_key": mapped,
                    "evidence_type": ev_type,
                    "freshness": freshness,
                    "proof_claims": sorted(set(claims))[:20],
                    "supports_certification": supports,
                    "blocker_or_caveat": caveat,
                }
            )
    inventory.sort(key=lambda x: x["path"])
    return inventory


def gh_json(args: List[str]) -> Any:
    ok, out, _ = run(["gh"] + args)
    if not ok:
        return {
            "__gh_error__": f"gh {' '.join(args)} failed",
            "__gh_stderr__": err,
        }
    if not out:
        return None
    try:
        return json.loads(out)
    except Exception as exc:
        return {
            "__gh_error__": f"gh {' '.join(args)} returned invalid JSON: {exc}",
            "__gh_stdout__": out,
        }


def summarize_checks(status_rollup: Any) -> Dict[str, Any]:
    result = {"total": 0, "success": 0, "failed": 0, "pending": 0, "names_failed": []}
    if not isinstance(status_rollup, list):
        return result
    for item in status_rollup:
        result["total"] += 1
        concl = (item.get("conclusion") or "").upper()
        state = (item.get("state") or "").upper()
        name = (
            item.get("name")
            or item.get("context")
            or item.get("workflowName")
            or "unknown"
        )
        if concl in {"SUCCESS", "NEUTRAL", "SKIPPED"}:
            result["success"] += 1
        elif concl in {
            "FAILURE",
            "TIMED_OUT",
            "CANCELLED",
            "ACTION_REQUIRED",
            "STARTUP_FAILURE",
        }:
            result["failed"] += 1
            result["names_failed"].append(name)
        elif state in {"QUEUED", "IN_PROGRESS", "PENDING", "EXPECTED"} or concl == "":
            result["pending"] += 1
    return result


def pr_truth() -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "queried_at": dt.datetime.now().isoformat(),
        "prs": [],
        "search_results": [],
        "errors": [],
    }
    search_result = gh_json(
        [
            "pr",
            "list",
            "--state",
            "all",
            "--search",
            PR_SEARCH,
            "--limit",
            "200",
            "--json",
            "number,title,state,isDraft,headRefName,headRefOid,baseRefName,url",
        ]
    )
    if isinstance(search_result, dict) and search_result.get("__gh_error__"):
        detail = search_result.get("__gh_error__")
        stderr = search_result.get("__gh_stderr__")
        if stderr:
            detail = f"{detail}: {stderr}"
        data["errors"].append(f"Unable to fetch PR search results: {detail}")
        search = []
    elif search_result is None:
        search = []
    else:
        search = search_result
    data["search_results"] = search
    pr_numbers = set(RELEVANT_PRS)
    for pr in search:
        n = pr.get("number")
        if isinstance(n, int):
            pr_numbers.add(n)
    for n in sorted(pr_numbers):
        pr = gh_json(
            [
                "pr",
                "view",
                str(n),
                "--json",
                "number,title,state,isDraft,headRefName,headRefOid,baseRefName,mergeStateStatus,reviewDecision,files,statusCheckRollup,url,body",
            ]
        )
        if isinstance(pr, dict) and pr.get("__gh_error__"):
            detail = pr.get("__gh_error__")
            stderr = pr.get("__gh_stderr__")
            if stderr:
                detail = f"{detail}: {stderr}"
            data["errors"].append(f"Unable to fetch PR #{n}: {detail}")
            continue
        if not pr:
            data["errors"].append(f"Unable to fetch PR #{n}: empty response")
            continue
        checks = summarize_checks(pr.get("statusCheckRollup"))
        files = [
            f.get("path")
            for f in pr.get("files", [])
            if isinstance(f, dict) and f.get("path")
        ]
        title_body = (pr.get("title", "") + "\n" + pr.get("body", "")).lower()
        makes_cert_claims = any(
            tok in title_body
            for tok in [
                "certified",
                "certification",
                "live-data complete",
                "fully certified",
            ]
        )

        blocker = "none"
        if checks["failed"] > 0:
            blocker = "failed checks: " + ", ".join(checks["names_failed"][:8])
        elif checks["pending"] > 0:
            blocker = "checks pending"
        elif (pr.get("mergeStateStatus") or "").upper() in {
            "DIRTY",
            "BEHIND",
            "BLOCKED",
            "DRAFT",
        }:
            blocker = f"merge state: {pr.get('mergeStateStatus')}"

        state = (pr.get("state") or "").lower()
        needed = state == "open"
        recommendation = "retained"
        if state == "open":
            recommendation = "retain"
        elif state == "closed":
            recommendation = "closed later"
        elif state == "merged":
            recommendation = "retained"

        data["prs"].append(
            {
                "number": pr.get("number"),
                "title": pr.get("title"),
                "state": pr.get("state"),
                "draft": pr.get("isDraft"),
                "branch": pr.get("headRefName"),
                "head_sha": pr.get("headRefOid"),
                "base_branch": pr.get("baseRefName"),
                "mergeability": pr.get("mergeStateStatus"),
                "review_state": pr.get("reviewDecision"),
                "changed_files": files,
                "check_summary": checks,
                "url": pr.get("url"),
                "still_needed": needed,
                "exact_blocker": blocker,
                "makes_certification_claims": makes_cert_claims,
                "recommended_disposition": recommendation,
            }
        )
    return data


def backend_impl_paths(slug: str) -> List[str]:
    if not slug:
        return []
    pattern = f"/api/v1/dashboards/{slug}/summary"
    ok, out, _ = run(["rg", "-l", pattern, "backend"])
    hits = [p.replace("\\", "/") for p in out.splitlines()] if ok and out else []
    if hits:
        return sorted(hits)

    generic_patterns = [
        "<slug:dashboard_key>/summary",
        "path('<slug:dashboard_key>/summary'",
        'path("<slug:dashboard_key>/summary"',
    ]
    for generic in generic_patterns:
        ok, out, _ = run(["rg", "-l", generic, "backend"])
        hits = [p.replace("\\", "/") for p in out.splitlines()] if ok and out else []
        if hits:
            return sorted(hits)
    return []


def classify_dashboard(rec: Dict[str, Any]) -> str:
    has_impl = bool(
        rec.get("route") and rec.get("page_component_file") and rec.get("summary_api")
    )
    perm = str(rec.get("permission_proof_status", "")).lower()
    tenant = str(rec.get("tenant_proof_status", "")).lower()
    browser = str(rec.get("browser_runtime_proof_status", "")).lower()
    evidence = str(rec.get("evidence_packet_status", "")).lower()
    review = str(rec.get("independent_review_or_workaround_status", "")).lower()
    matrix_status = str(rec.get("matrix_row_status", "")).lower()
    state_status = str(rec.get("state_register_status", "")).lower()

    browser_parts: Dict[str, str] = {}
    for part in browser.split(";"):
        label, sep, value = part.partition(":")
        if sep:
            browser_parts[label.strip()] = value.strip()
    frontend_ok = browser_parts.get("frontend", "") in {"pass", "passed", "done", "true"}
    playwright_ok = browser_parts.get("playwright", "") in {"pass", "passed", "done", "true"}

    proof_ok = (
        all(x in {"pass", "passed", "done", "true"} for x in [perm, tenant])
        and frontend_ok
        and playwright_ok
        and ("present" in evidence or "pass" in evidence)
    )

    review_ok = review in {
        "pass",
        "passed",
        "approved",
        "workaround_recorded",
        "independent_review_recorded",
    }
    matrix_live = matrix_status in {"certified", "live"}
    state_live = (
        state_status in {"certified", "live"}
        or rec.get("state_register_certification_decision") == "certified"
    )

    if has_impl and proof_ok and review_ok and matrix_live and state_live:
        return "CERTIFIED"
    if has_impl and proof_ok and review_ok and (not matrix_live or not state_live):
        return "CERTIFIABLE_NOW"
    if has_impl and proof_ok and not review_ok:
        return "MISSING_REVIEW_ONLY"
    if has_impl:
        return "MISSING_PROOF"
    return "MISSING_IMPLEMENTATION"


def build_dashboard_truth() -> Tuple[
    Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]
]:
    paths_map = parse_paths()
    registry = parse_registry(paths_map)
    matrix = parse_matrix()
    state = parse_state_register()
    state_dashboards = state.get("dashboards", {}) if isinstance(state, dict) else {}
    data_reg = parse_data_registry()
    cert_reg = parse_cert_registry()
    template_map, _ = parse_template_index()

    out_rows: List[Dict[str, Any]] = []
    widget_rows: List[Dict[str, Any]] = []

    for d in registry:
        key = d["dashboard_key"]
        matrix_row = matrix.get(key, {})
        st = state_dashboards.get(key, {}) if isinstance(state_dashboards, dict) else {}

        data_cfg = data_reg.get(key, {})
        summary_api = data_cfg.get("summary_api") or matrix_row.get("summary_api") or ""

        template_file = template_map.get(key) or template_map.get(slugify(key))
        template_key = Path(template_file).stem if template_file else ""

        impl_paths = backend_impl_paths(key)

        tenant_status = (
            matrix_row.get("tenant_test")
            or st.get("proof", {}).get("tenant_isolation")
            or "PENDING"
        )
        perm_status = (
            matrix_row.get("permission_test")
            or st.get("proof", {}).get("api_permission")
            or "PENDING"
        )
        front = (
            matrix_row.get("frontend_test")
            or st.get("proof", {}).get("frontend_static_wiring")
            or "PENDING"
        )
        play = (
            matrix_row.get("playwright_proof")
            or st.get("proof", {}).get("browser_role_experience")
            or "PENDING"
        )
        browser_status = f"frontend:{front};playwright:{play}"

        evidence_packet = (
            matrix_row.get("evidence_packet") or st.get("evidence_packet") or ""
        )
        evidence_packet_status = "present" if evidence_packet else "missing"
        review_status = "pending"
        if matrix_row.get("independent_reviewer") and matrix_row.get(
            "independent_reviewer"
        ) not in {"", "TBD"}:
            review_status = "independent_review_recorded"
        if st.get("proof", {}).get("independent_review") in {
            "pass",
            "passed",
            "approved",
        }:
            review_status = "independent_review_recorded"
        if "workaround" in json.dumps(st).lower():
            review_status = "workaround_recorded"

        screenshot_status = "missing"
        if isinstance(st, dict) and st.get("passing_browser_proof"):
            screenshot_status = "present"

        rec = {
            "dashboard_key": key,
            "label": d.get("label"),
            "batch": matrix_row.get("batch") or d.get("tier"),
            "route": d.get("route") or matrix_row.get("route") or "",
            "template_key": template_key,
            "template_file": template_file or "",
            "page_component_file": d.get("page_component_file") or "",
            "widget_card_template_presence": "present" if template_file else "missing",
            "summary_api": summary_api,
            "backend_implementation_paths": impl_paths,
            "data_source_type": data_cfg.get("data_source_type", "unknown"),
            "permission_proof_status": str(perm_status),
            "tenant_proof_status": str(tenant_status),
            "browser_runtime_proof_status": browser_status,
            "screenshot_trace_artifact_status": screenshot_status,
            "evidence_packet_status": evidence_packet_status,
            "independent_review_or_workaround_status": review_status,
            "matrix_row_status": matrix_row.get("status", "MISSING"),
            "state_register_status": st.get("state", "MISSING"),
            "state_register_certification_decision": st.get(
                "certification_decision", "unknown"
            ),
            "certification_registry_status": cert_reg.get(key, {}).get(
                "cert_registry_status", "unknown"
            ),
        }
        rec["final_classification"] = classify_dashboard(rec)
        out_rows.append(rec)

        if template_file:
            tpath = REPO_ROOT / template_file
            widgets = extract_widgets_from_template(tpath)
        else:
            widgets = [
                {
                    "widget_name": "NO_TEMPLATE_FILE",
                    "widget_key": "no-template-file",
                    "widget_type": "unknown",
                }
            ]

        for w in widgets:
            widget_rows.append(
                {
                    "dashboard_key": key,
                    "widget_name": w["widget_name"],
                    "widget_key": w["widget_key"],
                    "widget_type": w["widget_type"],
                    "label_or_title": w["widget_name"],
                    "data_source": summary_api or "unknown",
                    "data_source_type": rec["data_source_type"],
                    "source_truth_documented": bool(summary_api),
                    "widget_has_proof": rec["final_classification"]
                    in {"CERTIFIED", "CERTIFIABLE_NOW", "MISSING_REVIEW_ONLY"},
                    "blocker": "widget template existence is not certification proof"
                    if rec["final_classification"] != "CERTIFIED"
                    else "none",
                }
            )

    matrix_keys = sorted(matrix.keys())
    registry_keys = sorted([d["dashboard_key"] for d in registry])
    state_total = (
        state.get("totals", {}).get("dashboards_total")
        if isinstance(state, dict)
        else None
    )

    factory_report = (
        REPO_ROOT
        / "audit-artifacts"
        / "dashboard-completion"
        / "factory"
        / "dashboard-certification-factory-report.json"
    )
    factory_files = []
    if factory_report.exists():
        factory_files.append(str(factory_report.relative_to(REPO_ROOT)).replace("\\", "/"))
    factory_status = (
        "factory output present" if factory_files else "factory output not found"
    )

    summary = {
        "generated_at": dt.datetime.now().isoformat(),
        "counts": {
            "registry_count": len(registry_keys),
            "matrix_count": len(matrix_keys),
            "state_register_count": state_total,
            "factory_count": len(factory_files),
            "certified_count": sum(
                1 for r in out_rows if r["final_classification"] == "CERTIFIED"
            ),
            "certifiable_now_count": sum(
                1 for r in out_rows if r["final_classification"] == "CERTIFIABLE_NOW"
            ),
            "missing_review_only_count": sum(
                1
                for r in out_rows
                if r["final_classification"] == "MISSING_REVIEW_ONLY"
            ),
            "missing_proof_count": sum(
                1 for r in out_rows if r["final_classification"] == "MISSING_PROOF"
            ),
            "missing_implementation_count": sum(
                1
                for r in out_rows
                if r["final_classification"] == "MISSING_IMPLEMENTATION"
            ),
        },
        "denominator_reconciliation": {
            "recommended_canonical_count": len(registry_keys),
            "registry_keys_not_in_matrix": sorted(
                [k for k in registry_keys if k not in matrix_keys]
            ),
            "matrix_keys_not_in_registry": sorted(
                [k for k in matrix_keys if k not in registry_keys]
            ),
            "files_that_disagree": [
                "audit-artifacts/module-completion/current/05_completion_scorecard.md",
                "docs/dashboard-completion/DASHBOARD_CERTIFICATION_MATRIX_V2.csv",
                "audit-artifacts/dashboard-completion/state/dashboard-certification-state.json",
            ],
            "factory_status": factory_status,
            "factory_files": factory_files,
            "reconciliation_should_be_separate_pr": True,
        },
    }
    return summary, out_rows, widget_rows


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def md_table(rows: List[Dict[str, Any]], cols: List[str]) -> str:
    hdr = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    lines = [hdr, sep]
    for r in rows:
        vals = []
        for c in cols:
            v = r.get(c, "")
            if isinstance(v, list):
                v = ", ".join(map(str, v[:6]))
            vals.append(str(v).replace("\n", " "))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def write_markdowns(
    dashboard_summary: Dict[str, Any],
    dashboard_rows: List[Dict[str, Any]],
    widget_rows: List[Dict[str, Any]],
    pr_data: Dict[str, Any],
    evidence_rows: List[Dict[str, Any]],
) -> None:
    dcols = [
        "dashboard_key",
        "label",
        "batch",
        "route",
        "summary_api",
        "data_source_type",
        "permission_proof_status",
        "tenant_proof_status",
        "browser_runtime_proof_status",
        "evidence_packet_status",
        "independent_review_or_workaround_status",
        "matrix_row_status",
        "state_register_status",
        "final_classification",
    ]
    wcols = [
        "dashboard_key",
        "widget_name",
        "widget_type",
        "data_source",
        "data_source_type",
        "source_truth_documented",
        "widget_has_proof",
        "blocker",
    ]
    pcols = [
        "number",
        "title",
        "state",
        "draft",
        "branch",
        "head_sha",
        "base_branch",
        "mergeability",
        "review_state",
        "still_needed",
        "exact_blocker",
        "makes_certification_claims",
        "recommended_disposition",
    ]
    ecols = [
        "path",
        "dashboard_key",
        "evidence_type",
        "freshness",
        "supports_certification",
        "blocker_or_caveat",
    ]

    dashboard_md = [
        "# Dashboard Certification Truth",
        "",
        f"Generated: {dashboard_summary['generated_at']}",
        "",
        "## Counts",
        "",
        md_table(
            [dashboard_summary["counts"]], list(dashboard_summary["counts"].keys())
        ),
        "",
        "## Denominator Reconciliation",
        "",
        "```json",
        json.dumps(dashboard_summary["denominator_reconciliation"], indent=2),
        "```",
        "",
        "## Dashboard Rows",
        "",
        md_table(dashboard_rows, dcols),
    ]
    (OUT_DIR / "dashboard_truth.md").write_text(
        "\n".join(dashboard_md), encoding="utf-8"
    )

    widget_md = [
        "# Widget Truth",
        "",
        md_table(widget_rows, wcols),
    ]
    (OUT_DIR / "widget_truth.md").write_text("\n".join(widget_md), encoding="utf-8")

    pr_rows = pr_data.get("prs", [])
    pr_md = [
        "# PR Truth",
        "",
        f"Queried: {pr_data.get('queried_at')}",
        "",
        "## PR Rows",
        "",
        md_table(pr_rows, pcols),
        "",
        "## Search Results",
        "",
        "```json",
        json.dumps(pr_data.get("search_results", []), indent=2),
        "```",
        "",
        "## Errors",
        "",
        "```json",
        json.dumps(pr_data.get("errors", []), indent=2),
        "```",
    ]
    (OUT_DIR / "pr_truth.md").write_text("\n".join(pr_md), encoding="utf-8")

    evidence_md = [
        "# Evidence Inventory",
        "",
        md_table(evidence_rows, ecols),
    ]
    (OUT_DIR / "evidence_inventory.md").write_text(
        "\n".join(evidence_md), encoding="utf-8"
    )

    grouped: Dict[str, int] = {}
    for r in dashboard_rows:
        grouped[r["final_classification"]] = (
            grouped.get(r["final_classification"], 0) + 1
        )
    top_blockers: Dict[str, int] = {}
    for r in dashboard_rows:
        b = (
            "missing_review"
            if r["final_classification"] == "MISSING_REVIEW_ONLY"
            else (
                "missing_proof"
                if r["final_classification"] == "MISSING_PROOF"
                else r["final_classification"].lower()
            )
        )
        top_blockers[b] = top_blockers.get(b, 0) + 1

    closeout = [
        "# Dashboard Certification Closeout Plan",
        "",
        "## Current Truth",
        "",
        "```json",
        json.dumps(dashboard_summary["counts"], indent=2),
        "```",
        "",
        "## Ranked Path",
        "",
        "1. Reconcile denominator mismatch in a separate matrix/scorecard PR (no product code).",
        "2. Batch 0 first: dashboard-certification-center, release-reliability, compliance-audit.",
        "3. For each dashboard lane, close proof gates in this order: permission, tenant, runtime/browser, evidence packet, independent review/workaround record, matrix/state promotion.",
        "4. Keep certification reporting PRs separate from implementation PRs.",
        "",
        "## Blocker Groups",
        "",
        "```json",
        json.dumps(top_blockers, indent=2),
        "```",
        "",
        "## Actions That Close Multiple Dashboards",
        "",
        "1. Standardize tenant-proof test harness for dashboard summary endpoints.",
        "2. Standardize permission-proof matrix per route and role for dashboard endpoints.",
        "3. Standardize browser/runtime proof capture packet schema for all dashboard lanes.",
        "4. Add independent review/workaround record template linked from matrix rows.",
        "",
        "## Separation Rules",
        "",
        "- Keep product implementation separate from certification reporting and scorecard reconciliation.",
        "- Do not mark CERTIFIED until matrix, state register, evidence packet, runtime proof, and review/workaround record all agree.",
        "",
        "## Time Estimate",
        "",
        "- NOT VERIFIED: Batch 0 truth closure evidence-only updates: 1 to 2 days.",
        "- Remaining 39 dashboard proof completion depends on implementation and test readiness; NOT VERIFIED in this audit-only lane.",
    ]
    (OUT_DIR / "closeout_plan.md").write_text("\n".join(closeout), encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    dashboard_summary, dashboard_rows, widget_rows = build_dashboard_truth()
    pr_data = pr_truth()
    evidence_rows = evidence_inventory([r["dashboard_key"] for r in dashboard_rows])

    write_json(
        OUT_DIR / "dashboard_truth.json",
        {"summary": dashboard_summary, "rows": dashboard_rows},
    )
    write_json(OUT_DIR / "widget_truth.json", {"rows": widget_rows})
    write_json(OUT_DIR / "pr_truth.json", pr_data)
    write_json(OUT_DIR / "evidence_inventory.json", {"rows": evidence_rows})

    write_markdowns(
        dashboard_summary, dashboard_rows, widget_rows, pr_data, evidence_rows
    )

    print(f"Wrote reports to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
