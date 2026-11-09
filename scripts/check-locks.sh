#!/usr/bin/env bash
set -euo pipefail

# Determine which apps to check
if [ $# -gt 0 ]; then
    APPS=("$1")
    # Validate that the requested app directory exists
    if [ ! -d "apps/${APPS[0]}" ]; then
        echo "Error: App directory 'apps/${APPS[0]}' does not exist." >&2
        exit 1
    fi
    # Ensure a pyproject.toml exists within the app directory
    if [ ! -f "apps/${APPS[0]}/pyproject.toml" ]; then
        echo "Error: No pyproject.toml found in 'apps/${APPS[0]}'." >&2
        exit 1
    fi
else
    # Dynamically discover all apps containing a pyproject.toml if no argument is passed
    APPS=()
    for dir in apps/*/; do
        if [ -d "$dir" ] && [ -f "${dir}pyproject.toml" ]; then
            APPS+=("$(basename "$dir")")
        fi
    done

    if [ ${#APPS[@]} -eq 0 ]; then
        echo "No application projects found under apps/." >&2
        exit 1
    fi
fi

for app in "${APPS[@]}"; do
    app_project="apps/$app"
    echo "Checking lockfile for $app_project..."
    uv lock --check --project "$app_project"
done
