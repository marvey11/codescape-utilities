# Codescape Utilities

A uv workspace of Python utilities for services on the Achterhus home server.

## Applications and libraries

- `apps/audiothek-downloader` downloads new episodes from ARD Audiothek programme
  sets and records completed downloads in a manifest. See its
  [README](apps/audiothek-downloader/README.md) for CLI and Docker usage.
- `libs/core` contains shared domain models, repositories and services.

Each application has its own usage instructions and Dockerfile. The images expect input and destination directories to be mounted inside the container.
