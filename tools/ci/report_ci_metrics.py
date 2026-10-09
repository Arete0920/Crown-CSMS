"""Read-only, bounded Actions metrics; no production or repository mutations."""
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

REPOSITORY = 'Arete0920/Crown-CSMS'


def seconds(start, end):
    if not start or not end:
        return None
    duration = (datetime.fromisoformat(end.replace('Z', '+00:00')) -
                datetime.fromisoformat(start.replace('Z', '+00:00'))).total_seconds()
    if duration < 0:
        raise ValueError('negative Actions duration')
    return duration


def summarize(run, jobs, artifacts):
    durations = [seconds(j.get('started_at'), j.get('completed_at')) for j in jobs]
    complete = all(d is not None for d in durations)
    return {
        'run_id': run['id'], 'workflow': run['name'], 'source_sha': run['head_sha'],
        'conclusion': run.get('conclusion'), 'attempt': run.get('run_attempt', 1),
        'queue_seconds': seconds(run.get('created_at'), run.get('run_started_at')),
        'runner_seconds': sum(d for d in durations if d is not None),
        'runner_time_complete': complete,
        'artifact_bytes': sum(a.get('size_in_bytes', 0) for a in artifacts),
        'failed_jobs': [j['name'] for j in jobs if j.get('conclusion') == 'failure'],
        'url': run['html_url'],
    }


def main():
    token = os.environ.get('GH_TOKEN', '').strip()
    if not token:
        raise SystemExit('GH_TOKEN is required for bounded read-only CI metrics')

    def fetch(path):
        request = Request('https://api.github.com/repos/' + REPOSITORY + '/' + path,
                          headers={'Authorization': 'Bearer ' + token,
                                   'Accept': 'application/vnd.github+json',
                                   'X-GitHub-Api-Version': '2022-11-28'})
        with urlopen(request, timeout=30) as response:
            return json.load(response)

    runs = fetch('actions/runs?event=pull_request&status=completed&per_page=20')['workflow_runs']
    records = []
    for run in runs:
        jobs = fetch(f"actions/runs/{run['id']}/jobs?per_page=100")
        artifacts = fetch(f"actions/runs/{run['id']}/artifacts?per_page=100")
        if jobs.get('total_count', 0) > 100 or artifacts.get('total_count', 0) > 100:
            raise SystemExit('Metrics page is incomplete; add pagination before increasing sample')
        records.append(summarize(run, jobs['jobs'], artifacts['artifacts']))
    report = {
        'schema_version': 1, 'generated_at': datetime.now(timezone.utc).isoformat(),
        'repository': REPOSITORY, 'sample_kind': 'latest 20 completed PR workflow runs',
        'run_count': len(records), 'unique_source_heads': len({r['source_sha'] for r in records}),
        'conclusions': dict(Counter(r['conclusion'] for r in records)),
        'runner_minutes': sum(r['runner_seconds'] for r in records) / 60,
        'artifact_bytes': sum(r['artifact_bytes'] for r in records),
        'extra_run_attempts': sum(max(0, r['attempt'] - 1) for r in records),
        'runs': records,
        'limits': 'Bounded workflow sample; not billing data, command equivalence, or a full PR history.',
    }
    Path('ci-metrics.json').write_text(json.dumps(report, indent=2) + '\n')
    summary_path = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary_path:
        with open(summary_path, 'a') as output:
            output.write(f"## CI sample\n{len(records)} completed workflow runs; "
                         f"{report['unique_source_heads']} source heads; "
                         f"{report['runner_minutes']:.1f} runner minutes; "
                         f"{report['artifact_bytes'] / 1048576:.1f} MiB artifacts.\n")
            for r in records:
                if r['failed_jobs']:
                    output.write(f"- [{r['workflow']}]({r['url']}): {', '.join(r['failed_jobs'])}\n")
    print('Wrote bounded read-only CI metrics to ci-metrics.json')


if __name__ == '__main__':
    main()
