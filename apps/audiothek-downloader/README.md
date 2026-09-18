# Audiothek Podcast Downloader

Download new episodes from ARD Audiothek program sets and keep a manifest of
completed downloads.

## Usage

Install the workspace with `uv sync`, then run:

```sh
uv run --package audiothek-downloader audiothek-downloader \
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
