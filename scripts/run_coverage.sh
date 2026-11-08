#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Run the tests for each application and the shared libraries with coverage.

Options:
  -h, --html    Generate an HTML coverage report
  -x, --xml     Generate an XML coverage report
  -a, --all     Generate both HTML and XML coverage reports
  --help        Show this help message
EOF
}

report_html=false
report_xml=false
for arg in "$@"; do
  case "$arg" in
    -h|--html) report_html=true ;;
    -x|--xml) report_xml=true ;;
    -a|--all) report_html=true; report_xml=true ;;
    --help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done

app_projects=()
for app_manifest in apps/*/pyproject.toml; do
  [[ -f "$app_manifest" ]] && app_projects+=("${app_manifest%/pyproject.toml}")
done

if [[ ${#app_projects[@]} -eq 0 ]]; then
  echo "No application projects found under apps/." >&2
  exit 1
fi

coverage_dir=$(mktemp -d)
trap 'rm -rf "$coverage_dir"' EXIT

echo "Running application and shared-library tests with coverage..."
for app_project in "${app_projects[@]}"; do
  app_name=$(basename "$app_project")
  test_paths=("$app_project/tests")
  [[ -d libs/core/tests ]] && test_paths+=(libs/core/tests)

  COVERAGE_FILE="$coverage_dir/.coverage.$app_name" \
    uv run --project "$app_project" pytest \
      --cov=apps \
      --cov=libs \
      --cov-report= \
      "${test_paths[@]}"
done

COVERAGE_FILE="$coverage_dir/.coverage" \
  uv run --project "${app_projects[0]}" coverage combine --keep "$coverage_dir"
COVERAGE_FILE="$coverage_dir/.coverage" \
  uv run --project "${app_projects[0]}" coverage report

if [[ "$report_html" == true ]]; then
  COVERAGE_FILE="$coverage_dir/.coverage" \
    uv run --project "${app_projects[0]}" coverage html
fi
if [[ "$report_xml" == true ]]; then
  COVERAGE_FILE="$coverage_dir/.coverage" \
    uv run --project "${app_projects[0]}" coverage xml
fi
