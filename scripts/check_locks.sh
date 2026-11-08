#!/usr/bin/env bash
set -euo pipefail

app_manifests=(apps/*/pyproject.toml)
if [[ ! -e "${app_manifests[0]}" ]]; then
  echo "No application projects found under apps/." >&2
  exit 1
fi

for app_manifest in "${app_manifests[@]}"; do
  app_project=${app_manifest%/pyproject.toml}
  echo "Checking lockfile for $app_project..."
  uv lock --check --project "$app_project"
done
