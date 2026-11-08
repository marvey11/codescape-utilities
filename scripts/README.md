# Utility Scripts

Run scripts from the repository root.

- `check_locks.sh` verifies that every app lockfile matches its project manifest.
- `run_coverage.sh` runs each app test suite together with `libs/core` tests in
  that app's uv environment, then combines coverage. Pass `--html`, `--xml`, or
  `--all` to generate reports.
