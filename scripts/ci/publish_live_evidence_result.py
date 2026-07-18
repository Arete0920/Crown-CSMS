#!/usr/bin/env python3
import json, os, pathlib, urllib.request

repo = os.environ['GITHUB_REPOSITORY']
token = os.environ['GITHUB_TOKEN']
run_id = os.environ['GITHUB_RUN_ID']
sha = os.environ.get('CERTIFIED_SOURCE_SHA') or os.environ.get('GITHUB_SHA','')
run_url = f"https://github.com/{repo}/actions/runs/{run_id}"
summary_path = pathlib.Path('audit-artifacts/live-runtime-certification/current/certification-summary.md')
tenant_path = pathlib.Path