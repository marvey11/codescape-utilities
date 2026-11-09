# AGENTS.md

## Repository Overview

`codescape-utilities` contains independent Python 3.14+ uv application projects under
`apps`. Each application owns its `pyproject.toml` and `uv.lock`. Shared code lives
under `libs`; applications consume shared packages as local path dependencies.

- `apps/audiothek-downloader`: downloads ARD Audiothek podcasts.
- `libs/core`: shared worker telemetry context wrapper around the independently
  maintained Telemetry client and API.

The repository uses a `src` layout. Import packages through their installed package
names, not by reaching into source directories with relative filesystem assumptions.

## Source Boundaries

- Keep reusable domain behavior in the appropriate package under `libs`.
- Keep app-specific behavior under its application package.
- Keep tests next to the package they validate, under the corresponding `tests`
  directory.
- Preserve public service and repository APIs unless the task explicitly requires a
  contract change.
- Shared libraries are local path dependencies; do not copy their source into apps.

## Development Conventions

- Target Python 3.14 or newer.
- Use 4 spaces and a maximum line length of 88 characters.
- Use double-quoted strings, consistent with Ruff format configuration.
- Add explicit annotations for functions, parameters, and return values.
- Prefer `typing.Annotated` for Typer command arguments and options when defining
  CLI metadata.
- Use Rich `Console` instances for CLI output. Use a stderr console for warnings
  and errors and a stdout console for normal output.
- Preserve command exit codes and user-visible output unless changing the CLI
  contract is part of the task.
- Raise exceptions with `from err` when converting an underlying error at a
  boundary, such as a CLI handler.
- Avoid broad refactors and unrelated formatting changes.
- Do not add comments that merely restate the code. Add a comment only when the
  reason for a non-obvious decision cannot be expressed clearly in the code.

## Tests

Tests use pytest. Run an app's tests and the shared library tests in that app's
environment. Use fixtures and monkeypatching to isolate services, repositories,
filesystem paths, and other external state. For CLI tests, use
`typer.testing.CliRunner` and assert exit codes plus meaningful output. Follow the
existing worker test pattern when mocking a service factory.

## Validation and Verification Commands

Run commands from the repository root with uv available. Replace the project path
with the app being worked on.

### Install and synchronize

```sh
uv sync --locked --all-extras --dev --project apps/audiothek-downloader
```

Each app has an independent lockfile and depends on the shared `libs/core` package
from the local checkout. Re-lock only the affected app after changing its dependencies
or the shared package dependency metadata.

### CI checks

The authoritative CI workflow is
[.github/workflows/ci.yml](.github/workflows/ci.yml). It installs the app environment
and runs Ruff lint/format and the app-specific mypy and Pyright checks. The workflow
discovers applications from `apps/*/pyproject.toml`; its coverage job runs the full
test suite once across all apps and the shared library.

Release tags are handled by
[.github/workflows/release.yml](.github/workflows/release.yml). Git tag names use
`<application>-v<major>.<minor>.<patch>` and trigger a single app image build for
that application only. The release workflow publishes immutable version tags such
as `1.2.8`, plus floating aliases such as `1.2` and `1`.

```sh
./scripts/check-locks.sh
./scripts/run-mypy.sh
./scripts/run-pyright.sh
./scripts/run-coverage.sh
uv run --project apps/audiothek-downloader ruff check .
uv run --project apps/audiothek-downloader ruff format --check .
uv run --project apps/audiothek-downloader mypy .
uv run --project apps/audiothek-downloader pyright
```

Ruff, mypy, and Pyright use the shared root configuration. The coverage script runs
each app's tests and the shared library tests in the corresponding app environment,
then combines coverage results.
The lock and type-check scripts accept an optional app directory name to run a
targeted check; without one, they discover all app projects.

### Formatting and linting

```sh
uv run --project apps/audiothek-downloader ruff check .
uv run --project apps/audiothek-downloader ruff check . --fix
uv run --project apps/audiothek-downloader ruff format .
uv run --project apps/audiothek-downloader ruff format --check .
```

Use `--fix` and `ruff format .` only when you intend to modify files. Review the
resulting diff afterward. The CI-safe commands are the non-mutating checks.

### Type checking

```sh
uv run --project apps/audiothek-downloader mypy .
uv run --project apps/audiothek-downloader pyright
```

### Tests and coverage

```sh
./scripts/run-coverage.sh
uv run --project apps/audiothek-downloader pytest
uv run --project apps/audiothek-downloader pytest -o addopts='' \
  apps/audiothek-downloader/tests/test_main.py
```

The coverage script runs the complete app and shared library suites. It accepts
`--html`, `--xml`, or `--all` to generate coverage reports. Focused test commands
can clear repository-wide pytest options with `-o addopts=''`.

### Pre-commit verification

```sh
uv run --project apps/audiothek-downloader pre-commit run --all-files
uv run --project apps/audiothek-downloader pre-commit run --all-files --hook-stage pre-push
```

The configured hooks verify per-app uv lockfiles, large files, JSON, TOML, YAML,
Markdown, GitHub Actions workflows, EOFs, trailing whitespace, Ruff linting and
formatting, mypy, and Pyright. The pre-push stage also runs
`./scripts/run-coverage.sh`. Bash scripts are checked by ShellCheck.

### Syntax and diagnostics

```sh
python -m compileall apps libs
uv run --project apps/audiothek-downloader pytest --collect-only
```

Also check the VS Code Problems view with Pylance enabled for every changed Python
file and resolve reported errors before submitting a change. Pylance diagnostics
complement -- but do not replace -- the mypy check run in the app environment.

## Change Workflow

1. Read the owning implementation and its neighboring tests before editing.
2. Make the smallest change that addresses the requested behavior.
3. Run a focused test or check immediately after the first edit.
4. Run Ruff, mypy, Pyright, and relevant tests for the touched packages.
5. Run the complete CI-equivalent sequence for cross-package or shared changes.
6. Review `git diff` and ensure generated coverage artifacts or unrelated files are
   not included unintentionally.

## CI and Pull Requests

Changes targeting `main` are validated by the `code-quality` and coverage jobs in
[.github/workflows/ci.yml](.github/workflows/ci.yml). The workflow uses Python 3.14,
installs each app with `uv sync --locked`, and requires Ruff, mypy, Pyright, and
pytest checks to pass. App release tags use the form
`<application>-v<major>.<minor>.<patch>` and must point to a commit on `main`.
Adding an app requires a `pyproject.toml`, `uv.lock`, and Dockerfile under its
`apps/<application>/` directory for CI checks and image builds to include it.

Do not weaken lint, type, test, or coverage settings to make a change pass. Fix the
underlying code or add focused tests for the behavior being changed.
