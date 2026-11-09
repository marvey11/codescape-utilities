# Codescape Utilities

A collection of Python applications for services on the Achterhus home server. Each
application has its own uv project and lockfile, so its dependencies can be resolved
and versioned independently. Shared Python code lives in `libs` and is consumed by
applications as a local package dependency.

## Applications and libraries

- `apps/audiothek-downloader` downloads new episodes from ARD Audiothek programme
  sets and records completed downloads in a manifest. See its
  [README](apps/audiothek-downloader/README.md) for CLI and Docker usage.
- `libs/core` provides the shared Telemetry context wrapper used by worker services.
  The Telemetry client and API are maintained independently.

Each application has its own usage instructions, `pyproject.toml`, `uv.lock`, and
Dockerfile. CI discovers applications from `apps/*/pyproject.toml`, checks each
project, and builds its image. Run an application's commands from the repository
root with the project path, for example:

```sh
uv sync --project apps/audiothek-downloader
uv run --project apps/audiothek-downloader audiothek-downloader --help
```

Application version tags use the form `<application>-v<version>`, for example
`audiothek-downloader-v1.2.3`. A release tag must point to a commit on `main` and
identify an app with both a `pyproject.toml` and a Dockerfile. The GitHub release
workflow creates immutable Docker images for the full semantic version, plus
floating aliases for the major and major.minor variants. The images expect input
and destination directories to be mounted inside the container.

The regular `main`-branch Docker image is published from the CI workflow and
updated continuously as the branch advances. Release tags are handled separately
in the release workflow so only the tagged application’s image is built and
published.

## Repository checks

The support scripts discover application projects automatically. Run lock and type
checks for every app, or pass an app directory name to target one project:

```sh
./scripts/check-locks.sh
./scripts/run-mypy.sh
./scripts/run-pyright.sh
./scripts/run-mypy.sh audiothek-downloader
./scripts/run-pyright.sh audiothek-downloader
./scripts/run-coverage.sh
```

When adding an application, provide its `pyproject.toml`, lockfile, tests, and
Dockerfile. CI and the repository-wide checks will include it automatically.
