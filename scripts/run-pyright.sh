#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

if [[ $# -gt 1 ]]; then
    echo "Usage: $(basename "$0") [APP]" >&2
    exit 2
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required. Install uv before running this script." >&2
    exit 1
fi

app_projects=()
if [[ $# -eq 1 ]]; then
    app_project="apps/$1"
    if [[ "$1" == */* || "$1" == "." || "$1" == ".." ||
        ! -f "$app_project/pyproject.toml" ]]; then
        echo "No application project found for '$1'." >&2
        exit 1
    fi
    app_projects+=("$app_project")
else
    for app_manifest in apps/*/pyproject.toml; do
        [[ -f "$app_manifest" ]] || continue
        app_projects+=("${app_manifest%/pyproject.toml}")
    done

    if [[ ${#app_projects[@]} -eq 0 ]]; then
        echo "No application projects found under apps/." >&2
        exit 1
    fi
fi

for app_project in "${app_projects[@]}"; do
    echo "Running Pyright for $app_project..."
    pyright_paths=("$app_project")
    [[ -d libs/core ]] && pyright_paths+=(libs/core)
    uv run --project "$app_project" pyright "${pyright_paths[@]}"
done
