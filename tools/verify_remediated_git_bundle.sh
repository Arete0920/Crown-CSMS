#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  verify_remediated_git_bundle.sh --repo PATH --forbidden-path PATH
  verify_remediated_git_bundle.sh --bundle FILE --forbidden-path PATH

Validates that a repository or bundle can be restored and that the forbidden
path is absent from every retained ref and reachable history. It does not
perform key rotation or secret scanning.
EOF
}

repo=""
bundle=""
forbidden_path=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo)
      repo="${2:-}"
      shift 2
      ;;
    --bundle)
      bundle="${2:-}"
      shift 2
      ;;
    --forbidden-path)
      forbidden_path="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ -z "$forbidden_path" ]; then
  echo "ERROR: --forbidden-path is required" >&2
  exit 2
fi

if { [ -n "$repo" ] && [ -n "$bundle" ]; } || { [ -z "$repo" ] && [ -z "$bundle" ]; }; then
  echo "ERROR: provide exactly one of --repo or --bundle" >&2
  exit 2
fi

cleanup_dir=""
cleanup() {
  if [ -n "$cleanup_dir" ] && [ -d "$cleanup_dir" ]; then
    rm -rf "$cleanup_dir"
  fi
}
trap cleanup EXIT

if [ -n "$bundle" ]; then
  if [ ! -f "$bundle" ]; then
    echo "ERROR: bundle not found: $bundle" >&2
    exit 2
  fi
  bundle="$(realpath "$bundle")"
  cleanup_dir="$(mktemp -d)"
  git init --bare "$cleanup_dir/verify.git" >/dev/null
  git -C "$cleanup_dir/verify.git" bundle verify "$bundle" >/dev/null
  git clone --mirror "$bundle" "$cleanup_dir/repo.git" >/dev/null 2>&1
  repo="$cleanup_dir/repo.git"
fi

if [ ! -d "$repo" ]; then
  echo "ERROR: repository not found: $repo" >&2
  exit 2
fi

if ! git -C "$repo" rev-parse --git-dir >/dev/null 2>&1; then
  echo "ERROR: not a Git repository: $repo" >&2
  exit 2
fi

if [ "$(git -C "$repo" rev-parse --is-shallow-repository)" != "false" ]; then
  echo "ERROR: complete history is required; shallow repositories are not accepted" >&2
  exit 1
fi

# Replacement objects and grafts can hide original ancestry from traversal.
replacement_refs="$(git -C "$repo" for-each-ref --format='%(refname)' refs/replace)"
grafts_path="$(git -C "$repo" rev-parse --path-format=absolute --git-path info/grafts)"
if [ -n "$replacement_refs" ] || [ -s "$grafts_path" ]; then
  echo "ERROR: replacement refs or grafts can mask retained history" >&2
  exit 1
fi

# A failed traversal must not become an empty, apparently clean input stream.
# Check connectivity before interpreting a missing path as proof of absence.
git -C "$repo" fsck --full --no-reflogs --no-dangling >/dev/null
ref_output="$(git -C "$repo" for-each-ref --format='%(refname)')"
if [ -z "$ref_output" ]; then
  echo "ERROR: no retained refs found" >&2
  exit 1
fi
mapfile -t refs <<< "$ref_output"
if [ "${#refs[@]}" -eq 0 ]; then
  echo "ERROR: no retained branch, tag, or remote refs found" >&2
  exit 1
fi

found=0
for ref in "${refs[@]}"; do
  if git -C "$repo" cat-file -e "$ref:$forbidden_path" 2>/dev/null; then
    echo "ERROR: forbidden path exists at $ref" >&2
    found=1
  fi
done

commits="$(git -C "$repo" rev-list --all HEAD)"
while IFS= read -r commit; do
  if git -C "$repo" cat-file -e "$commit:$forbidden_path" 2>/dev/null; then
    echo "ERROR: forbidden path is reachable from commit $commit" >&2
    found=1
    break
  fi
done <<< "$commits"

if [ "$found" -ne 0 ]; then
  exit 1
fi

head_sha="$(git -C "$repo" rev-parse HEAD 2>/dev/null || true)"
commit_count="$(git -C "$repo" rev-list --all --count)"
branch_count="$(git -C "$repo" for-each-ref --format='%(refname)' refs/heads | wc -l | tr -d ' ')"
tag_count="$(git -C "$repo" for-each-ref --format='%(refname)' refs/tags | wc -l | tr -d ' ')"
ref_count="${#refs[@]}"

printf 'verification=success\n'
printf 'forbidden_path=%s\n' "$forbidden_path"
printf 'head_sha=%s\n' "$head_sha"
printf 'commit_count=%s\n' "$commit_count"
printf 'branch_count=%s\n' "$branch_count"
printf 'tag_count=%s\n' "$tag_count"
printf 'retained_ref_count=%s\n' "$ref_count"
printf 'boundary=This verifier does not prove key revocation, replacement, downstream trust updates, or all-ref secret scanning.\n'
