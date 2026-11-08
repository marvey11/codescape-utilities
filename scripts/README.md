# Utility Scripts

Run scripts from the repository root.

- `bootstrap.sh` locks and syncs every app's uv environment, then installs the
  pre-commit and pre-push Git hooks. Install `uv` first, then run
  `./scripts/bootstrap.sh` after cloning.
- `check_locks.sh` verifies that every app lockfile matches its project manifest.
- `run_coverage.sh` runs each app test suite together with `libs/core` tests in
  that app's uv environment, then combines coverage. Pass `--html`, `--xml`, or
  `--all` to generate reports.
