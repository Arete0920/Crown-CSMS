#!/usr/bin/env python3
import json
import os
import re
import sys
import urllib.error
import urllib.request

API_VERSION = "2022-11-28"
ISSUE_REFERENCE = re.compile(
    r"(?im)\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?|refs?|tracks?)\s+#(\d+)\b"
)


def api_get(url, token):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "crown-pr-preflight",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def tracked_issues(body):
    return {int(value) for value in ISSUE_REFERENCE.findall(body or "")}


def load_event(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main():
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    repository = os.environ.get("GITHUB_REPOSITORY")
    token = os.environ.get("GITHUB_TOKEN")

    if not event_path or not repository or not token:
        print("PR preflight requires GITHUB_EVENT_PATH, GITHUB_REPOSITORY, and GITHUB_TOKEN.", file=sys.stderr)
        return 2

    event = load_event(event_path)
    current = event.get("pull_request")
    if not current:
        print("PR preflight skipped: event does not contain a pull_request payload.")
        return 0

    current_number = int(current["number"])
    current_issues = tracked_issues(current.get("body"))
    if not current_issues:
        print(f"PR #{current_number}: no tracked issue reference found; duplicate-work-item check skipped.")
        return 0

    owner, repo = repository.split("/", 1)
    duplicates = []
    page = 1

    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state=open&per_page=100&page={page}"
        pulls = api_get(url, token)
        if not pulls:
            break

        for pull in pulls:
            number = int(pull["number"])
            if number == current_number:
                continue
            overlap = sorted(current_issues & tracked_issues(pull.get("body")))
            if overlap:
                duplicates.append(
                    {
                        "number": number,
                        "url": pull.get("html_url"),
                        "issues": overlap,
                    }
                )

        if len(pulls) < 100:
            break
        page += 1

    if duplicates:
        print(
            f"PR #{current_number} conflicts with other open PRs for the same tracked issue(s):",
            file=sys.stderr,
        )
        for duplicate in duplicates:
            issues = ", ".join(f"#{issue}" for issue in duplicate["issues"])
            print(
                f"- PR #{duplicate['number']} ({duplicate['url']}): {issues}",
                file=sys.stderr,
            )
        print(
            "Close or supersede the duplicate PR before continuing. One authoritative PR per tracked issue is required.",
            file=sys.stderr,
        )
        return 1

    issues = ", ".join(f"#{issue}" for issue in sorted(current_issues))
    print(f"PR #{current_number}: duplicate-work-item preflight PASS for {issues}.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"GitHub API request failed: HTTP {exc.code}: {detail}", file=sys.stderr)
        raise SystemExit(2)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"PR preflight failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
