# Audiothek Podcast Downloader

Download new episodes from ARD Audiothek program sets and keep a manifest of
completed downloads.

## Usage

From the repository root, install this application's environment and run:

```sh
uv sync --project apps/audiothek-downloader
uv run --project apps/audiothek-downloader audiothek-downloader \
    --application-data-dir /path/to/application-data \
    --podcast-storage-dir /path/to/podcasts
```

The application data directory must contain `metadata.json`. Each metadata entry
uses a podcast URN as its key and a `target_dir` value relative to the podcast
storage directory:

```json
{
    "urn:ard:podcast:example": {
         "target_dir": "Example Podcast"
    }
}
```

The downloader creates `manifest.json` in the application data directory and
records each successfully downloaded episode there. Existing manifest entries
are skipped on later runs.

This app has an independent `uv.lock`; it consumes the shared `core` package from
`libs/core` as a local dependency. Run the app's tests and tools using
`--project apps/audiothek-downloader` from the repository root.

## Dockerised Application

The application is available as a Docker image at
`ghcr.io/marvey11/codescape-utilities/audiothek-downloader:latest`. Versioned images
are published from tags such as `audiothek-downloader-v1.2.3` and use the app
version as the image tag.
