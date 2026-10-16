#!/usr/bin/env python3
"""Read-only Azure DEV root-cause metadata. Never print secret values or raw startup logs."""
import json
import re
import subprocess
from urllib.parse import urlparse, unquote
from pathlib import Path

def az(*args, timeout=45):
    try:
        p = subprocess.run(["az", *args, "--only-show-errors"], capture_output=True, text=True, timeout=timeout)
        if p.returncode: return None
        return json.loads(p.stdout)
    except (ValueError, OSError, subprocess.TimeoutExpired):
        return None

def main():
    print("DIAGNOSTIC=READ_ONLY")
    version=az("version")
    if isinstance(version,dict):
        v=version.get("azure-cli","UNKNOWN")
        print("AZURE_CLI_VERSION="+(v if re.fullmatch(r"[0-9.]+",v) else "UNKNOWN"))
    app=az("webapp","show","-g","crown-rg","-n","crown-api-dev","-o","json")
    if not isinstance(app,dict):
        print("APP=UNAVAILABLE")
        raise SystemExit(1)
    for key in ("state","enabled","usageState","availabilityState"):
        print("APP_"+key+"="+str(app.get(key,"UNKNOWN")))
    planid=app.get("serverFarmId")
    plan=az("appservice","plan","show","--ids",planid,"-o","json") if isinstance(planid,str) else None
    sku=plan.get("sku",{}) if isinstance(plan,dict) else {}
    for key in ("name","tier","capacity"):
        print("PLAN_"+key+"="+str(sku.get(key,"UNKNOWN")))
    cfg=az("webapp","config","show","-g","crown-rg","-n","crown-api-dev","-o","json")
    if isinstance(cfg,dict):
        for key in ("alwaysOn","healthCheckPath","acrUseManagedIdentityCreds"):
            print("CONFIG_"+key+"="+str(cfg.get(key,"UNKNOWN"))[:100])
    settings=az("webapp","config","appsettings","list","-g","crown-rg","-n","crown-api-dev","-o","json")
    if isinstance(settings,list):
        d={x.get("name"):x.get("value") for x in settings if isinstance(x,dict)}
        for key in ("WEBSITES_PORT","PORT"):
            v=d.get(key)
            print("SETTING_"+key+"="+(v if isinstance(v,str) and re.fullmatch(r"\d{1,5}",v) else "ABSENT" if v is None else "HIDDEN_OR_INVALID"))
        for key in ("DATABASE_URL","SECRET_KEY","DJANGO_SECRET_KEY","CI_SMOKE_USERNAME","RUN_MIGRATE","RUN_MIGRATIONS","RUN_DEV_BOOTSTRAP"):
            v=d.get(key)
            status="ABSENT" if v is None else "KEY_VAULT_REFERENCE" if isinstance(v,str) and v.startswith("@Microsoft.KeyVault(") else "SET" if v else "EMPTY"
            print("SETTING_"+key+"="+status)
    else:
        print("SETTINGS=UNAVAILABLE")
    appid=app.get("id")
    if isinstance(appid,str) and appid.startswith("/"):
        refs=az("rest","--method","get","--url","https://management.azure.com"+appid+"/config/configreferences/appsettings?api-version=2024-11-01","-o","json")
        props={}
        if isinstance(refs,dict):
            props=refs.get("properties",{})
            if isinstance(refs.get("value"),list):
                props={str(x.get("id","")).rsplit("/",1)[-1]:x.get("properties",{}) for x in refs["value"] if isinstance(x,dict)}
        for key in ("DATABASE_URL","SECRET_KEY"):
            ref=props.get(key,{})
            status=ref.get("status","UNKNOWN") if isinstance(ref,dict) else "UNKNOWN"
            print("KEYVAULT_"+key+"="+(status if isinstance(status,str) and re.fullmatch(r"[A-Za-z0-9_]{1,80}",status) else "UNKNOWN"))
        activity=az("monitor","activity-log","list","--resource-id",appid,"--offset","2d","--max-events","150","-o","json",timeout=55)
        if isinstance(activity,list):
            print("ACTIVITY_COUNT="+str(len(activity)))
            for x in sorted(activity,key=lambda d:d.get("eventTimestamp",""))[-50:]:
                op=x.get("operationName") or {}
                st=x.get("status") or {}
                op=op.get("value","") if isinstance(op,dict) else op
                st=st.get("value","") if isinstance(st,dict) else st
                if isinstance(op,str) and re.search("start|stop|restart|write|quota",op,re.I) and re.fullmatch(r"[A-Za-z0-9/._-]{1,120}",op):
                    print("ACTIVITY="+str(x.get("eventTimestamp",""))[:20]+"|"+op+"|"+str(st)[:30])
        else:
            print("ACTIVITY=UNAVAILABLE")
        usage=az("rest","--method","get","--url","https://management.azure.com"+appid+"/usages?api-version=2024-04-01","-o","json")
        if isinstance(usage,dict) and isinstance(usage.get("value"),list):
            print("QUOTA_COUNT="+str(len(usage["value"])))
            for x in usage["value"][:20]:
                name=x.get("name") or {}
                name=name.get("value","") if isinstance(name,dict) else name
                if isinstance(name,str) and re.fullmatch(r"[A-Za-z0-9_ .-]{1,80}",name):
                    print("QUOTA="+name+"|"+str(x.get("currentValue","?"))[:20]+"|"+str(x.get("limit","?"))[:20])
        else:
            print("QUOTA=UNAVAILABLE")
    try:
        p=subprocess.run(["az","webapp","log","startup","show","-g","crown-rg","-n","crown-api-dev","--only-show-errors"],capture_output=True,text=True,timeout=60)
        if p.returncode:
            print("STARTUP_LOG=UNAVAILABLE")
            err=p.stderr.lower()
            for label,pat in {"CLI_UNSUPPORTED":r"misspelled|not recognized|unrecognized|invalid choice", "ACCESS_DENIED":r"forbidden|authorizationfailed|unauthorized|403", "NO_LOGS":r"no .*logs|not found|404"}.items():
                print("STARTUP_FETCH_"+label+"="+str(bool(re.search(pat,err))))
        else:
            print("STARTUP_LOG=COLLECTED")
            body=p.stdout.lower()
            patterns={
                "MIGRATIONS":r"migrate --check|unapplied migration|inconsistentmigrationhistory",
                "DATABASE":r"operationalerror|could not connect|connection refused|timeout expired",
                "PORT_STARTUP":r"startup time limit|failed to respond to http pings|container did not start",
                "IMAGE_PULL":r"manifest unknown|pull access denied|failed to pull image",
                "MISSING_SECRET":r"missing required environment variable",
                "GUNICORN_8000":r"listening at:.*8000|binding to 0.0.0.0:8000",
            }
            for name,pat in patterns.items():
                print("STARTUP_"+name+"="+str(bool(re.search(pat,body))))
    except (OSError,subprocess.TimeoutExpired):
        print("STARTUP_LOG=UNAVAILABLE")
    shared=az("appservice","plan","show","-g","crown-rg","-n","crown-api-plan","-o","json")
    if isinstance(shared,dict):
        sku=shared.get("sku",{})
        print("EXISTING_PLAN_SKU="+str(sku.get("name","UNKNOWN")))
        print("EXISTING_PLAN_APPS="+str(shared.get("numberOfSites","UNKNOWN")))
        metrics=az("monitor","metrics","list","--resource",shared["id"],"--metric","CpuPercentage","MemoryPercentage","--interval","PT1H","--aggregation","Average","Maximum","-o","json")
        if isinstance(metrics,dict):
            for metric in metrics.get("value",[]):
                name=(metric.get("name") or {}).get("value","")
                if name not in ("CpuPercentage","MemoryPercentage"): continue
                for series in metric.get("timeseries",[]):
                    for row in series.get("data",[])[-2:]:
                        for stat in ("average","maximum"):
                            value=row.get(stat)
                            if isinstance(value,(float,int)):
                                print("EXISTING_PLAN_"+name+"_"+stat+"="+str(round(value,2)))
    # Read schema metadata only; never log values, endpoints, errors or credentials.
    try:
        raw=d.get("DATABASE_URL","")
        if raw.startswith("@Microsoft.KeyVault(") and raw.endswith(")"):
            fields=dict(part.strip().split("=",1) for part in raw[20:-1].split(";") if "=" in part)
            if fields.get("SecretUri"):
                uri=fields["SecretUri"]
                parsed=urlparse(uri)
                if parsed.scheme!="https" or not (parsed.hostname or "").endswith(".vault.azure.net") or not parsed.path.startswith("/secrets/"):
                    raise ValueError("Invalid reference")
                resolved=az("keyvault","secret","show","--id",uri,"-o","json")
            else:
                resolved=az("keyvault","secret","show","--vault-name",fields["VaultName"],"--name",fields["SecretName"],"-o","json")
            raw=resolved.get("value","") if isinstance(resolved,dict) else ""
        parsed=urlparse(raw)
        if parsed.scheme not in ("postgres","postgresql") or parsed.hostname!="crown-pg-dev.postgres.database.azure.com":
            raise ValueError("DEV database identity not verified")
        install=subprocess.run(["python3","-m","pip","install","--quiet","psycopg[binary]==3.3.6"],capture_output=True,text=True,timeout=90)
        if install.returncode: raise RuntimeError("Driver unavailable")
        import psycopg
        with psycopg.connect(raw,connect_timeout=8,sslmode="require",options="-c default_transaction_read_only=on") as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT app, name FROM django_migrations")
                applied=set(cur.fetchall())
                pending=[]
                for path in sorted(Path("backend").glob("*/migrations/[0-9]*.py")):
                    key=(path.parents[1].name,path.stem)
                    if key not in applied: pending.append(key)
                print("READ_DB=DEV_SCHEMA_METADATA_ONLY")
                print("PENDING_MIGRATION_COUNT="+str(len(pending)))
                for appname,name in pending:
                    if re.fullmatch(r"[a-zA-Z0-9_]+",appname+name):
                        print("PENDING_MIGRATION="+appname+"."+name)
    except Exception:
        print("READ_DB=UNAVAILABLE_OR_DEV_IDENTITY_NOT_VERIFIED")
    print("DIAGNOSTIC_COMPLETE")

if __name__=="__main__":
    main()
