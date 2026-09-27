#!/usr/bin/env bash

set -euo pipefail

REPO="Arete0920/Crown-CSMS"

echo "==> Open Pull Requests in ${REPO}"
echo "------------------------------------------------------------"
gh pr list --repo "$REPO" --state open \
  --json number,title,author,createdAt \
  --template '{{range .}}#{{.number}} | {{.author.login}} | {{.createdAt | timeago}} | {{.title}}{{"\n"}}{{end}}'

echo
echo "==> Updating repo description, website, and topics..."

gh api --method PATCH "/repos/${REPO}" \
  --field description="Crown - Cloud-based school management SaaS purpose-built for Christian and faith-based private schools. Django · React · PostgreSQL · Azure." \
  --field homepage="https://crownschoolsystem.com"

gh api --method PUT "/repos/${REPO}/topics" \
  --field names='["christian-school","school-management","edtech","saas","django","react","ferpa","faith-based"]'

echo "==> Repo metadata updated."
echo "ACTION REQUIRED: review the current open PR set and close only confirmed duplicates."