# AGENTS.md

## Repository Overview

`codescape-utilities` is a Python 3.12 uv workspace for a collection of Python utilities.
The workspace members are declared in the root `pyproject.toml`:

- `libs/core`: shared domain models, repositories, and services.
- `apps/audiothek-downloader`: podcast downloader tool.

The repository uses a `src` layout. Import packages through their installed package
names, not by reaching into source directories with relative filesystem assumptions.

## Source Boundaries

- Put reusable domain behavior in `libs/core/src/core`.
- Keep tests next to the package they validate, under the corresponding `tests`
  directory.
- Preserve public service and repository APIs unless the task explicitly requires a
  contract change.

## Development Conventions

- Target Python 3.12 or newer.
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

Tests use pytest and are discovered from `apps` and `libs` according to the root
`pyproject.toml`.

Use fixtures and monkeypatching to isolate services, repositories, filesystem paths,
and other external state. For CLI tests, use `typer.testing.CliRunner` and assert
exit codes plus meaningful output. Follow the existing worker test pattern when
mocking a service factory.

## Validation and Verification Commands

Run commands from the repository root with uv available.

### Install and synchronize

```sh
uv sync --locked --all-packages --all-extras --dev
```

Use this before validation or when dependencies, workspace metadata, or `uv.lock`
change. The locked form ensures the installed dependency graph matches the lockfile.

### CI checks

The authoritative CI workflow is [.github/workflows/ci.yml](.github/workflows/ci.yml).
It runs these commands after installing dependencies:

```sh
uv run ruff check .
uv run ruff format --check .
uv run --all-packages mypy .
uv run --all-packages pytest
```

Run the same sequence locally before submitting a change. Ruff lint checks rules
configured in `pyproject.toml`, Ruff format check detects unformatted files, mypy
runs strict type checking, and pytest runs the complete workspace suite with the
configured coverage threshold.

### Formatting and linting

```sh
uv run ruff check .
uv run ruff check . --fix
uv run ruff format .
uv run ruff format --check .
```

Use `--fix` and `ruff format .` only when you intend to modify files. Review the
resulting diff afterward. The CI-safe commands are the non-mutating checks.

### Type checking

```sh
uv run mypy .
uv run --all-packages mypy .
```

The workspace-wide form used by CI is `uv run --all-packages mypy .`. Use it when
validating imports and types across all workspace packages.

### Tests and coverage

```sh
uv run --all-packages pytest
uv run pytest
uv run pytest -o addopts='' <path/to/test_file.py>
uv run pytest -o addopts='' <path/to/test_file.py> -k <test_expression>
```

The first command is the CI-equivalent full suite. The second is useful for normal
local execution. The last two are focused checks that disable the repository-wide
coverage threshold so a small test slice can be evaluated quickly. The default
pytest configuration also writes terminal, XML, and HTML coverage reports.

For the downloader CLI tests, use:

```sh
uv run pytest -o addopts='' \
  apps/audiothek-downloader/tests/test_main.py
```

### Pre-commit verification

```sh
uv run pre-commit run --all-files
uv run pre-commit run --all-files --hook-stage pre-push
```

The configured hooks verify the uv lockfile, large files, JSON, TOML, YAML,
Markdown, EOFs, trailing whitespace, Ruff linting, and Ruff formatting. The
pre-push stage also runs:

```sh
uv run --all-packages pytest
```

Run pre-commit after changing Python, configuration, workflow, or lock files.

### Syntax and diagnostics

```sh
python -m compileall apps libs
uv run pytest --collect-only
```

Use `compileall` for a quick Python syntax check and `pytest --collect-only` to
verify test discovery without executing tests.

Also check the VS Code Problems view with Pylance enabled for every changed
Python file and resolve reported errors before submitting the change. Pylance
diagnostics complement -- but do not replace -- the workspace-wide mypy check.

## Change Workflow

1. Read the owning implementation and its neighboring tests before editing.
2. Make the smallest change that addresses the requested behavior.
3. Run a focused test or check immediately after the first edit.
4. Run Ruff, mypy, and relevant tests for the touched packages.
5. Run the complete CI-equivalent sequence for cross-package or shared changes.
6. Review `git diff` and ensure generated coverage artifacts or unrelated files are
   not included unintentionally.

## CI and Pull Requests

Changes targeting `main` are validated by the `code-quality` job in
[`.github/workflows/ci.yml`](.github/workflows/ci.yml) on pushes and pull requests.
The workflow uses Python 3.12, installs with `uv sync --locked`, and requires all
Ruff, mypy, and pytest checks to pass.

Do not weaken lint, type, test, or coverage settings to make a change pass. Fix the
underlying code or add focused tests for the behavior being changed.
