#!/usr/bin/env bash
set -euo pipefail

# Repair CROWN GitHub Actions -> Microsoft Entra workload identity federation
# for the authoritative Crown-CSMS repository after immutable GitHub OIDC
# subjects are enabled.
#
# Usage:
#   AZURE_CLIENT_ID=<app-client-id> ./scripts/execution/repair_entra_github_oidc_federation.sh
#   AZURE_CLIENT_ID=<app-client-id> ./scripts/execution/repair_entra_github_oidc_federation.sh --apply
#
# Audit mode is the default. --apply creates the required immutable federated
# credentials, verifies them, then removes only exact legacy Crown-CSMS
# name-only subjects that are superseded by the immutable subjects.

MODE="audit"
if [[ "${1:-}" == "--apply" ]]; then
  MODE="apply"
elif [[ -n "${1:-}" ]]; then
  echo "ERROR: unsupported argument '$1' (expected --apply or no argument)" >&2
  exit 2
fi

: "${AZURE_CLIENT_ID:?ERROR: AZURE_CLIENT_ID must contain the Entra application client ID}"

OWNER_NAME="${CROWN_GITHUB_OWNER_NAME:-Arete0920}"
OWNER_ID="${CROWN_GITHUB_OWNER_ID:-318664923}"
REPO_NAME="${CROWN_GITHUB_REPO_NAME:-Crown-CSMS}"
REPO_ID="${CROWN_GITHUB_REPO_ID:-1339719218}"
ISSUER="https://token.actions.githubusercontent.com"
AUDIENCE="api://AzureADTokenExchange"

IMMUTABLE_PREFIX="repo:${OWNER_NAME}@${OWNER_ID}/${REPO_NAME}@${REPO_ID}"
LEGACY_PREFIX="repo:${OWNER_NAME}/${REPO_NAME}"

DESIRED_NAMES=(
  "github-crown-csms-main"
  "github-crown-csms-production"
  "github-crown-csms-dev"
)
DESIRED_SUBJECTS=(
  "${IMMUTABLE_PREFIX}:ref:refs/heads/main"
  "${IMMUTABLE_PREFIX}:environment:production"
  "${IMMUTABLE_PREFIX}:environment:dev"
)
LEGACY_SUBJECTS=(
  "${LEGACY_PREFIX}:ref:refs/heads/main"
  "${LEGACY_PREFIX}:environment:production"
  "${LEGACY_PREFIX}:environment:dev"
)

command -v az >/dev/null 2>&1 || {
  echo "ERROR: Azure CLI (az) is required" >&2
  exit 1
}
command -v jq >/dev/null 2>&1 || {
  echo "ERROR: jq is required" >&2
  exit 1
}

az account show --output none >/dev/null 2>&1 || {
  echo "ERROR: Azure CLI is not authenticated. Run az login first." >&2
  exit 1
}

APP_OBJECT_ID="$(az ad app show --id "$AZURE_CLIENT_ID" --query id -o tsv --only-show-errors)"
[[ -n "$APP_OBJECT_ID" ]] || {
  echo "ERROR: Entra application could not be resolved from AZURE_CLIENT_ID" >&2
  exit 1
}

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
current="$tmpdir/federated-credentials.json"

refresh() {
  az ad app federated-credential list \
    --id "$AZURE_CLIENT_ID" \
    --output json \
    --only-show-errors > "$current"
}

has_exact_subject() {
  local subject="$1"
  jq -e \
    --arg issuer "$ISSUER" \
    --arg subject "$subject" \
    --arg audience "$AUDIENCE" \
    'any(.[]; .issuer == $issuer and .subject == $subject and ((.audiences // []) | index($audience) != null))' \
    "$current" >/dev/null
}

create_subject() {
  local name="$1"
  local subject="$2"
  local payload="$tmpdir/${name}.json"

  jq -n \
    --arg name "$name" \
    --arg issuer "$ISSUER" \
    --arg subject "$subject" \
    --arg audience "$AUDIENCE" \
    '{name:$name, issuer:$issuer, subject:$subject, audiences:[$audience]}' > "$payload"

  az ad app federated-credential create \
    --id "$AZURE_CLIENT_ID" \
    --parameters "@$payload" \
    --output none \
    --only-show-errors
}

refresh

echo "CROWN Entra OIDC federation audit"
echo "  repository: ${OWNER_NAME}/${REPO_NAME} (${REPO_ID})"
echo "  application object id: $APP_OBJECT_ID"
echo "  mode: $MODE"
echo "  issuer: $ISSUER"
echo "  audience: $AUDIENCE"
echo

missing=0
for i in "${!DESIRED_SUBJECTS[@]}"; do
  name="${DESIRED_NAMES[$i]}"
  subject="${DESIRED_SUBJECTS[$i]}"
  if has_exact_subject "$subject"; then
    echo "PASS  $name"
    echo "      $subject"
  else
    missing=$((missing + 1))
    echo "MISS  $name"
    echo "      $subject"
    if [[ "$MODE" == "apply" ]]; then
      create_subject "$name" "$subject"
      echo "CREATE $name"
    fi
  fi
done

if [[ "$MODE" == "audit" ]]; then
  echo
  if (( missing > 0 )); then
    echo "RESULT: $missing required immutable federated credential(s) missing."
    echo "Run again with --apply using an Entra identity authorized to manage this app registration."
    exit 1
  fi
  echo "RESULT: all required immutable federated credentials are present."
  exit 0
fi

# Refresh after creation and fail closed before deleting anything legacy.
refresh
for subject in "${DESIRED_SUBJECTS[@]}"; do
  has_exact_subject "$subject" || {
    echo "ERROR: immutable federation verification failed for: $subject" >&2
    exit 1
  }
done

echo
echo "All required immutable federated credentials verified."
echo "Pruning only exact superseded legacy Crown-CSMS subjects..."

for legacy_subject in "${LEGACY_SUBJECTS[@]}"; do
  mapfile -t stale_ids < <(
    jq -r \
      --arg issuer "$ISSUER" \
      --arg subject "$legacy_subject" \
      '.[] | select(.issuer == $issuer and .subject == $subject) | (.id // .name)' \
      "$current"
  )

  for stale_id in "${stale_ids[@]}"; do
    [[ -n "$stale_id" ]] || continue
    az ad app federated-credential delete \
      --id "$AZURE_CLIENT_ID" \
      --federated-credential-id "$stale_id" \
      --only-show-errors
    echo "DELETE legacy subject: $legacy_subject"
  done
done

refresh

# Final proof: all desired subjects exist; no exact legacy Crown-CSMS subjects remain.
for subject in "${DESIRED_SUBJECTS[@]}"; do
  has_exact_subject "$subject" || {
    echo "ERROR: final verification lost required immutable subject: $subject" >&2
    exit 1
  }
done

legacy_remaining="$(
  jq -r \
    --arg issuer "$ISSUER" \
    --arg s1 "${LEGACY_SUBJECTS[0]}" \
    --arg s2 "${LEGACY_SUBJECTS[1]}" \
    --arg s3 "${LEGACY_SUBJECTS[2]}" \
    '[.[] | select(.issuer == $issuer and (.subject == $s1 or .subject == $s2 or .subject == $s3))] | length' \
    "$current"
)"

[[ "$legacy_remaining" == "0" ]] || {
  echo "ERROR: legacy Crown-CSMS federated credentials remain after cleanup" >&2
  exit 1
}

echo
echo "RESULT: Entra federation cleanup complete."
echo "Required immutable subjects:"
for subject in "${DESIRED_SUBJECTS[@]}"; do
  echo "  - $subject"
done
