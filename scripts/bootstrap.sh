#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install uv before running this script." >&2
  exit 1
fi

app_projects=()
for app_manifest in apps/*/pyproject.toml; do
  [[ -f "$app_manifest" ]] && app_projects+=("${app_manifest%/pyproject.toml}")
done

if [[ ${#app_projects[@]} -eq 0 ]]; then
  echo "No application projects found under apps/." >&2
  exit 1
fi

for app_project in "${app_projects[@]}"; do
  echo "Locking dependencies for $app_project..."
  uv lock --project "$app_project"

  echo "Syncing dependencies for $app_project..."
  uv sync --locked --all-extras --dev --project "$app_project"
done

pre_commit_project=${app_projects[0]}
echo "Installing pre-commit and pre-push hooks..."
uv run --project "$pre_commit_project" pre-commit install --install-hooks
uv run --project "$pre_commit_project" pre-commit install \
  --hook-type pre-push \
  --install-hooks
