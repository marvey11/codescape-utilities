# Codescape Utilities

A uv workspace of Python utilities for services on the Achterhus home server.

## Applications and libraries

- `apps/audiothek-downloader` downloads new episodes from ARD Audiothek programme
  sets and records completed downloads in a manifest. See its
  [README](apps/audiothek-downloader/README.md) for CLI, Docker and systemd usage.
- `libs/core` contains shared domain models, repositories and services.

## Development

Requirements: Python 3.12 or newer and [uv](https://docs.astral.sh/uv/).

From the repository root, synchronise the workspace and run the checks:

```sh
uv sync --locked --all-packages --all-extras --dev
uv run ruff check .
uv run ruff format --check .
uv run --all-packages mypy .
uv run --all-packages pytest
```

The downloader reports lifecycle status and metrics to the Telemetry API when it is
launched with a valid `SERVICE_RUN_ID` registered by the service orchestrator. Direct
CLI and systemd runs without an orchestrator run ID continue downloading without
telemetry reporting.
