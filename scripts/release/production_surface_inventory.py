#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, hashlib, inspect, json, os, re, subprocess, sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

SUPPORTED={"CRAWLER","PLAYWRIGHT","API_CONTRACT","BACKEND_TEST","OPERATIONAL_DRILL","MANUAL_REVIEW","EXCLUDED_PAYMENT_PROCESSING","EXCLUDED_HANDOFF","NOT_APPLICABLE","UNMAPPED"}
SUPPORTED_CLASSIFICATIONS=SUPPORTED
REQUIRED={"frontend_route","dashboard","module","wizard","wizard_step","api","task","integration"}
PATH_RE=re.compile(r"^\s*([A-Z][A-Z0-9_]*)\s*:\s*['\"]([^'\"]+)['\"]",re.M)
WIZ_RE=re.compile(r"\{\s*slug:\s*['\"]([^'\"]+)['\"]\s*,\s*title:\s*['\"]([^'\"]+)['\"]\s*,\s*path:\s*['\"]([^'\"]+)['\"]\s*\}")
FIELD_RE=re.compile(r"\b(key|label|title|path)\s*:\s*([^,\n}]+)")
STEP_ARRAY_RE=re.compile(r"(?:const|let|var|export\s+const)\s+[A-Za-z0-9_]*steps?[A-Za-z0-9_]*\s*=\s*\[",re.I)
STEP_ID_RE=re.compile(r"\b(?:id|key|slug)\s*:\s*['\"]([^'\"]+)['\"]")
STEP_LABEL_RE=re.compile(r"\b(?:title|label|name)\s*:\s*['\"]([^'\"]+)['\"]")
PAYMENT_RE=re.compile(r"(?:checkout|payment[-_/ ]?(?:intent|method|provider|processor|webhook|confirm|charge)|(?:merchant|processor)[-_/ ]?(?:callback|webhook)|(?:confirm|charge)[-_/ ]?payment|billing/pay)",re.I)
HANDOFF_RE=re.compile(r"(?:buyer|successor|ownership[-_/ ]?transfer|handoff)",re.I)
INTERNAL_RE=re.compile(r"(?:^\*$|/(?:health|version|schema|docs|redoc|system-status|release-readiness|demo-readiness|forbidden|not-authorized)(?:/|$)|^/admin/?$|^/accounts/)",re.I)
OP_TASK_RE=re.compile(r"(?:backup|restore|rollback|rotate|reconcile|sync|import|export|dispatch|send|cleanup|purge|archive)",re.I)

@dataclass(frozen=True)
class Surface:
    surface_id:str; domain:str; name:str; path:str; source_file:str; source_line:int
    classification:str="UNMAPPED"; classification_rule:str="unclassified"; rationale:str="No supported proof rule matched."

def text(p:Path)->str:return p.read_text(encoding="utf-8-sig")
def line(s:str,o:int)->int:return s.count("\n",0,o)+1
def slug(v:str)->str:
    v=re.sub(r"[:{}<>]","param",v.strip().lower().replace("*","not-found"));return re.sub(r"[^a-z0-9]+","-",v).strip("-") or "root"
def literal(v:str)->str|None:
    v=v.strip();return v[1:-1] if len(v)>1 and v[0] in "'\"" and v[-1]==v[0] else None

def region(s:str,start:int,op:str,cl:str)->tuple[str,int]:
    depth=0;quote=None;esc=False
    for i in range(start,len(s)):
        c=s[i]
        if quote:
            if esc:esc=False
            elif c=="\\":esc=True
            elif c==quote:quote=None
            continue
        if c in "'\"`":quote=c;continue
        if c==op:depth+=1
        elif c==cl:
            depth-=1
            if depth==0:return s[start+1:i],i+1
    raise ValueError(f"unbalanced {op}{cl}")

def parse_paths(root:Path):
    p=root/"frontend/dashboards/src/routes/paths.js";s=text(p);vals={};rows=[]
    for m in PATH_RE.finditer(s):
        k,v=m.groups();vals[k]=v;rows.append(Surface(f"frontend_route:{k.lower()}","frontend_route",k,v,p.relative_to(root).as_posix(),line(s,m.start())))
    if not rows:raise ValueError("no frontend PATHS entries")
    return vals,rows

def dashboards(root:Path,paths:dict[str,str])->list[Surface]:
    p=root/"frontend/dashboards/src/config/dashboardRegistry.js";s=text(p);rows=[];cur=0;mark="createDashboard("
    while (pos:=s.find(mark,cur))>=0:
        brace=s.find("{",pos+len(mark));block,end=region(s,brace,"{","}");fields={k:v.strip() for k,v in FIELD_RE.findall(block)}
        key=literal(fields.get("key","")) or f"unresolved-line-{line(s,pos)}";raw=fields.get("path","");route=literal(raw) or (paths.get(raw.split(".",1)[1],"") if raw.startswith("PATHS.") else "")
        labelv=literal(fields.get("label","")) or literal(fields.get("title","")) or key
        rows.append(Surface(f"dashboard:{slug(key)}","dashboard",labelv,route,p.relative_to(root).as_posix(),line(s,pos)));cur=end
    if not rows:raise ValueError("no dashboard registry entries")
    return rows

def wizards(root:Path)->list[Surface]:
    p=root/"frontend/dashboards/src/routes/wizard-manifest.js";s=text(p);rows=[]
    for m in WIZ_RE.finditer(s):
        k,titlev,route=m.groups();rows.append(Surface(f"wizard:{slug(k)}","wizard",titlev,route,p.relative_to(root).as_posix(),line(s,m.start())))
    if not rows:raise ValueError("no wizard manifest entries")
    return rows

def object_literals(s:str):
    cur=0
    while (pos:=s.find("{",cur))>=0:
        try:block,end=region(s,pos,"{","}")
        except ValueError:return
        yield block,pos;cur=end

def wizard_steps(root:Path)->list[Surface]:
    base=root/"frontend/dashboards/src";files=sorted({p for pat in ("*Wizard*.js","*Wizard*.jsx","*Wizard*.ts","*Wizard*.tsx") for p in base.rglob(pat) if p.is_file()});rows=[]
    for p in files:
        s=text(p)
        for a in STEP_ARRAY_RE.finditer(s):
            b=s.find("[",a.start())
            try:arr,_=region(s,b,"[","]")
            except ValueError:continue
            for block,off in object_literals(arr):
                mid=STEP_ID_RE.search(block);ml=STEP_LABEL_RE.search(block)
                if mid and ml:rows.append(Surface(f"wizard_step:{slug(p.stem)}:{slug(mid.group(1))}","wizard_step",f"{p.stem}: {ml.group(1)}","",p.relative_to(root).as_posix(),line(s,b+1+off)))
    return rows

def modules(root:Path)->list[Surface]:
    rows=[]
    for p in sorted((root/"backend").glob("*/apps.py")):
        tree=ast.parse(text(p),filename=str(p))
        for n in tree.body:
            if not isinstance(n,ast.ClassDef):continue
            if not any((isinstance(b,ast.Name) and b.id=="AppConfig") or (isinstance(b,ast.Attribute) and b.attr=="AppConfig") for b in n.bases):continue
            for st in n.body:
                if isinstance(st,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="name" for t in st.targets) and isinstance(st.value,ast.Constant) and isinstance(st.value.value,str):
                    app=st.value.value;rows.append(Surface(f"module:backend:{slug(app)}","module",app,"",p.relative_to(root).as_posix(),n.lineno))
    return rows

def route_text(p)->str:return str(getattr(p,"pattern","")).replace("^","").replace("$","").replace("\\Z","")
def flatten(patterns,prefix=""):
    out=[]
    for p in patterns:
        current=prefix+route_text(p);children=getattr(p,"url_patterns",None)
        if children is not None:out.extend(flatten(children,current));continue
        out.append((current,str(getattr(p,"name","") or ""),getattr(p,"callback",None)))
    return out

def django_urls(root:Path)->list[Surface]:
    backend=root/"backend";sys.path.insert(0,str(backend));os.environ.setdefault("DJANGO_SETTINGS_MODULE","crown_api.settings");os.environ.setdefault("DJANGO_SECRET_KEY","inventory-only-not-a-secret");os.environ.setdefault("DATABASE_URL","sqlite:////tmp/crown-production-surface-inventory.sqlite3")
    try:
        import django
        from django.urls import get_resolver
        django.setup();patterns=get_resolver().url_patterns
    except Exception as e:raise RuntimeError(f"Django URL resolver initialization failed: {e}") from e
    rows=[]
    for route,name,cb in flatten(patterns):
        path="/"+route.lstrip("/");module=str(getattr(cb,"__module__","") or "");target=getattr(cb,"view_class",cb)
        try:sp=Path(inspect.getsourcefile(target) or "");sf=sp.relative_to(root).as_posix();sl=inspect.getsourcelines(target)[1]
        except (OSError,TypeError,ValueError):sf=module.replace(".","/")+".py" if module else "backend/crown_api/urls.py";sl=0
        domain="integration" if path.startswith(("/api/integrations/","/auth/","/api/iam/")) or module.startswith(("integrations.","msauth.","core.auth.")) else "api"
        rows.append(Surface(f"{domain}:{slug(path)}:{slug(name or module or 'unnamed')}",domain,name or module or path,path,sf,sl))
    return rows

def decname(n):
    if isinstance(n,ast.Name):return n.id
    if isinstance(n,ast.Attribute):return decname(n.value)+"."+n.attr
    if isinstance(n,ast.Call):return decname(n.func)
    return ""
def tasks(root:Path)->list[Surface]:
    rows=[]
    for p in sorted((root/"backend").rglob("tasks.py")):
        if any(x in {"migrations","tests","test"} for x in p.parts):continue
        tree=ast.parse(text(p),filename=str(p))
        for n in tree.body:
            if not isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) or n.name.startswith("_"):continue
            decorators={decname(x) for x in n.decorator_list}
            mod=p.parent.name;rows.append(Surface(f"task:{slug(mod)}:{slug(n.name)}","task",f"{mod}.{n.name}","",p.relative_to(root).as_posix(),n.lineno))
    return rows

def mapped(row:Surface,classification:str,rule:str,rationale:str)->Surface:return Surface(**{**asdict(row),"classification":classification,"classification_rule":rule,"rationale":rationale})
def classify(row:Surface)->Surface:
    value=" ".join((row.name,row.path,row.source_file))
    if HANDOFF_RE.search(value):return mapped(row,"EXCLUDED_HANDOFF","handoff-boundary","Buyer or successor execution is outside release scope.")
    if PAYMENT_RE.search(value):return mapped(row,"EXCLUDED_PAYMENT_PROCESSING","external-payment-boundary","External payment processing remains disabled and fail closed.")
    if row.domain=="frontend_route":return mapped(row,"NOT_APPLICABLE" if INTERNAL_RE.search(row.path) else "CRAWLER","frontend-route","Internal routes are tracked only." if INTERNAL_RE.search(row.path) else "Frontend routes require deployed crawler proof.")
    if row.domain=="dashboard":return row if not row.path else mapped(row,"PLAYWRIGHT","dashboard-browser-proof","Dashboards require authenticated browser proof.")
    if row.domain in {"wizard","wizard_step"}:return mapped(row,"PLAYWRIGHT","wizard-browser-proof","Wizard surfaces require browser workflow proof.")
    if row.domain=="module":return mapped(row,"BACKEND_TEST","module-test","Backend modules require focused tests.")
    if row.domain=="api":return mapped(row,"NOT_APPLICABLE" if INTERNAL_RE.search(row.path) else "API_CONTRACT","api-route","Internal endpoints are tracked only." if INTERNAL_RE.search(row.path) else "API endpoints require contract proof.")
    if row.domain=="task":return mapped(row,"OPERATIONAL_DRILL" if OP_TASK_RE.search(row.name) else "BACKEND_TEST","task-proof","Stateful tasks require a drill." if OP_TASK_RE.search(row.name) else "Deterministic tasks require focused tests.")
    if row.domain=="integration":return mapped(row,"MANUAL_REVIEW","integration-review","External integrations require configuration and operational review.")
    return row

def validate(rows, require_domains=True):
    errors=[];ids=Counter(r.surface_id for r in rows);dup=sorted(k for k,v in ids.items() if v>1)
    if dup:errors.append("duplicate surface_id values: "+", ".join(dup[:20]))
    if require_domains:
        missing=sorted(REQUIRED-{r.domain for r in rows})
        if missing:errors.append("missing required domains: "+", ".join(missing))
    errors.extend(f"unsupported classification {r.classification} for {r.surface_id}" for r in rows if r.classification not in SUPPORTED)
    return errors

def repo_sha(root:Path)->str:
    values=[os.getenv("INVENTORY_REPOSITORY_SHA",""),os.getenv("GITHUB_SHA","")]
    try:values.append(subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip())
    except (OSError,subprocess.CalledProcessError):pass
    for v in values:
        if re.fullmatch(r"[0-9a-f]{40}",v.lower().strip()):return v.lower().strip()
    raise RuntimeError("full 40-character repository SHA required")
def payload(rows):return [asdict(r) for r in sorted(rows,key=lambda r:(r.domain,r.surface_id,r.source_file,r.source_line))]
def digest(rows):return hashlib.sha256(json.dumps(payload(rows),sort_keys=True,separators=(",",":")).encode()).hexdigest()
def markdown(packet):
    lines=["# CROWN Production Surface Inventory","",f"- Repository SHA: `{packet['repository_sha']}`",f"- Inventory digest: `{packet['inventory_digest']}`",f"- Total surfaces: {packet['surface_count']}",f"- Unmapped surfaces: {packet['counts']['by_classification'].get('UNMAPPED',0)}","- Production authorization: not implied","","| ID | Domain | Path | Classification | Source |","| --- | --- | --- | --- | --- |"]
    for r in packet["surfaces"]:lines.append(f"| `{r['surface_id']}` | {r['domain']} | `{r['path']}` | {r['classification']} | `{r['source_file']}:{r['source_line']}` |")
    lines+=['',"This inventory records source-derived surfaces and assigned proof methods only. It does not claim proof completion or production authorization.",""]
    return "\n".join(lines)
def build(root):
    paths,rows=parse_paths(root);rows+=dashboards(root,paths)+wizards(root)+wizard_steps(root)+modules(root)+tasks(root)+django_urls(root);return [classify(r) for r in rows]

# Stable test and caller-facing names.
parse_dashboards = dashboards
parse_wizards = wizards
parse_wizard_steps = wizard_steps
parse_backend_modules = modules
parse_tasks = tasks
flatten_urlpatterns = flatten
digest_rows = digest
row_payload = payload

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",type=Path,default=Path.cwd());ap.add_argument("--output-dir",type=Path,required=True);ap.add_argument("--fail-on-unmapped",action="store_true");a=ap.parse_args();root=a.root.resolve();rows=build(root);errors=validate(rows);unmapped=[r.surface_id for r in rows if r.classification=="UNMAPPED"]
    if a.fail_on_unmapped and unmapped:errors.append("UNMAPPED surfaces: "+", ".join(unmapped[:50]))
    rows_payload=payload(rows);packet={"schema_version":1,"repository_sha":repo_sha(root),"inventory_digest":digest(rows),"surface_count":len(rows),"counts":{"by_domain":dict(sorted(Counter(r["domain"] for r in rows_payload).items())),"by_classification":dict(sorted(Counter(r["classification"] for r in rows_payload).items()))},"validation_errors":errors,"surfaces":rows_payload,"scope_boundary":"Inventory and proof mapping only; no production authorization is implied."};a.output_dir.mkdir(parents=True,exist_ok=True);(a.output_dir/"production-surface-inventory.json").write_text(json.dumps(packet,indent=2,sort_keys=True)+"\n");(a.output_dir/"production-surface-inventory.md").write_text(markdown(packet))
    if errors:
        for e in errors:print("ERROR:",e,file=sys.stderr)
        return 1
    print(json.dumps({"result":"PASS","surface_count":len(rows),"inventory_digest":packet["inventory_digest"]},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
